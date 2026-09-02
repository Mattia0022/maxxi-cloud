from pathlib import Path
from qgis.core import QgsProject, QgsLayoutExporter
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QFileDialog, QMessageBox, QListWidget, QDialog, QVBoxLayout, 
    QHBoxLayout, QPushButton, QAbstractItemView, QGroupBox, QLabel, QLineEdit
)
from qgis.PyQt.QtCore import Qt

class EsportazioneLayoutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Esportazione Avanzata Layout / Atlanti in PNG")
        self.resize(850, 500)
        
        # Applicazione dello stile chiaro coerente con il gestore temi
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
            QListWidget {
                background-color: #ffffff;
                color: #222222;
                border: 1px solid #cccccc;
                border-radius: 4px;
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

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # =====================================================
        # 1. PANNELLO SELEZIONE LAYOUT
        # =====================================================
        box_layout = QGroupBox("1. Layout di Stampa (CTRL o SHIFT per multipli)")
        lay_box = QVBoxLayout(box_layout)

        self.progetto = QgsProject.instance()
        self.layout_manager = self.progetto.layoutManager()
        self.tutti_i_layout = [l.name() for l in self.layout_manager.printLayouts()]

        self.lista_widget = QListWidget()
        self.lista_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lista_widget.addItems(self.tutti_i_layout)
        lay_box.addWidget(self.lista_widget)

        main_layout.addWidget(box_layout, 1)

        # =====================================================
        # 2. PANNELLO OPZIONI E DESTINAZIONE
        # =====================================================
        box_opzioni = QGroupBox("2. Configurazione e Destinazione")
        lay_opzioni = QVBoxLayout(box_opzioni)

        crs_progetto = self.progetto.crs().authid()
        crs_desc = self.progetto.crs().description()
        
        lbl_info = QLabel(f"• Sistema di Riferimento: {crs_progetto} ({crs_desc})\n• Risoluzione di rendering: 300 DPI")
        lbl_info.setStyleSheet("color: #555555; margin-bottom: 10px;")
        lay_opzioni.addWidget(lbl_info)

        lay_corso = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Seleziona la cartella di destinazione...")
        btn_browse = QPushButton("Sfoglia...")
        btn_browse.clicked.connect(self.scegli_cartella)
        lay_corso.addWidget(self.txt_path)
        lay_corso.addWidget(btn_browse)
        lay_opzioni.addLayout(lay_corso)

        lay_opzioni.addStretch()

        self.btn_conferma = QPushButton("Avvia Esportazione PNG")
        self.btn_conferma.clicked.connect(self.avvia_esportazione)
        lay_opzioni.addWidget(self.btn_conferma)

        main_layout.addWidget(box_opzioni, 1)

    def scegli_cartella(self):
        cartella = QFileDialog.getExistingDirectory(self, "Scegli la cartella di destinazione", "C:\\Users\\userm\\Desktop")
        if cartella:
            self.txt_path.setText(cartella)

    def avvia_esportazione(self):
        if not self.tutti_i_layout:
            QMessageBox.warning(self, "Attenzione", "Non ci sono layout di stampa creati in questo progetto!")
            return

        layout_scelti = [item.text() for item in self.lista_widget.selectedItems()]
        if not layout_scelti:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un layout dalla lista a sinistra.")
            return

        cartella_destinazione = self.txt_path.text().strip()
        if not cartella_destinazione:
            QMessageBox.warning(self, "Attenzione", "Seleziona una cartella di destinazione valida.")
            return

        percorso_out = Path(cartella_destinazione)
        print(f"Inizio esportazione di {len(layout_scelti)} elementi in formato PNG (mantenendo il CRS di progetto)...\n" + "-"*50)
        
        immagini_generate = 0
        impostazioni_immagine = QgsLayoutExporter.ImageExportSettings()
        impostazioni_immagine.dpi = 300 
        
        for nome_layout in layout_scelti:
            layout = self.layout_manager.layoutByName(nome_layout)
            
            if layout:
                esportatore = QgsLayoutExporter(layout)
                atlante = layout.atlas()
                
                if atlante.enabled():
                    print(f"[ATLANTE RILEVATO] Generazione immagini per l'atlante: {nome_layout}")
                    prefisso_file = str(percorso_out / f"{nome_layout}_pagina_")
                    risultato = esportatore.exportToImage(atlante, prefisso_file, "png", impostazioni_immagine)
                else:
                    percorso_completo = str(percorso_out / f"{nome_layout}.png")
                    risultato = esportatore.exportToImage(percorso_completo, impostazioni_immagine)
                
                if risultato == QgsLayoutExporter.Success:
                    print(f"[OK] Esportato correttamente elemento: {nome_layout}")
                    immagini_generate += 1
                else:
                    print(f"[ERRORE] Fallimento su: {nome_layout} (Codice errore: {risultato})")
                
        print("-"*50)
        print(f"PROCESSO CONCLUSO! Generati {immagini_generate} elementi grafici in PNG.")
        QMessageBox.information(self, "Fatto!", "Esportazione in PNG completata con successo!")
        self.accept()

def run():
    dlg = EsportazioneLayoutDialog(iface.mainWindow())
    dlg.show()
    iface.maxxi_esportazione_dlg = dlg