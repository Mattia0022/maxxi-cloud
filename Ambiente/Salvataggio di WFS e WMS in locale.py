import os
import json
import time
import xml.etree.ElementTree as ET

from qgis.core import (
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsProject,
    QgsMessageLog,
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsRectangle,
    QgsGeometry,
    QgsWkbTypes
)
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.PyQt.QtCore import QUrl, QEventLoop, Qt, QThread
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkAccessManager
from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QApplication,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox
)

try:
    from qgis.utils import iface
except ImportError:
    iface = None


# Funzione di supporto per leggere le Capabilities WFS
def leggi_capabilities_wfs(url_base, max_tentativi=3):
    url_base = url_base.strip()
    if not url_base.startswith("http://") and not url_base.startswith("https://"):
        url_base = "http://" + url_base

    sep = "&" if "?" in url_base else "?"
    url_cap = f"{url_base}{sep}SERVICE=WFS&REQUEST=GetCapabilities"
    
    nam = QNetworkAccessManager()
    err_str = ""
    
    for tentativo in range(1, max_tentativi + 1):
        request = QNetworkRequest(QUrl(url_cap))
        reply = nam.get(request)
        loop = QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec_()
        
        if not reply.error():
            dati = bytes(reply.readAll())
            reply.deleteLater()
            try:
                root = ET.fromstring(dati)
                typenames = []
                for elem in root.iter():
                    tag = elem.tag.split("}")[-1]
                    if tag == "FeatureType":
                        for child in elem:
                            if child.tag.split("}")[-1] == "Name":
                                if child.text:
                                    typenames.append(child.text.strip())
                                break
                if typenames:
                    return typenames
            except Exception as e:
                err_str = f"Errore parsing XML: {e}"
        else:
            err_str = reply.errorString()
            
        reply.deleteLater()
        
        if tentativo < max_tentativi:
            QgsMessageLog.logMessage(f"Tentativo {tentativo} fallito per {url_base}. Attesa di 30 secondi...", "WFS Script", level=Qgis.Warning)
            for _ in range(30):
                QThread.msleep(1000)
                QApplication.processEvents()
            
    raise RuntimeError(f"Server non raggiungibile dopo {max_tentativi} tentativi. Ultimo errore: {err_str}")


# ==========================================
# TOOL INTERATTIVO PER DISEGNARE IL RETTANGOLO
# ==========================================
class RectangleMapTool(QgsMapTool):
    def __init__(self, canvas, callback):
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback
        self.start_point = None
        self.end_point = None
        self.is_drawing = False
        
        self.rubber_band = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(Qt.red)
        self.rubber_band.setWidth(2)

    def canvasPressEvent(self, event):
        self.start_point = self.toMapCoordinates(event.pos())
        self.is_drawing = True
        self.rubber_band.reset(QWkbTypes.PolygonGeometry if 'QWkbTypes' in globals() else QgsWkbTypes.PolygonGeometry)

    def canvasMoveEvent(self, event):
        if not self.is_drawing:
            return
        self.end_point = self.toMapCoordinates(event.pos())
        rect = QgsRectangle(self.start_point, self.end_point)
        self.rubber_band.setToGeometry(QgsGeometry.fromRect(rect), None)

    def canvasReleaseEvent(self, event):
        if not self.is_drawing:
            return
        self.end_point = self.toMapCoordinates(event.pos())
        rect = QgsRectangle(self.start_point, self.end_point)
        self.is_drawing = False
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        self.canvas.unsetMapTool(self)
        if self.callback:
            self.callback(rect)


# ==========================================
# 0. FINESTRA DI ERRORE CON APERTURA DI OUTLOOK
# ==========================================
class DialogoErroreSorgente(QDialog):
    def __init__(self, errore_msg, url_fallito, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Errore Connessione Sorgente")
        self.setMinimumWidth(550)
        
        self.nuovo_url = None
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Impossibile connettersi al server dopo i tentativi automatici.</b><br><br>"
                                f"Dettaglio errore:<br><span style='color: red;'>{errore_msg}</span><br><br>"
                                f"<i>Inserisci un nuovo link da suggerire:</i>"))
        
        self.campo_nuovo_url = QLineEdit()
        self.campo_nuovo_url.setText(url_fallito)
        layout.addWidget(self.campo_nuovo_url)
        
        btn_prova = QPushButton("Verifica e Crea Messaggio in Outlook")
        btn_prova.setStyleSheet("background-color: #2d89ef; color: white; font-weight: bold; padding: 8px;")
        btn_prova.clicked.connect(self.verifica_nuovo_link)
        layout.addWidget(btn_prova)
        
        self.setLayout(layout)
        
    def verifica_nuovo_link(self):
        url = self.campo_nuovo_url.text().strip()
        if not url:
            QMessageBox.warning(self, "Attenzione", "Inserisci un URL valido.")
            return
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            typenames = leggi_capabilities_wfs(url, max_tentativi=3)
            QApplication.restoreOverrideCursor()
            if typenames:
                self.nuovo_url = url
                self.crea_messaggio_outlook(url)
                QMessageBox.information(self, "Successo", "Il nuovo link funziona correttamente! Outlook è stato aperto con la bozza pronta per i collaboratori (controlla e clicca su Invia).")
                self.accept()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Errore", f"Anche il nuovo link ha fallito dopo i tentativi:\n{e}")

    def crea_messaggio_outlook(self, url):
        email_destinatario = "m.zuddas@maxxiengineering.it; n.melis@maxxiengineering.it; a.cau@maxxiengineering.it"
        oggetto = "[Maxxi Cloud] Segnalazione link WFS non funzionante"
        corpo = f"Ciao a tutti,\n\nIl seguente link WFS non risultava funzionante ed è stato sostituito.\n\nNuovo URL verificato e funzionante:\n{url}"

        creato = False
        # Tentativo diretto tramite automazione COM di Outlook (ottimale per Windows)
        try:
            import win32com.client as win32
            outlook = win32.Dispatch('outlook.application')
            mail = outlook.CreateItem(0) # 0 corrisponde a olMailItem
            mail.To = email_destinatario
            mail.Subject = oggetto
            mail.Body = corpo
            mail.Display(True) # Apre la finestra di Outlook in primo piano
            creato = True
            QgsMessageLog.logMessage("Finestra di Outlook aperta con successo tramite win32com.", "WFS Script", Qgis.Info)
        except Exception as ex:
            QgsMessageLog.logMessage(f"Impossibile aprire Outlook via win32com ({ex}), provo con il protocollo di sistema...", "WFS Script", Qgis.Warning)

        # Fallback nel caso in cui win32com non sia disponibile
        if not creato:
            try:
                import urllib.parse
                import webbrowser
                params = {
                    'subject': oggetto,
                    'body': corpo
                }
                url_mailto = f"mailto:{email_destinatario}?" + urllib.parse.urlencode(params, safe='')
                webbrowser.open(url_mailto)
                QgsMessageLog.logMessage("Client di posta aperto tramite mailto.", "WFS Script", Qgis.Info)
            except Exception as e:
                QgsMessageLog.logMessage(f"Errore apertura client di posta: {e}", "WFS Script", Qgis.Critical)
                QMessageBox.warning(self, "Avviso", f"Il link è corretto, ma si è verificato un errore nell'apertura della mail:\n{e}")


# ==========================================
# 1. SCHERMATA DI SCELTA SORGENTE + HEALTH CHECK
# ==========================================
class FinestraSceltaSorgenti(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("1. Selezione Sorgente (Link Fissi)")
        self.setMinimumWidth(650)
        
        self.url_selezionato = None
        self.nome_sorgente = None
        
        self.sorgenti_fisse = [
            {
                "nome": "Bacini Idrografici (PCN MinAmbiente)",
                "url": "http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/WMS_v1.3/Vettoriali/Bacini_idrografici.map"
            },
            {
                "nome": "CTR Regione Toscana",
                "url": "https://www502.regione.toscana.it/ows_ctr/com.rt.wms.RTmap/ows?map=owsctr"
            },
            {
                "nome": "EUAP - Aree Protette (PCN MinAmbiente)",
                "url": "http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/WMS_v1.3/Vettoriali/EUAP.map&version=1.3.0"
            }
        ]
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Scegli una delle sorgenti predefinite:"))
        
        self.layout_bottoni_sorgenti = QVBoxLayout()
        self.aggiorna_pulsanti_sorgenti()
        layout.addLayout(self.layout_bottoni_sorgenti)
        
        # Pulsante Health Check
        btn_health_check = QPushButton("🔍 Verifica stato di tutti i link (Health Check)")
        btn_health_check.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; padding: 8px; margin-top: 10px;")
        btn_health_check.clicked.connect(self.esegui_health_check)
        layout.addWidget(btn_health_check)
        
        self.setLayout(layout)

    def aggiorna_pulsanti_sorgenti(self):
        for sorgente in self.sorgenti_fisse:
            nome = sorgente["nome"]
            url = sorgente["url"]
            
            btn = QPushButton(nome)
            btn.setStyleSheet("text-align: left; padding: 10px; font-size: 13px;")
            btn.clicked.connect(lambda checked, u=url, n=nome: self.on_bottone_cliccato(u, n))
            self.layout_bottoni_sorgenti.addWidget(btn)

    def on_bottone_cliccato(self, url, nome):
        self.url_selezionato = url
        self.nome_sorgente = nome
        self.accept()

    def esegui_health_check(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        report = []
        
        for sorgente in self.sorgenti_fisse:
            nome = sorgente["nome"]
            url = sorgente["url"]
            try:
                leggi_capabilities_wfs(url, max_tentativi=1)
                report.append(f"<b>{nome}</b><br><span style='color: green;'>✔ FUNZIONANTE</span>")
            except Exception as e:
                report.append(f"<b>{nome}</b><br><span style='color: red;'>✘ NON FUNZIONANTE</span><br><small style='color: gray;'>Dettaglio: {e}</small>")
                
        QApplication.restoreOverrideCursor()
        
        dlg_risultato = QDialog(self)
        dlg_risultato.setWindowTitle("Risultato Health Check Link")
        dlg_risultato.setMinimumWidth(550)
        dlg_layout = QVBoxLayout(dlg_risultato)
        
        dlg_layout.addWidget(QLabel("<b>Report sullo stato dei link WFS configurati:</b><br>"))
        
        txt_report = "<br><hr><br>".join(report)
        lbl_report = QLabel(txt_report)
        lbl_report.setWordWrap(True)
        dlg_layout.addWidget(lbl_report)
        
        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.clicked.connect(dlg_risultato.accept)
        dlg_layout.addWidget(btn_chiudi)
        
        dlg_risultato.exec_()


# ==========================================
# 2. SCHERMATA DI SELEZIONE LAYER E GPKG
# ==========================================
class FinestraSelezioneLayer(QDialog):
    def __init__(self, url_server, nome_sorgente, parent=None):
        super().__init__(parent)
        self.url_server = url_server
        self.nome_sorgente = nome_sorgente
        self.setWindowTitle(f"2. Layer disponibili da: {nome_sorgente}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        self.custom_extent = None
        
        self.layout_principale = QVBoxLayout(self)
        self.inizializza_interfaccia()

    def inizializza_interfaccia(self):
        while self.layout_principale.count():
            item = self.layout_principale.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.typenames = leggi_capabilities_wfs(self.url_server, max_tentativi=3)
            QApplication.restoreOverrideCursor()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            dlg_err = DialogoErroreSorgente(str(e), self.url_server, parent=self)
            if dlg_err.exec_() == QDialog.Accepted and dlg_err.nuovo_url:
                self.url_server = dlg_err.nuovo_url
                try:
                    QApplication.setOverrideCursor(Qt.WaitCursor)
                    self.typenames = leggi_capabilities_wfs(self.url_server, max_tentativi=3)
                    QApplication.restoreOverrideCursor()
                except Exception as ex:
                    QApplication.restoreOverrideCursor()
                    QMessageBox.critical(self, "Errore", f"Impossibile leggere le Capabilities con il nuovo link:\n{ex}")
                    self.reject()
                    return
            else:
                self.reject()
                return
            
        self.layout_principale.addWidget(QLabel(f"Trovati {len(self.typenames)} layer sul server. Spunta quelli da scaricare:"))
        
        self.tabella = QTableWidget(0, 3)
        self.tabella.setHorizontalHeaderLabels(["Scarica", "Layer sul server (TypeName)", "Nome personalizzato (Alias)"])
        self.tabella.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabella.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        for tn in self.typenames:
            r = self.tabella.rowCount()
            self.tabella.insertRow(r)
            
            item_chk = QTableWidgetItem()
            item_chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item_chk.setCheckState(Qt.Unchecked)
            self.tabella.setItem(r, 0, item_chk)
            
            item_tn = QTableWidgetItem(tn)
            item_tn.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tabella.setItem(r, 1, item_tn)
            
            alias_default = tn.split(":")[-1]
            item_alias = QTableWidgetItem(alias_default)
            item_alias.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.tabella.setItem(r, 2, item_alias)
            
        self.layout_principale.addWidget(self.tabella)
        
        layout_area = QHBoxLayout()
        self.lbl_stato_area = QLabel("Area: Nessuna area personalizzata (verrà usata l'estensione della mappa)")
        self.lbl_stato_area.setStyleSheet("color: gray; font-style: italic;")
        
        btn_disegna = QPushButton("Disegna area personalizzata sulla mappa")
        btn_disegna.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        btn_disegna.clicked.connect(self.attiva_strumento_disegno)
        
        layout_area.addWidget(self.lbl_stato_area, 1)
        layout_area.addWidget(btn_disegna)
        self.layout_principale.addLayout(layout_area)
        
        layout_dir = QHBoxLayout()
        self.campo_dir = QLineEdit()
        self.campo_dir.setPlaceholderText("Seleziona la cartella di output per i GeoPackage...")
        btn_sfoglia = QPushButton("Sfoglia...")
        btn_sfoglia.clicked.connect(self.scegli_cartella)
        layout_dir.addWidget(QLabel("Cartella:"))
        layout_dir.addWidget(self.campo_dir)
        layout_dir.addWidget(btn_sfoglia)
        self.layout_principale.addLayout(layout_dir)
        
        layout_bottoni = QHBoxLayout()
        btn_annulla = QPushButton("Annulla")
        btn_annulla.clicked.connect(self.reject)
        btn_scarica = QPushButton("Scarica, Aggiungi alla Mappa e Crea GPKG Individuali")
        btn_scarica.setStyleSheet("font-weight: bold; color: white; background-color: #2d89ef; padding: 6px;")
        btn_scarica.clicked.connect(self.avvia_download_ed_esportazione)
        
        layout_bottoni.addStretch()
        layout_bottoni.addWidget(btn_annulla)
        layout_bottoni.addWidget(btn_scarica)
        self.layout_principale.addLayout(layout_bottoni)

    def attiva_strumento_disegno(self):
        if not iface:
            QMessageBox.warning(self, "Attenzione", "Interfaccia QGIS non disponibile.")
            return
        
        self.hide()
        canvas = iface.mapCanvas()
        self.map_tool = RectangleMapTool(canvas, self.ricevi_area_disegnata)
        canvas.setMapTool(self.map_tool)
        iface.messageBar().pushMessage("Info", "Clicca e trascina sulla mappa per disegnare l'area di interesse.", level=Qgis.Info, duration=5)

    def ricevi_area_disegnata(self, rect):
        self.custom_extent = rect
        self.lbl_stato_area.setText("Area: Personalizzata disegnata a mano ✓")
        self.lbl_stato_area.setStyleSheet("color: green; font-weight: bold;")
        self.show()

    def scegli_cartella(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleziona Cartella di Output")
        if dir_path:
            self.campo_dir.setText(dir_path)

    def avvia_download_ed_esportazione(self):
        dir_path = self.campo_dir.text().strip()
        if not dir_path:
            QMessageBox.warning(self, "Attenzione", "Seleziona una cartella valida in cui salvare i GeoPackage.")
            return
            
        selezionati = []
        for r in range(self.tabella.rowCount()):
            if self.tabella.item(r, 0).checkState() == Qt.Checked:
                tn = self.tabella.item(r, 1).text()
                alias = self.tabella.item(r, 2).text()
                selezionati.append({"typename": tn, "alias": alias})
                
        if not selezionati:
            QMessageBox.warning(self, "Nessun layer", "Seleziona almeno un layer da scaricare.")
            return
            
        self.accept()
        self.processa_download(selezionati, dir_path)

    def processa_download(self, selezionati, dir_path):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        extent_da_usare = self.custom_extent
        extent_crs = iface.mapCanvas().mapSettings().destinationCrs() if iface else None
        
        if not extent_da_usare and iface:
            extent_da_usare = iface.mapCanvas().extent()
        
        falliti = 0
        salvati = 0
        for item in selezionati:
            tn = item["typename"]
            alias = item["alias"]
            
            safe_alias = "".join(c for c in alias if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
            if not safe_alias:
                safe_alias = "layer"
                
            gpkg_path = os.path.join(dir_path, f"{safe_alias}.gpkg")
            
            uri = f"pagingEnabled='true' restrictToRequestBBOX='0' typename='{tn}' url='{self.url_server}' version='auto'"
            layer = QgsVectorLayer(uri, alias, "WFS")
            
            if not layer.isValid():
                QgsMessageLog.logMessage(f"Impossibile scaricare il layer {tn}", "WFS Script", level=Qgis.Warning)
                falliti += 1
                continue
                
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = alias
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
            
            if extent_da_usare and extent_crs:
                try:
                    transform = QgsCoordinateTransform(extent_crs, layer.crs(), QgsProject.instance())
                    layer_extent = transform.transformBoundingBox(extent_da_usare)
                    options.filterExtent = layer_extent
                except Exception as ex:
                    QgsMessageLog.logMessage(f"Impossibile applicare il filtro spaziale per {alias}: {ex}", "WFS Script", level=Qgis.Warning)
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, gpkg_path, QgsProject.instance().transformContext(), options
            )
            
            if error[0] != QgsVectorFileWriter.NoError:
                QgsMessageLog.logMessage(f"Errore salvataggio GPKG per {alias}: {error[1]}", "WFS Script", level=Qgis.Critical)
                falliti += 1
            else:
                salvati += 1
                layer_gpkg = QgsVectorLayer(f"{gpkg_path}|layername={alias}", alias, "ogr")
                if layer_gpkg.isValid():
                    QgsProject.instance().addMapLayer(layer_gpkg)
                    
        QApplication.restoreOverrideCursor()
        QMessageBox.information(self, "Completato", f"Processo terminato!\nCreati {salvati} file GeoPackage individuali filtrati per l'area selezionata nella cartella:\n{dir_path}")


# ==========================================
# 3. AVVIATORE PRINCIPALE
# ==========================================
def avvia_plugin():
    dlg_sorgenti = FinestraSceltaSorgenti(iface.mainWindow() if iface else None)
    if dlg_sorgenti.exec_() == QDialog.Accepted and dlg_sorgenti.url_selezionato:
        url_scelto = dlg_sorgenti.url_selezionato
        nome_scelto = dlg_sorgenti.nome_sorgente
        
        dlg_layer = FinestraSelezioneLayer(url_scelto, nome_scelto, iface.mainWindow() if iface else None)
        dlg_layer.exec_()

def run():
    avvia_plugin()

if __name__ == "__main__":
    avvia_plugin()
