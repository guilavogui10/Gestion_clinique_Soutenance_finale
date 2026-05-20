    def _open_url(self, id_resultat):
        if not id_resultat:
            return
        
        # Vérifier les permissions pour ouvrir le fichier
        if not self.permission_helper:
            self._execute_open_url(id_resultat)
            return
        
        def ouvrir_fichier():
            self._execute_open_url(id_resultat)
        
        self.permission_helper.verifier_et_executer(
            action=self.permission_ctrl.ACTION_CONSULTATION,
            contexte=f"Ouverture fichier résultat {id_resultat}",
            callback_success=ouvrir_fichier
        )
    
    def _execute_open_url(self, id_resultat):
        try:
            integrite_ok, message_integrite = self.ctrl.verifier_integrite_resultat(id_resultat)
            if not integrite_ok:
                CustomMessageBox.warning(self, "Fichier bloque", message_integrite)
                return
            url = self.ctrl.get_url_temporaire(id_resultat, 60)
            if url:
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl(url))
            else:
                CustomMessageBox.warning(self, "URL introuvable", "Impossible de générer l'URL.\nVérifiez que le serveur MinIO est démarré.")
        except Exception as e:
            CustomMessageBox.warning(self, "Erreur", str(e))
