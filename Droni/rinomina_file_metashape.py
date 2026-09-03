import os
import re
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QLabel
)
from qgis.PyQt.QtCore import Qt

class RinominaFileAvanzato(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rinomina File Piani (Metashape)")
        self.resize(750, 450)
        self.cartella = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Sezione selezione cartella
        lay_cartella = QHBoxLayout()
        self.lbl_cartella = QLabel("Nessuna cartella selezionata")
        self.lbl_cartella.setStyleSheet("font-style: italic; color: #555;")
        btn_seleziona = QPushButton("📂 Scegli Cartella")
        btn_seleziona.clicked.connect(self.seleziona_cartella)
        
        lay_cartella.addWidget(self.lbl_cartella, 1)
        lay_cartella.addWidget(btn_seleziona)
        layout.addLayout(lay_cartella)

        # Tabella di anteprima
        self.tabella = QTableWidget()
        self.tabella.setColumnCount(2)
        self.tabella.setHorizontalHeaderLabels(["Nome Attuale", "Nuovo Nome Previsto"])
        self.tabella.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabella.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabella.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.tabella)

        # Pulsante di esecuzione
        self.btn_esegui = QPushButton("▶ Applica Rinomina")
        self.btn_esegui.setStyleSheet("font-weight: bold; background-color: #e1f5fe; padding: 10px;")
        self.btn_esegui.clicked.connect(self.esegui_rinomina)
        self.btn_esegui.setEnabled(False)
        layout.addWidget(self.btn_esegui)

    def seleziona_cartella(self):
        cartella = QFileDialog.getExistingDirectory(self, "Seleziona la cartella dei file")
        if cartella:
            self.cartella = cartella
            self.lbl_cartella.setText(cartella)
            self.aggiorna_anteprima()

    def aggiorna_anteprima(self):
        self.tabella.setRowCount(0)
        if not self.cartella:
            return

        files = sorted([
            f for f in os.listdir(self.cartella)
            if os.path.isfile(os.path.join(self.cartella, f))
        ])

        righe_valide = 0
        for file in files:
            nome, estensione = os.path.splitext(file)
            match = re.search(r'(\d+)$', nome)
            
            nuovo_nome = "-"
            if match:
                numero = match.group(1)
                if len(numero) >= 2:
                    piano = numero[:-1]
                    pagina = numero[-1]
                    nuovo_nome = f"Pag{piano}_{pagina}{estensione}"

            row_position = self.tabella.rowCount()
            self.tabella.insertRow(row_position)
            
            item_vecchio = QTableWidgetItem(file)
            item_nuovo = QTableWidgetItem(nuovo_nome)
            
            if nuovo_nome != "-":
                item_nuovo.setForeground(Qt.darkGreen)
            else:
                item_vecchio.setForeground(Qt.gray)
                item_nuovo.setForeground(Qt.gray)

            self.tabella.setItem(row_position, 0, item_vecchio)
            self.tabella.setItem(row_position, 1, item_nuovo)
            
            if nuovo_nome != "-":
                righe_valide += 1

        self.btn_esegui.setEnabled(righe_valide > 0)

    def esegui_rinomina(self):
        if not self.cartella:
            return

        risposta = QMessageBox.question(
            self, "Conferma", 
            "Vuoi procedere con la modifica definitiva dei nomi dei file?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if risposta != QMessageBox.Yes:
            return

        rinominati = 0
        for row in range(self.tabella.rowCount()):
            vecchio_nome = self.tabella.item(row, 0).text()
            nuovo_nome = self.tabella.item(row, 1).text()
            
            if nuovo_nome != "-":
                vecchio_path = os.path.join(self.cartella, vecchio_nome)
                nuovo_path = os.path.join(self.cartella, nuovo_nome)
                
                if os.path.exists(vecchio_path) and not os.path.exists(nuovo_path):
                    os.rename(vecchio_path, nuovo_path)
                    rinominati += 1

        QMessageBox.information(
            self,
            "Operazione completata",
            f"Rinominati con successo {rinominati} file."
        )
        self.aggiorna_anteprima()

def run():
    dlg = RinominaFileAvanzato(iface.mainWindow())
    dlg.show()
    iface.rinomina_file_dlg = dlg

run()
