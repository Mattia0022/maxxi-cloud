# -*- coding: utf-8 -*-
from qgis.core import QgsProject, QgsLayoutItemLegend
from qgis.PyQt.QtWidgets import (QInputDialog, QMessageBox, QDialog, 
                                 QVBoxLayout, QLabel, QListWidget, 
                                 QListWidgetItem, QDialogButtonBox, QAbstractItemView)

class DialogoSelezioneLayout(QDialog):
    def __init__(self, layout_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selezione Layout - QGIS")
        self.resize(350, 400)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Seleziona i layout da aggiornare:\n(Tieni premuto CTRL o MAIUSC per sceglierne più di uno)"))
        
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        for name in layout_names:
            self.list_widget.addItem(QListWidgetItem(name))
        layout.addWidget(self.list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_selected(self):
        return [item.text() for item in self.list_widget.selectedItems()]


def aggiungi_layer_a_legende_manuali():
    project = QgsProject.instance()
    manager = project.layoutManager()
    
    # 1. Recupera i layer del progetto
    layers_dict = {layer.name(): layer for layer in project.mapLayers().values()}
    layer_names = sorted(list(layers_dict.keys()))
    
    if not layer_names:
        QMessageBox.warning(None, "Attenzione", "Nessun layer trovato nel progetto.")
        return

    # 2. Scelta del layer
    target_layer_name, ok = QInputDialog.getItem(
        None, "Aggiungi Layer a Legenda", "Seleziona il layer da aggiungere:", layer_names, 0, False
    )
    if not ok or not target_layer_name:
        return

    # 3. Selezione dei layout
    all_layouts = manager.printLayouts()
    layout_names_list = [l.name() for l in all_layouts]
    
    if not layout_names_list:
        QMessageBox.warning(None, "Attenzione", "Nessun layout di stampa trovato in questo progetto.")
        return

    dialog = DialogoSelezioneLayout(layout_names_list)
    if dialog.exec_() != QDialog.Accepted:
        return
        
    selected_layout_names = dialog.get_selected()
    if not selected_layout_names:
        QMessageBox.warning(None, "Attenzione", "Non hai selezionato alcun layout.")
        return

    target_layer = layers_dict[target_layer_name]
    layouts_modificati = 0
    
    # 4. Modifica mirata solo sui layout scelti
    for layout in all_layouts:
        if layout.name() in selected_layout_names:
            layout_modificato = False
            
            for item in layout.items():
                if isinstance(item, QgsLayoutItemLegend):
                    model = item.model()
                    root = model.rootGroup()
                    
                    # Controlla se il layer è già presente nella legenda
                    layer_node = root.findLayer(target_layer.id())
                    
                    if not layer_node:
                        # Lo aggiunge esattamente come faresti con il tasto '+'
                        layer_node = root.addLayer(target_layer)
                    
                    if layer_node:
                        # Assicura che sia spuntato e visibile
                        layer_node.setItemVisibilityChecked(True)
                        layout_modificato = True
                    
                    if layout_modificato:
                        # Ricalcola la dimensione del box e forza il rendering grafico immediato
                        item.adjustBoxSize()
                        item.update()
                        layout.refresh()
                        layouts_modificati += 1
                        
    messaggio = f"Operazione completata!\nLayer '{target_layer_name}' aggiunto e visualizzato correttamente in {layouts_modificati} layout."
    print(f"\n{messaggio}")
    QMessageBox.information(None, "Completato", messaggio)

aggiungi_layer_a_legende_manuali()
