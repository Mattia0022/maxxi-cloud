# -*- coding: utf-8 -*-
from qgis.core import QgsProject, QgsLayoutItemLegend
from qgis.PyQt.QtWidgets import (
    QInputDialog,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QAbstractItemView,
)


class DialogoSelezioneLegende(QDialog):
    def __init__(self, legend_items_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selezione Specifica Legende - QGIS")
        self.resize(500, 450)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Seleziona le singole legende da modificare:\n(Tieni premuto CTRL o MAIUSC per selezioni multiple)"
            )
        )

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        
        self.mapping = {}
        for info_str, layout_obj, legend_item in legend_items_info:
            item_widget = QListWidgetItem(info_str)
            self.list_widget.addItem(item_widget)
            self.mapping[item_widget] = (layout_obj, legend_item)

        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_legends(self):
        return [self.mapping[item] for item in self.list_widget.selectedItems()]


def run():
    project = QgsProject.instance()
    manager = project.layoutManager()

    # 1. Recupera i layer del progetto
    layers_dict = {layer.name(): layer for layer in project.mapLayers().values()}
    layer_names = sorted(list(layers_dict.keys()))

    if not layer_names:
        QMessageBox.warning(None, "Attenzione", "Nessun layer trovato nel progetto.")
        return

    # 2. Scegli l'operazione (Aggiungi o Rimuovi)
    azioni = ["Aggiungi layer alla legenda", "Rimuovi layer dalla legenda"]
    azione_scelta, ok_azione = QInputDialog.getItem(
        None,
        "Gestione Layer Legenda",
        "Scegli l'operazione da eseguire:",
        azioni,
        0,
        False,
    )
    if not ok_azione or not azione_scelta:
        return

    is_aggiunta = "Aggiungi" in azione_scelta

    # 3. Scelta del layer su cui agire
    titolo_dialogo = "Aggiungi Layer a Legenda" if is_aggiunta else "Rimuovi Layer da Legenda"
    messaggio_dialogo = "Seleziona il layer da aggiungere:" if is_aggiunta else "Seleziona il layer da rimuovere:"
    
    target_layer_name, ok_layer = QInputDialog.getItem(
        None,
        titolo_dialogo,
        messaggio_dialogo,
        layer_names,
        0,
        False,
    )
    if not ok_layer or not target_layer_name:
        return

    # 4. Scansiona tutti i layout e raccoglie TUTTE le singole legende trovate
    all_layouts = manager.printLayouts()
    legend_items_info = []

    for layout in all_layouts:
        for item in layout.items():
            if isinstance(item, QgsLayoutItemLegend):
                leg_name = item.displayName() if hasattr(item, 'displayName') and item.displayName() else "Legenda"
                label_info = f"Layout: '{layout.name()}' ➔ Oggetto: '{leg_name}' (ID: {item.id()})"
                legend_items_info.append((label_info, layout, item))

    if not legend_items_info:
        QMessageBox.warning(
            None,
            "Attenzione",
            "Nessun elemento legenda trovato in alcun layout di stampa del progetto.",
        )
        return

    # 5. Mostra la finestra di dialogo con l'elenco analitico delle legende
    dialog = DialogoSelezioneLegende(legend_items_info)
    if dialog.exec_() != QDialog.Accepted:
        return

    selected_legends = dialog.get_selected_legends()
    if not selected_legends:
        QMessageBox.warning(None, "Attenzione", "Non hai selezionato alcuna legenda.")
        return

    target_layer = layers_dict[target_layer_name]
    legende_modificate = 0

    # 6. Applica l'azione (aggiunta o rimozione) solo sulle legende spuntate
    for layout, item in selected_legends:
        model = item.model()
        root = model.rootGroup()

        layer_node = root.findLayer(target_layer.id())
        modificato = False

        if is_aggiunta:
            if not layer_node:
                layer_node = root.addLayer(target_layer)
            if layer_node:
                layer_node.setItemVisibilityChecked(True)
                modificato = True
        else:
            if layer_node:
                parent = layer_node.parent()
                if parent:
                    parent.removeChildNode(layer_node)
                    modificato = True

        if modificato:
            item.adjustBoxSize()
            item.update()
            layout.refresh()
            legende_modificate += 1

    verbo = "aggiunto a" if is_aggiunta else "rimosso da"
    messaggio = f"Operazione completata!\nLayer '{target_layer_name}' {verbo} {legende_modificate} legende selezionate."
    print(f"\n{messaggio}")
    QMessageBox.information(None, "Completato", messaggio)
