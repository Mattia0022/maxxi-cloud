import os
from qgis.core import QgsMapLayer, QgsProject, QgsRasterLayer, QgsWkbTypes
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
)
from qgis.utils import iface
import processing


class RasterSelectDialog(QDialog):
    def __init__(self, rasters, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Step 1/2: Selezione Raster")
        self.resize(450, 480)
        layout = QVBoxLayout()

        label = QLabel("<b>Step 1:</b> Seleziona i layer raster da ritagliare:")
        label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Cerca layer raster per nome...")
        self.search_box.setStyleSheet("font-size: 10pt; padding: 5px;")
        self.search_box.textChanged.connect(self.filter_rasters)
        layout.addWidget(self.search_box)

        self.raster_list = QListWidget()
        self.raster_list.setStyleSheet("font-size: 10pt;")
        self.raster_list.setSelectionMode(QListWidget.MultiSelection)
        for r in rasters:
            item = QListWidgetItem(r.name())
            item.setData(Qt.UserRole, r)
            self.raster_list.addItem(item)
        layout.addWidget(self.raster_list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.setStyleSheet("font-size: 10pt;")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def filter_rasters(self, text):
        for index in range(self.raster_list.count()):
            item = self.raster_list.item(index)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def get_selected(self):
        return [
            item.data(Qt.UserRole)
            for item in self.raster_list.selectedItems()
            if not item.isHidden()
        ]


class MaskSelectDialog(QDialog):
    def __init__(self, vectors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Step 2/2: Selezione Maschera")
        self.resize(450, 400)
        layout = QVBoxLayout()

        label = QLabel("<b>Step 2:</b> Seleziona il layer maschera:")
        label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Cerca layer maschera per nome...")
        self.search_box.setStyleSheet("font-size: 10pt; padding: 5px;")
        self.search_box.textChanged.connect(self.filter_masks)
        layout.addWidget(self.search_box)

        self.mask_list = QListWidget()
        self.mask_list.setStyleSheet("font-size: 10pt;")
        self.mask_list.setSelectionMode(QListWidget.SingleSelection)
        for v in vectors:
            item = QListWidgetItem(v.name())
            item.setData(Qt.UserRole, v)
            self.mask_list.addItem(item)
        layout.addWidget(self.mask_list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.setStyleSheet("font-size: 10pt;")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def filter_masks(self, text):
        for index in range(self.mask_list.count()):
            item = self.mask_list.item(index)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def get_selected_mask(self):
        selected = self.mask_list.selectedItems()
        return (
            selected[0].data(Qt.UserRole)
            if selected and not selected[0].isHidden()
            else None
        )


def run():
    """Punto d'ingresso obbligatorio richiesto da QGIS / maxxi-cloud."""
    parent = iface.mainWindow() if iface else None

    # Trova tutti i layer raster e vettoriali poligonali
    raster_layers = [
        l
        for l in QgsProject.instance().mapLayers().values()
        if l.type() == QgsMapLayer.RasterLayer
    ]
    vector_layers = [
        l
        for l in QgsProject.instance().mapLayers().values()
        if l.type() == QgsMapLayer.VectorLayer
        and l.geometryType() == QgsWkbTypes.PolygonGeometry
    ]

    if not raster_layers:
        QMessageBox.critical(
            parent, "Errore", "Nessun layer raster trovato nel progetto QGIS."
        )
        return
    if not vector_layers:
        QMessageBox.critical(
            parent,
            "Errore",
            "Nessun layer poligonale (maschera) trovato nel progetto QGIS.",
        )
        return

    # Esecuzione del flusso a schermate
    dlg_raster = RasterSelectDialog(raster_layers, parent)
    if dlg_raster.exec_() == QDialog.Accepted:
        selected_rasters = dlg_raster.get_selected()

        if not selected_rasters:
            QMessageBox.warning(
                parent, "Attenzione", "Devi selezionare almeno un layer raster!"
            )
            return

        dlg_mask = MaskSelectDialog(vector_layers, parent)
        if dlg_mask.exec_() == QDialog.Accepted:
            mask_layer = dlg_mask.get_selected_mask()

            if not mask_layer:
                QMessageBox.critical(
                    parent,
                    "Errore",
                    "Non hai selezionato alcun layer maschera! Operazione annullata.",
                )
                return

            reply = QMessageBox.question(
                parent,
                "Personalizzazione Nome",
                "Vuoi aggiungere il suffisso '_ritagliato' alla fine del nome dei file?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            add_suffix = reply == QMessageBox.Yes

            output_dir = QFileDialog.getExistingDirectory(
                parent, "Seleziona la cartella in cui salvare i file ritagliati"
            )

            if not output_dir:
                print("Operazione annullata: nessuna cartella di destinazione scelta.")
                return

            success_count = 0
            for raster_layer in selected_rasters:
                source_path = raster_layer.source()
                if "|" in source_path:
                    source_path = source_path.split("|")[0]

                if os.path.exists(source_path):
                    _, filename = os.path.split(source_path)
                    name_no_ext, ext = os.path.splitext(filename)
                    if not ext:
                        ext = ".tif"
                else:
                    name_no_ext = raster_layer.name()
                    ext = ".tif"

                if add_suffix:
                    output_filename = f"{name_no_ext}_ritagliato{ext}"
                    out_name_layer = f"{raster_layer.name()}_ritagliato"
                else:
                    output_filename = f"{name_no_ext}{ext}"
                    out_name_layer = raster_layer.name()

                output_path = os.path.join(output_dir, output_filename)

                print(
                    f"Elaborazione in corso: {raster_layer.name()} -> {output_filename}"
                )

                params = {
                    "INPUT": raster_layer,
                    "MASK": mask_layer,
                    "SOURCE_CRS": None,
                    "TARGET_CRS": None,
                    "TARGET_EXTENT": None,
                    "NODATA": None,
                    "ALPHA": False,
                    "CROP_TO_CUTLINE": True,
                    "KEEP_RESOLUTION": True,
                    "OPTIONS": "",
                    "DATA_TYPE": 0,
                    "OUTPUT": output_path,
                }

                try:
                    res = processing.run("gdal:cliprasterbymasklayer", params)

                    if "OUTPUT" in res:
                        out_path = res["OUTPUT"]
                        if os.path.exists(out_path):
                            new_layer = QgsRasterLayer(out_path, out_name_layer)
                            if new_layer.isValid():
                                QgsProject.instance().addMapLayer(new_layer)

                    success_count += 1
                except Exception as e:
                    print(
                        f"Errore durante il ritaglio di {raster_layer.name()}: {e}"
                    )

            QMessageBox.information(
                parent,
                "Completato",
                f"Processo completato!\nRitagliati con successo {success_count} su {len(selected_rasters)} file.\nSalvati in: {output_dir}",
            )
