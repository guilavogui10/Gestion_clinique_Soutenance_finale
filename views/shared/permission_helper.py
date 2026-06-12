"""
permission_helper.py
--------------------
Helper pour gérer les permissions et autorisations OTP dans les interfaces.
Fournit des méthodes réutilisables pour vérifier les permissions et demander des autorisations.
"""

from typing import Tuple, Optional, Callable
from PySide6.QtWidgets import QWidget
from views.shared.message_box import CustomMessageBox
from views.otp_autorisation_dialog import OTPAutorisationDialog


class PermissionHelper:
    """
    Helper pour gérer les permissions dans les interfaces.
    Fournit des méthodes pour vérifier et demander des autorisations.
    """
    
    def __init__(self, parent_widget: QWidget, permission_ctrl, user_info: dict):
        """
        Args:
            parent_widget: Widget parent pour afficher les dialogues
            permission_ctrl: Contrôleur de permissions
            user_info: Informations de l'utilisateur connecté
        """
        self.parent = parent_widget
        self.permission_ctrl = permission_ctrl
        self.user_info = user_info
        
        # Extraire les infos utilisateur
        self.code_utilisateur = user_info.get("code", "")
        self.role = user_info.get("role", "")
        self.est_responsable = bool(user_info.get("est_responsable", 0))
    
    def verifier_et_executer(
        self,
        action: str,
        contexte: str,
        callback_success: Callable,
        callback_cancel: Optional[Callable] = None
    ) -> bool:
        """
        Vérifie les permissions et exécute l'action si autorisée.
        Gère automatiquement les demandes d'autorisation OTP si nécessaire.
        
        Args:
            action: Type d'action (lecture, modification, suppression, consultation)
            contexte: Description du contexte (ex: "Chirurgie #CH001")
            callback_success: Fonction à appeler si l'action est autorisée
            callback_cancel: Fonction à appeler si l'action est annulée (optionnel)
        
        Returns:
            True si l'action a été exécutée, False sinon
        """
        # Vérifier la permission
        result = self.permission_ctrl.verifier_permission(
            self.code_utilisateur,
            self.role,
            self.est_responsable,
            action
        )
        
        if result["autorise"]:
            # Responsable → accès direct, pas de confirmation supplémentaire
            callback_success()
            return True
        else:
            # Action non autorisée
            message = result["message"]
            
            # Proposer de demander l'autorisation
            reponse = CustomMessageBox.confirm(
                self.parent,
                "Autorisation requise",
                f"{message}\n\nVoulez-vous demander l'autorisation au responsable ?"
            )
            
            if reponse:
                return self._demander_autorisation_responsable(action, contexte, callback_success, callback_cancel)
            else:
                if callback_cancel:
                    callback_cancel()
                return False
    
    def _demander_confirmation_otp(
        self,
        action: str,
        contexte: str,
        callback_success: Callable,
        callback_cancel: Optional[Callable] = None
    ) -> bool:
        """
        Demande une confirmation OTP à l'utilisateur lui-même (responsable).
        Utilisé pour les actions sensibles comme la consultation de résultats.
        """
        # Demander l'envoi du code OTP
        result = self.permission_ctrl.demander_autorisation(
            self.code_utilisateur,
            self.role,
            action,
            contexte,
            est_responsable=self.est_responsable
        )
        
        if result["status"] != "success":
            CustomMessageBox.error(
                self.parent,
                "Erreur",
                result["message"]
            )
            if callback_cancel:
                callback_cancel()
            return False
        
        # Afficher le dialogue OTP
        email_masque = result.get("email_masque", "votre adresse")
        dialog = OTPAutorisationDialog(
            action=action,
            contexte=contexte,
            masked_email=email_masque,
            est_pour_soi=True,
            parent=self.parent
        )
        
        # Connecter le signal de renvoi
        dialog.resend_requested.connect(
            lambda: self._renvoyer_code_autorisation(action, contexte)
        )
        
        if dialog.exec() != OTPAutorisationDialog.Accepted:
            CustomMessageBox.info(
                self.parent,
                "Action annulée",
                "La confirmation a été annulée."
            )
            if callback_cancel:
                callback_cancel()
            return False
        
        # Valider le code OTP
        code_saisi = dialog.get_otp_code()
        validation = self.permission_ctrl.valider_autorisation(
            self.code_utilisateur,
            action,
            contexte,
            code_saisi
        )
        
        if validation["status"] == "success":
            # Code valide, exécuter l'action
            callback_success()
            return True
        else:
            CustomMessageBox.error(
                self.parent,
                "Code invalide",
                validation["message"]
            )
            if callback_cancel:
                callback_cancel()
            return False
    
    def _demander_autorisation_responsable(
        self,
        action: str,
        contexte: str,
        callback_success: Callable,
        callback_cancel: Optional[Callable] = None
    ) -> bool:
        """
        Demande l'autorisation au responsable du service.
        Envoie un code OTP au responsable et demande à l'utilisateur de le saisir.
        """
        # Demander l'envoi du code OTP au responsable
        result = self.permission_ctrl.demander_autorisation(
            self.code_utilisateur,
            self.role,
            action,
            contexte,
            est_responsable=self.est_responsable
        )
        
        if result["status"] != "success":
            CustomMessageBox.error(
                self.parent,
                "Erreur",
                result["message"]
            )
            if callback_cancel:
                callback_cancel()
            return False
        
        # Afficher le dialogue OTP
        email_masque = result.get("email_masque", "le responsable")
        dialog = OTPAutorisationDialog(
            action=action,
            contexte=contexte,
            masked_email=email_masque,
            est_pour_soi=False,
            parent=self.parent
        )
        
        if dialog.exec() != OTPAutorisationDialog.Accepted:
            CustomMessageBox.info(
                self.parent,
                "Action annulée",
                "La demande d'autorisation a été annulée."
            )
            if callback_cancel:
                callback_cancel()
            return False
        
        # Valider le code OTP
        code_saisi = dialog.get_otp_code()
        validation = self.permission_ctrl.valider_autorisation(
            self.code_utilisateur,
            action,
            contexte,
            code_saisi
        )
        
        if validation["status"] == "success":
            # Code valide, exécuter l'action
            CustomMessageBox.success(
                self.parent,
                "Autorisation accordée",
                "Le responsable a autorisé cette action."
            )
            callback_success()
            return True
        else:
            CustomMessageBox.error(
                self.parent,
                "Code invalide",
                validation["message"]
            )
            if callback_cancel:
                callback_cancel()
            return False
    
    def _renvoyer_code_autorisation(self, action: str, contexte: str):
        """Renvoie un nouveau code d'autorisation"""
        result = self.permission_ctrl.demander_autorisation(
            self.code_utilisateur,
            self.role,
            action,
            contexte,
            est_responsable=self.est_responsable
        )
        
        if result["status"] == "success":
            CustomMessageBox.info(
                self.parent,
                "Code renvoyé",
                "Un nouveau code d'autorisation a été envoyé."
            )
        else:
            CustomMessageBox.error(
                self.parent,
                "Erreur",
                result["message"]
            )
    
    def peut_creer(self) -> bool:
        """Vérifie si l'utilisateur peut créer des enregistrements"""
        return self.est_responsable or self.role in ["Directeur Général", "Administrateur"]
    
    def peut_modifier(self) -> bool:
        """Vérifie si l'utilisateur peut modifier des enregistrements"""
        return self.est_responsable or self.role in ["Directeur Général", "Administrateur"]
    
    def peut_supprimer(self) -> bool:
        """Vérifie si l'utilisateur peut supprimer des enregistrements (nécessite toujours autorisation DG)"""
        return self.role in ["Directeur Général", "Administrateur"]
    
    def peut_consulter_resultats(self) -> bool:
        """Vérifie si l'utilisateur peut consulter les résultats (nécessite toujours OTP)"""
        return self.est_responsable or self.role in ["Directeur Général", "Administrateur"]
