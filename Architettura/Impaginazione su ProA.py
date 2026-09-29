import os
import shutil
import time
import re
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QApplication

# Importazione dei moduli per comunicare con ProA
try:
    import win32gui
    import win32con
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
except ImportError:
    shell = None

def rinomina_e_invia_a_proa():
    print("=== AVVIO: COPIA, RINOMINA E INVIO A PROA ===")
    
    # 1. Seleziona la cartella di ORIGINE
    origine = QFileDialog.getExistingDirectory(None, "Seleziona la cartella di ORIGINE con le immagini")
    if not origine:
        print("Operazione annullata.")
        return

    # 2. Seleziona la cartella di DESTINAZIONE
    destinazione = QFileDialog.getExistingDirectory(None, "Seleziona la cartella di DESTINAZIONE per le immagini pulite")
    if not destinazione:
        print("Operazione annullata.")
        return

    os.makedirs(destinazione, exist_ok=True)
    estensioni_valide = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff')

    files = sorted(os.listdir(origine))
    contatore = 1
    img_paths = []

    # FASE 1: Rinomina, numera e copia i file nella destinazione
    for filename in files:
        if filename.lower().endswith(estensioni_valide):
            percorso_origine = os.path.join(origine, filename)
            stem, ext = os.path.splitext(filename)
            
            # Rimuove il prefisso solo se si trova all'inizio ed è corto (es. "A0_", "B2.", max 3 caratteri)
            # Lascia intatte parole lunghe come "Inquadramento_piscina"
            nuovo_nome_base = re.sub(r'^[a-zA-Z0-9]{1,3}[_\\.]\s*', '', stem)
            
            # Converte la prima lettera in maiuscolo e pulisce gli spazi
            nuovo_nome_base = nuovo_nome_base.strip().capitalize()
            
            # Compone il nuovo nome (es. 1. Inquadramento.png)
            nuovo_nome = f"{contatore}. {nuovo_nome_base}{ext}"
            percorso_destinazione = os.path.join(destinazione, nuovo_nome)
            
            shutil.copy2(percorso_origine, percorso_destinazione)
            print(f"Copiato e rinominato: {filename} -> {nuovo_nome}")
            
            # Memorizza il percorso pulito per la fase CAD
            img_paths.append(percorso_destinazione)
            contatore += 1

    if not img_paths:
        QMessageBox.warning(None, "Attenzione", "Nessuna immagine valida trovata nella cartella di origine!")
        return

    # FASE 2: Automazione ProA
    def enum_windows_callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
        if "ProA" in title or "progeCAD" in title or "icad" in title.lower():
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

        # FASE A: Duplica il layout iniziale pulito per ogni immagine
        for img_path in img_paths:
            layout_name = os.path.splitext(os.path.basename(img_path))[0]
            cmd_script += (
                "-LAYOUT\n"
                "_CO\n"
                "\n"  # Copia il layout corrente pulito
                f"{layout_name}\n"
            )

        # FASE B: Entra nei singoli layout creati, inserisce la foto e la porta dietro
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
        
        print(f"\nFatto! Rinominate {len(img_paths)} immagini, salvate nella cartella e inviate a ProA con successo.")
    else:
        QMessageBox.warning(None, "Errore", "Non trovo ProA aperto sul desktop! Apri prima il file CAD in ProA.")

# Esegue lo script
rinomina_e_invia_a_proa()
