# -*- coding: utf-8 -*-
from qgis.core import QgsProject, QgsLayoutItemLegend
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QAbstractItemView,
)

class DialogoAzioneELayer(QDialog):
    def __init__(self, layer_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestione Layer Legenda - QGIS")
        self.resize(520, 320)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Seleziona l'operazione da eseguire:"))
        self.combo_azione = QComboBox()
        self.combo_azione.addItems([
            "Aggiungi layer alla legenda", 
            "Rimuovi layer dalla legenda"
        ])
        layout.addWidget(self.combo_azione)

        layout.addWidget(QLabel("Seleziona il layer di riferimento:"))
        self.combo_layer = QComboBox()
        self.combo_layer.addItems(layer_names)
        layout.addWidget(self.combo_layer)

        layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        azione = self.combo_azione.currentText()
        layer_name = self.combo_layer.currentText()
        is_aggiunta = "Aggiungi" in azione
        return is_aggiunta, layer_name


class DialogoSelezioneLegende(QDialog):
    def __init__(self, legend_items_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selezione Specifica Legende - QGIS")
        self.resize(550, 450)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        layout.addWidget(
            QLabel("Seleziona le singole legende da modificare:\n(Tieni premuto CTRL o MAIUSC per selezioni multiple)")
        )

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        
        for info_str, layout_obj, legend_item in legend_items_info:
            item_widget = QListWidgetItem(info_str)
            # Memorizza i dati direttamente nell'elemento tramite Qt.UserRole
            item_widget.setData(Qt.UserRole, (layout_obj, legend_item))
            self.list_widget.addItem(item_widget)

        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_legends(self):
        # Recupera i dati associati agli elementi selezionati
        return [item.data(Qt.UserRole) for item in self.list_widget.selectedItems()]


def run():
    project = QgsProject.instance()
    manager = project.layoutManager()

    layers_dict = {layer.name(): layer for layer in project.mapLayers().values()}
    layer_names = sorted(list(layers_dict.keys()))

    if not layer_names:
        QMessageBox.warning(None, "Attenzione", "Nessun layer trovato nel progetto.")
        return

    dialog_azione = DialogoAzioneELayer(layer_names)
    if dialog_azione.exec_() != QDialog.Accepted:
        return

    is_aggiunta, target_layer_name = dialog_azione.get_data()
    if not target_layer_name:
        return

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

    dialog_legende = DialogoSelezioneLegende(legend_items_info)
    if dialog_legende.exec_() != QDialog.Accepted:
        return

    selected_legends = dialog_legende.get_selected_legends()
    if not selected_legends:
        QMessageBox.warning(None, "Attenzione", "Non hai selezionato alcuna legenda.")
        return

    target_layer = layers_dict[target_layer_name]
    legende_modificate = 0

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
