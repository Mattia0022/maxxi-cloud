import math
from pathlib import Path
from qgis.core import QgsProject, QgsWkbTypes
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, 
    QLabel, QLineEdit, QWidget, QTextEdit, QComboBox, QFileDialog, QMessageBox
)
from qgis.PyQt.QtCore import Qt
from qgis.utils import iface

class SezioniTrasversaliDialog(QDialog):
    def __init__(self, guida_testo="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sezioni Trasversali da Punti GNSS")
        self.resize(1100, 550)
        
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
            QLineEdit, QComboBox {
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

        self.init_ui(guida_testo)

    def init_ui(self, guida_testo):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # --- 1. INTERFACCIA DEL TOOL (A SINISTRA) ---
        widget_interfaccia = QWidget()
        widget_interfaccia.setStyleSheet("background: transparent;")
        layout_tool = QVBoxLayout(widget_interfaccia)
        layout_tool.setContentsMargins(0, 0, 0, 0)

        # Box 1: Selezione Layer e Verifica Punti
        box_layer = QGroupBox("1. Selezione Layer e Punti sulla Mappa")
        lay_layer = QVBoxLayout(box_layer)
        
        self.progetto = QgsProject.instance()
        all_layers = self.progetto.mapLayers().values()
        self.point_layers = [l for l in all_layers if l.type() == l.VectorLayer and l.geometryType() == QgsWkbTypes.PointGeometry]
        
        self.combo_layers = QComboBox()
        if self.point_layers:
            self.combo_layers.addItems([l.name() for l in self.point_layers])
            self.combo_layers.currentIndexChanged.connect(self.aggiorna_campi)
        else:
            self.combo_layers.addItem("Nessun layer di punti trovato")
            self.combo_layers.setEnabled(False)
            
        lay_layer.addWidget(QLabel("Layer di punti attivo:"))
        lay_layer.addWidget(self.combo_layers)
        
        self.lbl_stato_selezione = QLabel("Punti selezionati sulla mappa: 0")
        self.lbl_stato_selezione.setStyleSheet("color: #d9534f; font-weight: bold; margin-top: 5px;")
        lay_layer.addWidget(self.lbl_stato_selezione)
        
        btn_aggiorna = QPushButton("Aggiorna conteggio selezione")
        btn_aggiorna.clicked.connect(self.aggiorna_conteggio_selezione)
        lay_layer.addWidget(btn_aggiorna)

        layout_tool.addWidget(box_layer)

        # Box 2: Configurazione Quota
        box_quota = QGroupBox("2. Configurazione Quota")
        lay_quota = QVBoxLayout(box_quota)
        
        self.combo_quota = QComboBox()
        lay_quota.addWidget(QLabel("Scegli la colonna della quota o la Z 3D:"))
        lay_quota.addWidget(self.combo_quota)
        
        layout_tool.addWidget(box_quota)

        # Box 3: Destinazione e Generazione
        box_dest = QGroupBox("3. Destinazione ed Esportazione")
        lay_dest = QVBoxLayout(box_dest)
        
        lay_path = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Seleziona dove salvare lo script .scr...")
        btn_browse = QPushButton("Sfoglia...")
        btn_browse.clicked.connect(self.scegli_file)
        lay_path.addWidget(self.txt_path)
        lay_path.addWidget(btn_browse)
        lay_dest.addLayout(lay_path)

        lay_dest.addStretch()

        self.btn_genera = QPushButton("Genera Script AutoCAD (.scr)")
        self.btn_genera.clicked.connect(self.avvia_generazione)
        lay_dest.addWidget(self.btn_genera)

        layout_tool.addWidget(box_dest)
        main_layout.addWidget(widget_interfaccia, stretch=3)

        # --- 2. PANNELLO GUIDA (A DESTRA) ---
        widget_guida = QWidget()
        widget_guida.setStyleSheet("background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 8px;")
        layout_dx = QVBoxLayout(widget_guida)
        layout_dx.setContentsMargins(8, 8, 8, 8)

        lbl_titolo_guida = QLabel("📖 Guida Passo-Passo")
        lbl_titolo_guida.setStyleSheet("color: #0078d7; font-weight: bold; font-size: 13px; border: none; background: transparent; margin-bottom: 4px;")
        layout_dx.addWidget(lbl_titolo_guida)

        txt_guida = QTextEdit()
        txt_guida.setReadOnly(True)
        txt_guida.setHtml(f"<div style='color: #333333; font-size: 12px; line-height: 1.5;'>{guida_testo}</div>")
        txt_guida.setStyleSheet("background-color: #ffffff; color: #222222; border: 1px solid #cccccc; border-radius: 4px; padding: 8px;")
        layout_dx.addWidget(txt_guida)

        main_layout.addWidget(widget_guida, stretch=1)

        if self.point_layers:
            self.aggiorna_campi()
            self.aggiorna_conteggio_selezione()

    def get_layer_corrente(self):
        if not self.point_layers:
            return None
        idx = self.combo_layers.currentIndex()
        if 0 <= idx < len(self.point_layers):
            return self.point_layers[idx]
        return None

    def aggiorna_campi(self):
        self.combo_quota.clear()
        layer = self.get_layer_corrente()
        if layer:
            fields = [field.name() for field in layer.fields()]
            options = ["[ Usa Geometria Z (Punti 3D) ]"] + fields
            self.combo_quota.addItems(options)
            self.aggiorna_conteggio_selezione()

    def aggiorna_conteggio_selezione(self):
        layer = self.get_layer_corrente()
        if layer:
            count = layer.selectedFeatureCount()
            self.lbl_stato_selezione.setText(f"Punti selezionati sulla mappa: {count}")
            if count >= 2:
                self.lbl_stato_selezione.setStyleSheet("color: #2b982b; font-weight: bold; margin-top: 5px;")
            else:
                self.lbl_stato_selezione.setStyleSheet("color: #d9534f; font-weight: bold; margin-top: 5px;")

    def scegli_file(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Salva Script AutoCAD", "profilo_proiettato.scr", "AutoCAD Script (*.scr)")
        if filepath:
            self.txt_path.setText(filepath)

    def avvia_generazione(self):
        layer = self.get_layer_corrente()
        if not layer:
            QMessageBox.warning(self, "Attenzione", "Nessun layer di punti valido selezionato.")
            return

        selected_features = list(layer.selectedFeatures())
        if len(selected_features) < 2:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno 2 punti sulla mappa prima di generare lo script!")
            return

        filepath = self.txt_path.text().strip()
        if not filepath:
            QMessageBox.warning(self, "Attenzione", "Specifica un percorso di destinazione valido per il file .scr.")
            return

        quota_choice = self.combo_quota.currentText()
        raw_pts = []
        for feat in selected_features:
            geom = feat.geometry()
            pt_xy = geom.asPoint() if not geom.isMultipart() else geom.asMultiPoint()[0]

            quota = 0.0
            if quota_choice == "[ Usa Geometria Z (Punti 3D) ]":
                quota = geom.get().z() if geom.get().is3D() else 0.0
            else:
                idx = layer.fields().indexOf(quota_choice)
                val = feat.attributes()[idx]
                if val is not None:
                    try:
                        quota = float(val)
                    except (ValueError, TypeError):
                        quota = 0.0

            raw_pts.append({'id': feat.id(), 'x': pt_xy.x(), 'y': pt_xy.y(), 'z': quota})

        p_start = raw_pts[0]
        p_end = raw_pts[-1]

        dx = p_end['x'] - p_start['x']
        dy = p_end['y'] - p_start['y']
        lunghezza_asse_sq = dx**2 + dy**2
        lunghezza_asse = math.sqrt(lunghezza_asse_sq)

        if lunghezza_asse == 0:
            QMessageBox.critical(self, "Errore", "Il primo e l'ultimo punto selezionato coincidono!")
            return

        dati_profilo = []
        for pt in raw_pts:
            u = ((pt['x'] - p_start['x']) * dx + (pt['y'] - p_start['y']) * dy) / lunghezza_asse_sq
            progressiva = u * lunghezza_asse
            x_proj = p_start['x'] + u * dx
            y_proj = p_start['y'] + u * dy

            dati_profilo.append({
                'prog': progressiva,
                'z': pt['z'],
                'x_real': pt['x'],
                'y_real': pt['y'],
                'x_proj': x_proj,
                'y_proj': y_proj
            })

        dati_profilo.sort(key=lambda item: item['prog'])

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("_CMDECHO 0\n")
                f.write("_OSMODE 0\n")

                f.write("_PLINE\n")
                for item in dati_profilo:
                    f.write(f"{item['prog']:.3f},{item['z']:.3f}\n")
                f.write("\n")

                for item in dati_profilo:
                    f.write(f"_TEXT {item['prog']:.3f},{item['z'] + 0.5:.3f} 0.3 90 Q={item['z']:.2f}\n")
                    f.write(f"_TEXT {item['prog']:.3f},{item['z'] - 1.5:.3f} 0.3 90 P={item['prog']:.2f}m\n")

                f.write("_3DPOLY\n")
                for item in dati_profilo:
                    f.write(f"{item['x_proj']:.3f},{item['y_proj']:.3f},{item['z']:.3f}\n")
                f.write("\n")

                f.write("_ZOOM _E\n")
                f.write("_CMDECHO 1\n")

            QMessageBox.information(
                self, "Completato", 
                f"Script AutoCAD generato con successo!\n"
                f"Lunghezza Asse Sezione: {lunghezza_asse:.2f} m\n"
                f"Punti elaborati: {len(dati_profilo)}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile scrivere il file:\n{str(e)}")

def run():
    guida_testo = (
        "<b>1. Selezione dei punti sulla mappa:</b><br>"
        "Prima di aprire questo strumento, usa gli strumenti di selezione nativi di QGIS per selezionare almeno <b>2 punti</b> lungo l'asse della sezione.<br><br>"
        "<b>2. Verifica e Scelta Quota:</b><br>"
        "Seleziona il layer di punti dal menu a tendina e indica se estrarre la quota dalla coordinata Z geometrica 3D o da una colonna degli attributi.<br><br>"
        "<b>3. Esportazione Script:</b><br>"
        "Scegli la cartella/file di destinazione ed esegui il comando in AutoCAD (comando <code>SCRIPT</code>) per importare automaticamente il profilo e la polilinea 3D."
    )
    dlg = SezioniTrasversaliDialog(guida_testo, iface.mainWindow())
    dlg.show()
    iface.maxxi_sezioni_dlg = dlg
