import math
from qgis.core import QgsProject, QgsWkbTypes, QgsPointXY
from qgis.PyQt.QtWidgets import QInputDialog, QFileDialog, QMessageBox

def run():
    # 1. SELEZIONE LAYER
    all_layers = QgsProject.instance().mapLayers().values()
    point_layers = [l for l in all_layers if l.type() == l.VectorLayer and l.geometryType() == QgsWkbTypes.PointGeometry]

    if not point_layers:
        QMessageBox.critical(None, "Errore", "Nessun layer di punti trovato nel progetto.")
        return

    layer_names = [l.name() for l in point_layers]
    selected_layer_name, ok = QInputDialog.getItem(
        None, "Seleziona Layer", "Scegli il layer di punti:", layer_names, 0, False
    )

    if not ok or not selected_layer_name:
        return

    layer = [l for l in point_layers if l.name() == selected_layer_name][0]
    selected_features = list(layer.selectedFeatures())

    if len(selected_features) < 2:
        QMessageBox.warning(None, "Attenzione", "Seleziona almeno 2 punti sulla mappa!")
        return

    # 2. SELEZIONE CAMPO QUOTA
    fields = [field.name() for field in layer.fields()]
    options = ["[ Usa Geometria Z (Punti 3D) ]"] + fields
    quota_choice, ok_q = QInputDialog.getItem(
        None, "Seleziona Quota", "Scegli la colonna della quota o la Z 3D:", options, 0, False
    )

    if not ok_q or not quota_choice:
        return

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

    # 3. DEFINIZIONE ASSE DI SEZIONE (Primo -> Ultimo punto)
    p_start = raw_pts[0]
    p_end = raw_pts[-1]

    dx = p_end['x'] - p_start['x']
    dy = p_end['y'] - p_start['y']
    lunghezza_asse_sq = dx**2 + dy**2
    lunghezza_asse = math.sqrt(lunghezza_asse_sq)

    if lunghezza_asse == 0:
        QMessageBox.critical(None, "Errore", "Il primo e l'ultimo punto coincidono!")
        return

    # 4. PROIEZIONE ORTOGONALE DEI PUNTI SULL'ASSE
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

    # 5. GENERAZIONE FILE .SCR
    filepath, _ = QFileDialog.getSaveFileName(
        None, "Salva Script AutoCAD", "profilo_proiettato.scr", "AutoCAD Script (*.scr)"
    )

    if filepath:
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
            None, "Completato", 
            f"Profilo proiettato generato con successo!\n"
            f"Lunghezza Asse Sezione: {lunghezza_asse:.2f} m\n"
            f"Punti elaborati: {len(dati_profilo)}"
        )
