import json
import urllib.request
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QMessageBox
from qgis.utils import iface

# 1. Configurazione del Catalogo JSON con le risorse GitHub
CATALOGO_SCRIPTS = {
    "Generici": {
        "Gestore Temi Mappa": "https://raw.githubusercontent.com/Mattia0022/maxxi-cloud/main/Generici/gestore_temi_mappa.py",
        "Esportazione Layout in PNG": "https://raw.githubusercontent.com/Mattia0022/maxxi-cloud/main/Generici/Esportazione%20Layout%20in%20PNG.py"
    },
    "Ambiente": {},
    "Architettura": {},
    "Civile": {},
    "Droni": {
        "Gestione Foto e Layout": "https://raw.githubusercontent.com/Mattia0022/maxxi-cloud/main/Droni/gestione_foto_plugin.py",
        "zio": "https://raw.githubusercontent.com/Mattia0022/maxxi-cloud/main/Droni/zio.py"
    },
    "Impianti": {},
    "Strutture": {}
}

# 2. Interfaccia Grafica per la Selezione degli Script
class MaxxiCloudLoaderDialog(QDialog):
    def __init__(self, catalogo):
        super().__init__()
        self.setWindowTitle("Maxxi Cloud - Seleziona Script")
        self.resize(400, 450)
        self.catalogo = catalogo
        self.url_selezionato = None

        layout = QVBoxLayout()

        # Albero di selezione per le categorie ed i relativi script
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Libreria Strumenti QGIS")
        self.popola_albero()
        layout.addWidget(self.tree)

        # Pulsante di esecuzione
        btn_esegui = QPushButton("Esegui Script Selezionato")
        btn_esegui.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        btn_esegui.clicked.connect(self.conferma_selezione)
        layout.addWidget(btn_esegui)

        self.setLayout(layout)

    def popola_albero(self):
        for categoria, elementi in self.catalogo.items():
            node_cat = QTreeWidgetItem(self.tree, [categoria])
            if isinstance(elementi, dict):
                for nome_script, url in elementi.items():
                    node_script = QTreeWidgetItem(node_cat, [nome_script])
                    node_script.setData(0, 32, url) # Memorizza l'URL direttamente nel nodo dell'albero

    def conferma_selezione(self):
        item_selezionato = self.tree.currentItem()
        if item_selezionato:
            url = item_selezionato.data(0, 32)
            if url:
                self.url_selezionato = url
                self.accept()
            else:
                QMessageBox.warning(self, "Attenzione", "Seleziona uno script valido, non una categoria!")
        else:
            QMessageBox.warning(self, "Attenzione", "Nessun elemento selezionato!")

# 3. Funzione di Download ed Esecuzione Dinamica dello Script
def esegui_script_da_url(url):
    try:
        # Scarica il codice sorgente dallo storage GitHub
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            codice_python = response.read().decode('utf-8')
        
        # Prepara l'ambiente di esecuzione globale includendo l'interfaccia di QGIS
        ambiente_globale = {
            'iface': iface,
            '__name__': '__main__'
        }
        
        # Esegue lo codice scaricato
        exec(codice_python, ambiente_globale)
        
        # Se lo script scaricato definisce una funzione `run()`, la invoca direttamente
        if 'run' in ambiente_globale and callable(ambiente_globale['run']):
            ambiente_globale['run']()

    except Exception as e:
        QMessageBox.critical(None, "Errore di Esecuzione", f"Impossibile scaricare o eseguire lo script:\n{str(e)}")

# 4. Entrypoint Principale
def run():
    dialogo = MaxxiCloudLoaderDialog(CATALOGO_SCRIPTS)
    if dialogo.exec_() == QDialog.Accepted and dialogo.url_selezionato:
        esegui_script_da_url(dialogo.url_selezionato)

# Consente l'esecuzione immediata dalla console Python di QGIS
if __name__ == '__main__':
    run()
