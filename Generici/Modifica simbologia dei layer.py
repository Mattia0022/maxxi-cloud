import os
from pathlib import Path
from qgis.core import (
    QgsProject, QgsMapLayer, QgsCategorizedSymbolRenderer, 
    QgsRendererCategory, QgsMarkerSymbol, QgsSvgMarkerSymbolLayer
)
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QFileDialog, QMessageBox, QListWidget, QDialog, QVBoxLayout, 
    QHBoxLayout, QPushButton, QAbstractItemView, QGroupBox, QLabel, QLineEdit, QWidget, QTextEdit, QComboBox
)
from qgs.PyQt.QtCore import Qt  # oppure qgis.PyQt.QtCore se preferisci

class AssociazioneSvgDialog(QDialog):
    def __init__(self, guida_testo="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Associazione Avanzata Icone SVG da Cartella")
        self.resize(1100, 500)
        
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
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #0078d7;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
        """)

        self.init_ui(guida_testo)

    def init_ui(self, guida_testo):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # --- 1. INTERFACCIA DEL TOOL (A SINISTRA) ---
        widget_interfaccia = QWidget()
        widget_interfaccia.setStyleSheet("background: transparent;")
        layout_tool = QHBoxLayout(widget_interfaccia)
        layout_tool.setContentsMargins(0, 0, 0, 0)

        # Box 1: Selezione Layer e Attributo
        box_layer = QGroupBox("1. Selezione Layer Vettoriale e Campo")
        lay_layer = QVBoxLayout(box_layer)

        self.progetto = QgsProject.instance()
        self.layers_vettoriali = [l for l in self.progetto.mapLayers().values() if l.type() == QgsMapLayer.VectorLayer]
        self.layers_dict = {l.name(): l for l in self.layers_vettoriali}

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Cerca layer...")
        self.search_box.textChanged.connect(self.filter_layers)
        lay_layer.addWidget(self.search_box)

        self.lista_layer = QListWidget()
        self.lista_layer.addItems(self.layers_dict.keys())
        self.lista_layer.itemSelectionChanged.connect(self.aggiorna_campi)
        lay_layer.addWidget(self.lista_layer)

        lbl_campo = QLabel("Campo Tabella da associare:")
        lbl_campo.setStyleSheet("margin-top: 5px; color: #333333;")
        lay_layer.addWidget(lbl_campo)

        self.combo_campi = QComboBox()
        lay_layer.addWidget(self.combo_campi)

        layout_tool.addWidget(box_layer, 1)

        # Box 2: Cartella SVG e Avvio
        box_opzioni = QGroupBox("2. Cartella SVG e Operazioni")
        lay_opzioni = QVBoxLayout(box_opzioni)

        lbl_info = QLabel("• Associazione automatica basata sui valori unici.\n• I file mancanti useranno un pallino grigio di fallback.")
        lbl_info.setStyleSheet("color: #555555; margin-bottom: 10px;")
        lay_opzioni.addWidget(lbl_info)

        lay_corso = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Seleziona la cartella con i file SVG...")
        btn_browse = QPushButton("Sfoglia...")
        btn_browse.clicked.connect(self.scegli_cartella)
        lay_corso.addWidget(self.txt_path)
        lay_corso.addWidget(btn_browse)
        lay_opzioni.addLayout(lay_corso)

        lay_opzioni.addStretch()

        self.btn_conferma = QPushButton("Avvia Associazione SVG")
        self.btn_conferma.clicked.connect(self.avvia_associazione)
        lay_opzioni.addWidget(self.btn_conferma)

        layout_tool.addWidget(box_opzioni, 1)
        main_layout.addWidget(widget_interfaccia, stretch=3)

        # --- 2. PANNELLO GUIDA (A DESTRA) ---
        widget_guida = QWidget()
        widget_guida.setStyleSheet("background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 8px;")
        layout_dx = QVBoxLayout(widget_guida)
        layout_dx.setContentsMargins(8, 8, 8, 8)

        lbl_titolo_guida = QLabel("📖 Guida Passo-Passo")
        lbl_titolo_guida.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 13px; border: none; background: transparent; margin-bottom: 4px;")
        layout_dx.addWidget(lbl_titolo_guida)

        txt_guida = QTextEdit()
        txt_guida.setReadOnly(True)
        txt_guida.setHtml(f"<div style='color: #333333; font-size: 12px; line-height: 1.5;'>{guida_testo}</div>")
        txt_guida.setStyleSheet("background-color: #ffffff; color: #222222; border: 1px solid #cccccc; border-radius: 4px; padding: 8px;")
        layout_dx.addWidget(txt_guida)

        main_layout.addWidget(widget_guida, stretch=1)

        # Seleziona il primo elemento di default se disponibile
        if self.layers_dict:
            self.lista_layer.setCurrentRow(0)

    def filter_layers(self, text):
        self.lista_layer.clear()
        for name in self.layers_dict.keys():
            if text.lower() in name.lower():
                self.lista_layer.addItem(name)

    def aggiorna_campi(self):
        self.combo_campi.clear()
        selected = self.lista_layer.selectedItems()
        if selected:
            layer_name = selected[0].text()
            layer = self.layers_dict.get(layer_name)
            if layer:
                fields = [field.name() for field in layer.fields()]
                self.combo_campi.addItems(fields)

    def scegli_cartella(self):
        cartella = QFileDialog.getExistingDirectory(self, "Seleziona la cartella contenente i file SVG")
        if cartella:
            self.txt_path.setText(cartella)

    def get_selected_layer(self):
        selected = self.lista_layer.selectedItems()
        if selected:
            return self.layers_dict.get(selected[0].text())
        return None

    def avvia_associazione(self):
        layer = self.get_selected_layer()
        if not layer:
            QMessageBox.warning(self, "Attenzione", "Seleziona un layer vettoriale dalla lista.")
            return

        field_name = self.combo_campi.currentText()
        if not field_name:
            QMessageBox.warning(self, "Attenzione", "Seleziona un campo attributo valido.")
            return

        icon_dir = self.txt_path.text().strip()
        if not icon_dir or not os.path.exists(icon_dir):
            QMessageBox.warning(self, "Attenzione", "Seleziona una cartella SVG valida.")
            return

        field_index = layer.fields().indexOf(field_name)
        unique_values = sorted([str(v) for v in layer.uniqueValues(field_index) if v is not None])

        if not unique_values:
            QMessageBox.warning(self, "Attenzione", "Nessun valore unico trovato nel campo selezionato.")
            return

        categories = []
        trovati = 0
        mancanti = 0

        print(f"Inizio associazione icone SVG per il layer '{layer.name()}'...\n" + "-"*50)

        for val in unique_values:
            val_clean = "".join(c for c in str(val).lower() if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
            icon_filename = f"{val_clean}.svg"
            icon_path = os.path.join(icon_dir, icon_filename)
            
            symbol = QgsMarkerSymbol()
            
            if os.path.exists(icon_path):
                marker_layer = QgsSvgMarkerSymbolLayer(icon_path)
                marker_layer.setSize(5.0)
                symbol.changeSymbolLayer(0, marker_layer)
                trovati += 1
            else:
                symbol = QgsMarkerSymbol.createSimple({
                    'name': 'circle', 
                    'color': '180,180,180', 
                    'size': '4', 
                    'outline_color': '0,0,0'
                })
                mancanti += 1
                print(f"SVG non trovato per '{val}' (cercato: {icon_filename}). Applicato fallback.")
                
            category = QgsRendererCategory(val, symbol, val)
            categories.append(category)
            
        renderer = QgsCategorizedSymbolRenderer(field_name, categories)
        if renderer:
            layer.setRenderer(renderer)
            layer.triggerRepaint()
            msg = f"Completato!\nIcone SVG associate: {trovati}\nFallback applicati: {mancanti}"
            print("-" * 50 + "\n" + msg)
            QMessageBox.information(self, "Fatto!", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Errore", "Errore nella creazione del renderer categorizzato.")

def run():
    guida_testo = (
        "<b>Strumento di Associazione Icone SVG</b><br><br>"
        "1. <b>Seleziona Layer:</b> Scegli il layer vettoriale desiderato dall'elenco a sinistra (puoi filtrarlo con la barra di ricerca).<br><br>"
        "2. <b>Seleziona Campo:</b> Scegli dal menu a tendina l'attributo da confrontare con i nomi dei file SVG.<br><br>"
        "3. <b>Cartella SVG:</b> Clicca su 'Sfoglia...' per indicare la directory contenente le icone.<br><br>"
        "4. <b>Avvia:</b> Clicca sul pulsante in basso per applicare automaticamente la simbologia al layer."
    )
    dlg = AssociazioneSvgDialog(guida_testo, iface.mainWindow())
    dlg.show()
    iface.maxxi_svg_dlg = dlg
