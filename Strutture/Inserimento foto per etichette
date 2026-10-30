from pathlib import Path
import os
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsExpression, 
    QgsExpressionContext, QgsExpressionContextUtils
)
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QFileDialog, QMessageBox, QListWidget, QDialog, QVBoxLayout, 
    QHBoxLayout, QPushButton, QAbstractItemView, QGroupBox, QLabel, 
    QLineEdit, QWidget, QTextEdit, QComboBox, QProgressBar
)
from qgis.PyQt.QtCore import Qt, QVariant

class InserimentoFotoEtichetteDialog(QDialog):
    def __init__(self, guida_testo="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inserimento foto per etichette")
        self.resize(1250, 680)  # Schermata ampia e strutturata
        
        # Stile visivo coerente e moderno
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                color: #222222;
                font-family: Arial, sans-serif;
            }
            QGroupBox {
                border: 1px solid #dcdcdc;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                color: #333333;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QListWidget, QComboBox {
                background-color: #ffffff;
                color: #222222;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #222222;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #e6e6e6;
                color: #222222;
                border: 1px solid #adadad;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #0078d7;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                background-color: #ffffff;
                color: #222222;
                font-weight: bold;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
                border-radius: 3px;
            }
        """)

        self.init_ui(guida_testo)

    def init_ui(self, guida_testo):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- 1. INTERFACCIA DEL TOOL (A SINISTRA) ---
        widget_interfaccia = QWidget()
        widget_interfaccia.setStyleSheet("background: transparent;")
        layout_tool = QHBoxLayout(widget_interfaccia)
        layout_tool.setContentsMargins(0, 0, 0, 0)

        # Box 1: Selezione Layer con barra di ricerca
        box_layer = QGroupBox("1. Seleziona Layer Vettoriali (Multipli)")
        lay_box_layer = QVBoxLayout(box_layer)

        self.txt_cerca = QLineEdit()
        self.txt_cerca.setPlaceholderText("🔍 Cerca layer per nome...")
        self.txt_cerca.textChanged.connect(self.filtra_layer)
        lay_box_layer.addWidget(self.txt_cerca)

        self.progetto = QgsProject.instance()
        layers = self.progetto.mapLayers()
        self.vector_layers = {layer_id: layer for layer_id, layer in layers.items() if isinstance(layer, QgsVectorLayer)}

        self.lista_widget = QListWidget()
        self.lista_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        for lid, lyr in self.vector_layers.items():
            self.lista_widget.addItem(lyr.name())
            
        lay_box_layer.addWidget(self.lista_widget)
        
        # Aggiorna la tendina delle colonne quando cambia la selezione dei layer
        self.lista_widget.itemSelectionChanged.connect(self.aggiorna_campi_confronto)

        layout_tool.addWidget(box_layer, 1)

        # Box 2: Opzioni, Foto, Configurazione e Azione
        box_opzioni = QGroupBox("2. Configurazione Campi, Foto e Azione")
        lay_opzioni = QVBoxLayout(box_opzioni)

        # Selezione Colonna di Confronto
        lay_colonna = QHBoxLayout()
        lbl_col = QLabel("• Colonna Tabella da Confrontare:")
        lbl_col.setStyleSheet("color: #555555;")
        self.combo_campi = QComboBox()
        self.combo_campi.addItem("-- Seleziona prima un layer --", None)
        lay_colonna.addWidget(lbl_col)
        lay_colonna.addWidget(self.combo_campi)
        lay_opzioni.addLayout(lay_colonna)

        # Selezione Foto
        lbl_foto_info = QLabel("• Selezione Immagini da associare:")
        lbl_foto_info.setStyleSheet("color: #555555; margin-top: 5px;")
        lay_opzioni.addWidget(lbl_foto_info)

        lay_corso = QHBoxLayout()
        self.txt_path_foto = QLineEdit()
        self.txt_path_foto.setPlaceholderText("Nessuna foto selezionata (opzionale)...")
        self.txt_path_foto.setReadOnly(True)
        btn_browse = QPushButton("Sfoglia Foto...")
        btn_browse.clicked.connect(self.seleziona_foto)
        lay_corso.addWidget(self.txt_path_foto)
        lay_corso.addWidget(btn_browse)
        lay_opzioni.addLayout(lay_corso)
        
        self.photo_paths = []

        # Barra di avanzamento (%)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        lay_opzioni.addWidget(self.progress_bar)

        lay_opzioni.addStretch()

        # Pulsante di avvio elaborazione
        self.btn_esegui = QPushButton("Avvia Inserimento Foto e Coordinate")
        self.btn_esegui.setStyleSheet("background-color: #0078d7; color: white; padding: 10px; font-size: 11pt;")
        self.btn_esegui.clicked.connect(self.avvia_elaborazione)
        lay_opzioni.addWidget(self.btn_esegui)

        layout_tool.addWidget(box_opzioni, 1)
        main_layout.addWidget(widget_interfaccia, stretch=3)

        # --- 2. PANNELLO GUIDA (A DESTRA) ---
        widget_guida = QWidget()
        widget_guida.setStyleSheet("background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 8px;")
        layout_dx = QVBoxLayout(widget_guida)
        layout_dx.setContentsMargins(10, 10, 10, 10)

        lbl_titolo_guida = QLabel("📖 Guida Passo-Passo")
        lbl_titolo_guida.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 13px; border: none; background: transparent; margin-bottom: 4px;")
        layout_dx.addWidget(lbl_titolo_guida)

        txt_guida = QTextEdit()
        txt_guida.setReadOnly(True)
        default_guida = """
        <b>Benvenuto in Inserimento Foto per Etichette!</b><br><br>
        1. <b>Seleziona i Layer:</b> Scegli uno o più layer vettoriali dalla lista (usa la ricerca rapida in alto).<br><br>
        2. <b>Scegli la Colonna:</b> Seleziona quale campo della tabella attributi confrontare con i nomi delle foto.<br><br>
        3. <b>Collega le Foto:</b> Clicca su 'Sfoglia Foto' per selezionare le immagini dal computer.<br><br>
        4. <b>Esegui:</b> Il tool creerà o aggiornerà i campi <b>FOTO</b>, <b>POS_X</b> e <b>POS_Y</b> (in formato decimale), associando i percorsi corretti!
        """
        guida_finale = guida_testo if guida_testo else default_guida
        txt_guida.setHtml(f"<div style='color: #333333; font-size: 12px; line-height: 1.5;'>{guida_finale}</div>")
        txt_guida.setStyleSheet("background-color: #ffffff; color: #222222; border: 1px solid #cccccc; border-radius: 4px; padding: 8px;")
        layout_dx.addWidget(txt_guida)

        main_layout.addWidget(widget_guida, stretch=1)

    def filtra_layer(self, testo):
        for index in range(self.lista_widget.count()):
            item = self.lista_widget.item(index)
            item.setHidden(testo.lower() not in item.text().lower())

    def aggiorna_campi_confronto(self):
        self.combo_campi.clear()
        selected_items = self.lista_widget.selectedItems()
        if not selected_items:
            self.combo_campi.addItem("-- Seleziona prima un layer --", None)
            return

        nome_primo_layer = selected_items[0].text()
        layer_selezionato = None
        for lid, lyr in self.vector_layers.items():
            if lyr.name() == nome_primo_layer:
                layer_selezionato = lyr
                break

        if layer_selezionato:
            campi = [field.name() for field in layer_selezionato.fields()]
            for campo in campi:
                self.combo_campi.addItem(campo, campo)

    def seleziona_foto(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Seleziona le foto da associare", 
            "", 
            "Immagini (*.png *.jpg *.jpeg *.JPG *.PNG)"
        )
        if paths:
            self.photo_paths = paths
            self.txt_path_foto.setText(f"{len(paths)} foto selezionate")

    def avvia_elaborazione(self):
        selected_items = self.lista_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un layer vettoriale dalla lista.")
            return

        colonna_scelta = self.combo_campi.currentData()

        img_dict = {}
        for path in self.photo_paths:
            base_name = os.path.basename(path)
            name_no_ext, _ = os.path.splitext(base_name)
            img_dict[base_name.lower()] = path
            img_dict[name_no_ext.lower()] = path

        expr_x = QgsExpression("X($geometry)")
        expr_y = QgsExpression("Y($geometry)")
        context = QgsExpressionContext()
        context.appendScope(QgsExpressionContextUtils.globalScope())
        context.appendScope(QgsExpressionContextUtils.projectScope(self.progetto))

        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(selected_items))
        self.progress_bar.show()

        successi = 0

        for index, item in enumerate(selected_items):
            nome_layer = item.text()
            layer = None
            for lid, lyr in self.vector_layers.items():
                if lyr.name() == nome_layer:
                    layer = lyr
                    break

            if layer:
                layer.startEditing()

                existing_fields = [f.name() for f in layer.fields()]
                fields_to_add = []

                if "FOTO" not in existing_fields:
                    fields_to_add.append(QgsField("FOTO", QVariant.String))
                if "POS_X" not in existing_fields:
                    fields_to_add.append(QgsField("POS_X", QVariant.Double))
                if "POS_Y" not in existing_fields:
                    fields_to_add.append(QgsField("POS_Y", QVariant.Double))

                if fields_to_add:
                    layer.dataProvider().addAttributes(fields_to_add)
                    layer.updateFields()

                idx_foto = layer.fields().indexOf("FOTO")
                idx_x = layer.fields().indexOf("POS_X")
                idx_y = layer.fields().indexOf("POS_Y")

                layer_fields = [f.name() for f in layer.fields()]
                can_match = colonna_scelta and (colonna_scelta in layer_fields)

                features = list(layer.getFeatures())
                for feat in features:
                    feat_id = feat.id()
                    context.setFeature(feat)

                    res_x = expr_x.evaluate(context)
                    res_y = expr_y.evaluate(context)

                    val_x = float(res_x) if res_x is not None else 0.0
                    val_y = float(res_y) if res_y is not None else 0.0

                    layer.changeAttributeValue(feat_id, idx_x, val_x)
                    layer.changeAttributeValue(feat_id, idx_y, val_y)

                    if can_match and self.photo_paths:
                        cell_value = feat[colonna_scelta]
                        if cell_value is not None:
                            val_str = str(cell_value).strip().lower()
                            if val_str in img_dict:
                                layer.changeAttributeValue(feat_id, idx_foto, img_dict[val_str])

                layer.commitChanges()
                successi += 1

            self.progress_bar.setValue(index + 1)

        QMessageBox.information(self, "Completato", f"Elaborazione terminata con successo su {successi} layer!")
        self.accept()

def run():
    guida_personalizzata = """
    <b>Guida Rapida all'Uso:</b><br><br>
    • <b>Multi-selezione:</b> Seleziona uno o più layer tenendo premuto CTRL o SHIFT.<br>
    • <b>Confronto Attributi:</b> Scegli il campo chiave (es. ID o Nome) per abbinare automaticamente le immagini.<br>
    • <b>Campi Automatici:</b> Vengono create o aggiornate le colonne <b>FOTO</b>, <b>POS_X</b> e <b>POS_Y</b> in formato decimale.
    """
    dlg = InserimentoFotoEtichetteDialog(guida_personalizzata, iface.mainWindow())
    dlg.show()
    iface.inserimento_foto_etichette_dlg = dlg
