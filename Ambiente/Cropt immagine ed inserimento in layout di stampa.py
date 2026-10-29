import os
import tempfile
import numpy as np
from difflib import SequenceMatcher
from qgis.core import (
    QgsProject, 
    QgsLayoutItemPicture, 
    QgsUnitTypes, 
    QgsLayoutPoint, 
    QgsLayoutSize
)
from qgis.PyQt.QtWidgets import (
    QFileDialog, 
    QApplication, 
    QMessageBox, 
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QLabel, 
    QRubberBand
)
from qgis.PyQt.QtCore import Qt, QRect, QPoint, QSize
from qgis.PyQt.QtGui import QPixmap
from qgis.utils import iface
from PIL import Image


def run():
    """Punto d'ingresso obbligatorio richiesto da QGIS / maxxi-cloud."""
    parent = iface.mainWindow() if iface else None

    # 1. Seleziona tutti i file in blocco
    input_paths, _ = QFileDialog.getOpenFileNames(
        parent, 
        "Seleziona tutte le immagini delle tavole", 
        "", 
        "Tutti i file (*.*);;File immagine (*.png *.jpg *.jpeg *.tiff *.bmp)"
    )

    if not input_paths:
        print("Nessun file selezionato.")
        return

    # 2. Seleziona la cartella di destinazione
    output_dir = QFileDialog.getExistingDirectory(
        parent, 
        "Seleziona la cartella di destinazione per i PNG puliti"
    )
    
    if not output_dir:
        print("Selezione della cartella di output annullata.")
        return

    success_count = 0
    fail_count = 0
    skipped_count = 0
    global_last_box = None  # Memorizza l'ultimo ritaglio effettuato

    # Classe personalizzata per la gestione del rettangolo di selezione
    class CropLabel(QLabel):
        def __init__(self, parent_lbl=None):
            super().__init__(parent_lbl)
            self.origin = QPoint()
            self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
            self.rect_selected = None

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.origin = event.pos()
                self.rubberBand.setGeometry(QRect(self.origin, QSize()))
                self.rubberBand.show()

        def mouseMoveEvent(self, event):
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

        def mouseReleaseEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.rect_selected = self.rubberBand.geometry()

    # Finestra di dialogo interattiva grande e massimizzata
    class InteractiveCropDialog(QDialog):
        def __init__(self, image_path, last_box_available, parent_dlg=None):
            super().__init__(parent_dlg)
            base_filename = os.path.basename(image_path)
            self.setWindowTitle(f"Ritaglia legenda per: {base_filename}")
            self.image_path = image_path
            self.original_img = Image.open(image_path).convert("RGB")
            self.orig_w, self.orig_h = self.original_img.size
            self.last_box_available = last_box_available
            
            self.showMaximized()
            
            screen = QApplication.primaryScreen().geometry() if QApplication.primaryScreen() else QRect(0, 0, 1920, 1080)
            max_w, max_h = screen.width() - 100, screen.height() - 200
            
            self.scale_factor = min(max_w / self.orig_w, max_h / self.orig_h, 1.0)
            self.disp_w = int(self.orig_w * self.scale_factor)
            self.disp_h = int(self.orig_h * self.scale_factor)
            
            pil_resized = self.original_img.resize((self.disp_w, self.disp_h), Image.Resampling.LANCZOS)
            
            self.temp_preview_path = os.path.join(tempfile.gettempdir(), f"qgis_preview_{os.getpid()}.png")
            pil_resized.save(self.temp_preview_path)
            
            self.initUI()
            
        def initUI(self):
            layout = QVBoxLayout(self)
            
            instruction = QLabel("👉 Trascina il mouse per creare il rettangolo (rimarrà selezionato al rilascio), oppure usa il pulsante per ripetere l'ultimo ritaglio.")
            instruction.setWordWrap(True)
            instruction.setStyleSheet("font-weight: bold; font-size: 12pt; color: #2C3E50; margin-bottom: 5px;")
            layout.addWidget(instruction)
            
            self.image_label = CropLabel()
            self.pixmap = QPixmap(self.temp_preview_path)
            self.image_label.setPixmap(self.pixmap)
            self.image_label.setFixedSize(self.disp_w, self.disp_h)
            self.image_label.setCursor(Qt.CrossCursor)
            layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
            
            btn_layout = QHBoxLayout()
            
            self.btn_confirm = QPushButton("Conferma Taglio")
            self.btn_confirm.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 12px; font-size: 11pt;")
            self.btn_confirm.clicked.connect(self.accept_crop)
            btn_layout.addWidget(self.btn_confirm)
            
            if self.last_box_available:
                self.btn_same = QPushButton("Usa stesso ritaglio precedente")
                self.btn_same.setStyleSheet("background-color: #2980B9; color: white; font-weight: bold; padding: 12px; font-size: 11pt;")
                self.btn_same.clicked.connect(self.accept_same_crop)
                btn_layout.addWidget(self.btn_same)
            
            self.btn_skip = QPushButton("Salta questo file")
            self.btn_skip.setStyleSheet("background-color: #E74C3C; color: white; padding: 12px; font-size: 11pt;")
            self.btn_skip.clicked.connect(self.reject)
            btn_layout.addWidget(self.btn_skip)
            
            layout.addLayout(btn_layout)
            self.final_box = None
            
        def accept_crop(self):
            if self.image_label.rect_selected and self.image_label.rect_selected.width() > 10 and self.image_label.rect_selected.height() > 10:
                r = self.image_label.rect_selected
                x1 = int(r.x() / self.scale_factor)
                y1 = int(r.y() / self.scale_factor)
                x2 = int((r.x() + r.width()) / self.scale_factor)
                y2 = int((r.y() + r.height()) / self.scale_factor)
                
                x1 = max(0, min(x1, self.orig_w))
                y1 = max(0, min(y1, self.orig_h))
                x2 = max(0, min(x2, self.orig_w))
                y2 = max(0, min(y2, self.orig_h))
                
                if x2 > x1 and y2 > y1:
                    self.final_box = (x1, y1, x2, y2)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Attenzione", "Selezione non valida. Riprova.")
            else:
                QMessageBox.warning(self, "Attenzione", "Trascina e rilascia un rettangolo sull'immagine prima di confermare!")

        def accept_same_crop(self):
            self.final_box = self.last_box_available
            self.accept()
                
        def closeEvent(self, event):
            if os.path.exists(self.temp_preview_path):
                try:
                    os.remove(self.temp_preview_path)
                except:
                    pass
            super().closeEvent(event)

    # Ciclo sui file selezionati
    for input_path in input_paths:
        try:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_filename = f"LEGENDA_{base_name}.png"
            output_path = os.path.join(output_dir, output_filename)
            
            dialog = InteractiveCropDialog(input_path, global_last_box, parent)
            result = dialog.exec_()
            
            if result == QDialog.Accepted and dialog.final_box:
                global_last_box = dialog.final_box
                
                img = Image.open(input_path).convert("RGB")
                cropped_img = img.crop(dialog.final_box)
                cw, ch = cropped_img.size
                pixels = cropped_img.load()
                bg_color = (255, 255, 255)
                
                for y in range(ch):
                    for x in range(cw):
                        cr, cg, cb = pixels[x, y]
                        if abs(cr - cg) < 15 and abs(cg - cb) < 15 and cr > 160:
                            pixels[x, y] = bg_color
                            
                def is_row_empty(y_c):
                    for x in range(cw):
                        if pixels[x, y_c] != bg_color:
                            return False
                    return True

                def is_col_empty(x_c):
                    for y in range(ch):
                        if pixels[x_c, y] != bg_color:
                            return False
                    return True

                valid_y = []
                whit_count_y = 0
                for y in range(ch):
                    if is_row_empty(y):
                        whit_count_y += 1
                        if whit_count_y <= 24:
                            valid_y.append(y)
                        else:
                            whit_count_y = 0
                            valid_y.append(y)
                    else:
                        whit_count_y = 0
                        valid_y.append(y)

                if valid_y:
                    temp_img = Image.new("RGB", (cw, len(valid_y)), bg_color)
                    temp_pix = temp_img.load()
                    for new_y, old_y in enumerate(valid_y):
                        for x in range(cw):
                            temp_pix[x, new_y] = pixels[x, old_y]
                    cropped_img = temp_img
                    cw, ch = cropped_img.size
                    pixels = cropped_img.load()

                valid_x = []
                whit_count_x = 0
                for x in range(cw):
                    if is_col_empty(x):
                        whit_count_x += 1
                        if whit_count_x <= 25:
                            valid_x.append(x)
                        else:
                            whit_count_x = 0
                            valid_x.append(x)
                    else:
                        whit_count_x = 0
                        valid_x.append(x)

                if valid_x:
                    final_img = Image.new("RGB", (len(valid_x), ch), bg_color)
                    final_pix = final_img.load()
                    for y in range(ch):
                        for new_x, old_x in enumerate(valid_x):
                            final_pix[new_x, y] = pixels[old_x, y]
                else:
                    final_img = cropped_img

                final_img.save(output_path, "PNG")
                success_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            fail_count += 1
            print(f"Errore sul file {input_path}: {e}")
    
    # Chiede all'utente se vuole inserire automaticamente le immagini nei layout di stampa di QGIS
    if success_count > 0:
        reply = QMessageBox.question(
            parent, 
            "Inserimento nei Layout di Stampa", 
            f"Elaborazione ritagli completata!\n\n"
            f"✅ Salvati: {success_count} file nella cartella.\n\n"
            f"Vuoi inserire automaticamente queste immagini nei layout di stampa corrispondenti di QGIS?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            project = QgsProject.instance()
            layout_manager = project.layoutManager()
            layouts = layout_manager.layouts()
            
            layout_success = 0
            png_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.png')]
            
            for png in png_files:
                clean_png_name = os.path.splitext(png)[0].replace("LEGENDA_", "")
                matched_layout = None
                highest_ratio = 0.0
                
                for layout in layouts:
                    layout_name = layout.name().strip()
                    ratio = SequenceMatcher(None, clean_png_name.lower(), layout_name.lower()).ratio()
                    
                    if ratio > highest_ratio:
                        highest_ratio = ratio
                        matched_layout = layout
                
                if matched_layout and highest_ratio > 0.35:
                    pages = matched_layout.pageCollection().pages()
                    if pages:
                        page_w = pages[0].rect().width()
                        page_h = pages[0].rect().height()
                    else:
                        page_w, page_h = 420.0, 297.0
                    
                    img_path_full = os.path.join(output_dir, png)
                    with Image.open(img_path_full) as p_img:
                        pw, ph = p_img.size
                        aspect_ratio = ph / pw
                    
                    width = 80.0
                    img_height = width * aspect_ratio
                    
                    min_height = 150.0
                    if img_height < min_height:
                        img_height = min_height
                        width = img_height / aspect_ratio
                    
                    pos_x = page_w - width - 15
                    pos_y = (page_h - img_height) / 2
                    
                    picture_item = QgsLayoutItemPicture(matched_layout)
                    picture_item.setPicturePath(img_path_full)
                    picture_item.attemptMove(QgsLayoutPoint(pos_x, pos_y, QgsUnitTypes.LayoutMillimeters))
                    picture_item.attemptResize(QgsLayoutSize(width, img_height, QgsUnitTypes.LayoutMillimeters))
                    picture_item.setResizeMode(QgsLayoutItemPicture.Zoom)
                    
                    matched_layout.addLayoutItem(picture_item)
                    layout_success += 1
            
            QMessageBox.information(
                parent, 
                "Fatto!", 
                f"Immagini posizionate con successo al centro-destra (min 80x150mm) in {layout_success} layout di stampa!"
            )
    else:
        QMessageBox.information(
            parent, 
            "Elaborazione Completata", 
            f"Processo terminato!\n\n"
            f"✅ Salvati con successo: {success_count}\n"
            f"⏭️ Saltati: {skipped_count}\n"
            f"❌ Falliti: {fail_count}\n\n"
            f"📁 Cartella di destinazione:\n{output_dir}"
        )
