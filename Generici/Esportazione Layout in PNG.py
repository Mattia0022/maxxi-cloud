# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSpinBox, QPushButton, QFileDialog, QMessageBox
)
from qgis.core import QgsProject, QgsLayoutExporter

class EsportazioneLayoutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Esportazione Layout di Stampa")
        self.resize(420, 180)
        
        layout_principale = QVBoxLayout()
        
        # 1. Selezione del Layout di Stampa
        layout_layout = QHBoxLayout()
        lbl_layout = QLabel("Layout:")
        self.cmb_layouts = QComboBox()
        
        manager = QgsProject.instance().layoutManager()
        self.layouts_disponibili = manager.layouts()
        for lay in self.layouts_disponibili:
            self.cmb_layouts.addItem(lay.name())
            
        layout_layout.addWidget(lbl_layout)
        layout_layout.addWidget(self.cmb_layouts)
        layout_principale.addLayout(layout_layout)
        
        # 2. Inserimento DPI personalizzati direttamente nella schermata principale
        dpi_layout = QHBoxLayout()
        lbl_dpi = QLabel("Risoluzione (DPI):")
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(72, 2400)
        self.spin_dpi.setValue(300)  # Valore predefinito standard
        self.spin_dpi.setSingleStep(50)
        
        dpi_layout.addWidget(lbl_dpi)
        dpi_layout.addWidget(self.spin_dpi)
        layout_principale.addLayout(dpi_layout)
        
        layout_principale.addSpacing(10)
        
        # 3. Pulsanti per l'esportazione in PNG e PDF
        btn_layout = QHBoxLayout()
        
        self.btn_png = QPushButton("Esporta PNG")
        self.btn_png.setStyleSheet("font-weight: bold; padding: 8px;")
        self.btn_png.clicked.connect(lambda: self.esegui_esportazione("png"))
        
        self.btn_pdf = QPushButton("Esporta PDF")
        self.btn_pdf.setStyleSheet("font-weight: bold; padding: 8px;")
        self.btn_pdf.clicked.connect(lambda: self.esegui_esportazione("pdf"))
        
        btn_layout.addWidget(self.btn_png)
        btn_layout.addWidget(self.btn_pdf)
        layout_principale.addLayout(btn_layout)
        
        self.setLayout(layout_principale)
        
    def esegui_esportazione(self, formato):
        if not self.layouts_disponibili:
            QMessageBox.warning(self, "Attenzione", "Nessun layout di stampa trovato nel progetto.")
            return
            
        index_selezionato = self.cmb_layouts.currentIndex()
        layout_scelto = self.layouts_disponibili[index_selezionato]
        valore_dpi = float(self.spin_dpi.value())
        
        if formato == "pdf":
            filtro = "Documento PDF (*.pdf)"
            titolo = "Salva Layout in PDF"
        else:
            filtro = "Immagine PNG (*.png)"
            titolo = "Salva Layout in PNG"
            
        percorso_file, _ = QFileDialog.getSaveFileName(
            self, 
            titolo, 
            os.path.expanduser("~"), 
            filtro
        )
        
        if not percorso_file:
            return
            
        exporter = QgsLayoutExporter(layout_scelto)
        
        try:
            if formato == "pdf":
                if not percorso_file.lower().endswith('.pdf'):
                    percorso_file += '.pdf'
                settings = QgsLayoutExporter.PdfExportSettings()
                settings.dpi = valore_dpi
                risultato = exporter.exportToPdf(percorso_file, settings)
            else:
                if not percorso_file.lower().endswith('.png'):
                    percorso_file += '.png'
                settings = QgsLayoutExporter.ImageExportSettings()
                settings.dpi = valore_dpi
                risultato = exporter.exportToImage(percorso_file, settings)
                
            if risultato == QgsLayoutExporter.Success:
                QMessageBox.information(
                    self, 
                    "Successo", 
                    f"Esportazione in {formato.upper()} completata!\nFile: {percorso_file}\nDPI: {int(valore_dpi)}"
                )
                self.accept()
            else:
                QMessageBox.critical(self, "Errore", "Errore riscontrato durante l'esportazione del layout.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore imprevisto:\n{str(e)}")

def run():
    """Funzione d'ingresso standard richiesta per l'esecuzione in QGIS."""
    dialog = EsportazioneLayoutDialog()
    dialog.exec_()

if __name__ == '__main__':
    run()
