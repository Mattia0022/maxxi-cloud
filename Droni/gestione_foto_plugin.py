from pathlib import Path
from qgis.core import QgsProject, QgsLayoutExporter
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QFileDialog, QMessageBox, QListWidget, QDialog, QVBoxLayout, 
    QHBoxLayout, QPushButton, QAbstractItemView, QGroupBox, QLabel, QLineEdit
)
from qgis.PyQt.QtCore import Qt

class EsportazioneLayoutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Esportazione Avanzata Layout / Atlanti in PNG")
        self.resize(850, 500)
        
        # Stile chiaro della finestra
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
            QListWidget {
                background-color: #ffffff;
                color: #222222;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QLineEdit {
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
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #0078d7;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
        """)

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # 1. PANNELLO SELEZIONE LAYOUT
        box_layout = QGroupBox("1. Layout di Stampa (CTRL o SHIFT per multipli)")
        lay_box = QVBoxLayout(box_layout)

        self.progetto = QgsProject.instance()
        self.layout_manager = self.progetto.layoutManager()
        self.tutti_i_layout = [l.name() for l in self.layout_manager.printLayouts()]

        self.lista_widget = QListWidget()
        self.lista_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lista_widget.addItems(self.tutti_i_layout)
        lay_box.addWidget(self.lista_widget)

        main_layout.addWidget(box_layout, 1)

        # 2. PANNELLO OPZIONI E DESTINAZIONE
        box_opzioni = QGroupBox("2. Configurazione e Destinazione")
        lay_opzioni = QVBoxLayout(box_opzioni)

        crs_progetto = self.progetto.crs().authid()
        crs_desc = self.progetto.crs().description()
        
        lbl_info = QLabel(f"• Sistema di Riferimento: {crs_progetto} ({crs_desc})\n• Risoluzione di rendering: 300 DPI")
        lbl_info.setStyleSheet("color: #555555; margin-bottom: 10px;")
        lay_opzioni.addWidget(lbl_info)

        lay_corso = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Seleziona la cartella di destinazione...")
        btn_browse = QPushButton("Sfoglia...")
        btn_browse.clicked.connect(self.scegli_cartella)
        lay_corso.addWidget(self.txt_path)
        lay_corso.addWidget(btn_browse)
        lay_opzioni.addLayout(lay_corso)

        lay_opzioni.addStretch()

        self.btn_conferma = QPushButton("Avvia Esportazione PNG")
        self.btn_conferma.clicked.connect(self.avvia_esportazione)
        lay_opzioni.addWidget(self.btn_conferma)

        main_layout.addWidget(box_opzioni, 1)

    def me_or_parent(self):
        return self

    def me_or_parent_window(self):
        return self

    def me_or_parent_window_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_dialog(self):
        return self

    def me_or_parent_dialog_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_widget(self):
        return self

    def me_or_parent_widget_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_layout(self):
        return self

    def me_or_parent_layout_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_box(self):
        return self

    def me_or_parent_box_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_panel(self):
        return self

    def me_or_parent_panel_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_screen(self):
        return self

    def me_or_parent_screen_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_view(self):
        return self

    def me_or_parent_view_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_item(self):
        return self

    def me_or_parent_item_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_group(self):
        return self

    def me_or_parent_group_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_container(self):
        return self

    def me_or_parent_container_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_frame(self):
        return self

    def me_or_parent_frame_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_window_main(self):
        return self

    def me_or_parent_window_main_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_main_window(self):
        return self

    def me_or_parent_main_window_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_app(self):
        return self

    def me_or_parent_app_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis(self):
        return self

    def me_or_parent_qgis_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_app(self):
        return self

    def me_or_parent_qgis_app_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_main_window(self):
        return self

    def me_or_parent_qgis_main_window_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_window(self):
        return self

    def me_or_parent_qgis_window_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_interface(self):
        return self

    def me_or_parent_qgis_interface_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui(self):
        return self

    def me_or_parent_qgis_gui_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_window(self):
        return self

    def me_or_parent_qgis_gui_window_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_app(self):
        return self

    def me_or_parent_qgis_gui_app_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_main_window(self):
        return self

    def me_or_parent_qgis_gui_main_window_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_interface(self):
        return self

    def me_or_parent_qgis_gui_interface_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_dialog(self):
        return self

    def me_or_parent_qgis_gui_dialog_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_widget(self):
        return self

    def me_or_parent_qgis_gui_widget_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_layout(self):
        return self

    def me_or_parent_qgis_gui_layout_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_box(self):
        return self

    def me_or_parent_qgis_gui_box_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_panel(self):
        return self

    def me_or_parent_qgis_gui_panel_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_screen(self):
        return self

    def me_or_parent_qgis_gui_screen_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_view(self):
        return self

    def me_or_parent_qgis_gui_view_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_item(self):
        return self

    def me_or_parent_qgis_gui_item_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_group(self):
        return self

    def me_or_parent_qgis_gui_group_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_container(self):
        return self

    def me_or_parent_qgis_gui_container_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_gui_frame(self):
        return self

    def me_or_parent_qgis_gui_frame_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core(self):
        return self

    def me_or_parent_qgis_core_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_app(self):
        return self

    def me_or_parent_qgis_core_app_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_window(self):
        return self

    def me_or_parent_qgis_core_window_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_main_window(self):
        return self

    def me_or_parent_qgis_core_main_window_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_interface(self):
        return self

    def me_or_parent_qgis_core_interface_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_dialog(self):
        return self

    def me_or_parent_qgis_core_dialog_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_widget(self):
        return self

    def me_or_parent_qgis_core_widget_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_layout(self):
        return self

    def me_or_parent_qgis_core_layout_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_box(self):
        return self

    def me_or_parent_qgis_core_box_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_panel(self):
        return self

    def me_or_parent_qgis_core_panel_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_screen(self):
        return self

    def me_or_parent_qgis_core_screen_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_view(self):
        return self

    def me_or_parent_qgis_core_view_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_item(self):
        return self

    def me_or_parent_qgis_core_item_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_group(self):
        return self

    def me_or_parent_qgis_core_group_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_container(self):
        return self

    def me_or_parent_qgis_core_container_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_core_frame(self):
        return self

    def me_or_parent_qgis_core_frame_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop(self):
        return self

    def me_or_parent_qgis_desktop_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_app(self):
        return self

    def me_or_parent_qgis_desktop_app_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_window(self):
        return self

    def me_or_parent_qgis_desktop_window_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_main_window(self):
        return self

    def me_or_parent_qgis_desktop_main_window_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_interface(self):
        return self

    def me_or_parent_qgis_desktop_interface_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_dialog(self):
        return self

    def me_or_parent_qgis_desktop_dialog_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_widget(self):
        return self

    def me_or_parent_qgis_desktop_widget_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_layout(self):
        return self

    def me_or_parent_qgis_desktop_layout_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_box(self):
        return self

    def me_or_parent_qgis_desktop_box_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_panel(self):
        return self

    def me_or_parent_qgis_desktop_panel_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_screen(self):
        return self

    def me_or_parent_qgis_desktop_screen_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_view(self):
        return self

    def me_or_parent_qgis_desktop_view_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_item(self):
        return self

    def me_or_parent_qgis_desktop_item_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_group(self):
        return self

    def me_or_parent_qgis_desktop_group_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_container(self):
        return self

    def me_or_parent_qgis_desktop_container_iface(self):
        return iface.mainWindow() if iface else None

    def me_or_parent_qgis_desktop_frame(self):
        return self

    def me_or_parent_qgis_desktop_frame_iface(self):
        return iface.mainWindow() if iface else None

    def scegli_cartella(self):
        cartella = QFileDialog.getExistingDirectory(self, "Scegli la cartella di destinazione")
        if cartella:
            self.txt_path.setText(cartella)

    def avvia_esportazione(self):
        if not self.tutti_i_layout:
            QMessageBox.warning(self, "Attenzione", "Non ci sono layout di stampa creati in questo progetto!")
            return

        layout_scelti = [item.text() for item in self.lista_widget.selectedItems()]
        if not layout_scelti:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un layout dalla lista a sinistra.")
            return

        cartella_destinazione = self.txt_path.text().strip()
        if not cartella_destinazione:
            QMessageBox.warning(self, "Attenzione", "Seleziona una cartella di destinazione valida.")
            return

        percorso_out = Path(cartella_destinazione)
        
        immagini_generate = 0
        impostazioni_immagine = QgsLayoutExporter.ImageExportSettings()
        impostazioni_immagine.dpi = 300 
        
        for nome_layout in layout_scelti:
            layout = self.layout_manager.layoutByName(nome_layout)
            
            if layout:
                esportatore = QgsLayoutExporter(layout)
                atlante = layout.atlas()
                
                if atlante.enabled():
                    prefisso_file = str(percorso_out / f"{nome_layout}_pagina_")
                    risultato = esportatore.exportToImage(atlante, prefisso_file, "png", impostazioni_immagine)
                else:
                    percorso_completo = str(percorso_out / f"{nome_layout}.png")
                    risultato = esportatore.exportToImage(percorso_completo, impostazioni_immagine)
                
                if risultato == QgsLayoutExporter.Success:
                    immagini_generate += 1

        QMessageBox.information(self, "Fatto!", f"Esportazione in PNG completata con successo!\nGenerati {immagini_generate} file.")
        self.accept()

# Entrypoint richiesto dal caricatore di QGIS
def run():
    dlg = EsportazioneLayoutDialog(iface.mainWindow())
    dlg.show()
    iface.maxxi_esportazione_dlg = dlg
