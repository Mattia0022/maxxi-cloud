# -*- coding: utf-8 -*-
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QInputDialog, QLabel, QAbstractItemView
)
from qgis.core import QgsProject

class MatriceTemiLayer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Matrice Completa: Layer & Temi di Mappa")
        self.resize(1150, 700)
        self.setStyleSheet("font-size: 11pt;")

        self.project = QgsProject.instance()
        self.themes = self.project.mapThemeCollection()

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ----------------------------------------------------
        # BARRA SUPERIORE: GESTIONE TEMI E SALVATAGGIO
        # ----------------------------------------------------
        lay_top = QHBoxLayout()
        
        btn_nuovo = QPushButton("➕ Crea Nuovo Tema")
        btn_nuovo.setStyleSheet("background-color: #e1f5fe; font-weight: bold; padding: 6px; border-radius: 4px;")
        btn_nuovo.clicked.connect(self.crea_tema)
        lay_top.addWidget(btn_nuovo)

        btn_elimina = QPushButton("🗑️ Elimina Tema...")
        btn_elimina.setStyleSheet("background-color: #ffebee; font-weight: bold; padding: 6px; border-radius: 4px;")
        btn_elimina.clicked.connect(self.elimina_tema)
        lay_top.addWidget(btn_elimina)

        lay_top.addStretch()

        btn_salva = QPushButton("💾 Salva Tutte le Modifiche")
        btn_salva.setStyleSheet("background-color: #e8f5e9; font-weight: bold; padding: 8px 12px; border-radius: 4px;")
        btn_salva.clicked.connect(self.salva_tutto)
        lay_top.addWidget(btn_salva)

        layout.addLayout(lay_top)

        # ----------------------------------------------------
        # BARRA DI RICERCA E AZIONI RAPIDE IN MASSA
        # ----------------------------------------------------
        lay_tools = QHBoxLayout()
        
        lay_tools.addWidget(QLabel("🔍 Cerca:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filtra per nome layer...")
        self.search_input.textChanged.connect(self.filtra_tabella)
        lay_tools.addWidget(self.search_input, 2)

        # Pulsanti rapidi per gestire più layer su TUTTI i temi in un click
        btn_tutti_si = QPushButton("✔ Spunta Sel. in TUTTI i Temi")
        btn_tutti_si.setStyleSheet("background-color: #e0f7fa; padding: 5px;")
        btn_tutti_si.clicked.connect(lambda: self.imposta_selezionati_in_tutti(True))
        lay_tools.addWidget(btn_tutti_si)

        btn_tutti_no = QPushButton("✖ Togli da TUTTI i Temi")
        btn_tutti_no.setStyleSheet("background-color: #fce4ec; padding: 5px;")
        btn_tutti_no.clicked.connect(lambda: self.imposta_selezionati_in_tutti(False))
        lay_tools.addWidget(btn_tutti_no)

        layout.addLayout(lay_tools)

        # ----------------------------------------------------
        # TABELLA A MATRICE (Layer x Temi)
        # ----------------------------------------------------
        self.tabella = QTableWidget()
        self.tabella.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabella.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.tabella)

        self.carica_dati()

    def get_visibilita_layer_in_tema(self, theme_name, layer_id):
        visible_layers = self.themes.mapThemeVisibleLayers(theme_name)
        return any(layer.id() == layer_id for layer in visible_layers)

    def carica_dati(self):
        self.tabella.blockSignals(True)
        self.tabella.clear()

        tema_names = sorted(self.themes.mapThemes())
        layers = sorted(self.project.mapLayers().values(), key=lambda l: l.name().lower())

        if not tema_names:
            self.tabella.setColumnCount(1)
            self.tabella.setHorizontalHeaderLabels(["Layer Progetto (Usa 'Crea Nuovo Tema' in alto per iniziare!)"])
            self.tabella.setRowCount(len(layers))
            for idx, layer in enumerate(layers):
                item = QTableWidgetItem(layer.name())
                item.setFlags(Qt.ItemIsEnabled)
                self.tabella.setItem(idx, 0, item)
            self.tabella.blockSignals(False)
            return

        columns = ["Layer Progetto"] + tema_names
        self.tabella.setColumnCount(len(columns))
        self.tabella.setHorizontalHeaderLabels(columns)
        self.tabella.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, len(columns)):
            self.tabella.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)

        self.tabella.setRowCount(len(layers))

        for r_idx, layer in enumerate(layers):
            item_layer = QTableWidgetItem(layer.name())
            item_layer.setData(Qt.UserRole, layer.id())
            item_layer.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tabella.setItem(r_idx, 0, item_layer)

            for c_idx, tema_name in enumerate(tema_names, start=1):
                visibile = self.get_visibilita_layer_in_tema(tema_name, layer.id())
                item_chk = QTableWidgetItem()
                item_chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item_chk.setCheckState(Qt.Checked if visibile else Qt.Unchecked)
                self.tabella.setItem(r_idx, c_idx, item_chk)

        self.tabella.blockSignals(False)

    def filtra_tabella(self, text):
        text_lower = text.lower()
        for r in range(self.tabella.rowCount()):
            item = self.tabella.item(r, 0)
            if item:
                match = text_lower in item.text().lower()
                self.tabella.setRowHidden(r, not match)

    def imposta_selezionati_in_tutti(self, stato):
        righe_sel = set(item.row() for item in self.tabella.selectedItems())
        if not righe_sel:
            QMessageBox.warning(self, "Attenzione", "Seleziona una o più righe di layer nella tabella (puoi usare CTRL o SHIFT).")
            return
        
        state_chk = Qt.Checked if stato else Qt.Unchecked
        self.tabella.blockSignals(True)
        for r in righe_sel:
            if not self.tabella.isRowHidden(r):
                for c in range(1, self.tabella.columnCount()):
                    item = self.tabella.item(r, c)
                    if item:
                        item.setCheckState(state_chk)
        self.tabella.blockSignals(False)
        QMessageBox.information(self, "Fatto", f"Stato aggiornato per i layer delle {len(righe_sel)} righe selezionate. Ricorda di cliccare 'Salva Tutte le Modifiche' in alto!")

    def crea_tema(self):
        nome, ok = QInputDialog.getText(self, "Nuovo Tema", "Inserisci il nome del nuovo tema di mappa:")
        if ok and nome.strip():
            nome = nome.strip()
            if self.themes.hasMapTheme(nome):
                QMessageBox.warning(self, "Errore", "Esiste già un tema con questo nome.")
                return
            root = self.project.layerTreeRoot()
            model = iface.layerTreeView().layerTreeModel()
            rec = self.themes.createThemeFromCurrentState(root, model)
            self.themes.insert(nome, rec)
            self.carica_dati()
            QMessageBox.information(self, "Successo", f"Tema '{nome}' creato con successo!")

    def elimina_tema(self):
        tema_names = sorted(self.themes.mapThemes())
        if not tema_names:
            QMessageBox.warning(self, "Attenzione", "Nessun tema presente nel progetto.")
            return
        
        tema_scelto, ok = QInputDialog.getItem(self, "Elimina Tema", "Seleziona il tema da eliminare:", tema_names, 0, False)
        if ok and tema_scelto:
            if QMessageBox.question(self, "Conferma", f"Vuoi davvero eliminare il tema '{tema_scelto}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.themes.removeMapTheme(tema_scelto)
                self.carica_dati()
                QMessageBox.information(self, "Eliminato", f"Tema '{tema_scelto}' eliminato.")

    def salva_tutto(self):
        root = self.project.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        tema_names = sorted(self.themes.mapThemes())

        if not tema_names:
            QMessageBox.warning(self, "Attenzione", "Nessun tema da aggiornare.")
            return

        for c_idx, tema_name in enumerate(tema_names, start=1):
            self.themes.applyTheme(tema_name, root, model)

            for r_idx in range(self.tabella.rowCount()):
                item_layer = self.tabella.item(r_idx, 0)
                if not item_layer:
                    continue
                layer_id = item_layer.data(Qt.UserRole)
                
                item_chk = self.tabella.item(r_idx, c_idx)
                if item_chk:
                    deve_essere_visibile = (item_chk.checkState() == Qt.Checked)
                    
                    node = root.findLayer(layer_id)
                    if node:
                        node.setItemVisibilityChecked(deve_essere_visibile)
                        if deve_essere_visibile:
                            p = node.parent()
                            while p and p != root:
                                p.setItemVisibilityChecked(True)
                                p = p.parent()

            rec = self.themes.createThemeFromCurrentState(root, model)
            self.themes.insert(tema_name, rec)

        QMessageBox.information(self, "Completato", "Tutte le modifiche ai temi sono state salvate con successo!")

def run():
    # Gestione finestra singola (evita duplicati)
    if hasattr(iface, "maxxi_matrice_dlg") and iface.maxxi_matrice_dlg is not None:
        try:
            if iface.maxxi_matrice_dlg.isVisible():
                iface.maxxi_matrice_dlg.raise_()
                iface.maxxi_matrice_dlg.activateWindow()
                return
        except RuntimeError:
            pass

    iface.maxxi_matrice_dlg = MatriceTemiLayer(iface.mainWindow())
    iface.maxxi_matrice_dlg.show()

run()
