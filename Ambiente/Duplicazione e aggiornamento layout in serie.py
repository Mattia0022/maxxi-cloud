from pathlib import Path
from qgis.core import QgsProject, QgsLayoutItemMap
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QAbstractItemView, 
    QGroupBox, QLabel, QLineEdit, QWidget, QTextEdit, QListWidget, 
    QListWidgetItem, QComboBox, QProgressBar, QMessageBox
)
from qgis.PyQt.QtCore import Qt

class DuplicazioneLayoutDialog(QDialog):
    def __init__(self, guida_testo="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicazione Avanzata Layout e Temi Mappa")
        self.resize(1250, 680)
        
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
            QListWidget, QComboBox {
                background-color: #ffffff;
                color: #222222;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit, QSpinBox {
                background-color: #ffffff;
                color: #222222;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #e6e6e6;
                color: #222222;
                border: 1px solid #adadad;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #0078d7;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                background-color: #ffffff;
                color: #222222;
                font-weight: bold;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
                border-radius: 3px;
            }
        """)

        self.progetto = QgsProject.instance()
        self.layout_manager = self.progetto.layoutManager()
        self.layouts = self.layout_manager.printLayouts()
        self.themes = self.progetto.mapThemeCollection().mapThemes()

        self.init_ui(guida_testo)

    def init_ui(self, guida_testo):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- 1. INTERFACCIA DEL TOOL (A SINISTRA) ---
        widget_interfaccia = QWidget()
        widget_interfaccia.setStyleSheet("background: transparent;")
        layout_tool = QHBoxLayout(widget_interfaccia)
        layout_tool.setContentsMargins(0, 0, 0, 0)

        # Box 1: Layout Master e Mappe da aggiornare
        box_master = QGroupBox("1. Master Layout e Mappe (CTRL o SHIFT per multipli)")
        lay_master = QVBoxLayout(box_master)

        lbl_master = QLabel("• Seleziona il Layout Master (modello):")
        lbl_master.setStyleSheet("color: #555555; margin-bottom: 2px;")
        lay_master.addWidget(lbl_master)

        self.layout_combo = QComboBox()
        for l in self.layouts:
            self.layout_combo.addItem(l.name())
        lay_master.addWidget(self.layout_combo)
        self.layout_combo.currentIndexChanged.connect(self.update_map_items)

        lbl_mappe = QLabel("• Seleziona le mappe da aggiornare col tema:")
        lbl_mappe.setStyleSheet("color: #555555; margin-top: 8px; margin-bottom: 2px;")
        lay_master.addWidget(lbl_mappe)

        self.map_list = QListWidget()
        self.map_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        lay_master.addWidget(self.map_list)

        layout_tool.addWidget(box_master, 1)

        # Box 2: Configurazione Prefisso, Temi Mappa e Azione
        box_opzioni = QGroupBox("2. Prefisso, Temi Mappa e Azione")
        lay_opzioni = QVBoxLayout(box_opzioni)

        lbl_pref = QLabel("• Prefisso per i nuovi layout:")
        lbl_pref.setStyleSheet("color: #555555; margin-bottom: 2px;")
        lay_opzioni.addWidget(lbl_pref)

        self.prefix_input = QLineEdit()
        self.prefix_input.setText("Tavola")
        lay_opzioni.addWidget(self.prefix_input)

        lbl_temi = QLabel("• Seleziona i Temi Mappa (multi-selezione):")
        lbl_temi.setStyleSheet("color: #555555; margin-top: 8px; margin-bottom: 2px;")
        lay_opzioni.addWidget(lbl_temi)

        self.theme_list = QListWidget()
        self.theme_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for t in self.themes:
            self.theme_list.addItem(QListWidgetItem(t))
        lay_opzioni.addWidget(self.theme_list)

        # Barra di avanzamento (%)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        lay_opzioni.addWidget(self.progress_bar)

        lay_opzioni.addStretch()

        # Pulsante di esecuzione
        self.btn_esegui = QPushButton("Duplica e Aggiorna Layout")
        self.btn_esegui.clicked.connect(self.avvia_duplicazione)
        lay_opzioni.addWidget(self.btn_esegui)

        layout_tool.addWidget(box_opzioni, 1)
        main_layout.addWidget(widget_interfaccia, stretch=3)

        # --- 2. PANNELLO GUIDA (A DESTRA) ---
        widget_guida = QWidget()
        widget_guida.setStyleSheet("background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 8px;")
        layout_dx = QVBoxLayout(widget_guida)
        layout_dx.setContentsMargins(10, 10, 10, 10)

        lbl_titolo_guida = QLabel("📖 Guida Passo-Passo")
        lbl_titolo_guida.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 13px; border: none; background: transparent; margin-bottom: 4px;")
        layout_dx.addWidget(lbl_titolo_guida)

        txt_guida = QTextEdit()
        txt_guida.setReadOnly(True)
        txt_guida.setHtml(f"<div style='color: #333333; font-size: 12px; line-height: 1.5;'>{guida_testo}</div>")
        txt_guida.setStyleSheet("background-color: #ffffff; color: #222222; border: 1px solid #cccccc; border-radius: 4px; padding: 8px;")
        layout_dx.addWidget(txt_guida)

        main_layout.addWidget(widget_guida, stretch=1)

        self.update_map_items()

    def update_map_items(self):
        self.map_list.clear()
        master_name = self.layout_combo.currentText()
        master_layout = self.layout_manager.layoutByName(master_name)
        if master_layout:
            map_items = [
                item for item in master_layout.items()
                if isinstance(item, QgsLayoutItemMap)
            ]
            for item in map_items:
                m_id = item.id() if item.id() else f"Mappa (ID: {item.uuid()[:6]})"
                self.map_list.addItem(QListWidgetItem(m_id))

    def avvia_duplicazione(self):
        if not self.layouts:
            QMessageBox.warning(self, "Attenzione", "Nessun layout di stampa trovato nel progetto.")
            return
        if not self.themes:
            QMessageBox.warning(self, "Attenzione", "Nessun tema mappa trovato nel progetto.")
            return

        master_name = self.layout_combo.currentText()
        target_map_ids = [item.text() for item in self.map_list.selectedItems()]
        prefix = self.prefix_input.text().strip()
        selected_themes = [item.text() for item in self.theme_list.selectedItems()]

        if not selected_themes:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un tema mappa!")
            return
        if not target_map_ids:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno una mappa da aggiornare!")
            return

        master_layout = self.layout_manager.layoutByName(master_name)
        if not master_layout:
            QMessageBox.critical(self, "Errore", f"Layout master '{master_name}' non trovato.")
            return

        # Configura barra di progresso
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(selected_themes))
        self.progress_bar.show()

        created_count = 0
        successi = []
        falliti = []

        for index, theme in enumerate(selected_themes):
            new_layout_name = f"{prefix}_{theme}" if prefix else theme
            if self.layout_manager.layoutByName(new_layout_name):
                new_layout_name = self.layout_manager.generateUniqueTitle(new_layout_name)

            new_layout = self.layout_manager.duplicateLayout(master_layout, new_layout_name)

            if new_layout:
                map_items = [
                    item for item in new_layout.items()
                    if isinstance(item, QgsLayoutItemMap)
                ]
                for map_item in map_items:
                    m_id = map_item.id() if map_item.id() else f"Mappa (ID: {map_item.uuid()[:6]})"
                    if m_id in target_map_ids:
                        map_item.setFollowVisibilityPreset(True)
                        map_item.setFollowVisibilityPresetName(theme)
                created_count += 1
                successi.append(new_layout_name)
            else:
                falliti.append(theme)

            self.progress_bar.setValue(index + 1)

        report_msg = f"Processo completato!\n\n• Layout creati con successo: {created_count}\n• Falliti: {len(falliti)}"
        if falliti:
            QMessageBox.warning(self, "Completato con errori", report_msg)
        else:
            QMessageBox.information(self, "Completato", report_msg)

        self.accept()

def run():
    guida_testo = globals().get("MAXXI_GUIDA", "<b>Guida non disponibile.</b><br>1. Seleziona il layout master.<br>2. Seleziona le mappe da aggiornare.<br>3. Inserisci il prefisso.<br>4. Seleziona uno o più temi mappa e avvia la duplicazione.")
    dlg = DuplicazioneLayoutDialog(guida_testo, iface.mainWindow())
    dlg.show()
    iface.maxxi_duplicazione_layout_dlg = dlg
