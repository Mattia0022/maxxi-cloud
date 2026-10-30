# -*- coding: utf-8 -*-
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QMessageBox, QLabel, QInputDialog, QAbstractItemView
)
from qgis.core import QgsProject

class GestoreLayerNeiTemi(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestione Rapida: Layer nei Temi di Mappa")
        self.resize(800, 520)
        self.setStyleSheet("font-size: 11pt;")

        self.project = QgsProject.instance()
        self.themes = self.project.mapThemeCollection()

        layout = QHBoxLayout(self)
        layout.setSpacing(15)

        # ----------------------------------------------------
        # PANNELLO SINISTRO: SELEZIONE MULTIPLA LAYER
        # ----------------------------------------------------
        lay_sinistra = QVBoxLayout()
        lay_sinistra.addWidget(QLabel("<b>1. Seleziona uno o più Layer:</b><br>(Usa CTRL o SHIFT per selezioni multiple)"))
        
        self.search_layer = QLineEdit()
        self.search_layer.setPlaceholderText("🔍 Cerca layer...")
        self.search_layer.textChanged.connect(self.filtra_layer)
        lay_sinistra.addWidget(self.search_layer)

        self.list_layers = QListWidget()
        self.list_layers.setSelectionMode(QAbstractItemView.ExtendedSelection) # ABILITA MULTI-SELEZIONE
        self.list_layers.itemSelectionChanged.connect(self.aggiorna_stato_temi)
        lay_sinistra.addWidget(self.list_layers)
        
        layout.addLayout(lay_sinistra, 1)

        # ----------------------------------------------------
        # PANNELLO DESTRO: TEMI E SPUNTE
        # ----------------------------------------------------
        lay_destra = QVBoxLayout()
        lay_destra.addWidget(QLabel("<b>2. In quali temi devono essere visibili?</b><br>(Spunta per aggiungere, deseleziona per rimuovere)"))

        self.list_temi = QListWidget()
        lay_destra.addWidget(self.list_temi)

        # Pulsante per creare un tema al volo se la lista è vuota
        btn_nuovo_tema = QPushButton("➕ Crea Nuovo Tema in QGIS")
        btn_nuovo_tema.clicked.connect(self.crea_nuovo_tema)
        lay_destra.addWidget(btn_nuovo_tema)

        btn_salva = QPushButton("💾 Salva Modifiche per i Layer Selezionati")
        btn_salva.setStyleSheet("font-weight: bold; background-color: #e1f5fe; padding: 10px; border-radius: 4px;")
        btn_salva.clicked.connect(self.salva_modifiche)
        lay_destra.addWidget(btn_salva)

        layout.addLayout(lay_destra, 1)

        self.popola_layers()
        self.popola_temi()

    def popola_layers(self):
        self.list_layers.blockSignals(True)
        self.list_layers.clear()
        for layer in sorted(self.project.mapLayers().values(), key=lambda l: l.name().lower()):
            item = QListWidgetItem(layer.name())
            item.setData(Qt.UserRole, layer.id())
            self.list_layers.addItem(item)
        self.list_layers.blockSignals(False)

        if self.list_layers.count() > 0:
            self.list_layers.setCurrentRow(0)

    def popola_temi(self):
        self.list_temi.clear()
        tutti_temi = sorted(self.themes.mapThemes())
        
        if not tutti_temi:
            item = QListWidgetItem("⚠️ Nessun tema trovato nel progetto. Creane uno!")
            item.setFlags(Qt.NoItemFlags)
            self.list_temi.addItem(item)
            return

        for tema_nome in tutti_temi:
            item = QListWidgetItem(tema_nome)
            item.setData(Qt.UserRole, tema_nome)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_temi.addItem(item)

    def filtra_layer(self, text):
        text_lower = text.lower()
        for i in range(self.list_layers.count()):
            item = self.list_layers.item(i)
            match = text_lower in item.text().lower()
            item.setHidden(not match)

    def aggiorna_stato_temi(self):
        selected_items = self.list_layers.selectedItems()
        tutti_temi = sorted(self.themes.mapThemes())
        
        if not tutti_temi:
            return

        self.list_temi.clear()
        root = self.project.layerTreeRoot()

        for tema_nome in tutti_temi:
            state = self.themes.mapThemeState(tema_nome)
            
            # Se ci sono layer selezionati, verifichiamo se TUTTI i layer selezionati sono visibili in questo tema
            visibile_in_tutti = True
            if selected_items:
                for sel_item in selected_items:
                    layer_id = sel_item.data(Qt.UserRole)
                    visibile_singolo = False
                    
                    is_in_tema = False
                    for rec in state.layerRecords():
                        if rec.layer() and rec.layer().id() == layer_id:
                            is_in_tema = True
                            if rec.isVisible:
                                visibile_singolo = True
                            break
                    
                    if not is_in_tema:
                        tree_group = state.toGroup()
                        if tree_group:
                            node = tree_group.findLayer(layer_id)
                            if node and node.isVisible():
                                visibile_singolo = True
                                
                    if not visibile_singolo:
                        visibile_in_tutti = False
                        break
            else:
                visibile_in_tutti = False

            item = QListWidgetItem(tema_nome)
            item.setData(Qt.UserRole, tema_nome)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked if visibile_in_tutti else Qt.Unchecked)
            self.list_temi.addItem(item)

    def crea_nuovo_tema(self):
        nome, ok = QInputDialog.getText(self, "Nuovo Tema", "Nome del nuovo tema mappa:")
        if ok and nome.strip():
            nome = nome.strip()
            if self.themes.hasMapTheme(nome):
                QMessageBox.warning(self, "Errore", "Esiste già un tema con questo nome.")
                return
            root = self.project.layerTreeRoot()
            model = iface.layerTreeView().layerTreeModel()
            rec = self.themes.createThemeFromCurrentState(root, model)
            self.themes.insert(nome, rec)
            self.popola_temi()
            self.aggiorna_stato_temi()
            QMessageBox.information(self, "Creato", f"Tema '{nome}' creato con successo!")

    def salva_modifiche(self):
        selected_layer_items = self.list_layers.selectedItems()
        if not selected_layer_items:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un layer a sinistra.")
            return

        layer_ids = [item.data(Qt.UserRole) for item in selected_layer_items]
        root = self.project.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()

        # Cicla su tutti i temi presenti nella lista di destra
        for i in range(self.list_temi.count()):
            item = self.list_temi.item(i)
            tema_nome = item.data(Qt.UserRole)
            if not tema_nome:
                continue
            
            deve_essere_visibile = (item.checkState() == Qt.Checked)

            # Carica il tema in QGIS
            self.themes.applyTheme(tema_nome, root, model)

            # Modifica lo stato per ciascuno dei layer selezionati
            for layer_id in layer_ids:
                node = root.findLayer(layer_id)
                if node:
                    node.setItemVisibilityChecked(deve_essere_visibile)
                    if deve_essere_visibile:
                        p = node.parent()
                        while p and p != root:
                            p.setItemVisibilityChecked(True)
                            p = p.parent()

            # Salva le modifiche nel tema
            rec = self.themes.createThemeFromCurrentState(root, model)
            self.themes.insert(tema_nome, rec)

        QMessageBox.information(self, "Successo", f"Stato aggiornato con successo per i {len(layer_ids)} layer selezionati!")

def run():
    dlg = GestoreLayerNeiTemi(iface.mainWindow())
    dlg.show()
    iface.maxxi_layer_temi_dlg = dlg

run()
