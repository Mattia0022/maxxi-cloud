import os
import re
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox

# Selezione cartella
cartella = QFileDialog.getExistingDirectory(
    None,
    "Seleziona la cartella"
)

if cartella:

    files = sorted([
        f for f in os.listdir(cartella)
        if os.path.isfile(os.path.join(cartella, f))
    ])

    rinominati = 0

    for file in files:

        nome, estensione = os.path.splitext(file)

        # Cerca il numero finale nel nome file
        match = re.search(r'(\d+)$', nome)

        if match:

            numero = match.group(1)

            if len(numero) >= 2:

                piano = numero[:-1]
                pagina = numero[-1]

                nuovo_nome = f"Pag{piano}_{pagina}{estensione}"

                vecchio = os.path.join(cartella, file)
                nuovo = os.path.join(cartella, nuovo_nome)

                os.rename(vecchio, nuovo)

                rinominati += 1

    QMessageBox.information(
        None,
        "Operazione completata",
        f"Rinominati {rinominati} file."
    )
