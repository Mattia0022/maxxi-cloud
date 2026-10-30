# -*- coding: utf-8 -*-
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QLabel, 
    QAbstractItemView, QWidget, QTextBrowser
)
from qgis.core import QgsProject

class GestoreTemiVerticale(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestione Rapida Layer-Temi")
        self.resize(1300, 700)
        self.setStyleSheet("font-size: 11pt;")

        self.project = QgsProject.instance()
        self.themes = self.project.mapThemeCollection()

        # Cache interna in memoria per non perdere le modifiche prima del salvataggio
        # Struttura: { layer_id: set(nomi_temi_in_cui_e_visibile) }
        self.cache_stati = {}
        self._inizializza_cache()

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

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

        btn_salva = QPushButton("💾 Salva Tutte le Modifiche nel Progetto")
        btn_salva.setStyleSheet("background-color: #e8f5e9; font-weight: bold; padding: 8px 14px; border-radius: 4px;")
        btn_salva.clicked.connect(self.salva_modifiche)
        lay_top.addWidget(btn_salva)

        main_layout.addLayout(lay_top)

        # ----------------------------------------------------
        # PANNELLI CENTRALI A 3 COLONNE (Layer | Temi | Guida)
        # ----------------------------------------------------
        lay_split = QHBoxLayout()
        lay_split.setSpacing(15)

        # --- COLONNA 1: LAYER ---
        lay_sinistra = QVBoxLayout()
        lay_sinistra.addWidget(QLabel("<b>1. Seleziona Layer (uno o più con CTRL/SHIFT):</b>"))
        
        self.search_layer = QLineEdit()
        self.search_layer.setPlaceholderText("🔍 Cerca layer...")
        self.search_layer.textChanged.connect(self.filtra_layer)
        lay_sinistra.addWidget(self.search_layer)

        self.list_layers = QListWidget()
        self.list_layers.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_layers.itemSelectionChanged.connect(self.aggiorna_stato_temi_destra)
        lay_sinistra.addWidget(self.list_layers)

        lay_split.addLayout(lay_sinistra, 1)

        # --- COLONNA 2: TEMI DI MAPPA ---
        lay_centro = QVBoxLayout()
        lay_centro.addWidget(QLabel("<b>2. In quali temi devono essere visibili?</b>"))
        
        self.search_tema = QLineEdit()
        self.search_tema.setPlaceholderText("🔍 Cerca tema...")
        self.search_tema.textChanged.connect(self.filtra_temi)
        lay_centro.addWidget(self.search_tema)

        self.list_temi = QListWidget()
        self.list_temi.itemChanged.connect(self.on_tema_item_changed)
        lay_centro.addWidget(self.list_temi)

        # Pulsanti rapidi per la lista dei temi
        lay_temi_rec = QHBoxLayout()
        btn_tutti_si = QPushButton("✔ Spunta Tutti")
        btn_tutti_si.clicked.connect(lambda: self.imposta_tutti_temi(True))
        btn_tutti_no = QPushButton("✖ Togli Tutti")
        btn_tutti_no.clicked.connect(lambda: self.imposta_tutti_temi(False))
        lay_temi_rec.addWidget(btn_tutti_si)
        lay_temi_rec.addWidget(btn_tutti_no)
        lay_centro.addLayout(lay_temi_rec)

        lay_split.addLayout(lay_centro, 1)

        # --- COLONNA 3: GUIDA DETTAGLIATA FISSA A DESTRA ---
        lay_destra = QVBoxLayout()
        lay_destra.addWidget(QLabel("<b>ℹ️ Guida d'Uso Rapida:</b>"))
        
        guida_browser = QTextBrowser()
        guida_browser.setOpenExternalLinks(True)
        guida_browser.setHtml("""
            <h3 style='color: #0277bd; margin-top: 0;'>📖 Come funziona</h3>
            <p>Gestisci centinaia di layer su decine di temi senza scorrimenti orizzontali.</p>
            
            <hr style='border: 0; border-top: 1px solid #ccc;'>
            
            <h4 style='color: #333;'>1. Selezione Layer</h4>
            <ul>
                <li>Cerca o seleziona uno o più layer a sinistra (usa <code>CTRL</code> o <code>SHIFT</code>).</li>
            </ul>

            <h4 style='color: #333;'>2. Modifiche in Memoria</h4>
            <ul>
                <li>Spunta o togli i temi al centro: <b>le modifiche vengono memorizzate subito in memoria</b> mentre clicchi.</li>
                <li>Puoi cambiare selezione a sinistra senza perdere nulla.</li>
            </ul>

            <h4 style='color: #333;'>3. Salvataggio Definitivo</h4>
            <ul>
                <li>Solo quando hai finito, clicca in alto su <b>💾 Salva Tutte le Modifiche nel Progetto</b> per applicarle a QGIS.</li>
            </ul>

            <h4 style='color: #333;'>4. Gestione Temi</h4>
            <ul>
                <li>Usa i pulsanti in alto per creare nuovi temi o eliminarne di esistenti.</li>
            </ul>
        """)
        lay_destra.addWidget(guida_browser)
        
        lay_split.addLayout(lay_destra, 1)
        main_layout.addLayout(lay_split)

        self.carica_layers()
        self.carica_temi_struttura()

    def _inizializza_cache(self):
        tema_names = self.themes.mapThemes()
        layers = self.project.mapLayers().values()
        for layer in layers:
            layer_id = layer.id()
            temi_visibili = set()
            for tema_name in tema_names:
                visible_layers = self.themes.mapThemeVisibleLayers(tema_name)
                if any(l and l.id() == layer_id for l in visible_layers):
                    temi_visibili.add(tema_name)
            self.cache_stati[layer_id] = temi_visibili

    def carica_layers(self):
        self.list_layers.blockSignals(True)
        self.list_layers.clear()
        layers = sorted(self.project.mapLayers().values(), key=lambda l: l.name().lower())
        for layer in layers:
            item = QListWidgetItem(layer.name())
            item.setData(Qt.UserRole, layer.id())
            self.list_layers.addItem(item)
        self.list_layers.blockSignals(False)
        if self.list_layers.count() > 0:
            self.list_layers.setCurrentRow(0)

    def carica_temi_struttura(self):
        self.list_temi.blockSignals(True)
        self.list_temi.clear()
        tema_names = sorted(self.themes.mapThemes())
        for tema_name in tema_names:
            item = QListWidgetItem(tema_name)
            item.setData(Qt.UserRole, tema_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_temi.addItem(item)
        self.list_temi.blockSignals(False)

    def filtra_layer(self, text):
        text_lower = text.lower()
        for i in range(self.list_layers.count()):
            item = self.list_layers.item(i)
            item.setHidden(text_lower not in item.text().lower())

    def filtra_temi(self, text):
        text_lower = text.lower()
        for i in range(self.list_temi.count()):
            item = self.list_temi.item(i)
            item.setHidden(text_lower not in item.text().lower())

    def aggiorna_stato_temi_destra(self):
        selected_items = self.list_layers.selectedItems()
        self.list_temi.blockSignals(True)
        
        if not selected_items:
            for i in range(self.list_temi.count()):
                self.list_temi.item(i).setCheckState(Qt.Unchecked)
            self.list_temi.blockSignals(False)
            return

        selected_layer_ids = [item.data(Qt.UserRole) for item in selected_items]
        
        for i in range(self.list_temi.count()):
            item_tema = self.list_temi.item(i)
            tema_name = item_tema.data(Qt.UserRole)
            
            # Verifica nella cache se il tema è attivo per TUTTI i layer selezionati
            tutti_attivi = all(tema_name in self.cache_stati.get(l_id, set()) for l_id in selected_layer_ids)
            item_tema.setCheckState(Qt.Checked if tutti_attivi else Qt.Unchecked)
            
        self.list_temi.blockSignals(False)

    def on_tema_item_changed(self, item):
        # Aggiorna immediatamente la cache in memoria quando l'utente spunta/toglie un tema
        if not item.flags() & Qt.ItemIsUserCheckable:
            return
        
        selected_items = self.list_layers.selectedItems()
        if not selected_items:
            return

        tema_name = item.data(Qt.UserRole)
        is_checked = (item.checkState() == Qt.Checked)
        selected_layer_ids = [li.data(Qt.UserRole) for li in selected_items]

        for layer_id in selected_layer_ids:
            if layer_id not in self.cache_stati:
                self.cache_stati[layer_id] = set()
            
            if is_checked:
                self.cache_stati[layer_id].add(tema_name)
            else:
                self.cache_stati[layer_id].discard(tema_name)

    def imposta_tutti_temi(self, stato):
        self.list_temi.blockSignals(True)
        state_chk = Qt.Checked if stato else Qt.Unchecked
        selected_items = self.list_layers.selectedItems()
        selected_layer_ids = [li.data(Qt.UserRole) for li in selected_items]

        for i in range(self.list_temi.count()):
            item = self.list_temi.item(i)
            if not item.isHidden():
                item.setCheckState(state_chk)
                tema_name = item.data(Qt.UserRole)
                if selected_items:
                    for layer_id in selected_layer_ids:
                        if layer_id not in self.cache_stati:
                            self.cache_stati[layer_id] = set()
                        if stato:
                            self.cache_stati[layer_id].add(tema_name)
                        else:
                            self.cache_stati[layer_id].discard(tema_name)
                            
        self.list_temi.blockSignals(False)

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
            
            # Aggiorna la cache per includere il nuovo tema
            for layer_id in self.cache_stati:
                visible_layers = self.themes.mapThemeVisibleLayers(nome)
                if any(l and l.id() == layer_id for l in visible_layers):
                    self.cache_stati[layer_id].add(nome)

            self.carica_temi_struttura()
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
                
                # Rimuovi il tema eliminato dalla cache
                for layer_id in self.cache_stati:
                    self.cache_stati[layer_id].discard(tema_scelto)

                self.carica_temi_struttura()
                QMessageBox.information(self, "Eliminato", f"Tema '{tema_scelto}' eliminato.")

    def salva_modifiche(self):
        root = self.project.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        tema_names = sorted(self.themes.mapThemes())

        if not tema_names:
            QMessageBox.warning(self, "Attenzione", "Nessun tema da aggiornare.")
            return

        # Scrive la cache in memoria dentro i temi di mappa effettivi di QGIS
        for tema_name in tema_names:
            self.themes.applyTheme(tema_name, root, model)

            for layer_id, temi_attivi in self.cache_stati.items():
                deve_essere_visibile = (tema_name in temi_attivi)
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

        iface.mapCanvas().refresh()
        QMessageBox.information(self, "Completato", "Tutte le modifiche memorizzate sono state salvate con successo nel progetto QGIS!")

def run():
    if hasattr(iface, "maxxi_matrice_dlg") and iface.maxxi_matrice_dlg is not None:
        try:
            if iface.maxxi_matrice_dlg.isVisible():
                iface.maxxi_matrice_dlg.raise_()
                iface.maxxi_matrice_dlg.activateWindow()
                return
        except RuntimeError:
            pass

    iface.maxxi_matrice_dlg = GestoreTemiVerticale(iface.mainWindow())
    iface.maxxi_matrice_dlg.show()

run()
