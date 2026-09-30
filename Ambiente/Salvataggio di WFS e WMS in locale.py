error = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, gpkg_path, QgsProject.instance().transformContext(), options
            )
            
            if error[0] != QgsVectorFileWriter.NoError:
                QgsMessageLog.logMessage(f"Errore salvataggio GPKG per {alias}: {error[1]}", "WFS Script", level=Qgis.Critical)
                falliti += 1
            else:
                # CONTROLLO DI SICUREZZA: verifichiamo se il file creato contiene effettivamente dei dati
                layer_verifica = QgsVectorLayer(gpkg_path, alias, "ogr")
                if layer_verifica.isValid() and layer_verifica.featureCount() > 0:
                    salvati += 1
                    QgsProject.instance().addMapLayer(layer_verifica)
                else:
                    # Il file è vuoto! (0 feature scaricate)
                    if layer_verifica.isValid():
                        layer_verifica.deleteLater()
                    # Rimuoviamo il file vuoto dal disco per non lasciare file spazzatura
                    if os.path.exists(gpkg_path):
                        try:
                            os.remove(gpkg_path)
                        except:
                            pass
                    
                    QgsMessageLog.logMessage(f"Il layer {alias} è stato scaricato ma il GPKG è vuoto (0 feature). Probabile filtro spaziale non valido o server vuoto.", "WFS Script", level=Qgis.Warning)
                    falliti += 1
