# -*- coding: utf-8 -*-
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QMessageBox, QLabel
)
from qgis.core import QgsProject

class GestoreLayerNeiTemi(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestione Rapida: Layer nei Temi di Mappa")
        self.resize(750, 480)
        self.setStyleSheet("font-size: 11pt;")

        self.project = QgsProject.instance()
        self.themes = self.project.mapThemeCollection()

        layout = QHBoxLayout(self)
        layout.setSpacing(15)

        # ----------------------------------------------------
        # PANNELLO SINISTRO: SELEZIONE LAYER
        # ----------------------------------------------------
        lay_sinistra = QVBoxLayout()
        lay_sinistra.addWidget(QLabel("<b>1. Seleziona il Layer:</b>"))
        
        self.search_layer = QLineEdit()
        self.search_layer.setPlaceholderText("🔍 Cerca layer...")
        self.search_layer.textChanged.connect(self.filtra_layer)
        lay_sinistra.addWidget(self.search_layer)

        self.list_layers = QListWidget()
        self.list_layers.currentItemChanged.connect(self.aggiorna_stato_temi)
        lay_sinistra.addWidget(self.list_layers)
        
        layout.addLayout(lay_sinistra, 1)

        # ----------------------------------------------------
        # PANNELLO DESTRO: TEMI E SPUNTE
        # ----------------------------------------------------
        lay_destra = QVBoxLayout()
        lay_destra.addWidget(QLabel("<b>2. In quali temi deve essere visibile?</b><br>(Spunta per aggiungere, deseleziona per rimuovere)"))

        self.list_temi = QListWidget()
        lay_destra.addWidget(self.list_temi)

        btn_salva = QPushButton("💾 Salva Modifiche per questo Layer")
        btn_salva.setStyleSheet("font-weight: bold; background-color: #e1f5fe; padding: 10px; border-radius: 4px;")
        btn_salva.clicked.connect(self.salva_modifiche)
        lay_destra.addWidget(btn_salva)

        layout.addLayout(lay_destra, 1)

        self.popola_layers()

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

    def filtra_layer(self, text):
        text_lower = text.lower()
        for i in range(self.list_layers.count()):
            item = self.list_layers.item(i)
            match = text_lower in item.text().lower()
            item.setHidden(not match)

    def aggiorna_stato_temi(self, current_item, previous_item):
        if not current_item:
            self.list_temi.clear()
            return

        self.list_temi.clear()
        layer_id = current_item.data(Qt.UserRole)
        tutti_temi = sorted(self.themes.mapThemes())

        root = self.project.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()

        for tema_nome in tutti_temi:
            state = self.themes.mapThemeState(tema_nome)
            visibile = False
            
            # Controlla se il layer è visibile nel tema specifico
            is_in_tema = False
            for rec in state.layerRecords():
                if rec.layer() and rec.layer().id() == layer_id:
                    is_in_tema = True
                    if rec.isVisible:
                        visibile = True
                    break
            
            if not is_in_tema:
                tree_group = state.toGroup()
                if tree_group:
                    node = tree_group.findLayer(layer_id)
                    if node and node.isVisible():
                        visibile = True

            item = QListWidgetItem(tema_nome)
            item.setData(Qt.UserRole, tema_nome)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if visibile else Qt.Unchecked)
            self.list_temi.addItem(item)

    def salva_modifiche(self):
        current_layer_item = self.list_layers.currentItem()
        if not current_layer_item:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un layer.")
            return

        layer_id = current_layer_item.data(Qt.UserRole)
        layer_nome = current_layer_item.text()

        root = self.project.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()

        # Aggiorna lo stato del layer per ogni tema spuntato o desuntato a destra
        for i in range(self.list_temi.count()):
            item = self.list_temi.item(i)
            tema_nome = item.data(Qt.UserRole)
            deve_essere_visibile = (item.checkState() == Qt.Checked)

            # Carica il tema in QGIS
            self.themes.applyTheme(tema_nome, root, model)

            # Modifica la visibilità del layer (e accende i gruppi genitori se serve)
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

        QMessageBox.information(self, "Successo", f"Stato del layer '{layer_nome}' aggiornato con successo in tutti i temi!")

def run():
    dlg = GestoreLayerNeiTemi(iface.mainWindow())
    dlg.show()
    iface.maxxi_layer_temi_dlg = dlg

run()
