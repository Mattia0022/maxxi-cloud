# -*- coding: utf-8 -*-
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QLabel, 
    QAbstractItemView, QWidget, QTextBrowser
)
from qgis.core import QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer

class GestoreTemiVerticale(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestione Rapida Layer e Gruppi nei Temi")
        self.resize(1300, 700)
        self.setStyleSheet("font-size: 11pt;")

        self.project = QgsProject.instance()
        self.themes = self.project.mapThemeCollection()

        # Cache interna in memoria per layer e gruppi: { chiave_elemento: set(temi_attivi) }
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
        # PANNELLI CENTRALI A 3 COLONNE (Elementi | Temi | Guida)
        # ----------------------------------------------------
        lay_split = QHBoxLayout()
        lay_split.setSpacing(15)

        # --- COLONNA 1: LAYER E GRUPPI ---
        lay_sinistra = QVBoxLayout()
        lay_sinistra.addWidget(QLabel("<b>1. Seleziona Layer o Gruppi (anche multipli):</b>"))
        
        self.search_layer = QLineEdit()
        self.search_layer.setPlaceholderText("🔍 Cerca layer o gruppo...")
        self.search_layer.textChanged.connect(self.filtra_elementi)
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
            
            <hr style='border: 0; border-top: 1px solid #ccc;'>
            
            <h4 style='color: #333;'>1. Selezione Elementi</h4>
            <ul>
                <li>Puoi selezionare sia singoli <b>Layer</b> che interi <b>Gruppi</b> (usa <code>CTRL</code> o <code>SHIFT</code> per selezioni multiple).</li>
            </ul>

            <h4 style='color: #333;'>2. Modifiche in Memoria</h4>
            <ul>
                <li>Spunta o togli i temi al centro: <b>le modifiche vengono memorizzate subito in memoria</b>.</li>
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

        self.carica_elementi_albero()
        self.carica_temi_struttura()

    def get_group_path(self, group_node):
        parts = []
        curr = group_node
        root = self.project.layerTreeRoot()
        while curr and curr != root:
            parts.insert(0, curr.name())
            curr = curr.parent()
        return "/".join(parts)

    def _inizializza_cache(self):
        tema_names = self.themes.mapThemes()
        root = self.project.layerTreeRoot()
        self.cache_stati = {}

        def collect_keys(node):
            keys = []
            for child in node.children():
                if isinstance(child, QgsLayerTreeGroup):
                    keys.append(f"G:{self.get_group_path(child)}")
                    keys.extend(collect_keys(child))
                elif isinstance(child, QgsLayerTreeLayer):
                    if child.layer():
                        keys.append(f"L:{child.layer().id()}")
            return keys

        all_keys = collect_keys(root)
        for k in all_keys:
            self.cache_stati[k] = set()

        for tema_name in tema_names:
            clone_root = root.clone()
            self.themes.applyTheme(tema_name, clone_root, None)

            def check_clone_node(node):
                for child in node.children():
                    if isinstance(child, QgsLayerTreeGroup):
                        g_key = f"G:{self.get_group_path(child)}"
                        if child.itemVisibilityChecked():
                            self.cache_stati[g_key].add(tema_name)
                        check_clone_node(child)
                    elif isinstance(child, QgsLayerTreeLayer):
                        layer = child.layer()
                        if layer:
                            l_key = f"L:{layer.id()}"
                            if child.itemVisibilityChecked():
                                self.cache_stati[l_key].add(tema_name)

            check_clone_node(clone_root)

    def carica_elementi_albero(self):
        self.list_layers.blockSignals(True)
        self.list_layers.clear()
        root = self.project.layerTreeRoot()

        def add_nodes(node, indent=0):
            for child in node.children():
                prefix = "    " * indent
                if isinstance(child, QgsLayerTreeGroup):
                    item = QListWidgetItem(f"{prefix}📁 {child.name()}")
                    item.setData(Qt.UserRole, f"G:{self.get_group_path(child)}")
                    item.setForeground(Qt.darkBlue)
                    self.list_layers.addItem(item)
                    add_nodes(child, indent + 1)
                elif isinstance(child, QgsLayerTreeLayer):
                    layer = child.layer()
                    if layer:
                        item = QListWidgetItem(f"{prefix} 📄 {layer.name()}")
                        item.setData(Qt.UserRole, f"L:{layer.id()}")
                        self.list_layers.addItem(item)

        add_nodes(root)
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

    def filtra_elementi(self, text):
        text_lower = text.lower()
        for i in range(self.list_layers.count()):
            item = self.list_layers.item(i)
            item.setHidden(text_lower not in item.text().lower())

    def filtra_temi(self, text):
        text_lower = text.lower()
        for i in range(self.list_temi.count()):
            item = self.
