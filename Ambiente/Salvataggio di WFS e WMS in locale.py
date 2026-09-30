import os
import re
import html
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
    QgsWkbTypes,
    QgsFeatureRequest
)
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.PyQt.QtCore import (
    QUrl,
    QEventLoop,
    Qt,
    QThread
)
from qgis.PyQt.QtNetwork import (
    QNetworkRequest,
    QNetworkAccessManager
)
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
    QCheckBox,
    QProgressBar
)

try:
    from qgis.utils import iface
except Exception:
    iface = None

# ============================================================
# CONFIGURAZIONE SORGENTI
# ============================================================
SORGENTI = [
    {
        "nome": "Bacini Idrografici - PCN",
        "url": (
            "http://wms.pcn.minambiente.it/ogc"
            "?map=/ms_ogc/wfs/Bacini_idrografici.map"
        )
    },
    {
        "nome": "EUAP - Aree Protette - PCN",
        "url": (
            "http://wms.pcn.minambiente.it/ogc"
            "?map=/ms_ogc/wfs/EUAP.map"
        )
    },
    {
        "nome": "Natura 2000 - SIC / ZSC / ZPS - PCN",
        "url": (
            "http://wms.pcn.minambiente.it/ogc"
            "?map=/ms_ogc/wfs/SIC_ZSC_ZPS.map"
        )
    },
    {
        "nome": "ReNDiS - ISPRA",
        "url": (
            "https://www.rendis.isprambiente.it"
            "/geoserver/open_rendis/ows"
        )
    },
    {
        "nome": "WebGIS Regione Sardegna - SITR",
        "url": (
            "https://webgis.regione.sardegna.it"
            "/geoserver/ows"
        )
    },
    {
        "nome": "RAMSAR - Zone Umide - PCN",
        "url": (
            "http://wms.pcn.minambiente.it/ogc"
            "?map=/ms_ogc/wfs/RAMSAR.map"
        )
    }
]

# ============================================================
# FUNZIONI GENERALI
# ============================================================
def normalizza_url(url):
    """
    Normalizza l'URL inserito dall'utente.
    """
    url = url.strip()
    if not url:
        raise ValueError("URL vuoto.")
    if not url.lower().startswith(("http://", "https://")):
        url = "http://" + url
    return url

def url_get_capabilities(url):
    """
    Costruisce l'URL GetCapabilities WFS.
    """
    url = normalizza_url(url)
    parametri = [
        "SERVICE=WFS",
        "REQUEST=GetCapabilities"
    ]
    separatore = "&" if "?" in url else "?"
    return url + separatore + "&".join(parametri)

def nome_file_sicuro(nome):
    """
    Trasforma il nome del layer in un nome utilizzabile
    come file/cartella.
    """
    if not nome:
        nome = "layer"
    nome = html.unescape(nome)
    if ":" in nome:
        nome = nome.split(":")[-1]
    nome = nome.strip()
    nome = re.sub(
        r'[<>:"/\\|?*\x00-\x1F]',
        "_",
        nome
    )
    nome = nome.replace(" ", "_")
    nome = re.sub(
        r"_+",
        "_",
        nome
    )
    nome = nome.strip("._ ")
    if not nome:
        nome = "layer"
    return nome[:150]

# ============================================================
# DOWNLOAD HTTP SINCRONO
# ============================================================
def scarica_url(url, timeout_ms=60000):
    """
    Scarica una URL utilizzando QNetworkAccessManager.
    Restituisce: bytes
    """
    manager = QNetworkAccessManager()
    request = QNetworkRequest(QUrl(url))
    request.setRawHeader(
        b"User-Agent",
        b"QGIS-WFS-Offline-Downloader/1.0"
    )
    reply = manager.get(request)
    loop = QEventLoop()
    try:
        reply.finished.connect(loop.quit)
        loop.exec_()
        if reply.error():
            errore = reply.errorString()
            try:
                reply.deleteLater()
            except Exception:
                pass
            raise RuntimeError(
                f"Errore HTTP: {errore}"
            )
        dati = bytes(reply.readAll())
        try:
            reply.deleteLater()
        except Exception:
            pass
        if not dati:
            raise RuntimeError(
                "Il server ha restituito una risposta vuota."
            )
        return dati
    except Exception:
        try:
            reply.abort()
            reply.deleteLater()
        except Exception:
            pass
        raise

# ============================================================
# LETTURA WFS GETCAPABILITIES
# ============================================================
def leggi_capabilities_wfs(
    url_base,
    max_tentativi=2,
    pausa_secondi=5):
    """
    Legge le Capabilities WFS e restituisce una lista di FeatureType.
    """
    url_base = normalizza_url(url_base)
    url_capabilities = url_get_capabilities(url_base)
    ultimo_errore = ""
    for tentativo in range(1, max_tentativi + 1):
        try:
            QgsMessageLog.logMessage(
                f"Lettura WFS: {url_capabilities}",
                "GIS Offline",
                Qgis.Info
            )
            dati = scarica_url(
                url_capabilities,
                timeout_ms=60000
            )
            testo = dati.decode(
                "utf-8",
                errors="ignore"
            ).strip()
            if not testo:
                raise RuntimeError(
                    "Risposta vuota dal server."
                )
            inizio = testo[:1000].lower()
            if (
                "<html" in inizio
                or "<!doctype html" in inizio
                or "<body" in inizio
            ):
                raise RuntimeError(
                    "Il server ha restituito HTML "
                    "anziché XML WFS."
                )
            try:
                root = ET.fromstring(dati)
            except Exception as ex:
                estratto = testo[:500]
                raise RuntimeError(
                    "Risposta non interpretabile come XML.\n"
                    f"Dettaglio: {ex}\n\n"
                    f"Inizio risposta:\n{estratto}"
                )
            feature_types = []
            for elem in root.iter():
                tag = elem.tag.split("}")[-1]
                if tag.lower() != "featuretype":
                    continue
                nome = ""
                titolo = ""
                abstract = ""
                for child in elem:
                    child_tag = child.tag.split("}")[-1].lower()
                    testo_child = (
                        child.text.strip()
                        if child.text
                        else ""
                    )
                    if child_tag == "name":
                        nome = testo_child
                    elif child_tag == "title":
                        titolo = testo_child
                    elif child_tag == "abstract":
                        abstract = testo_child
                if nome:
                    feature_types.append({
                        "name": nome,
                        "title": titolo or nome,
                        "abstract": abstract
                    })
            if not feature_types:
                raise RuntimeError(
                    "Il WFS ha risposto correttamente, "
                    "ma non sono stati trovati FeatureType."
                )
            risultato = []
            visti = set()
            for ft in feature_types:
                nome = ft["name"]
                if nome not in visti:
                    risultato.append(ft)
                    visti.add(nome)
            risultato.sort(
                key=lambda x: x["name"].lower()
            )
            QgsMessageLog.logMessage(
                f"Trovati {len(risultato)} FeatureType.",
                "GIS Offline",
                Qgis.Info
            )
            return risultato
        except Exception as ex:
            ultimo_errore = str(ex)
            QgsMessageLog.logMessage(
                f"Tentativo {tentativo} fallito: "
                f"{ultimo_errore}",
                "GIS Offline",
                Qgis.Warning
            )
            if tentativo < max_tentativi:
                for _ in range(pausa_secondi):
                    QThread.msleep(1000)
                    QApplication.processEvents()
    raise RuntimeError(
        "Impossibile leggere le Capabilities WFS "
        f"dopo {max_tentativi} tentativi.\n\n"
        f"Ultimo errore:\n{ultimo_errore}"
    )

# ============================================================
# TOOL DISEGNO RETTANGOLO
# ============================================================
class RectangleMapTool(QgsMapTool):
    def __init__(
        self,
        canvas,
        callback
    ):
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback
        self.start_point = None
        self.end_point = None
        self.is_drawing = False
        self.rubber_band = QgsRubberBand(
            canvas,
            QgsWkbTypes.PolygonGeometry
        )
        self.rubber_band.setColor(
            Qt.red
        )
        self.rubber_band.setWidth(2)
    def canvasPressEvent(self, event):
        self.start_point = (
            self.toMapCoordinates(event.pos())
        )
        self.end_point = self.start_point
        self.is_drawing = True
        self.rubber_band.reset(
            QgsWkbTypes.PolygonGeometry
        )
    def canvasMoveEvent(self, event):
        if not self.is_drawing:
            return
        self.end_point = (
            self.toMapCoordinates(event.pos())
        )
        rect = QgsRectangle(
            self.start_point,
            self.end_point
        )
        self.rubber_band.setToGeometry(
            QgsGeometry.fromRect(rect),
            None
        )
    def canvasReleaseEvent(self, event):
        if not self.is_drawing:
            return
        self.end_point = (
            self.toMapCoordinates(event.pos())
        )
        rect = QgsRectangle(
            self.start_point,
            self.end_point
        )
        self.is_drawing = False
        self.rubber_band.reset(
            QgsWkbTypes.PolygonGeometry
        )
        self.canvas.unsetMapTool(self)
        if self.callback:
            self.callback(rect)

# ============================================================
# DIALOG ERRORE
# ============================================================
class DialogoErroreSorgente(QDialog):
    def __init__(
        self,
        errore_msg,
        url_fallito,
        parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(
            "Errore connessione WFS"
        )
        self.setMinimumWidth(650)
        self.nuovo_url = None
        layout = QVBoxLayout(self)
        testo = QLabel(
            "<b>Impossibile leggere il servizio WFS.</b>"
            "<br><br>"
            "<b>Errore:</b><br>"
            f"<span style='color:red;'>"
            f"{html.escape(str(errore_msg))}"
            f"</span>"
            "<br><br>"
            "Puoi inserire manualmente un altro endpoint WFS:"
        )
        testo.setWordWrap(True)
        layout.addWidget(testo)
        self.campo_url = QLineEdit()
        self.campo_url.setText(
            url_fallito
        )
        layout.addWidget(
            self.campo_url
        )
        layout_bottoni = QHBoxLayout()
        btn_verifica = QPushButton(
            "Verifica nuovo URL"
        )
        btn_verifica.clicked.connect(
            self.verifica
        )
        btn_annulla = QPushButton(
            "Annulla"
        )
        btn_annulla.clicked.connect(
            self.reject
        )
        layout_bottoni.addStretch()
        layout_bottoni.addWidget(
            btn_verifica
        )
        layout_bottoni.addWidget(
            btn_annulla
        )
        layout.addLayout(
            layout_bottoni
        )
    def verifica(self):
        url = self.campo_url.text().strip()
        if not url:
            QMessageBox.warning(
                self,
                "Attenzione",
                "Inserisci un URL."
            )
            return
        QApplication.setOverrideCursor(
            Qt.WaitCursor
        )
        try:
            feature_types = (
                leggi_capabilities_wfs(
                    url,
                    max_tentativi=1
                )
            )
            QApplication.restoreOverrideCursor()
            if feature_types:
                self.nuovo_url = url
                QMessageBox.information(
                    self,
                    "WFS funzionante",
                    "Il nuovo endpoint WFS "
                    "risponde correttamente."
                )
                self.accept()
        except Exception as ex:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(
                self,
                "Errore",
                str(ex)
            )

# ============================================================
# FINESTRA SCELTA SORGENTE
# ============================================================
class FinestraSceltaSorgenti(QDialog):
    def __init__(
        self,
        parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(
            "1. Selezione sorgente WFS"
        )
        self.setMinimumWidth(700)
        self.url_selezionato = None
        self.nome_sorgente = None
        layout = QVBoxLayout(self)
        titolo = QLabel(
            "<b>Seleziona la sorgente WFS da scaricare "
            "in locale.</b><br>"
            "CTR Toscana esclusa."
        )
        layout.addWidget(titolo)
        self.layout_sorgenti = QVBoxLayout()
        layout.addLayout(
            self.layout_sorgenti
        )
        self.aggiorna_pulsanti()
        btn_health = QPushButton(
            "🔍 Verifica tutte le sorgenti"
        )
        btn_health.setStyleSheet(
            """
            background-color:#f39c12;
            color:white;
            font-weight:bold;
            padding:8px;
            """
        )
        btn_health.clicked.connect(
            self.health_check
        )
        layout.addWidget(
            btn_health
        )
    def aggiorna_pulsanti(self):
        for sorgente in SORGENTI:
            btn = QPushButton(
                sorgente["nome"]
            )
            btn.setStyleSheet(
                """
                text-align:left;
                padding:10px;
                font-size:13px;
                """
            )
            btn.clicked.connect(
                lambda checked,
                u=sorgente["url"],
                n=sorgente["nome"]:
                self.seleziona(u, n)
            )
            self.layout_sorgenti.addWidget(
                btn
            )
    def seleziona(
        self,
        url,
        nome
    ):
        self.url_selezionato = url
        self.nome_sorgente = nome
        self.accept()
    def health_check(self):
        QApplication.setOverrideCursor(
            Qt.WaitCursor
        )
        risultati = []
        try:
            for sorgente in SORGENTI:
                nome = sorgente["nome"]
                url = sorgente["url"]
                try:
                    layers = (
                        leggi_capabilities_wfs(
                            url,
                            max_tentativi=1
                        )
                    )
                    risultati.append(
                        f"""
                        <b>{html.escape(nome)}</b><br>
                        <span style='color:green;'>
                        ✔ FUNZIONANTE
                        </span>
                        &nbsp;({len(layers)} layer)
                        """
                    )
                except Exception as ex:
                    risultati.append(
                        f"""
                        <b>{html.escape(nome)}</b><br>
                        <span style='color:red;'>
                        ✘ NON FUNZIONANTE
                        </span><br>
                        <small>
                        {html.escape(str(ex))}
                        </small>
                        """
                    )
        finally:
            QApplication.restoreOverrideCursor()
        dlg = QDialog(self)
        dlg.setWindowTitle(
            "Health Check WFS"
        )
        dlg.setMinimumWidth(750)
        layout = QVBoxLayout(dlg)
        layout.addWidget(
            QLabel(
                "<b>Risultato verifica:</b>"
            )
        )
        report = QLabel(
            "<hr>".join(risultati)
        )
        report.setWordWrap(True)
        layout.addWidget(
            report
        )
        btn = QPushButton(
            "Chiudi"
        )
        btn.clicked.connect(
            dlg.accept
        )
        layout.addWidget(
            btn
        )
        dlg.exec_()

# ============================================================
# FINESTRA SELEZIONE LAYER
# ============================================================
class FinestraSelezioneLayer(QDialog):
    def __init__(
        self,
        url_server,
        nome_sorgente,
        parent=None
    ):
        super().__init__(parent)
        self.url_server = url_server
        self.nome_sorgente = nome_sorgente
        self.setWindowTitle(
            f"2. Layer - {nome_sorgente}"
        )
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)
        self.custom_extent = None
        self.feature_types = []
        self.layout_principale = QVBoxLayout(
            self
        )
        self.inizializza()

    def inizializza(self):
        QApplication.setOverrideCursor(
            Qt.WaitCursor
        )
        try:
            self.feature_types = (
                leggi_capabilities_wfs(
                    self.url_server,
                    max_tentativi=2
                )
            )
        except Exception as ex:
            QApplication.restoreOverrideCursor()
            dlg = DialogoErroreSorgente(
                str(ex),
                self.url_server,
                self
            )
            if dlg.exec_() == QDialog.Accepted:
                if dlg.nuovo_url:
                    self.url_server = dlg.nuovo_url
                    try:
                        QApplication.setOverrideCursor(
                            Qt.WaitCursor
                        )
                        self.feature_types = (
                            leggi_capabilities_wfs(
                                self.url_server,
                                max_tentativi=2
                            )
                        )
                    except Exception as ex2:
                        QApplication.restoreOverrideCursor()
                        QMessageBox.critical(
                            self,
                            "Errore",
                            str(ex2)
                        )
                        self.reject()
                        return
            else:
                self.reject()
                return
        finally:
            QApplication.restoreOverrideCursor()
        self.costruisci_interfaccia()

    def costruisci_interfaccia(self):
        while self.layout_principale.count():
            item = (
                self.layout_principale.takeAt(0)
            )
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.layout_principale.addWidget(
            QLabel(
                f"""
                <b>Sorgente:</b>
                {html.escape(self.nome_sorgente)}
                <br>
                <b>URL:</b>
                {html.escape(self.url_server)}
                <br><br>
                Trovati
                <b>{len(self.feature_types)}</b>
                FeatureType.
                Seleziona i layer da scaricare.
                """
            )
        )

        layout_filtro = QHBoxLayout()
        layout_filtro.addWidget(
            QLabel("Filtra layer:")
        )
        self.campo_filtro = QLineEdit()
        self.campo_filtro.setPlaceholderText(
            "Scrivi SIC, ZSC, ZPS, bacini, ecc..."
        )
        self.campo_filtro.textChanged.connect(
            self.filtra_tabella
        )
        layout_filtro.addWidget(
            self.campo_filtro
        )
        self.layout_principale.addLayout(
            layout_filtro
        )

        layout_selezione = QHBoxLayout()
        btn_tutti = QPushButton(
            "Seleziona tutti"
        )
        btn_tutti.clicked.connect(
            lambda: self.seleziona_tutti(True)
        )
        btn_nessuno = QPushButton(
            "Deseleziona tutti"
        )
        btn_nessuno.clicked.connect(
            lambda: self.seleziona_tutti(False)
        )
        layout_selezione.addWidget(
            btn_tutti
        )
        layout_selezione.addWidget(
            btn_nessuno
        )
        layout_selezione.addStretch()
        self.layout_principale.addLayout(
            layout_selezione
        )

        self.tabella = QTableWidget(
            0,
            3
        )
        self.tabella.setHorizontalHeaderLabels(
            [
                "Scarica",
                "FeatureType WFS",
                "Alias / Nome GPKG"
            ]
        )
        self.tabella.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )
        self.tabella.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.Stretch
        )
        self.tabella.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.Stretch
        )
        self.riempi_tabella()
        self.layout_principale.addWidget(
            self.tabella
        )

        layout_area = QHBoxLayout()
        self.lbl_area = QLabel(
            "Area: estensione corrente della mappa"
        )
        self.lbl_area.setStyleSheet(
            "color:gray;font-style:italic;"
        )
        btn_disegna = QPushButton(
            "🖍 Disegna area sulla mappa"
        )
        btn_disegna.clicked.connect(
            self.attiva_disegno
        )
        btn_mappa = QPushButton(
            "Usa estensione mappa"
        )
        btn_mappa.clicked.connect(
            self.usa_estensione_mappa
        )
        layout_area.addWidget(
            self.lbl_area,
            1
        )
        layout_area.addWidget(
            btn_mappa
        )
        layout_area.addWidget(
            btn_disegna
        )
        self.layout_principale.addLayout(
            layout_area
        )

        layout_cartella = QHBoxLayout()
        layout_cartella.addWidget(
            QLabel("Cartella:")
        )
        self.campo_dir = QLineEdit()
        self.campo_dir.setPlaceholderText(
            "Cartella dove salvare i GeoPackage..."
        )
        btn_sfoglia = QPushButton(
            "Sfoglia..."
        )
        btn_sfoglia.clicked.connect(
            self.scegli_cartella
        )
        layout_cartella.addWidget(
            self.campo_dir
        )
        layout_cartella.addWidget(
            btn_sfoglia
        )
        self.layout_principale.addLayout(
            layout_cartella
        )

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        self.layout_principale.addWidget(
            self.progress
        )

        layout_bottoni = QHBoxLayout()
        btn_annulla = QPushButton(
            "Annulla"
        )
        btn_annulla.clicked.connect(
            self.reject
        )
        btn_download = QPushButton(
            "⬇ SCARICA IN LOCALE - GPKG"
        )
        btn_download.setStyleSheet(
            """
            background-color:#2d89ef;
            color:white;
            font-weight:bold;
            padding:10px;
            """
        )
        btn_download.clicked.connect(
            self.avvia_download
        )
        layout_bottoni.addStretch()
        layout_bottoni.addWidget(
            btn_annulla
        )
        layout_bottoni.addWidget(
            btn_download
        )
        self.layout_principale.addLayout(
            layout_bottoni
        )

    def riempi_tabella(
        self,
        filtro=""
    ):
        self.tabella.setRowCount(0)
        filtro = filtro.lower().strip()
        for ft in self.feature_types:
            nome = ft["name"]
            titolo = ft["title"]
            testo_ricerca = (
                nome + " " + titolo
            ).lower()
            if filtro and filtro not in testo_ricerca:
                continue
            r = self.tabella.rowCount()
            self.tabella.insertRow(r)

            item_check = QTableWidgetItem()
            item_check.setFlags(
                Qt.ItemIsUserCheckable |
                Qt.ItemIsEnabled
            )
            item_check.setCheckState(
                Qt.Unchecked
            )
            self.tabella.setItem(
                r,
                0,
                item_check
            )

            item_nome = QTableWidgetItem(
                nome
            )
            item_nome.setToolTip(
                titolo
            )
            item_nome.setFlags(
                Qt.ItemIsEnabled |
                Qt.ItemIsSelectable
            )
            self.tabella.setItem(
                r,
                1,
                item_nome
            )

            alias = nome
            if ":" in alias:
                alias = alias.split(":")[-1]
            alias = nome_file_sicuro(
                alias
            )
            item_alias = QTableWidgetItem(
                alias
            )
            item_alias.setFlags(
                Qt.ItemIsEnabled |
                Qt.ItemIsSelectable |
                Qt.ItemIsEditable
            )
            self.tabella.setItem(
                r,
                2,
                item_alias
            )

    def filtra_tabella(
        self,
        testo
    ):
        self.riempi_tabella(
            testo
        )

    def seleziona_tutti(
        self,
        seleziona=True
    ):
        for r in range(
            self.tabella.rowCount()
        ):
            item = self.tabella.item(
                r,
                0
            )
            if item:
                item.setCheckState(
                    Qt.Checked
                    if seleziona
                    else Qt.Unchecked
                )

    def scegli_cartella(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Seleziona cartella di output"
        )
        if path:
            self.campo_dir.setText(
                path
            )

    def usa_estensione_mappa(self):
        if not iface:
            QMessageBox.warning(
                self,
                "QGIS",
                "Interfaccia QGIS non disponibile."
            )
            return
        self.custom_extent = None
        self.lbl_area.setText(
            "Area: estensione corrente della mappa"
        )
        self.lbl_area.setStyleSheet(
            "color:gray;font-style:italic;"
        )

    def attiva_disegno(self):
        if not iface:
            QMessageBox.warning(
                self,
                "QGIS",
                "Interfaccia QGIS non disponibile."
            )
            return
        self.hide()
        canvas = iface.mapCanvas()
        self.map_tool = RectangleMapTool(
            canvas,
            self.ricevi_area
        )
        canvas.setMapTool(
            self.map_tool
        )
        iface.messageBar().pushMessage(
            "Area WFS",
            "Clicca e trascina sulla mappa "
            "per definire l'area di download.",
            level=Qgis.Info,
            duration=5
        )

    def ricevi_area(
        self,
        rect
    ):
        self.custom_extent = rect
        self.lbl_area.setText(
            "Area: rettangolo personalizzato ✓"
        )
        self.lbl_area.setStyleSheet(
            "color:green;font-weight:bold;"
        )
        self.show()
        self.raise_()
        self.activateWindow()

    def get_selezionati(self):
        risultati = []
        for r in range(
            self.tabella.rowCount()
        ):
            check = self.tabella.item(
                r,
                0
            )
            if (
                check
                and
                check.checkState() == Qt.Checked
            ):
                nome = self.tabella.item(
                    r,
                    1
                ).text()
                alias = self.tabella.item(
                    r,
                    2
                ).text()
                risultati.append({
                    "typename": nome,
                    "alias": alias
                })
        return risultati

    # ========================================================
    # DOWNLOAD
    # ========================================================
    def avvia_download(self):
        directory = self.campo_dir.text().strip()
        if not directory:
            QMessageBox.warning(
                self,
                "Attenzione",
                "Seleziona una cartella di output."
            )
            return

        selezionati = self.get_selezionati()
        if not selezionati:
            QMessageBox.warning(
                self,
                "Attenzione",
                "Seleziona almeno un layer da scaricare."
            )
            return

        estensione = self.custom_extent
        if estensione is None and iface:
            canvas = iface.mapCanvas()
            estensione = canvas.extent()

        self.progress.setVisible(True)
        self.progress.setValue(0)
        totale = len(selezionati)
        scaricati_ok = []
        errori = []

        for i, sel in enumerate(selezionati):
            typename = sel["typename"]
            alias = sel["alias"]
            nome_gpkg = f"{alias}.gpkg"
            percorso_gpkg = os.path.join(directory, nome_gpkg)

            percentuale = int((i / totale) * 100)
            self.progress.setValue(percentuale)
            QApplication.processEvents()

            try:
                wfs_uri = f"url='{self.url_server}' typename='{typename}'"
                if estensione:
                    xmin = estensione.xMinimum()
                    ymin = estensione.yMinimum()
                    xmax = estensione.xMaximum()
                    ymax = estensione.yMaximum()
                    wfs_uri += f" restrictToRequestBBOX='1' bbox='{xmin},{ymin},{xmax},{ymax}'"

                layer_wfs = QgsVectorLayer(wfs_uri, alias, "WFS")
                if not layer_wfs.isValid():
                    raise RuntimeError(f"Impossibile caricare il layer WFS '{typename}'.")

                error = QgsVectorFileWriter.writeAsVectorFormat(
                    layer_wfs,
                    percorso_gpkg,
                    "UTF-8",
                    layer_wfs.crs(),
                    "GPKG"
                )

                if isinstance(error, tuple):
                    err_code = error[0]
                    err_msg = error[1]
                else:
                    err_code = error
                    err_msg = ""

                if err_code != QgsVectorFileWriter.NoError:
                    raise RuntimeError(f"Errore scrittura GPKG: {err_msg}")

                scaricati_ok.append(alias)
                QgsMessageLog.logMessage(
                    f"Layer WFS '{typename}' salvato con successo in '{percorso_gpkg}'",
                    "GIS Offline",
                    Qgis.Info
                )

            except Exception as ex:
                errori.append(f"{typename}: {str(ex)}")
                QgsMessageLog.logMessage(
                    f"Errore download '{typename}': {str(ex)}",
                    "GIS Offline",
                    Qgis.Warning
                )

        self.progress.setValue(100)
        self.progress.setVisible(False)

        msg = f"Download completato!\n\nLayer salvati con successo: {len(scaricati_ok)}/{totale}"
        if errori:
            msg += f"\n\nErrori riscontrati ({len(errori)}):\n" + "\n".join(errori[:5])
            if len(errori) > 5:
                msg += "\n...e altri errori (vedi log)."
            QMessageBox.warning(self, "Completato con errori", msg)
        else:
            QMessageBox.information(self, "Successo", msg)

        self.accept()

# ============================================================
# ESECUZIONE PRINCIPALE
# ============================================================
if __name__ == "__main__" or iface is not None:
    dlg_sorgenti = FinestraSceltaSorgenti()
    if dlg_sorgenti.exec_() == QDialog.Accepted and dlg_sorgenti.url_selezionato:
        dlg_layer = FinestraSelezioneLayer(
            dlg_sorgenti.url_selezionato,
            dlg_sorgenti.nome_sorgente
        )
        dlg_layer.exec_()
