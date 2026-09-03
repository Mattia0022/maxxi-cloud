from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QGroupBox, QMessageBox, QInputDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QWidget, QTextEdit, QLabel
)
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject

class GestoreTemiAvanzato(QDialog):
    def __init__(self, guida_testo="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestore Temi Mappa")
        self.resize(1200, 600)

        self.project = QgsProject.instance()
        self.themes = self.project.mapThemeCollection()
        self.caricamento = False

        self.init_ui(guida_testo)
        self.carica_temi()

    def init_ui(self, guida_testo):
        # Layout principale orizzontale a tre sezioni
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # =====================================================
        # 1. PANNELLO TEMI MAPPA (A SINISTRA)
        # =====================================================
        box_temi = QGroupBox("1. Temi Mappa (CTRL per multipli)")
        lay_temi = QVBoxLayout(box_temi)

        self.lista_temi = QListWidget()
        self.lista_temi.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lista_temi.itemSelectionChanged.connect(self.aggiorna_vista_layer)
        lay_temi.addWidget(self.lista_temi)

        lay_btns = QHBoxLayout()
        btn_add = QPushButton("+ Nuovo Tema")
        btn_del = QPushButton("- Elimina Temi")
        btn_add.clicked.connect(self.crea_tema)
        btn_del.clicked.connect(self.elimina_temi)
        lay_btns.addWidget(btn_add)
        lay_btns.addWidget(btn_del)
        lay_temi.addLayout(lay_btns)

        main_layout.addWidget(box_temi, 1)

        # =====================================================
        # 2. PANNELLO LAYER E AZIONI MULTIPLE (AL CENTRO)
        # =====================================================
        box_layer = QGroupBox("2. Visibilità Layer (Spunta = presente in TUTTI i temi sel.)")
        lay_layer = QVBoxLayout(box_layer)

        self.search_layer = QLineEdit()
        self.search_layer.setPlaceholderText("Cerca layer...")
        self.search_layer.textChanged.connect(self.filtra_layer)
        lay_layer.addWidget(self.search_layer)

        self.tabella = QTableWidget()
        self.tabella.setColumnCount(2)
        self.tabella.setHorizontalHeaderLabels(["Layer Progetto", "Presente in TUTTI i Temi"])
        self.tabella.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabella.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        self.tabella.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabella.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tabella.itemChanged.connect(self.modifica_spunta_singola)
        lay_layer.addWidget(self.tabella)

        # Pulsanti di azione di gruppo
        lay_azioni = QHBoxLayout()
        btn_aggiungi_sel = QPushButton("➕ Aggiungi Layer Sel. ai Temi Sel.")
        btn_rimuovi_sel = QPushButton("➖ Rimuovi Layer Sel. dai Temi Sel.")
        
        btn_aggiungi_sel.setStyleSheet("font-weight: bold; background-color: #e1f5fe; border-radius: 4px; padding: 6px;")
        btn_rimuovi_sel.setStyleSheet("font-weight: bold; background-color: #ffebee; border-radius: 4px; padding: 6px;")
        
        btn_aggiungi_sel.clicked.connect(lambda: self.applica_azione_multipla(True))
        btn_rimuovi_sel.clicked.connect(lambda: self.applica_azione_multipla(False))
        
        lay_azioni.addWidget(btn_aggiungi_sel)
        lay_azioni.addWidget(btn_rimuovi_sel)
        lay_layer.addLayout(lay_azioni)

        # Aggiunto correttamente al layout principale
        main_layout.addWidget(box_layer, 2)

        # =====================================================
        # 3. PANNELLO GUIDA PASSO-PASSO (A DESTRA)
        # =====================================================
        widget_guida = QWidget()
        widget_guida.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px;")
        layout_dx = QVBoxLayout(widget_guida)
        layout_dx.setContentsMargins(10, 10, 10, 10)

        lbl_titolo_guida = QLabel("📖 Guida Passo-Passo")
        lbl_titolo_guida.setStyleSheet("color: #0284c7; font-weight: bold; font-size: 13px; border: none; background: transparent; margin-bottom: 4px;")
        layout_dx.addWidget(lbl_titolo_guida)

        txt_guida = QTextEdit()
        txt_guida.setReadOnly(True)
        txt_guida.setHtml(f"<div style='color: #334155; font-size: 12px; line-height: 1.5;'>{guida_testo}</div>")
        txt_guida.setStyleSheet("border: none; background: transparent;")
        layout_dx.addWidget(txt_guida)

        main_layout.addWidget(widget_guida, stretch=1)

    # ----------------------------------------------------
    # UTILITIES PER ESTRARRE I LAYER DI UN TEMA
    # ----------------------------------------------------
    def estrai_ids_visibili_tema(self, nome_tema):
        ids_visibili = set()
        record = self.themes.mapThemeState(nome_tema)

        for rec in record.layerRecords():
            if rec.isVisible and rec.layer():
                ids_visibili.add(rec.layer().id())

        if not ids_visibili:
            tree_group = record.toGroup()
            if tree_group:
                for node in tree_group.findLayers():
                    if node.isVisible():
                        ids_visibili.add(node.layerId())

        return ids_visibili

    # ----------------------------------------------------
    # CARICAMENTO DATI CON LOGICA INTERSEZIONE
    # ----------------------------------------------------
    def carica_temi(self):
        self.lista_temi.blockSignals(True)
        self.lista_temi.clear()
        temi = sorted(self.themes.mapThemes())
        for t in temi:
            self.lista_temi.addItem(t)
        self.lista_temi.blockSignals(False)

        if self.lista_temi.count() > 0:
            self.lista_temi.setCurrentRow(0)

    def aggiorna_vista_layer(self):
        temi_sel = [i.text() for i in self.lista_temi.selectedItems()]
        if not temi_sel:
            self.tabella.setRowCount(0)
            return

        ids_in_tutti = self.estrai_ids_visibili_tema(temi_sel[0])
        for nome_tema in temi_sel[1:]:
            ids_in_tutti = ids_in_tutti.intersection(self.estrai_ids_visibili_tema(nome_tema))

        self.caricamento = True
        self.tabella.blockSignals(True)
        self.tabella.setRowCount(0)

        layers = sorted(self.project.mapLayers().values(), key=lambda l: l.name().lower())
        self.tabella.setRowCount(len(layers))

        for idx, layer in enumerate(layers):
            item_nome = QTableWidgetItem(layer.name())
            item_nome.setData(Qt.UserRole, layer.id())
            item_nome.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tabella.setItem(idx, 0, item_nome)

            item_chk = QTableWidgetItem()
            item_chk.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            
            if layer.id() in ids_in_tutti:
                item_chk.setCheckState(Qt.Checked)
            else:
                item_chk.setCheckState(Qt.Unchecked)

            self.tabella.setItem(idx, 1, item_chk)

        self.tabella.blockSignals(False)
        self.caricamento = False
        self.filtra_layer(self.search_layer.text())

    # ----------------------------------------------------
    # MODIFICHE SINGOLE E MULTIPLE
    # ----------------------------------------------------
    def modifica_spunta_singola(self, item):
        if self.caricamento or item.column() != 1:
            return

        row = item.row()
        layer_id = self.tabella.item(row, 0).data(Qt.UserRole)
        is_checked = (item.checkState() == Qt.Checked)
        
        self.esegui_modifica([layer_id], rendi_visibile=is_checked)

    def applica_azione_multipla(self, rendi_visibile):
        temi_sel = [i.text() for i in self.lista_temi.selectedItems()]
        righe_sel = set(item.row() for item in self.tabella.selectedItems())

        if not temi_sel:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un tema a sinistra.")
            return

        if not righe_sel:
            QMessageBox.warning(self, "Attenzione", "Seleziona uno o più layer evidenziandoli nella tabella.")
            return

        layer_ids = [self.tabella.item(r, 0).data(Qt.UserRole) for r in righe_sel]
        self.esegui_modifica(layer_ids, rendi_visibile)
        self.aggiorna_vista_layer()

    def esegui_modifica(self, layer_ids, rendi_visibile):
        temi_sel = [i.text() for i in self.lista_temi.selectedItems()]
        if not temi_sel:
            return

        root = self.project.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()

        for nome_tema in temi_sel:
            self.themes.applyTheme(nome_tema, root, model)

            for lid in layer_ids:
                node = root.findLayer(lid)
                if node:
                    node.setItemVisibilityChecked(rendi_visibile)

            rec = self.themes.createThemeFromCurrentState(root, model)
            self.themes.insert(nome_tema, rec)

    # ----------------------------------------------------
    # UTILITY
    # ----------------------------------------------------
    def filtra_layer(self, testo):
        for row in range(self.tabella.rowCount()):
            nome = self.tabella.item(row, 0).text()
            self.tabella.setRowHidden(row, testo.lower() not in nome.lower())

    def crea_tema(self):
        nome, ok = QInputDialog.getText(self, "Nuovo Tema", "Nome del nuovo tema:")
        if ok and nome.strip():
            nome = nome.strip()
            if self.themes.hasMapTheme(nome):
                QMessageBox.warning(self, "Errore", "Tema già esistente.")
                return

            root = self.project.layerTreeRoot()
            model = iface.layerTreeView().layerTreeModel()
            rec = self.themes.createThemeFromCurrentState(root, model)
            self.themes.insert(nome, rec)
            self.carica_temi()

    def elimina_temi(self):
        temi_sel = [item.text() for item in self.lista_temi.selectedItems()]
        if not temi_sel:
            return

        if QMessageBox.question(self, "Conferma", f"Eliminare i {len(temi_sel)} temi selezionati?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for nome in temi_sel:
                self.themes.removeMapTheme(nome)
            self.carica_temi()

def run():
    guida_testo = """
    1. Seleziona uno o più temi dalla lista a sinistra (usa CTRL per selezioni multiple).<br><br>
    2. Nella tabella centrale vedrai l'elenco dei layer: la spunta indica se il layer è visibile in <b>tutti</b> i temi selezionati.<br><br>
    3. Modifica direttamente le spunte o usa i pulsanti in basso per aggiungere/rimuovere in blocco i layer selezionati dai temi attivi.
    """
    dlg = GestoreTemiAvanzato(guida_testo, iface.mainWindow())
    dlg.show()
    iface.maxxi_temi_dlg = dlg

run()
