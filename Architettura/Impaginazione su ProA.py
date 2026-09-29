import os
import shutil
import time
import re
import tempfile
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QLabel, QApplication, QFileDialog
)

# Importazione dei moduli per comunicare con ProA
try:
    import win32gui
    import win32con
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
except ImportError:
    shell = None

class ImpaginazioneProADialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or iface.mainWindow())
        self.setWindowTitle("Impaginazione Automatica su ProA")
        self.resize(900, 500)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. Sezione Cartelle e Scala
        box_config = QGroupBox("1. Selezione Cartelle e Parametri")
        lay_config = QVBoxLayout(box_config)

        # Origine
        h_orig = QHBoxLayout()
        h_orig.addWidget(QLabel("Cartella Origine Immagini:"))
        self.txt_origine = QLineEdit()
        btn_orig = QPushButton("Sfoglia...")
        btn_orig.clicked.connect(self.seleziona_origine)
        h_orig.addWidget(self.txt_origine)
        h_orig.addWidget(btn_orig)
        lay_config.addLayout(h_orig)

        # Destinazione
        h_dest = QHBoxLayout()
        h_dest.addWidget(QLabel("Cartella Destinazione (Pulite):"))
        self.txt_destinazione = QLineEdit()
        btn_dest = QPushButton("Sfoglia...")
        btn_dest.clicked.connect(self.seleziona_destinazione)
        h_dest.addWidget(self.txt_destinazione)
        h_dest.addWidget(btn_dest)
        lay_config.addLayout(h_dest)

        # Scala CAD
        h_scale = QHBoxLayout()
        h_scale.addWidget(QLabel("Scala CAD (es. 1000):"))
        self.txt_scala = QLineEdit("1000")
        h_scale.addWidget(self.txt_scala)
        lay_config.addLayout(h_scale)

        main_layout.addWidget(box_config)

        # 2. Anteprima
        box_preview = QGroupBox("2. Anteprima File da Rinominare")
        lay_preview = QVBoxLayout(box_preview)

        self.tabella_file = QTableWidget()
        self.tabella_file.setColumnCount(2)
        self.tabella_file.setHorizontalHeaderLabels(["File Originale", "Nuovo Nome"])
        self.tabella_file.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabella_file.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabella_file.setSelectionBehavior(QAbstractItemView.SelectRows)
        lay_preview.addWidget(self.tabella_file)

        main_layout.addWidget(box_preview)

        # 3. Pulsante Avvio
        self.btn_avvia = QPushButton("🚀 Avvia Rinomina e Invia a ProA")
        self.btn_avvia.setStyleSheet("font-weight: bold; padding: 10px; font-size: 13px; background-color: #d1fae5;")
        self.btn_avvia.clicked.connect(self.esegui_processo)
        main_layout.addWidget(self.btn_avvia)

    def seleziona_origine(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleziona Cartella Origine")
        if dir_path:
            self.txt_origine.setText(dir_path)
            self.aggiorna_anteprima()

    def seleziona_destinazione(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleziona Cartella Destinazione")
        if dir_path:
            self.txt_destinazione.setText(dir_path)

    def pulisci_nome(self, stem):
        # Rimuove prefissi brevi iniziali (es. "A0_", "B2.", "1-", max 3 caratteri) lasciando intatte parole lunghe
        nuovo = re.sub(r'^[a-zA-Z0-9]{1,3}[_\\.\-\s]+\s*', '', stem)
        return nuovo.strip().capitalize()

    def aggiorna_anteprima(self):
        origine = self.txt_origine.text()
        if not origine or not os.path.exists(origine):
            return

        estensioni_valide = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff')
        try:
            files = sorted([f for f in os.listdir(origine) if f.lower().endswith(estensioni_valide)])
        except Exception:
            files = []

        self.tabella_file.setRowCount(len(files))
        for idx, filename in enumerate(files):
            stem, ext = os.path.splitext(filename)
            nuovo_nome_base = self.pulisci_nome(stem)
            nuovo_nome = f"{idx + 1}. {nuovo_nome_base}{ext}"

            self.tabella_file.setItem(idx, 0, QTableWidgetItem(filename))
            self.tabella_file.setItem(idx, 1, QTableWidgetItem(nuovo_nome))

    def esegui_processo(self):
        origine = self.txt_origine.text()
        destinazione = self.txt_destinazione.text()
        scale_str = self.txt_scala.text().strip() or "1000"

        if not origine or not os.path.exists(origine):
            QMessageBox.warning(self, "Attenzione", "Seleziona una cartella di origine valida!")
            return

        if not destinazione:
            QMessageBox.warning(self, "Attenzione", "Seleziona una cartella di destinazione valida!")
            return

        os.makedirs(destinazione, exist_ok=True)
        estensioni_valide = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff')

        try:
            files = sorted([f for f in os.listdir(origine) if f.lower().endswith(estensioni_valide)])
        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Impossibile leggere i file:\n{e}")
            return

        img_paths = []
        for idx, filename in enumerate(files):
            percorso_origine = os.path.join(origine, filename)
            stem, ext = os.path.splitext(filename)
            
            nuovo_nome_base = self.pulisci_nome(stem)
            nuovo_nome = f"{idx + 1}. {nuovo_nome_base}{ext}"
            percorso_destinazione = os.path.join(destinazione, nuovo_nome)
            
            shutil.copy2(percorso_origine, percorso_destinazione)
            img_paths.append(percorso_destinazione)

        if not img_paths:
            QMessageBox.warning(self, "Attenzione", "Nessuna immagine valida trovata!")
            return

        if shell is None:
            QMessageBox.information(self, "Completato", f"Rinominate {len(img_paths)} immagini in destinazione.\nAutomazione CAD non disponibile su questo sistema.")
            self.accept()
            return

        # Automazione ProA
        def enum_windows_callback(hwnd, extra):
            title = win32gui.GetWindowText(hwnd)
            if title and win32gui.IsWindowVisible(hwnd):
                title_lower = title.lower()
                if any(k in title_lower for k in ["proa", "progecad", "icad", "autocad", "oem", "dwg"]):
                    extra.append((hwnd, title))

        top_windows = []
        win32gui.EnumWindows(enum_windows_callback, top_windows)

        if top_windows:
            hwnd, titolo_rilevato = top_windows[0]
            self.hide()
            QApplication.processEvents()
            time.sleep(0.5)

            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                shell.SendKeys('%')
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.5)
            except Exception as e:
                QMessageBox.warning(None, "Errore Focus", f"Impossibile attivare la finestra CAD:\n{e}")
                self.show()
                return

            # Generazione del blocco comandi CAD
            cmd_script = "FILEDIA 0\n_TILEMODE 0\n"

            for img_path in img_paths:
                layout_name = os.path.splitext(os.path.basename(img_path))[0]
                cmd_script += f"-LAYOUT\n_CO\n\n{layout_name}\n"

            for img_path in img_paths:
                img_path_clean = img_path.replace("\\", "/")
                layout_name = os.path.splitext(os.path.basename(img_path))[0]
                cmd_script += (
                    f"-LAYOUT\n_SET\n{layout_name}\n"
                    f"-IMAGE\n_ATTACH\n\"{img_path_clean}\"\n"
                    f"0,0\n{scale_str}\n0\n"
                    f"_DRAWORDER\n_L\n\n_BACK\n"
                )

            cmd_script += "FILEDIA 1\n"

            # SCRITTURA DI UN FILE SCRIPT TEMPORANEO (.scr) per massima affidabilità
            with tempfile.NamedTemporaryFile(mode='w', suffix='.scr', delete=False, encoding='utf-8') as tmp:
                tmp.write(cmd_script)
                script_path = tmp.name
            
            script_path_clean = script_path.replace("\\", "/")
            cad_command = f"_SCRIPT\n{script_path_clean}\n"

            # Inserisce il comando per lanciare lo script nel CAD
            QApplication.clipboard().setText(cad_command)
            shell.SendKeys('{ESC}{ESC}')
            time.sleep(0.3)
            shell.SendKeys('^v')
            time.sleep(0.4)
            shell.SendKeys('{ENTER}')

            QMessageBox.information(None, "Successo", f"Rinominate {len(img_paths)} immagini e inviate a ProA in automatico!")
            self.close()
        else:
            QMessageBox.warning(self, "Errore", "Nessuna finestra ProA/CAD aperta sul desktop!")
            self.show()

def run():
    """Punto di ingresso principale per QGIS / Script Runner"""
    dlg = ImpaginazioneProADialog()
    dlg.exec_()
