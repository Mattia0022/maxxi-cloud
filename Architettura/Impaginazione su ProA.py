import os
import shutil
import time
import re
from qgis.utils import iface
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QWidget, QTextEdit, QLabel, QApplication, QFileDialog
)
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject

# Importazione dei moduli per comunicare con ProA
try:
    import win32gui
    import win32con
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
except ImportError:
    shell = None

class ImpaginazioneProADialog(QDialog):
    def __init__(self, guida_testo="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Impaginazione Automatica su ProA")
        self.resize(1150, 600)

        self.init_ui(guida_testo)

    def init_ui(self, guida_testo):
        # Layout principale orizzontale a tre sezioni
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # =====================================================
        # 1. PANNELLO CONFIGURAZIONE CARTELLE (A SINISTRA)
        # =====================================================
        box_config = QGroupBox("1. Configurazione Cartelle e Parametri")
        lay_config = QVBoxLayout(box_config)
        lay_config.setSpacing(10)

        # Origine
        lay_orig = QVBoxLayout()
        lay_orig.addWidget(QLabel("Cartella Origine Immagini:"))
        h_orig = QHBoxLayout()
        self.txt_origine = QLineEdit()
        self.txt_origine.setPlaceholderText("Seleziona cartella origine...")
        btn_orig = QPushButton("Sfoglia...")
        btn_orig.clicked.connect(self.seleziona_origine)
        h_orig.addWidget(self.txt_origine)
        h_orig.addWidget(btn_orig)
        lay_orig.addLayout(h_orig)
        lay_config.addLayout(lay_orig)

        # Destinazione
        lay_dest = QVBoxLayout()
        lay_dest.addWidget(QLabel("Cartella Destinazione (Pulite):"))
        h_dest = QHBoxLayout()
        self.txt_destinazione = QLineEdit()
        self.txt_destinazione.setPlaceholderText("Seleziona cartella destinazione...")
        btn_dest = QPushButton("Sfoglia...")
        btn_dest.clicked.connect(self.seleziona_destinazione)
        h_dest.addWidget(self.txt_destinazione)
        h_dest.addWidget(btn_dest)
        lay_dest.addLayout(h_dest)
        lay_config.addLayout(lay_dest)

        # Scala CAD
        lay_scale = QVBoxLayout()
        lay_scale.addWidget(QLabel("Scala CAD (es. 1000):"))
        self.txt_scala = QLineEdit("1000")
        lay_scale.addWidget(self.txt_scala)
        lay_config.addLayout(lay_scale)

        lay_config.addStretch()
        main_layout.addWidget(box_config, 1)

        # =====================================================
        # 2. PANNELLO ANTEPRIMA E AZIONE (AL CENTRO)
        # =====================================================
        box_preview = QGroupBox("2. Anteprima File e Avvio Automazione")
        lay_preview = QVBoxLayout(box_preview)

        self.tabella_file = QTableWidget()
        self.tabella_file.setColumnCount(2)
        self.tabella_file.setHorizontalHeaderLabels(["File Originale", "Nuovo Nome (Anteprima)"])
        self.tabella_file.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabella_file.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabella_file.setSelectionBehavior(QAbstractItemView.SelectRows)
        lay_preview.addWidget(self.tabella_file)

        self.btn_avvia = QPushButton("🚀 Avvia Rinomina e Invio a ProA")
        self.btn_avvia.setStyleSheet("font-weight: bold; background-color: #e1f5fe; border-radius: 4px; padding: 10px; font-size: 13px;")
        self.btn_avvia.clicked.connect(self.esegui_processo)
        lay_preview.addWidget(self.btn_avvia)

        main_layout.addWidget(box_preview, 2)

        # =====================================================
        # 3. PANNELLO GUIDA PASSO-PASSO (A DESTRA)
        # =====================================================
        widget_guida = QWidget()
        widget_guida.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px;")
        layout_dx = QVBoxLayout(widget_guida)
        layout_dx.setContentsMargins(10, 10, 10, 10)

        lbl_titolo_guida = QLabel("📖 Guida Passo-Passo")
        lbl_titolo_guida.setStyleSheet("color: #0284c7; font-weight: bold; font-size: 13px; border: none; background: transparent; margin-bottom: 4px;")
        layout_dx.addWidget(lbl_titolo_guida)

        txt_guida = QTextEdit()
        txt_guida.setReadOnly(True)
        txt_guida.setHtml(f"<div style='color: #334155; font-size: 12px; line-height: 1.5;'>{guida_testo}</div>")
        txt_guida.setStyleSheet("border: none; background: transparent;")
        layout_dx.addWidget(txt_guida)

        main_layout.addWidget(widget_guida, stretch=1)

    # ----------------------------------------------------
    # UTILITIES PER LA SELEZIONE E L'ANTEPRIMA
    # ----------------------------------------------------
    def seleziona_origine(self):
        dir_path = QFileDialog.getExistingDirectory(iface.mainWindow(), "Seleziona la cartella di ORIGINE con le immagini")
        if dir_path:
            self.txt_origine.setText(dir_path)
            self.aggiorna_anteprima()

    def seleziona_destinazione(self):
        dir_path = QFileDialog.getExistingDirectory(iface.mainWindow(), "Seleziona la cartella di DESTINAZIONE")
        if dir_path:
            self.txt_destinazione.setText(dir_path)

    def aggiorna_anteprima(self):
        origine = self.txt_origine.text()
        if not origine or not os.path.exists(origine):
            return

        estensioni_valide = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff')
        try:
            files = sorted([f for f in os.listdir(origine) if f.lower().endswith(estensioni_valide)])
        except Exception:
            files = []

        self.tabella_file.setRowCount(len(files))
        contatore = 1
        for idx, filename in enumerate(files):
            stem, ext = os.path.splitext(filename)
            nuovo_nome_base = re.sub(r'^[a-zA-Z0-9]{1,3}[_\\.]\s*', '', stem)
            nuovo_nome_base = nuovo_nome_base.strip().capitalize()
            nuovo_nome = f"{contatore}. {nuovo_nome_base}{ext}"

            self.tabella_file.setItem(idx, 0, QTableWidgetItem(filename))
            self.tabella_file.setItem(idx, 1, QTableWidgetItem(nuovo_nome))
            contatore += 1

    # ----------------------------------------------------
    # ESECUZIONE DEL PROCESSO TRAMITE SCRIPT CAD (.scr)
    # ----------------------------------------------------
    def esegui_processo(self):
        origine = self.txt_origine.text()
        destinazione = self.txt_destinazione.text()
        scale_str = self.txt_scala.text().strip() or "1000"

        if not origine or not os.path.exists(origine):
            QMessageBox.warning(self, "Attenzione", "Seleziona una cartella di origine valida!")
            return

        if not destinazione:
            QMessageBox.warning(self, "Attenzione", "Seleziona una cartella di destinazione valida!")
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
                
                nuovo_nome_base = re.sub(r'^[a-zA-Z0-9]{1,3}[_\\.]\s*', '', stem)
                nuovo_nome_base = nuovo_nome_base.strip().capitalize()
                
                nuovo_nome = f"{contatore}. {nuovo_nome_base}{ext}"
                percorso_destinazione = os.path.join(destinazione, nuovo_nome)
                
                shutil.copy2(percorso_origine, percorso_destinazione)
                img_paths.append(percorso_destinazione)
                contatore += 1

        if not img_paths:
            QMessageBox.warning(self, "Attenzione", "Nessuna immagine valida trovata nella cartella di origine!")
            return

        if shell is None:
            QMessageBox.warning(self, "Attenzione", "Librerie win32 non disponibili. Copia e rinomina completate, ma l'automazione CAD richiede Windows.")
            self.accept()
            return

        # FASE 2: Generazione del file script CAD (.scr)
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

            # Scrittura dei comandi nel file di script .scr
            cmd_script = "FILEDIA 0\n_TILEMODE 0\n"

            # FASE A: Duplica il layout iniziale pulito per ogni immagine
            for img_path in img_paths:
                layout_name = os.path.splitext(os.path.basename(img_path))[0]
                cmd_script += (
                    "-LAYOUT\n"
                    "_CO\n"
                    "\n"
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

            # Salvataggio del file .scr nella cartella di destinazione
            scr_path = os.path.join(destinazione, "impaginazione_proa.scr")
            try:
                with open(scr_path, "w", encoding="utf-8") as f:
                    f.write(cmd_script)
            except Exception as e:
                QMessageBox.warning(self, "Errore", f"Impossibile creare il file script: {e}")
                return

            # Comando pulito da inviare a ProA per eseguire lo script in un sol colpo
            scr_path_clean = scr_path.replace("\\", "/")
            comando_lancio = f"_SCRIPT\n\"{scr_path_clean}\"\n"

            QApplication.clipboard().setText(comando_lancio)
            shell.SendKeys('{ESC}{ESC}')
            time.sleep(0.2)
            shell.SendKeys('^v')
            time.sleep(0.3)
            shell.SendKeys('{ENTER}')
            
            QMessageBox.information(self, "Successo", f"Rinominate {len(img_paths)} immagini e script avviato su ProA con successo!")
            self.accept()
        else:
            QMessageBox.warning(self, "Errore", "Non trovo ProA aperto sul desktop! Apri prima il file CAD in ProA.")

def run():
    guida_testo = """
    1. Seleziona la cartella di origine contenente le immagini grezze.<br><br>
    2. Scegli la cartella di destinazione in cui verranno salvate le immagini pulite e numerate in serie.<br><br>
    3. Verifica l'anteprima dei nuovi nomi nella tabella centrale, imposta la scala CAD e clicca su 'Avvia Rinomina e Invio a ProA' (assicurati di avere ProA aperto sul desktop).
    """
    dlg = ImpaginazioneProADialog(guida_testo, iface.mainWindow())
    dlg.show()
    iface.impaginazione_proa_dlg = dlg
