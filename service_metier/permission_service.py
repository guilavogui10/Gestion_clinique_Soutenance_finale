"""
permission_service.py
---------------------
Service métier pour la gestion des permissions et droits d'accès.

Gère :
- Vérification des droits selon le rôle (fonction) et le statut responsable
- Génération et validation OTP pour actions non autorisées
- Envoi des codes OTP au responsable du service ou DG
"""

import logging
from typing import Dict, Tuple, Optional, List

from core.vault_service import VaultService
from data.dao_personnel import PersonnelDAO
from data.dao_audit_permission import AuditPermissionDAO
from data.dao_otp_tentatives import OTPTentativesDAO


class PermissionService:
    """
    Service de gestion des permissions et autorisations.
    """
    
    # Définition des actions possibles
    ACTION_LECTURE = "lecture"
    ACTION_IMPRESSION = "impression"
    ACTION_MODIFICATION = "modification"
    ACTION_SUPPRESSION = "suppression"
    ACTION_CONSULTATION = "consultation"
    ACTION_CREATION = "creation"
    
    # Rôles spéciaux
    ROLE_DG = "Directeur Général"
    
    # Mapping rôle (normalisé) -> interfaces autorisées
    ROLE_INTERFACES = {
        "medecin": [
            "Consultation", "Consultations",
            "Prescription", "Prescriptions",
            "Rendez-vous", "Rendezvous",
            "Resultat", "Résultats", "Resultats",
            "Acte medical", "Actes",
            "Accueil", "Parametre", "Paramètres",
        ],
        "chirurgien": [
            "Chirurgie", "Chirurgies",
            "Rendez-vous", "Rendezvous",
            "Acte medical", "Actes",
            "Resultat", "Résultats", "Resultats",
            "Accueil", "Parametre", "Paramètres",
        ],
        "laborantin": [
            "Examen", "Examens", "examen", "examens",
            "Rendez-vous", "Rendezvous",
            "Acte medical", "Actes",
            "Resultat", "Résultats", "Resultats",
            "Accueil", "Parametre", "Paramètres",
        ],
        "caissier": [
            "Patient", "Patients",
            "Visite", "Visites",
            "Fournisseur", "Fournisseurs",
            "Facturation", "Pharmacie",
            "Rendez-vous", "Rendezvous",
            "Parametre", "Paramètres", "Accueil",
        ],
        # Autres rôles conservés pour ne pas casser l'application :
        "infirmiere": ["Soins", "Examens", "Patients", "Rendez-vous"],
        "ingenieur": ["Maintenance", "Équipements", "Inventaire"],
        "ingenieur_informaticien": ["Système", "Utilisateurs", "Sécurité", "Base de données"],
        "opticien": ["Lunettes", "Optique"],
        "pharmacien": ["Pharmacie", "Prescriptions", "Médicaments"],
        "receptionniste": ["Rendez-vous", "Patients", "Accueil"],
        "secretaire": ["Rendez-vous", "Patients", "Facturation", "Documents"],
    }
    
    def _normaliser_role(self, role: str) -> str:
        """Normalise le rôle en retirant les accents, la casse et en groupant les synonymes."""
        if not role:
            return ""
        import unicodedata
        r = unicodedata.normalize('NFD', role).encode('ascii', 'ignore').decode('utf-8').lower().strip()
        
        if r in ["medecin", "Medecin","Médécin","Médecin"]: return "medecin"
        if r in ["chirurgien", "chirurgienne","Chirurgien","Chirurgienne"]: return "chirurgien"
        if r in ["laborantin", "Laborantin"]: return "laborantin"
        if r in ["caissier", "caissiere", "comptable","Caissière","caissière"]: return "caissier"
        if r in ["directeur general", "dg", "DG", "Directeur Général"]: return "directeur_general"
        if r in ["infirmiere", "infirmier"]: return "infirmiere"
        if r in ["ingenieur informaticien", "informaticien"]: return "ingenieur_informaticien"
        return r

    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vault = VaultService()
        self.personnel_dao = PersonnelDAO()
        
        # Fonctionnalités activées (tables créées)
        try:
            self.audit_dao = AuditPermissionDAO()
            self.tentatives_dao = OTPTentativesDAO()
            self.logger.info("Audit et limitation des tentatives activés")
        except Exception as e:
            self.logger.error(f"Erreur initialisation audit/tentatives: {e}")
            self.audit_dao = None
            self.tentatives_dao = None
    
    # =========================================================================
    # VÉRIFICATION DES PERMISSIONS
    # =========================================================================
    
    def verifier_permission(
        self, 
        code_utilisateur: str,
        role: str,
        est_responsable: bool,
        action: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si un utilisateur a la permission d'effectuer une action.
        
        Args:
            code_utilisateur: Code de l'utilisateur
            role: Rôle/fonction de l'utilisateur
            est_responsable: True si l'utilisateur est responsable
            action: Action à vérifier (lecture, modification, suppression, etc.)
        
        Returns:
            Tuple (autorisé, message):
                - (True, None) si autorisé
                - (False, "message") si refusé avec raison
        """
        role_norm = self._normaliser_role(role)
        
        # DG a tous les droits
        if role_norm == "directeur_general":
            return True, None
        
        # Lecture et impression : autorisés pour tous
        if action in [self.ACTION_LECTURE, self.ACTION_IMPRESSION]:
            return True, None
        
        # Consultation : autorisée pour les responsables uniquement
        if action == self.ACTION_CONSULTATION:
            if est_responsable:
                return True, None
            return False, "Seuls les responsables peuvent consulter les résultats détaillés."
        
        # Création : autorisée pour les responsables uniquement
        if action == self.ACTION_CREATION:
            if est_responsable:
                return True, None
            return False, "Seuls les responsables peuvent créer de nouvelles entrées."
        
        # Modification : autorisée pour les responsables uniquement
        if action == self.ACTION_MODIFICATION:
            if est_responsable:
                return True, None
            return False, "Seuls les responsables peuvent modifier les données."
        
        # Suppression : nécessite validation du DG
        if action == self.ACTION_SUPPRESSION:
            return False, "La suppression nécessite l'approbation du Directeur Général."
        
        # Action inconnue
        return False, f"Action '{action}' non reconnue."
    
    def peut_effectuer_action(
        self,
        code_utilisateur: str,
        role: str,
        est_responsable: bool,
        action: str
    ) -> bool:
        """
        Vérifie rapidement si une action est autorisée (sans message).
        
        Returns:
            True si autorisé, False sinon
        """
        autorise, _ = self.verifier_permission(
            code_utilisateur, role, est_responsable, action
        )
        return autorise
    
    # =========================================================================
    # VÉRIFICATION D'ACCÈS AUX INTERFACES
    # =========================================================================
    
    def peut_acceder_interface(self, role: str, interface: str) -> bool:
        """
        Vérifie si un rôle peut accéder à une interface donnée.
        
        Args:
            role: Rôle/fonction de l'utilisateur
            interface: Nom de l'interface (ex: "Examens", "Consultations")
        
        Returns:
            True si accès autorisé, False sinon
        """
        role_norm = self._normaliser_role(role)
            
        # DG a accès à tout
        if role_norm == "directeur_general":
            return True
        
        # Vérifier dans le mapping avec le rôle normalisé
        interfaces_autorisees = self.ROLE_INTERFACES.get(role_norm, [])
        
        # On peut aussi normaliser l'interface pour être plus tolérant, 
        # mais on va d'abord chercher l'interface exacte, puis faire une recherche insensible à la casse
        if interface in interfaces_autorisees:
            return True
            
        interface_lower = interface.lower()
        for itf in interfaces_autorisees:
            if itf.lower() == interface_lower:
                return True
                
        return False
    
    # =========================================================================
    # GESTION OTP POUR ACTIONS NON AUTORISÉES
    # =========================================================================
    
    def demander_autorisation_otp(
        self,
        code_utilisateur: str,
        role: str,
        action: str,
        contexte: str = "",
        est_responsable: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Génère un code OTP et l'envoie au responsable pour autoriser une action.
        
        Args:
            code_utilisateur: Code de l'utilisateur demandeur
            role: Rôle/fonction de l'utilisateur
            action: Action demandée (modification, suppression)
            contexte: Description du contexte (ex: "Modification examen #123")
            est_responsable: True si l'utilisateur est responsable
        
        Returns:
            Tuple (succès, message, email_masqué):
                - (True, "message", "e***@***.com") si OTP envoyé
                - (False, "erreur", None) si échec
        """
        try:
            role_norm = self._normaliser_role(role)
            
            # 1. Vérification d'accès direct (Bypass OTP si l'utilisateur est déjà autorisé)
            if role_norm == "directeur_general":
                return True, "Accès direct accordé (Directeur Général).", None
                
            if est_responsable and action in [self.ACTION_CONSULTATION, self.ACTION_MODIFICATION, self.ACTION_CREATION]:
                return True, "Accès direct accordé (Responsable de service).", None
            
            # 2. Déterminer le destinataire (le valideur) selon l'action et le rôle
            if action == self.ACTION_SUPPRESSION:
                # Suppression : toujours envoyer au DG
                destinataire = self._obtenir_responsable(self.ROLE_DG)
                if not destinataire:
                    return False, "Impossible de contacter le Directeur Général.", None
            else:
                # Autres actions : envoyer au responsable du service du demandeur
                destinataire = self._obtenir_responsable(role)
                if not destinataire:
                    return False, f"Aucun responsable trouvé pour le service '{role}'.", None
            
            # Vérifier que Vault est connecté
            if not self.vault.est_connecte():
                return False, "Service d'authentification indisponible.", None
            
            # Créer une clé TOTP unique pour cette demande (nettoyer les caractères spéciaux)
            identifiant_otp = self._nettoyer_identifiant(f"{code_utilisateur}_{action}_{contexte}")
            
            # Vérifier si l'OTP n'est pas bloqué
            if self.tentatives_dao:
                if self.tentatives_dao.est_bloque(identifiant_otp):
                    info = self.tentatives_dao.obtenir_info_tentative(identifiant_otp)
                    minutes_restantes = info.get('minutes_restantes_blocage', 0) if info else 0
                    return False, f"Trop de tentatives échouées. Réessayez dans {minutes_restantes} minutes.", None
                
                # Créer ou obtenir l'enregistrement de tentative
                self.tentatives_dao.creer_ou_obtenir_tentative(code_utilisateur, identifiant_otp)
            
            if not self.vault.creer_cle_totp(identifiant_otp):
                return False, "Impossible de générer le code d'autorisation.", None
            
            # Générer le code OTP
            code_otp = self.vault.generer_code_otp(identifiant_otp)
            if not code_otp:
                return False, "Impossible de générer le code d'autorisation.", None
            
            # Envoyer par email au responsable
            email = destinataire["mail"]
            prenom = destinataire["prenom"]
            code_autorisateur = destinataire["code"]
            
            # Personnaliser le message selon l'action
            if action == self.ACTION_SUPPRESSION:
                sujet = "Demande d'autorisation de suppression"
                message_action = f"Une demande de suppression a été effectuée.\n\nContexte : {contexte}"
            elif action == self.ACTION_CONSULTATION:
                sujet = "Demande d'autorisation de consultation"
                message_action = f"Un membre de votre équipe souhaite consulter des résultats médicaux et a besoin de votre autorisation.\n\nContexte : {contexte}"
            else:
                sujet = "Demande d'autorisation de modification"
                message_action = f"Une demande de modification a été effectuée.\n\nContexte : {contexte}"
            
            # Envoyer l'email avec le code OTP
            if not self._envoyer_email_autorisation(
                email, code_otp, prenom, message_action
            ):
                return False, "Impossible d'envoyer le code par email.", None
            
            # Enregistrer dans l'audit
            if self.audit_dao:
                self.audit_dao.creer_demande(
                    code_demandeur=code_utilisateur,
                    role_demandeur=role,
                    est_responsable=est_responsable,
                    action=action,
                    contexte=contexte,
                    code_autorisateur=code_autorisateur,
                    email_destinataire=email,
                    code_otp_envoye=code_otp
                )
            
            # Masquer l'email
            email_masque = self._masquer_email(email)
            
            message = f"Un code d'autorisation a été envoyé à {email_masque}."
            return True, message, email_masque
            
        except Exception as e:
            self.logger.error(f"Erreur demander_autorisation_otp: {e}")
            return False, "Erreur lors de la génération du code d'autorisation.", None
    
    def valider_autorisation_otp(
        self,
        code_utilisateur: str,
        action: str,
        contexte: str,
        code_saisi: str
    ) -> Tuple[bool, str]:
        """
        Valide le code OTP saisi pour autoriser une action.
        
        Args:
            code_utilisateur: Code de l'utilisateur demandeur
            action: Action demandée
            contexte: Contexte de la demande
            code_saisi: Code OTP saisi par l'utilisateur
        
        Returns:
            Tuple (valide, message):
                - (True, "Action autorisée") si code valide
                - (False, "Code invalide") si code incorrect
        """
        try:
            identifiant_otp = self._nettoyer_identifiant(f"{code_utilisateur}_{action}_{contexte}")
            
            # Vérifier si bloqué
            if self.tentatives_dao:
                if self.tentatives_dao.est_bloque(identifiant_otp):
                    info = self.tentatives_dao.obtenir_info_tentative(identifiant_otp)
                    minutes_restantes = info.get('minutes_restantes_blocage', 0) if info else 0
                    return False, f"Compte bloqué. Réessayez dans {minutes_restantes} minutes."
                
                # Incrémenter le compteur de tentatives
                self.tentatives_dao.incrementer_tentative(identifiant_otp, est_echec=False)
            
            # Vérifier le code via Vault
            if self.vault.verifier_code_otp(identifiant_otp, code_saisi):
                # Code valide - Nettoyer
                if self.tentatives_dao:
                    self.tentatives_dao.supprimer_tentative(identifiant_otp)
                
                self.vault.supprimer_cle_totp(identifiant_otp)
                
                # Mettre à jour l'audit
                if self.audit_dao:
                    self.audit_dao.mettre_a_jour_statut(
                        identifiant_otp=identifiant_otp,
                        statut='autorise'
                    )
                
                return True, "Action autorisée par le responsable."
            else:
                # Code invalide - Incrémenter les échecs
                if self.tentatives_dao:
                    self.tentatives_dao.incrementer_tentative(identifiant_otp, est_echec=True)
                    
                    # Vérifier le nombre de tentatives restantes
                    info = self.tentatives_dao.obtenir_info_tentative(identifiant_otp)
                    if info:
                        nb_echecs = info.get('nb_echecs', 0)
                        tentatives_restantes = self.tentatives_dao.MAX_TENTATIVES - nb_echecs
                        
                        if tentatives_restantes > 0:
                            return False, f"Code invalide. {tentatives_restantes} tentative(s) restante(s)."
                        else:
                            # Mettre à jour l'audit comme refusé
                            if self.audit_dao:
                                self.audit_dao.mettre_a_jour_statut(
                                    identifiant_otp=identifiant_otp,
                                    statut='refuse'
                                )
                            return False, f"Trop de tentatives. Compte bloqué pour {self.tentatives_dao.DUREE_BLOCAGE_MINUTES} minutes."
                
                return False, "Code d'autorisation invalide ou expiré."
                
        except Exception as e:
            self.logger.error(f"Erreur valider_autorisation_otp: {e}")
            return False, "Erreur lors de la validation du code."
    
    def refuser_autorisation(
        self,
        code_utilisateur: str,
        action: str,
        contexte: str,
        code_autorisateur: str,
        raison: str = "Refusé par le responsable"
    ) -> Tuple[bool, str]:
        """
        Permet au responsable de refuser explicitement une demande d'autorisation.
        
        Args:
            code_utilisateur: Code de l'utilisateur demandeur
            action: Action demandée
            contexte: Contexte de la demande
            code_autorisateur: Code du responsable qui refuse
            raison: Raison du refus
        
        Returns:
            Tuple (succès, message)
        """
        if not self.audit_dao:
            return False, "Fonctionnalité d'audit non disponible."
        
        try:
            identifiant_otp = self._nettoyer_identifiant(f"{code_utilisateur}_{action}_{contexte}")
            
            # Mettre à jour l'audit
            self.audit_dao.mettre_a_jour_statut(
                identifiant_otp=identifiant_otp,
                statut='refuse',
                code_autorisateur=code_autorisateur
            )
            
            # Nettoyer les tentatives et la clé TOTP
            if self.tentatives_dao:
                self.tentatives_dao.supprimer_tentative(identifiant_otp)
            
            self.vault.supprimer_cle_totp(identifiant_otp)
            
            return True, f"Demande refusée. Raison : {raison}"
            
        except Exception as e:
            self.logger.error(f"Erreur refuser_autorisation: {e}")
            return False, "Erreur lors du refus de l'autorisation."
    
    def obtenir_demandes_en_attente(self, code_autorisateur: str) -> List[Dict]:
        """
        Récupère toutes les demandes en attente pour un autorisateur.
        
        Args:
            code_autorisateur: Code du responsable/DG
        
        Returns:
            Liste des demandes en attente
        """
        if not self.audit_dao:
            return []
        
        try:
            return self.audit_dao.obtenir_demandes_en_attente(code_autorisateur)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_demandes_en_attente: {e}")
            return []
    
    def obtenir_historique_utilisateur(
        self,
        code_utilisateur: str,
        limite: int = 50
    ) -> List[Dict]:
        """
        Récupère l'historique des demandes d'un utilisateur.
        
        Args:
            code_utilisateur: Code de l'utilisateur
            limite: Nombre maximum de résultats
        
        Returns:
            Liste des demandes
        """
        if not self.audit_dao:
            return []
        
        try:
            return self.audit_dao.obtenir_historique_utilisateur(code_utilisateur, limite)
        except Exception as e:
            self.logger.error(f"Erreur obtenir_historique_utilisateur: {e}")
            return []
    
    # =========================================================================
    # MÉTHODES UTILITAIRES
    # =========================================================================
    
    def _obtenir_responsable(self, fonction: str) -> Optional[Dict]:
        """
        Récupère les informations du responsable d'un service.
        
        Args:
            fonction: Fonction/rôle du service
        
        Returns:
            Dict avec code, nom, prenom, mail ou None
        """
        try:
            # Normaliser la fonction en minuscule pour la recherche
            fonction_normalized = fonction.lower() if fonction else ""
            
            # Essayer d'abord avec la fonction exacte
            responsable = self.personnel_dao.get_responsable(fonction_normalized)
            
            # Si pas trouvé, essayer avec les variantes (masculin/féminin)
            if not responsable:
                variantes = self._get_variantes_fonction(fonction_normalized)
                for variante in variantes:
                    responsable = self.personnel_dao.get_responsable(variante)
                    if responsable:
                        break
            
            return responsable
        except Exception as e:
            self.logger.error(f"Erreur _obtenir_responsable({fonction}): {e}")
            return None
    
    def _nettoyer_identifiant(self, identifiant: str) -> str:
        """
        Nettoie un identifiant pour Vault (supprime espaces, accents, caractères spéciaux).
        
        Args:
            identifiant: Identifiant brut
        
        Returns:
            Identifiant nettoyé (alphanumérique + underscore)
        """
        import re
        import unicodedata
        
        # Normaliser les accents
        identifiant = unicodedata.normalize('NFKD', identifiant)
        identifiant = identifiant.encode('ascii', 'ignore').decode('ascii')
        
        # Remplacer espaces et tirets par underscore
        identifiant = identifiant.replace(' ', '_').replace('-', '_')
        
        # Garder uniquement alphanumérique et underscore
        identifiant = re.sub(r'[^a-zA-Z0-9_]', '', identifiant)
        
        return identifiant
    
    def _get_variantes_fonction(self, fonction: str) -> List[str]:
        """
        Retourne les variantes masculin/féminin d'une fonction.
        
        Args:
            fonction: Fonction normalisée en minuscule
        
        Returns:
            Liste des variantes possibles
        """
        variantes_map = {
            "chirurgien": ["chirurgienne"],
            "chirurgienne": ["chirurgien"],
            "infirmier": ["infirmière", "infimiere"],
            "infirmière": ["infirmier"],
            "infimiere": ["infirmier"],
            "pharmacien": ["pharmacienne"],
            "pharmacienne": ["pharmacien"],
        }
        return variantes_map.get(fonction, [])
    
    def _masquer_email(self, email: str) -> str:
        """
        Masque partiellement un email pour l'affichage.
        
        Exemple: john.doe@example.com -> j***@e***.com
        """
        if not email or "@" not in email:
            return "***@***.***"
        
        local, domaine = email.split("@", 1)
        
        # Masquer la partie locale
        if len(local) <= 2:
            local_masque = local[0] + "***"
        else:
            local_masque = local[0] + "***" + local[-1]
        
        # Masquer le domaine
        if "." in domaine:
            nom_domaine, extension = domaine.rsplit(".", 1)
            if len(nom_domaine) <= 2:
                domaine_masque = nom_domaine[0] + "***." + extension
            else:
                domaine_masque = nom_domaine[0] + "***." + extension
        else:
            domaine_masque = domaine[0] + "***"
        
        return f"{local_masque}@{domaine_masque}"
    
    def _envoyer_email_autorisation(
        self,
        destinataire: str,
        code_otp: str,
        prenom: str,
        message_action: str
    ) -> bool:
        """
        Envoie un email d'autorisation avec le code OTP.
        
        Args:
            destinataire: Email du responsable
            code_otp: Code OTP à 6 chiffres
            prenom: Prénom du responsable
            message_action: Description de l'action demandée
        
        Returns:
            True si envoyé, False sinon
        """
        try:
            # Utiliser la méthode d'envoi de Vault
            # On va personnaliser le message
            salutation = f"Bonjour {prenom.strip()}," if prenom.strip() else "Bonjour,"
            
            corps = (
                f"{salutation}\n\n"
                f"{message_action}\n\n"
                "Un membre de votre équipe demande une autorisation pour effectuer cette action.\n\n"
                "Votre code d'autorisation est :\n\n"
                f"        {code_otp}\n\n"
                "Ce code est valable 5 minutes. Ne le communiquez qu'à la personne concernée.\n\n"
                "Si vous n'êtes pas à l'origine de cette demande, "
                "veuillez contacter l'administrateur immédiatement.\n\n"
                "Cordialement,\n"
                "Le système de gestion de la clinique"
            )
            
            # Utiliser directement la méthode d'envoi SMTP du VaultService
            import os
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            
            email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
            email_port = int(os.getenv("EMAIL_PORT", 587))
            email_user = os.getenv("EMAIL_USER", "")
            email_pass = os.getenv("EMAIL_PASS", "")
            
            if not email_user or not email_pass:
                raise ValueError("Configuration EMAIL_USER/EMAIL_PASS manquante")
            
            msg = MIMEMultipart()
            msg["From"] = email_user
            msg["To"] = destinataire
            msg["Subject"] = "Code d'autorisation - Action sécurisée"
            msg.attach(MIMEText(corps, "plain", "utf-8"))
            
            with smtplib.SMTP(email_host, email_port) as serveur:
                serveur.ehlo()
                serveur.starttls()
                serveur.login(email_user, email_pass)
                serveur.sendmail(email_user, destinataire, msg.as_string())
            
            self.logger.info(f"Email d'autorisation envoyé à {destinataire}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur _envoyer_email_autorisation: {e}")
            return False

