# -*- coding: utf-8 -*-
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QLabel, 
    QAbstractItemView, QTabWidget, QWidget, QTextBrowser
)
from qgis.core import QgsProject

class GestoreTemiVerticale(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestione Rapida Layer-Temi (Verticale)")
        self.resize(1150, 700)
        self.setStyleSheet("font-size: 11pt;")

        self.project = QgsProject.instance()
        self.themes = self.project.mapThemeCollection()

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

        btn_salva = QPushButton("💾 Salva Modifiche per i Layer Selezionati")
        btn_salva.setStyleSheet("background-color: #e8f5e9; font-weight: bold; padding: 8px 14px; border-radius: 4px;")
        btn_salva.clicked.connect(self.salva_modifiche)
        lay_top.addWidget(btn_salva)

        main_layout.addLayout(lay_top)

        # ----------------------------------------------------
        # PANNELLI CENTRALI (2 Colonne Verticali)
        # ----------------------------------------------------
        lay_split = QHBoxLayout()
        lay_split.setSpacing(15)

        # --- COLONNA SINISTRA: LAYER ---
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

        # --- COLONNA DESTRA: TAB WIDGET (Temi di Mappa + Guida) ---
        self.tab_destra = QTabWidget()

        # SCHEDA 1: ELENCO TEMI
        w_temi = QWidget()
        lay_temi_tab = QVBoxLayout(w_temi)
        lay_temi_tab.addWidget(QLabel("<b>2. In quali temi devono essere visibili? (Spunta/Togli):</b>"))
        
        self.search_tema = QLineEdit()
        self.search_tema.setPlaceholderText("🔍 Cerca tema...")
        self.search_tema.textChanged.connect(self.filtra_temi)
        lay_temi_tab.addWidget(self.search_tema)

        self.list_temi = QListWidget()
        lay_temi_tab.addWidget(self.list_temi)

        # Pulsanti rapidi per la lista dei temi
        lay_temi_rec = QHBoxLayout()
        btn_tutti_si = QPushButton("✔ Spunta Tutti")
        btn_tutti_si.clicked.connect(lambda: self.imposta_tutti_temi(True))
        btn_tutti_no = QPushButton("✖ Togli Tutti")
        btn_tutti_no.clicked.connect(lambda: self.imposta_tutti_temi(False))
        lay_temi_rec.addWidget(btn_tutti_si)
        lay_temi_rec.addWidget(btn_tutti_no)
        lay_temi_tab.addLayout(lay_temi_rec)

        self.tab_destra.addTab(w_temi, "🗺️ Temi di Mappa")

        # SCHEDA 2: GUIDA DETTAGLIATA
        w_guida = QWidget()
        lay_guida = QVBoxLayout(w_guida)
        guida_browser = QTextBrowser()
        guida_browser.setOpenExternalLinks(True)
        guida_browser.setHtml("""
            <h3 style='color: #0277bd; margin-top: 0;'>📖 Guida d'Uso: Gestore Temi di Mappa</h3>
            <p>Questo strumento è progettato per gestire in modo rapido e senza scorrimenti orizzontali grandi quantità di layer (~200) su numerosi temi mappa (~40).</p>
            
            <hr style='border: 0; border-top: 1px solid #ccc;'>
            
            <h4 style='color: #333;'>1. Selezione dei Layer (a sinistra)</h4>
            <ul>
                <li>Usa la casella <b>🔍 Cerca layer...</b> per filtrare rapidamente l'elenco.</li>
                <li>Puoi selezionare <b>un singolo layer</b> oppure <b>più layer insieme</b> tenendo premuto <code>CTRL</code> o <code>SHIFT</code>.</li>
            </ul>

            <h4 style='color: #333;'>2. Gestione delle Spunte (scheda 'Temi di Mappa')</h4>
            <ul>
                <li>Selezionando uno o più layer, la colonna di destra mostrerà lo stato: un tema ha la spunta solo se <b>tutti</b> i layer selezionati sono visibili in esso.</li>
                <li><b>Spunta o rimuovi la spunta</b> dai temi in cui vuoi aggiungere o togliere i layer selezionati.</li>
                <li>Usa i pulsanti in basso <b>Spunta Tutti / Togli Tutti</b> o la ricerca rapida dei temi per velocizzare l'operazione.</li>
            </ul>

            <h4 style='color: #333;'>3. Salvataggio delle Modifiche</h4>
            <ul>
                <li>Dopo aver configurato le spunte, clicca sul pulsante verde in alto a destra: <br><b>💾 Salva Modifiche per i Layer Selezionati</b>.</li>
                <li>Il sistema aggiornerà istantaneamente il progetto QGIS, accendendo automaticamente anche i gruppi genitori necessari per la corretta visualizzazione.</li>
            </ul>

            <h4 style='color: #333;'>4. Creazione ed Eliminazione Temi</h4>
            <ul>
                <li><b>➕ Crea Nuovo Tema:</b> Registra un nuovo tema basato sullo stato attuale della mappa.</li>
                <li><b>🗑️ Elimina Tema...:</b> Cancella un tema esistente dal progetto.</li>
            </ul>
        """)
        lay_guida.addWidget(guida_browser)
        self.tab_destra.addTab(w_guida, "ℹ️ Guida Dettagliata")

        lay_split.addWidget(self.tab_destra, 1)
        main_layout.addLayout(lay_split)

        self.carica_layers()
        self.carica_temi_struttura()

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
        self.list_temi.clear()
        tema_names = sorted(self.themes.mapThemes())
        for tema_name in tema_names:
            item = QListWidgetItem(tema_name)
            item.setData(Qt.UserRole, tema_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_temi.addItem(item)

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
        if not selected_items:
            for i in range(self.list_temi.count()):
                self.list_temi.item(i).setCheckState(Qt.Unchecked)
            return

        selected_layer_ids = [item.data(Qt.UserRole) for item in selected_items]
        
        for i in range(self.list_temi.count()):
            item_tema = self.list_temi.item(i)
            tema_name = item_tema.data(Qt.UserRole)
            
            visible_layers = self.themes.mapThemeVisibleLayers(tema_name)
            visible_ids = {l.id() for l in visible_layers if l}
            
            tutti_visibili = all(layer_id in visible_ids for layer_id in selected_layer_ids)
            item_tema.setCheckState(Qt.Checked if tutti_visibili else Qt.Unchecked)

    def imposta_tutti_temi(self, stato):
        state_chk = Qt.Checked if stato else Qt.Unchecked
        for i in range(self.list_temi.count()):
            item = self.list_temi.item(i)
            if not item.isHidden():
                item.setCheckState(state_chk)

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
                self.carica_temi_struttura()
                QMessageBox.information(self, "Eliminato", f"Tema '{tema_scelto}' eliminato.")

    def salva_modifiche(self):
        selected_layer_items = self.list_layers.selectedItems()
        if not selected_layer_items:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un layer nella colonna di sinistra.")
            return

        layer_ids = [item.data(Qt.UserRole) for item in selected_layer_items]
        root = self.project.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()

        temi_stati = {}
        for i in range(self.list_temi.count()):
            item_tema = self.list_temi.item(i)
            tema_name = item_tema.data(Qt.UserRole)
            temi_stati[tema_name] = (item_tema.checkState() == Qt.Checked)

        for tema_name, deve_essere_visibile in temi_stati.items():
            self.themes.applyTheme(tema_name, root, model)

            for layer_id in layer_ids:
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
        QMessageBox.information(self, "Completato", f"Stato aggiornato con successo per i {len(layer_ids)} layer selezionati in tutti i temi!")

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
