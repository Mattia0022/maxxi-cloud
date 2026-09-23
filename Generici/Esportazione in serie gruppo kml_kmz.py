import os
from pathlib import Path
from qgis.core import QgsProject, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QListWidget, QDialog, QVBoxLayout, QPushButton, QAbstractItemView

def run():
    # 1. Recupera il gruppo selezionato nel pannello dei Layer
    nodo_corrente = iface.layerTreeView().currentNode()

    if not nodo_corrente or nodo_corrente.nodeType() != 0:  # 0 corrisponde a un Gruppo
        QMessageBox.warning(None, "Attenzione", "Seleziona prima il GRUPPO di layer nel pannello a sinistra!")
    else:
        nome_gruppo = nodo_corrente.name()
        figli = nodo_corrente.findLayers()
        
        # Filtra solo i layer vettoriali validi presenti nel gruppo
        dict_layer = {f.layer().name(): f.layer() for f in figli if f.layer() and f.layer().type() == 0}
        
        if not dict_layer:
            QMessageBox.warning(None, "Attenzione", f"Non ci sono layer vettoriali validi nel gruppo '{nome_gruppo}'.")
        else:
            # 2. Crea una finestra di dialogo personalizzata per la multi-selezione dei layer
            dialog = QDialog()
            dialog.setWindowTitle("Seleziona i layer da esportare")
            dialog.setMinimumWidth(400)
            layout = QVBoxLayout(dialog)
            
            lista_widget = QListWidget()
            lista_widget.setSelectionMode(QAbstractItemView.ExtendedSelection) # Permette la selezione multipla con Ctrl o Shift
            lista_widget.addItems(dict_layer.keys())
            layout.addWidget(lista_widget)
            
            btn_conferma = QPushButton("Conferma Selezione")
            btn_conferma.clicked.connect(dialog.accept)
            layout.addWidget(btn_conferma)
            
            # Mostra la finestra e controlla se l'utente ha confermato
            if dialog.exec_() == QDialog.Accepted:
                layer_scelti = [item.text() for item in lista_widget.selectedItems()]
                
                if not layer_scelti:
                    QMessageBox.information(None, "Info", "Nessun layer selezionato. Operazione annullata.")
                else:
                    # 3. Chiede all'utente il formato desiderato (.kml o .kmz)
                    formati = ["KML (.kml)", "KMZ (.kmz)"]
                    formato_scelto, ok = QInputDialog.getItem(None, "Scegli il formato", "In quale formato vuoi esportare?", formati, 0, False)
                    
                    if ok and formato_scelto:
                        estensione = ".kml" if "KML" in formato_scelto else ".kmz"
                        driver_name = "KML" if estensione == ".kml" else "LIBKML"
                        
                        # 4. Chiede dove salvare i file esportati
                        cartella_destinazione = QFileDialog.getExistingDirectory(None, f"Scegli dove salvare i file {estensione.upper()}", "C:\\Users\\userm\\Desktop")
                        
                        if not cartella_destinazione:
                            print("Esportazione annullata.")
                        else:
                            percorso_out = Path(cartella_destinazione)
                            print(f"Inizio esportazione di {len(layer_scelti)} layer in SR EPSG:32632...\n" + "-"*50)
                            
                            file_esportati = 0
                            
                            # Definizione del Sistema di Riferimento (UTM 32N)
                            sr_utm32n = QgsCoordinateReferenceSystem("EPSG:32632")
                            
                            for nome_l in layer_scelti:
                                layer = dict_layer[nome_l]
                                nome_file = f"{layer.name()}{estensione}"
                                percorso_completo = str(percorso_out / nome_file)
                                
                                # Configura le opzioni di salvataggio
                                opzioni = QgsVectorFileWriter.SaveVectorOptions()
                                opzioni.driverName = driver_name
                                opzioni.fileEncoding = "UTF-8"
                                
                                # TRASFORMAZIONE COORD: Forza la riproiezione
                                opzioni.ct = QgsCoordinateTransform(layer.crs(), sr_utm32n, QgsProject.instance())
                                
                                # Esegue la scrittura intercettando l'output
                                risultato = QgsVectorFileWriter.writeAsVectorFormatV3(
                                    layer,
                                    percorso_completo,
                                    QgsProject.instance().transformContext(),
                                    opzioni
                                )
                                
                                errore = risultato[0]
                                messaggio = risultato[1]
                                
                                if errore == QgsVectorFileWriter.NoError:
                                    print(f"[OK] Esportato in EPSG:32632: {nome_file}")
                                    file_esportati += 1
                                else:
                                    print(f"[ERRORE] Impossibile convertire {layer.name()}: {messaggio}")
                                    
                            print("-"*50)
                            print(f"PROCESSO CONCLUSO! Esportati con successo {file_esportati} file {estensione.upper()} in UTM zone 32N.")
