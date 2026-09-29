import os
import shutil
import time
import re
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QApplication

try:
    import win32gui
    import win32con
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
except ImportError:
    shell = None

def pulisci_nome(stem):
    # Rimuove prefissi brevi iniziali e formatta il nome
    nuovo = re.sub(r'^[a-zA-Z0-9]{1,3}[_\\.\-\s]+\s*', '', stem)
    return nuovo.strip().capitalize()

# 1. Seleziona più immagini contemporaneamente
file_paths, _ = QFileDialog.getOpenFileNames(
    None, "Seleziona le immagini da pulire e inviare", "", "Immagini (*.png *.jpg *.jpeg)"
)

if file_paths:
    # 2. Chiedi la cartella di destinazione per i file rinominati
    dest_dir = QFileDialog.getExistingDirectory(None, "Seleziona la cartella di destinazione per i file puliti")
    
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)
        img_paths = []
        
        # 3. Rinomina e copia i file nella destinazione
        for idx, file_path in enumerate(file_paths):
            dirname, filename = os.path.split(file_path)
            stem, ext = os.path.splitext(filename)
            
            nuovo_nome_base = pulisci_nome(stem)
            nuovo_nome = f"{idx + 1}. {nuovo_nome_base}{ext}"
            percorso_destinazione = os.path.join(dest_dir, nuovo_nome)
            
            shutil.copy2(file_path, percorso_destinazione)
            img_paths.append(percorso_destinazione)

        print(f"Rinominate e copiate {len(img_paths)} immagini in: {dest_dir}")

        if shell is None:
            QMessageBox.warning(None, "Attenzione", "Librerie win32 non disponibili. File rinominati ma impossibile inviare a ProA.")
        else:
            # 4. Cerca la finestra di ProA già aperta sul desktop
            def enum_windows_callback(hwnd, extra):
                title = win32gui.GetWindowText(hwnd)
                if title and win32gui.IsWindowVisible(hwnd):
                    if "ProA" in title or "progecad" in title or "icad" in title.lower():
                        extra.append(hwnd)

            top_windows = []
            win32gui.EnumWindows(enum_windows_callback, top_windows)

            if top_windows:
                hwnd = top_windows[0]
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                shell.SendKeys('%')
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.3)

                # Inizio blocco comandi globali
                cmd_script = "FILEDIA 0\n_TILEMODE 0\n"
                scale_str = "1000"  # Scala fissa

                # FASE 1: Duplica il layout iniziale pulito per ogni immagine
                for img_path in img_paths:
                    layout_name = os.path.splitext(os.path.basename(img_path))[0]
                    cmd_script += (
                        "-LAYOUT\n"
                        "_CO\n"
                        "\n"  # Copia il layout corrente pulito
                        f"{layout_name}\n"
                    )

                # FASE 2: Entra nei singoli layout creati, inserisce la foto e la porta dietro
                for img_path in img_paths:
                    img_path_clean = img_path.replace("\\", "/")
                    layout_name = os.path.splitext(os.path.basename(img_path))[0]
                    cmd_script += (
                        "-LAYOUT\n"
                        "_SET\n"
                        f"{layout_name}\n"
                        "-IMAGE\n"
                        "_ATTACH\n"
                        f'"{img_path_clean}"\n'
                        "0,0\n"
                        f"{scale_str}\n"
                        "0\n"
                        "_DRAWORDER\n"
                        "_L\n"
                        "\n"
                        "_BACK\n"
                    )

                cmd_script += "FILEDIA 1\n"

                # Incolla ed esegue l'intera sequenza di comandi in ProA
                QApplication.clipboard().setText(cmd_script)
                shell.SendKeys('{ESC}{ESC}')
                time.sleep(0.2)
                shell.SendKeys('^v')
                time.sleep(0.3)
                shell.SendKeys('{ENTER}')
                
                print(f"Creati {len(img_paths)} layout puliti e inserite le rispettive immagini senza sovrapposizioni!")
            else:
                QMessageBox.warning(None, "Errore", "Non trovo ProA aperto sul desktop! Apri prima il file CAD in ProA.")
