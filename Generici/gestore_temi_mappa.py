from qgis.core import QgsProject
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QMessageBox, QLabel
)
from qgis.PyQt.QtCore import Qt

class GestoreTemiAvanzato(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestore Temi Mappa Avanzato")
        self.resize(400, 450)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                color: #222222;
                font-family: Arial, sans-serif;
            }
            QListWidget {
                background-color: #ffffff;
                color: #222222;
                border: 1px solid #cccccc;
                border-radius: 4px;
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
        """)

        layout = QVBoxLayout(self)
        
        lbl = QLabel("<b>Temi mappa disponibili nel progetto:</b>")
        layout.addWidget(lbl)
        
        self.lista_temi = QListWidget()
        layout.addWidget(self.lista_temi)
        
        self.aggiorna_lista()
        
        btn_layout = QHBoxLayout()
        btn_applica = QPushButton("Applica Tema")
        btn_applica.clicked.connect(self.applica_tema)
        
        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_applica)
        btn_layout.addWidget(btn_chiudi)
        layout.addLayout(btn_layout)

    def aggiorna_lista(self):
        self.lista_temi.clear()
        collection = QgsProject.instance().mapThemeCollection()
        temi = collection.mapThemes()
        for tema in temi:
            self.lista_temi.addItem(tema)

    def applica_tema(self):
        item = self.lista_temi.currentItem()
        if not item:
            QMessageBox.warning(self, "Attenzione", "Seleziona un tema dalla lista.")
            return
        
        nome_tema = item.text()
        collection = QgsProject.instance().mapThemeCollection()
        
        canvas = iface.mapCanvas()
        collection.applyTheme(nome_tema, canvas.layerTreeRoot(), canvas)
        iface.mapCanvas().refresh()
        QMessageBox.information(self, "Successo", f"Tema '{nome_tema}' applicato correttamente!")

def run():
    dlg = GestoreTemiAvanzato(iface.mainWindow())
    dlg.show()
    iface.maxxi_temi_dlg = dlg
