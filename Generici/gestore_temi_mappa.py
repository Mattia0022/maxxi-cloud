from qgis.core import QgsProject
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QMessageBox, QLabel, QGroupBox
)
from qgis.PyQt.QtCore import Qt

class GestoreTemiAvanzato(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestore Temi Mappa Avanzato")
        self.resize(450, 450)
        
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
        main_layout = QVBoxLayout(self)

        box_temi = QGroupBox("Temi Mappa Disponibili nel Progetto")
        lay_box = QVBoxLayout(box_temi)

        self.lista_widget = QListWidget()
        lay_box.addWidget(self.lista_widget)
        main_layout.addWidget(box_temi)

        self.aggiorna_lista()

        lay_btn = QHBoxLayout()
        btn_applica = QPushButton("Applica Tema")
        btn_applica.clicked.connect(self.applica_tema)
        
        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.clicked.connect(self.accept)

        lay_btn.addWidget(btn_applica)
        lay_btn.addWidget(btn_chiudi)
        main_layout.addLayout(lay_btn)

    def aggiorna_lista(self):
        self.lista_widget.clear()
        collection = QgsProject.instance().mapThemeCollection()
        temi = collection.mapThemes()
        if temi:
            self.lista_widget.addItems(temi)
        else:
            self.lista_widget.addItem("(Nessun tema mappa trovato nel progetto)")

    def applica_tema(self):
        item = self.lista_widget.currentItem()
        if not item or item.text().startswith("("):
            QMessageBox.warning(self, "Attenzione", "Seleziona un tema valido dalla lista.")
            return

        nome_tema = item.text()
        collection = QgsProject.instance().mapThemeCollection()
        canvas = iface.mapCanvas()
        
        collection.applyTheme(nome_tema, canvas.layerTreeRoot(), canvas)
        canvas.refresh()
        
        QMessageBox.information(self, "Fatto!", f"Tema '{nome_tema}' applicato con successo!")

def run():
    dlg = GestoreTemiAvanzato(iface.mainWindow())
    dlg.show()
    iface.maxxi_temi_dlg = dlg
