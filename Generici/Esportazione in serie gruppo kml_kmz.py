import os
from pathlib import Path
from qgis.core import QgsProject, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, 
    QLabel, QLineEdit, QWidget, QTextEdit, QComboBox, QFileDialog, QMessageBox, QListWidget, QAbstractItemView
)
from qgis.PyQt.QtCore import Qt

class EsportazioneKmlDialog(QDialog):
    def __init__(self, guida_testo="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Esportazione in serie gruppo KML / KMZ")
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
            QLineEdit, QComboBox, QListWidget {
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

        self.dict_layer = {}
        self.nome_gruppo = ""
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

        # Box 1: Selezione Gruppo e Layer
        box_layer = QGroupBox("1. Selezione Gruppo e Layer da Esportare")
        lay_layer = QVBoxLayout(box_layer)
        
        nodo_corrente = iface.layerTreeView().currentNode()
        if nodo_corrente and nodo_corrente.nodeType() == 0:  # 0 corrisponde a un Gruppo
            self.nome_gruppo = nodo_corrente.name()
            figli = nodo_corrente.findLayers()
            self.dict_layer = {f.layer().name(): f.layer() for f in figli if f.layer() and f.layer().type() == 0}
        
        lay_layer.addWidget(QLabel(f"Gruppo attivo rilevato: <b>{self.nome_gruppo if self.nome_gruppo else 'Nessun gruppo selezionato'}</b>"))
        lay_layer.addWidget(QLabel("Seleziona i layer vettoriali (usa Ctrl o Shift per la multi-selezione):"))
        
        self.lista_widget = QListWidget()
        self.lista_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        if self.dict_layer:
            self.lista_widget.addItems(self.dict_layer.keys())
            for i in range(self.lista_widget.count()):
                self.lista_widget.item(i).setSelected(True)
        else:
            self.lista_widget.addItem("Nessun layer vettoriale valido nel gruppo selezionato")
            self.lista_widget.setEnabled(False)
            
        lay_layer.addWidget(self.lista_widget)
        layout_tool.addWidget(box_layer)

        # Box 2: Configurazione Formato e Percorso
        box_dest = QGroupBox("2. Formato e Cartella di Destinazione")
        lay_dest = QVBoxLayout(box_dest)
        
        lay_formato = QHBoxLayout()
        lay_formato.addWidget(QLabel("Formato:"))
        self.combo_formato = QComboBox()
        self.combo_formato.addItems(["KML (.kml)", "KMZ (.kmz)"])
        lay_formato.addWidget(self.combo_formato)
        lay_dest.addLayout(lay_formato)

        lay_path = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Seleziona la cartella di destinazione...")
        btn_browse = QPushButton("Sfoglia...")
        btn_browse.clicked.connect(self.scegli_cartella)
        lay_path.addWidget(self.txt_path)
        lay_path.addWidget(btn_browse)
        lay_dest.addLayout(lay_path)

        lay_dest.addStretch()

        self.btn_genera = QPushButton("Avvia Esportazione in Serie")
        self.btn_genera.clicked.connect(self.avvia_esportazione)
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

    def scegli_cartella(self):
        dirpath = QFileDialog.getExistingDirectory(self, "Scegli Cartella di Destinazione", "")
        if dirpath:
            self.txt_path.setText(dirpath)

    def avvia_esportazione(self):
        if not self.dict_layer:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un GRUPPO valido di layer nel pannello laterale di QGIS e riapri lo strumento.")
            return

        layer_scelti = [item.text() for item in self.lista_widget.selectedItems() if item.text() in self.dict_layer]
        if not layer_scelti:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un layer dalla lista!")
            return

        cartella_destinazione = self.txt_path.text().strip()
        if not cartella_destinazione:
            QMessageBox.warning(self, "Attenzione", "Specifica una cartella di destinazione valida.")
            return

        formato_scelto = self.combo_formato.currentText()
        estensione = ".kml" if "KML" in formato_scelto else ".kmz"
        driver_name = "KML" if estensione == ".kml" else "LIBKML"
        
        percorso_out = Path(cartella_destinazione)
        sr_utm32n = QgsCoordinateReferenceSystem("EPSG:32632")
        
        file_esportati = 0
        errori = []

        for nome_l in layer_scelti:
            layer = self.dict_layer[nome_l]
            nome_file = f"{layer.name()}{estensione}"
            percorso_completo = str(percorso_out / nome_file)
            
            opzioni = QgsVectorFileWriter.SaveVectorOptions()
            opzioni.driverName = driver_name
            opzioni.fileEncoding = "UTF-8"
            opzioni.ct = QgsCoordinateTransform(layer.crs(), sr_utm32n, QgsProject.instance())
            
            risultato = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer,
                percorso_completo,
                QgsProject.instance().transformContext(),
                opzioni
            )
            
            if risultato[0] == QgsVectorFileWriter.NoError:
                file_esportati += 1
            else:
                errori.append(f"{layer.name()}: {risultato[1]}")

        if not errori:
            QMessageBox.information(
                self, "Completato", 
                f"Esportazione completata con successo!\n"
                f"File esportati: {file_esportati}\n"
                f"Formato: {estensione.upper()}\n"
                f"CRS: EPSG:32632"
            )
            self.accept()
        else:
            msg_err = f"Esportati {file_esportati} file, ma si sono verificati errori:\n" + "\n".join(errori[:5])
            QMessageBox.warning(self, "Completato con errori", msg_err)

def run():
    guida_testo = (
        "<b>1. Selezione del Gruppo:</b><br>"
        "Prima di avviare lo strumento, assicurati di aver selezionato un <b>gruppo di layer</b> nel pannello dei Layer a sinistra di QGIS.<br><br>"
        "<b>2. Scelta dei Layer e Formato:</b><br>"
        "Dalla lista puoi selezionare o deselezionare i singoli layer vettoriali tenendo premuto <code>Ctrl</code> o <code>Shift</code>. Scegli quindi se esportare in formato <code>.kml</code> o <code>.kmz</code>.<br><br>"
        "<b>3. Destinazione:</b><br>"
        "Scegli la cartella di salvataggio e avvia l'esportazione. Tutti i layer selezionati verranno riproiettati automaticamente in <b>EPSG:32632</b>."
    )
    dlg = EsportazioneKmlDialog(guida_testo, iface.mainWindow())
    dlg.show()
    iface.maxxi_kml_dlg = dlg
