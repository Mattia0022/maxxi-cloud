def avvia_strumento(self, settore, nome):
        try:
            with urllib.request.urlopen(self.url_indice) as response:
                indice = json.loads(response.read().decode("utf-8"))
                url_script = indice.get(settore, {}).get(nome)
            
            if not url_script:
                QMessageBox.warning(self.iface.mainWindow(), "Errore", f"URL non trovato per lo strumento: {nome}")
                return
            
            with urllib.request.urlopen(url_script) as response:
                codice_sorgente = response.read().decode("utf-8")
                
                spazio_nomi = {"iface": self.iface}
                exec(codice_sorgente, spazio_nomi)
                
                # Esegue la funzione run() definita nello script remoto se presente
                if "run" in spazio_nomi:
                    spazio_nomi["run"]()
                else:
                    QMessageBox.warning(self.iface.mainWindow(), "Attenzione", f"Lo script '{nome}' non definisce una funzione run().")
                
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Errore di Esecuzione", f"Impossibile eseguire lo strumento dal cloud:\n{str(e)}")
