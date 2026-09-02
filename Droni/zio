import os
import shutil
import tempfile

# Moduli principali di QGIS per gestire progetti, vettori, geometrie, stili e azioni
from qgis.core import (
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsField,
    QgsSymbol,
    QgsSingleSymbolRenderer,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsAction,
    Qgis
)

# Moduli di PyQt5 per la gestione dei tipi di dati, grafica e componenti di interfaccia
from PyQt5.QtCore import QVariant, Qt
from PyQt5.QtGui import QColor, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QAction, QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, 
    QFileDialog, QMessageBox, QInputDialog, QListWidget, QAbstractItemView, QHBoxLayout, QProgressBar, QApplication
)

# Interfaccia utente standard di QGIS
from qgis.utils import iface

# ==========================================
# 1. INTERFACCIA PER IL MENU DI SCELTA INIZIALE
# ==========================================
class MenuSceltaDialog(QDialog):
    def __init__(self, plugin_dir):
        super().__init__()
        # Impostiamo il titolo e le dimensioni della finestra di scelta
        self.setWindowTitle("Gestione Foto & QGIS")
        self.resize(450, 360)
        
        # Disposizione verticale degli elementi dell'interfaccia
        layout = QVBoxLayout()
        
        # Tentiamo di caricare e mostrare un logo visivo all'apertura
        img_path = os.path.join(plugin_dir, "logo_inizio.png")
        if os.path.exists(img_path):
            lbl_img = QLabel()
            pixmap = QPixmap(img_path).scaled(400, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_img.setPixmap(pixmap)
            lbl_img.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_img)
            
        # Testo e menu a tendina per selezionare la funzionalità desiderata
        layout.addWidget(QLabel("<b>Seleziona l'operazione da eseguire:</b>"))
        
        self.combo = QComboBox()
        self.combo.addItem("1. Importa foto da cartella, crea Shapefile e configura QGIS")
        self.combo.addItem("2. Esporta/Copia foto da layer multipli basandoti su Poligoni")
        layout.addWidget(self.combo)
        
        # Pulsante per confermare la scelta
        btn_layout = QHBoxLayout()
        btn_esegui = QPushButton("Esegui")
        btn_esegui.clicked.connect(self.accept)
        btn_esegui.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        btn_layout.addWidget(btn_esegui)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

# ==========================================
# 2. INTERFACCIA PER LA SELEZIONE MULTIPLA DEI LAYER
# ==========================================
class MultiLayerSelectDialog(QDialog):
    def __init__(self, layer_names, titolo):
        super().__init__()
        self.setWindowTitle(titolo)
        self.resize(350, 250)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Seleziona uno o più layer (usa Ctrl + Click):"))
        
        # Lista personalizzata che permette di selezionare più layer contemporaneamente
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        for name in layer_names:
            self.list_widget.addItem(name)
        layout.addWidget(self.list_widget)
        
        btn_ok = QPushButton("Conferma")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)
        self.setLayout(layout)
        
    def get_selected_layers(self):
        # Restituisce l'elenco dei nomi di layer selezionati dall'utente
        return [item.text() for item in self.list_widget.selectedItems()]

# ==========================================
# 3. INTERFACCIA CON BARRA DI PROGRESSO
# ==========================================
class ProgressDialog(QDialog):
    def __init__(self, titolo, plugin_dir):
        super().__init__()
        self.setWindowTitle(titolo)
        self.resize(450, 220)
        self.setModal(True) # Blocca l'interazione con altre finestre fino al termine
        
        layout = QVBoxLayout()
        
        # Caricamento eventuale del logo iniziale
        img_path = os.path.join(plugin_dir, "logo_inizio.png")
        if os.path.exists(img_path):
            lbl_img = QLabel()
            pixmap = QPixmap(img_path).scaled(400, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_img.setPixmap(pixmap)
            lbl_img.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_img)
            
        # Testo descrittivo dello stato dell'operazione
        self.lbl_status = QLabel("Preparazione elaborazione...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_status)
        
        # Definizione visiva della barra di avanzamento
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar { border: 2px solid grey; border-radius: 5px; text-align: center; } QProgressBar::chunk { background-color: #4CAF50; width: 10px; }")
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
    def update_progress(self, valore, testo):
        # Aggiorna la percentuale e il testo, forzando il ridisegno della finestra
        self.progress_bar.setValue(valore)
        self.lbl_status.setText(testo)
        QApplication.processEvents()

# ==========================================
# 4. INTERFACCIA DI NOTIFICA DI FINE LAVORO
# ==========================================
class FinalMessageDialog(QDialog):
    def __init__(self, messaggio, plugin_dir):
        super().__init__()
        self.setWindowTitle("Elaborazione Completata")
        self.resize(420, 380)
        
        # Configurazione dello stile della finestra (sfondo scuro)
        self.setStyleSheet("background-color: #121212; color: #ffffff;")
        
        layout = QVBoxLayout()
        
        # Caricamento del logo di fine lavoro
        img_path = os.path.join(plugin_dir, "logo_fine.png")
        if os.path.exists(img_path):
            lbl_img = QLabel()
            pixmap = QPixmap(img_path).scaled(380, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_img.setPixmap(pixmap)
            lbl_img.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_img)
        
        lbl_msg = QLabel(messaggio)
        lbl_msg.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        lbl_msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_msg)
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setStyleSheet("background-color: #333333; color: white; border: 1px solid #555555; padding: 6px; font-weight: bold;")
        layout.addWidget(btn_ok)
        
        self.setLayout(layout)

# ==========================================
# 5. CLASSE PRINCIPALE DEL PLUGIN QGIS
# ==========================================
class GestioneFotoPlugin:
    def __init__(self, iface_param=None):
        self.iface = iface_param if iface_param else iface
        
        # Identifica dove si trova il plugin per caricare icone e immagini
        try:
            self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            self.plugin_dir = tempfile.gettempdir()
            
        self.action = None

    def initGui(self):
        # Aggiunge l'icona del plugin ai menu e alla barra degli strumenti di QGIS
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        
        parent_win = self.iface.mainWindow() if self.iface else None
        self.action = QAction(icon, "Gestione Foto & QGIS", parent_win)
        self.action.triggered.connect(self.run)
        if self.iface:
            self.iface.addToolBarIcon(self.action)
            self.iface.addPluginToMenu("&Gestione Foto", self.action)

    def unload(self):
        # Rimuove il plugin da QGIS quando viene disattivato
        if self.iface and self.action:
            self.iface.removePluginMenu("&Gestione Foto", self.action)
            self.iface.removeToolBarIcon(self.action)

    def run(self):
        # Mostra la finestra iniziale e richiama l'operazione scelta
        dialogo = MenuSceltaDialog(self.plugin_dir)
        if dialogo.exec_() == QDialog.Accepted:
            scelta = dialogo.combo.currentIndex()
            if scelta == 0:
                self.esegui_opzione_1()
            elif scelta == 1:
                self.esegui_opzione_2()

    # ----------------------------------------------------
    # OPZIONE 1: LORENZ/SHAPEFILE DA FOTO CON EXIF
    # ----------------------------------------------------
    def esegui_opzione_1(self):
        # Selezione cartella delle foto in ingresso
        cartella_madre = QFileDialog.getExistingDirectory(None, "1/2 - Seleziona la Cartella Madre contenente le foto")
        if not cartella_madre:
            return
            
        # Selezione cartella in cui salvare gli Shapefile di output
        cartella_output = QFileDialog.getExistingDirectory(None, "2/2 - Seleziona la Cartella dove SALVARE i file SHP")
        if not cartella_output:
            return

        # Funzione di estrazione coordinate dai metadati EXIF delle immagini
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            
            def get_exif_location(image_path):
                try:
                    image = Image.open(image_path)
                    info = image._getexif()
                    if not info:
                        return None, None
                    exif = {}
                    for tag, value in info.items():
                        decoded = TAGS.get(tag, tag)
                        if decoded == "GPSInfo":
                            gps_data = {}
                            for t in value:
                                sub_decoded = GPSTAGS.get(t, t)
                                gps_data[sub_decoded] = value[t]
                            exif["GPSInfo"] = gps_data
                        else:
                            exif[decoded] = value
                    if "GPSInfo" not in exif:
                        return None, None
                        
                    # Conversione da Gradi, Minuti, Secondi a Gradi Decimali
                    def convert_to_degrees(value):
                        return value[0] + (value[1] / 60.0) + (value[2] / 3600.0)
                        
                    gps_info = exif["GPSInfo"]
                    lat = convert_to_degrees(gps_info["GPSLatitude"])
                    if gps_info["GPSLatitudeRef"] != "N":
                        lat = -lat
                    lon = convert_to_degrees(gps_info["GPSLongitude"])
                    if gps_info["GPSLongitudeRef"] != "E":
                        lon = -lon
                    return lon, lat
                except Exception:
                    return None, None
        except ImportError:
            # Ritorna vuoto se la libreria PIL per la lettura delle foto manca
            def get_exif_location(image_path):
                return None, None

        # Ricerca ricorsiva di tutti i file immagine all'interno delle cartelle
        estensioni_valide = (".jpg", ".jpeg", ".JPG", ".JPEG", ".tif", ".TIFF")
        dizionario_cartelle = {}
        for root_dir, dirs, files in os.walk(cartella_madre):
            foto_trovate = [os.path.join(root_dir, f) for f in files if f.endswith(estensioni_valide)]
            if foto_trovate:
                nome_sottocartella = os.path.basename(root_dir)
                if not nome_sottocartella:
                    nome_sottocartella = "Radice"
                dizionario_cartelle[nome_sottocartella] = foto_trovate

        if not dizionario_cartelle:
            QMessageBox.warning(None, "Attenzione", "Nessuna foto trovata nella cartella selezionata!")
            return

        totale_foto = sum(len(v) for v in dizionario_cartelle.values())
        processate = 0

        progress_dlg = ProgressDialog("Importazione Foto e Creazione Shapefile", self.plugin_dir)
        progress_dlg.show()

        # Palette di colori per distinguere visivamente i layer importati
        colori = [QColor("#e41a1c"), QColor("#377eb8"), QColor("#4daf4a"), QColor("#984ea3"), QColor("#ff7f00"), QColor("#ffff33"), QColor("#a65628")]
        
        # Creazione di un gruppo dedicato nella legenda di QGIS
        root_node = QgsProject.instance().layerTreeRoot()
        gruppo_foto = root_node.addGroup(f"Foto - {os.path.basename(cartella_madre)}")

        idx_colore = 0
        totale_importate = 0

        # Ciclo di lettura ed elaborazione per ciascuna cartella e foto trovata
        for nome_cartella, lista_file in dizionario_cartelle.items():
            # Layer temporaneo in memoria per la georeferenziazione iniziale
            layer_mem = QgsVectorLayer("Point?crs=EPSG:4326", f"Cartella: {nome_cartella}", "memory")
            pr = layer_mem.dataProvider()
            pr.addAttributes([
                QgsField("file_name", QVariant.String),
                QgsField("file_path", QVariant.String),
                QgsField("folder", QVariant.String)
            ])
            layer_mem.updateFields()
            
            count_cartella = 0
            for f_path in lista_file:
                processate += 1
                percentuale = int((processate / totale_foto) * 100) if totale_foto > 0 else 100
                progress_dlg.update_progress(percentuale, f"Elaborazione: {percentuale}% ({processate}/{totale_foto} foto)")
                
                if not os.path.exists(f_path):
                    continue
                lon, lat = get_exif_location(f_path)
                if lon is None or lat is None:
                    continue
                    
                # Creazione del punto geografico basato sulle coordinate EXIF
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
                file_name = os.path.basename(f_path)
                feat.setAttributes([file_name, f_path, nome_cartella])
                pr.addFeature(feat)
                count_cartella += 1
                totale_importate += 1
                
            if count_cartella == 0:
                continue
            layer_mem.updateExtents()
            
            # Scrittura fisica su disco del file Shapefile (.shp)
            nome_shp_pulito = "".join([c if c.isalnum() else "_" for c in nome_cartella])
            shp_path = os.path.join(cartella_output, f"foto_{nome_shp_pulito}.shp")
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "ESRI Shapefile"
            options.fileEncoding = "UTF-8"
            transform_context = QgsProject.instance().transformContext()
            
            result = QgsVectorFileWriter.writeAsVectorFormatV3(layer_mem, shp_path, transform_context, options)
            error = result[0] if isinstance(result, tuple) else result
            if error != QgsVectorFileWriter.NoError:
                continue
                
            # Caricamento dello Shapefile appena creato nel progetto
            layer = QgsVectorLayer(shp_path, f"Foto - {nome_cartella}", "ogr")
            if not layer.isValid():
                continue
                
            # Configurazione dello stile grafico del punto
            colore_corrente = colori[idx_colore % len(colori)]
            idx_colore += 1
            
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.setColor(colore_corrente)
            symbol.setSize(4.0)
            layer.setRenderer(QgsSingleSymbolRenderer(symbol))
            
            # Configurazione delle etichette del punto (nome del file con sfondo bianco)
            lbl_settings = QgsPalLayerSettings()
            lbl_settings.fieldName = "file_name"
            lbl_settings.enabled = True
            text_format = QgsTextFormat()
            text_format.setSize(8)
            text_format.setColor(QColor("#333333"))
            buffer_settings = QgsTextBufferSettings()
            buffer_settings.setEnabled(True)
            buffer_settings.setSize(0.8)
            buffer_settings.setColor(QColor(255, 255, 255, 200))
            text_format.setBuffer(buffer_settings)
            lbl_settings.setFormat(text_format)
            layer.setLabeling(QgsVectorLayerSimpleLabeling(lbl_settings))
            layer.setLabelsEnabled(True)
            
            # Aggiunta di un'Azione per aprire la cartella della foto con un click nel layer
            action_text = 'import os, subprocess; subprocess.Popen(r"explorer " + os.path.dirname(r"[% "file_path" %]"))'
            action = QgsAction(Qgis.AttributeActionType.Generic, "Apri Cartella", action_text, False)
            layer.actions().addAction(action)
            
            # Aggiunta formale al progetto QGIS all'interno del gruppo dedicato
            QgsProject.instance().addMapLayer(layer, False)
            gruppo_foto.addLayer(layer)

        progress_dlg.close()
        msg_finale = f"Elaborazione riuscita!\n\nFoto georeferenziate caricate: {totale_importate}\nShapefile salvati in:\n{cartella_output}"
        FinalMessageDialog(msg_finale, self.plugin_dir).exec_()

    # ----------------------------------------------------
    # OPZIONE 2: ORGANIZZAZIONE FOTO TRAMITE POLIGONI
    # ----------------------------------------------------
    def esegui_opzione_2(self):
        layers_progetto = QgsProject.instance().mapLayers().values()
        
        # Filtriamo solo i layer con geometrie poligonali (geometryType == 2)
        layer_poligoni_list = [l for l in layers_progetto if isinstance(l, QgsVectorLayer) and l.geometryType() == 2]
        if not layer_poligoni_list:
            QMessageBox.warning(None, "Attenzione", "Non ci sono layer poligonali caricati nel progetto QGIS!")
            return
            
        dlg_poly = MultiLayerSelectDialog([l.name() for l in layer_poligoni_list], "Seleziona Layer Poligonali")
        if dlg_poly.exec_() != QDialog.Accepted:
            return
        poly_scelti_nomi = dlg_poly.get_selected_layers()
        if not poly_scelti_nomi:
            return
        layers_poligoni_selezionati = [l for l in layer_poligoni_list if l.name() in poly_scelti_nomi]
        
        # Selezione del campo/colonna che identifica in modo univoco ogni poligono
        campi = [f.name() for f in layers_poligoni_selezionati[0].fields()]
        campo_scelto, ok = QInputDialog.getItem(None, "Campo Identificativo", "Seleziona il campo del poligono:", campi, 0, False)
        if not ok:
            return

        # Filtriamo solo i layer con geometrie puntuali (geometryType == 0)
        layer_punti_list = [l for l in layers_progetto if isinstance(l, QgsVectorLayer) and l.geometryType() == 0]
        if not layer_punti_list:
            QMessageBox.warning(None, "Attenzione", "Non ci sono layer puntuali (foto) caricati nel progetto QGIS!")
            return
            
        dlg_punti = MultiLayerSelectDialog([l.name() for l in layer_punti_list], "Seleziona Layer Punti Foto")
        if dlg_punti.exec_() != QDialog.Accepted:
            return
        punti_scelti_nomi = dlg_punti.get_selected_layers()
        if not punti_scelti_nomi:
            return
        layers_punti_selezionati = [l for l in layer_punti_list if l.name() in punti_scelti_nomi]

        # Cartella base in cui creare la struttura di sottocartelle
        cartella_destinazione = QFileDialog.getExistingDirectory(None, "Seleziona la cartella radice di destinazione")
        if not cartella_destinazione:
            return

        totale_features = sum(l.featureCount() for l in layers_punti_selezionati)
        processate = 0
        copiate = 0

        progress_dlg = ProgressDialog("Esportazione e Copia Foto su Poligoni", self.plugin_dir)
        progress_dlg.show()

        # Ciclo spaziale: controlliamo ogni punto in quale poligono ricade
        for layer_punto in layers_punti_selezionati:
            campi_punti = [f.name() for f in layer_punto.fields()]
            if "file_path" not in campi_punti:
                continue
                
            for feat_punto in layer_punto.getFeatures():
                processate += 1
                if totale_features > 0:
                    percentuale = int((processate / totale_features) * 100)
                    progress_dlg.update_progress(percentuale, f"Analisi punti: {percentuale}% ({processate}/{totale_features})")
                
                geom_punto = feat_punto.geometry()
                file_path = feat_punto["file_path"]
                
                if not file_path or not os.path.exists(file_path):
                    continue
                    
                trovato = False
                for layer_poly in layers_poligoni_selezionati:
                    if layer_poly.fields().indexOf(campo_scelto) == -1:
                        continue
                        
                    for feat_poly in layer_poly.getFeatures():
                        # Verifica spaziale: il punto si trova dentro il poligono?
                        if feat_poly.geometry().contains(geom_punto):
                            valore_id = str(feat_poly[campo_scelto]).strip()
                            valore_pulito = "".join([c if c.isalnum() else "_" for c in valore_id])
                            
                            # Creazione della sottocartella dedicata al poligono se non esiste
                            cartella_poligono = os.path.join(cartella_destinazione, valore_pulito)
                            if not os.path.exists(cartella_poligono):
                                os.makedirs(cartella_poligono)
                            
                            # Copia fisica del file immagine rinominato nella sottocartella di destinazione
                            nome_file_orig = os.path.basename(file_path)
                            nuovo_nome_file = f"{valore_pulito}_{nome_file_orig}"
                            dest_path = os.path.join(cartella_destinazione, valore_pulito, nuovo_nome_file)
                            
                            shutil.copy2(file_path, dest_path)
                            copiate += 1
                            trovato = True
                            break
                    if trovato:
                        break

        progress_dlg.close()
        msg_finale = f"Processo completato!\n\nSono state copiate e organizzate {copiate} foto nelle sottocartelle dei poligoni dentro:\n{cartella_destinazione}"
        FinalMessageDialog(msg_finale, self.plugin_dir).exec_()

# ==========================================
# PUNTO DI INGRESSO (ENTRYPOINT) DEL PLUGIN
# ==========================================
def run():
    plugin = GestioneFotoPlugin(iface)
    plugin.run()
