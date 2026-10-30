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
        self.resize(650, 380)
        self.setStyleSheet("font-size: 13pt;")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addWidget(QLabel("<b>Seleziona l'operazione da eseguire:</b>"))
        self.combo_azione = QComboBox()
        self.combo_azione.addItems([
            "Aggiungi layer alla legenda", 
            "Rimuovi layer dalla legenda"
        ])
        layout.addWidget(self.combo_azione)

        layout.addWidget(QLabel("<b>Seleziona il layer di riferimento:</b>"))
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


class DialogoSelezioneLayout(QDialog):
    def __init__(self, layout_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("1. Selezione Layout di Stampa - QGIS")
        self.resize(650, 500)
        self.setStyleSheet("font-size: 12pt;")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        layout.addWidget(
            QLabel("<b>Seleziona i layout di stampa da includere:</b><br>(Tieni premuto CTRL o MAIUSC per selezioni multiple)")
        )

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        for name in layout_names:
            self.list_widget.addItem(QListWidgetItem(name))
        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_layouts(self):
        return [item.text() for item in self.list_widget.selectedItems()]


class DialogoSelezioneLegende(QDialog):
    def __init__(self, legend_choices, parent=None):
        super().__init__(parent)
        self.setWindowTitle("2. Selezione Legenda da Modificare - QGIS")
        self.resize(650, 450)
        self.setStyleSheet("font-size: 12pt;")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        layout.addWidget(
            QLabel("<b>Seleziona il tipo di legenda da modificare nei layout scelti:</b><br>(Se più layout hanno lo stesso nome/ID di legenda, basterà selezionarlo una sola volta)")
        )

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        
        for desc_str, legend_key in legend_choices:
            item_widget = QListWidgetItem(desc_str)
            item_widget.setData(Qt.UserRole, legend_key)
            self.list_widget.addItem(item_widget)

        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_legend_keys(self):
        return [item.data(Qt.UserRole) for item in self.list_widget.selectedItems()]


def run():
    project = QgsProject.instance()
    manager = project.layoutManager()

    layers_dict = {layer.name(): layer for layer in project.mapLayers().values()}
    layer_names = sorted(list(layers_dict.keys()))

    if not layer_names:
        QMessageBox.warning(None, "Attenzione", "Nessun layer trovato nel progetto.")
        return

    # 1. Scelta operazione e layer (finestra grande)
    dialog_azione = DialogoAzioneELayer(layer_names)
    if dialog_azione.exec_() != QDialog.Accepted:
        return

    is_aggiunta, target_layer_name = dialog_azione.get_data()
    if not target_layer_name:
        return

    # 2. Scelta dei layout di stampa
    all_layouts = manager.printLayouts()
    layout_names_list = [l.name() for l in all_layouts]

    if not layout_names_list:
        QMessageBox.warning(None, "Attenzione", "Nessun layout di stampa trovato in questo progetto.")
        return

    dialog_layout = DialogoSelezioneLayout(layout_names_list)
    if dialog_layout.exec_() != QDialog.Accepted:
        return

    selected_layout_names = dialog_layout.get_selected_layouts()
    if not selected_layout_names:
        QMessageBox.warning(None, "Attenzione", "Non hai selezionato alcun layout.")
        return

    # 3. Raggruppa le legende per nome/ID univoco presenti SOLO nei layout selezionati
    # Mappa: chiave_legenda -> lista di coppie (layout, item_legenda)
    legend_groups = {}
    
    for layout in all_layouts:
        if layout.name() in selected_layout_names:
            for item in layout.items():
                if isinstance(item, QgsLayoutItemLegend):
                    leg_name = item.displayName() if hasattr(item, 'displayName') and item.displayName() else "Legenda"
                    leg_id = item.id() if item.id() else "Senza ID"
                    
                    # Chiave per unificare legende identiche
                    legend_key = (leg_name, leg_id)
                    desc_str = f"Oggetto Legenda: '{leg_name}' (ID: {leg_id})"
                    
                    if legend_key not in legend_groups:
                        legend_groups[legend_key] = {
                            "desc": desc_str,
                            "targets": []
                        }
                    legend_groups[legend_key]["targets"].append((layout, item))

    if not legend_groups:
        QMessageBox.warning(None, "Attenzione", "Nessuna legenda trovata nei layout selezionati.")
        return

    legend_choices = [(data["desc"], key) for key, data in legend_groups.items()]

    # 4. Finestra di scelta della legenda unificata
    dialog_legende = DialogoSelezioneLegende(legend_choices)
    if dialog_legende.exec_() != QDialog.Accepted:
        return

    selected_keys = dialog_legende.get_selected_legend_keys()
    if not selected_keys:
        QMessageBox.warning(None, "Attenzione", "Non hai selezionato alcuna legenda.")
        return

    target_layer = layers_dict[target_layer_name]
    legende_modificate = 0

    # 5. Applica le modifiche su tutte le legende corrispondenti nei layout scelti
    for key in selected_keys:
        targets = legend_groups[key]["targets"]
        for layout, item in targets:
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
    messaggio = f"Operazione completata!\nLayer '{target_layer_name}' {verbo} {legende_modificate} legende aggiornate."
    print(f"\n{messaggio}")
    QMessageBox.information(None, "Completato", messaggio)
