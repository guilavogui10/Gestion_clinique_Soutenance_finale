"""
Widget Prescription Produit.
Architecture : MVC + Composition + Separation of Concerns.
ResponsabilitÃ© : Orchestration des composants et gestion du workflow.

Flux principal :
  1. charger_donnees(session) â†’ remplit combo_patient (visites 'Attente pharmacie')
                              â†’ remplit combo_produit
  2. SÃ©lection patient  â†’ _on_patient_change() â†’ carte patient + activation formulaire
  3. SÃ©lection produit  â†’ _on_produit_change() â†’ auto-remplissage dÃ©signation + prix
  4. Saisie quantitÃ©    â†’ validation temps rÃ©el
  5. Clic 'Prescrire'   â†’ _prescrire() â†’ ctrl.ajouter_ligne() â†’ FEFO auto dans DAO
  6. Ligne ajoutÃ©e      â†’ visuel + badge++ + total mis Ã  jour
  7. Clic 'Valider'     â†’ _valider_prescription() â†’ confirmation â†’ reset + rechargement
  8. Clic 'Annuler'     â†’ _annuler_prescription() â†’ suppression toutes lignes â†’ reset

Injection du contrÃ´leur via __init__ (Architecture MVC â€” pas d'import direct).
"""

from typing import Dict, Any, List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout

from views.shared.theme_manager import theme_manager

# Composants UI
from .components.animated_frame          import AnimatedFrame
from .components.prescription_header     import PrescriptionHeader
from .components.prescription_form       import PrescriptionForm
from .components.prescription_footer     import PrescriptionFooter
from .components.prescription_ligne_items import PrescriptionLigneItem
from views.shared.message_box import CustomMessageBox

# Handlers mÃ©tier
from .handlers.data_loader             import PrescriptionDataLoader
from .handlers.validation_handler      import PrescriptionValidationHandler
from .handlers.prescription_operation import PrescriptionOperations

# Styles
from .styles.prescription_style import PrescriptionStyles


class PrescriptionWidget(AnimatedFrame):
    """
    Widget de gestion des prescriptions produits (service pharmacie).
    Version modulaire â€” Architecture MVC stricte.

    ResponsabilitÃ©s :
      - Orchestration des composants UI
      - Gestion du workflow mÃ©tier prescription
      - Communication avec PrescriptionControleur
    """

    # Signal emis apres validation reussie (rafraichir la vue parente)
    prescription_validee = Signal()

    def __init__(self, prescription_ctrl=None, parent=None):
        super().__init__(parent)

        print("[PrescriptionWidget] Initialisation")

        # ----------------------------------------------------------------
        # Injection du contrÃ´leur (Architecture MVC)
        # ----------------------------------------------------------------
        self.prescription_ctrl = prescription_ctrl

        # ----------------------------------------------------------------
        # Ã‰tat courant
        # ----------------------------------------------------------------
        self.code_session      : Optional[str] = None
        self.code_visite       : Optional[str] = None
        self.code_consultation : Optional[str] = None
        self.lignes_panier     : List[Any]     = []

        # ----------------------------------------------------------------
        # Composants UI
        # ----------------------------------------------------------------
        _bleu = theme_manager.colors()['primary']
        _rouge = theme_manager.colors()['danger']
        self.header_component    = PrescriptionHeader(_bleu)
        self.form_component      = PrescriptionForm(_bleu)
        self.footer_component    = PrescriptionFooter(_bleu)
        self.ligne_item_factory  = PrescriptionLigneItem(_bleu, _rouge)

        # ----------------------------------------------------------------
        # Handlers mÃ©tier
        # ----------------------------------------------------------------
        self.data_loader         = PrescriptionDataLoader(_bleu)
        self.validation_handler  = PrescriptionValidationHandler(prescription_ctrl)
        self.operations          = PrescriptionOperations(prescription_ctrl)

        # ----------------------------------------------------------------
        # Construction de l'interface
        # ----------------------------------------------------------------
        self._init_ui()
        self._connecter_signaux()

    # =========================================================================
    # CONSTRUCTION UI
    # =========================================================================

    def _init_ui(self) -> None:
        """Initialise et assemble tous les composants de l'interface."""
        self.setStyleSheet(
            "background-color: white; border-radius: 18px; border: 1px solid #eaeaea;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header â€” retourne le badge QLabel
        self.badge_panier = self.header_component.create(layout)

        # Formulaire â€” retourne (container, layout_lignes)
        self.container_panier, self.layout_lignes_panier = self.form_component.create(
            layout,
            self._appliquer_style_scrollbar
        )

        # Exposition des widgets du formulaire
        self.combo_consultation = self.form_component.combo_consultation
        self.edit_code_visite   = self.form_component.edit_code_visite
        self.combo_produit      = self.form_component.combo_produit
        self.input_designation  = self.form_component.input_designation
        self.input_quantite     = self.form_component.input_quantite
        self.input_prix         = self.form_component.input_prix
        self.btn_prescrire      = self.form_component.btn_prescrire

        # Footer â€” retourne (lbl_total, btn_valider, btn_annuler)
        self.lbl_total, self.btn_valider, self.btn_annuler = \
            self.footer_component.create(layout)

    def _connecter_signaux(self) -> None:
        """Connecte tous les signaux pour la validation et les interactions."""

        # SÃ©lection consultation â†’ auto-remplit code_visite + carte patient
        self.combo_consultation.currentIndexChanged.connect(self._on_consultation_change)

        # Auto-remplissage dÃ©signation + prix Ã  la sÃ©lection produit
        self.combo_produit.currentIndexChanged.connect(self._on_produit_change)

        # Validation quantitÃ© en temps rÃ©el (ModernQuantitySpinner â†’ valueChanged(int))
        self.input_quantite.valueChanged.connect(
            lambda value: self.validation_handler.valider_quantite(
                self.input_quantite, str(value)
            )
        )

        # Ajout Ã  la prescription
        self.btn_prescrire.clicked.connect(self._prescrire)

        # Validation et annulation
        self.btn_valider.clicked.connect(self._valider_prescription)
        self.btn_annuler.clicked.connect(self._annuler_prescription)

    # =========================================================================
    # CHARGEMENT DONNÃ‰ES
    # =========================================================================

    def charger_donnees(self, code_session: str) -> None:
        """
        Point d'entrÃ©e depuis la vue parente.
        Charge les produits et les patients en attente de prescription.

        Args:
            code_session: Code de la session active
        """
        print(f"[PrescriptionWidget] charger_donnees session={code_session}")
        self.code_session = code_session

        if not self.prescription_ctrl:
            return

        # Charger les produits dans le combo produit
        self.data_loader.charger_produits(
            self.prescription_ctrl,
            self.combo_produit
        )

        # Charger les consultations 'Attente pharmacie' dans le combo
        self.data_loader.charger_patients_en_attente(
            self.prescription_ctrl,
            self.combo_consultation,
            code_session
        )

    def _on_consultation_change(self, index: int) -> None:
        """
        SÃ©lection dans combo_consultation â†’
          - auto-remplit edit_code_visite (pattern CommandeLunetteFormDialog)
          - auto-remplit la carte patient
          - active le formulaire produit

        userData = dict retournÃ© par patients_en_attente_prescription :
          {'code_visite', 'code_consultation', 'nom', 'prenom', ...}
        """
        patient_data = self.combo_consultation.currentData()

        if not patient_data:
            self.code_visite       = None
            self.code_consultation = None
            self.form_component.vider_patient()
            self.form_component.desactiver_formulaire()
            self._reinitialiser_lignes()
            return

        # Extraire les codes depuis le dict DAO
        self.code_visite       = patient_data.get('code_visite', '')
        self.code_consultation = patient_data.get('code_consultation', '')

        # Auto-remplir carte patient + code_visite (pattern lunettes)
        self.form_component.charger_patient(
            nom               = patient_data.get('nom', ''),
            prenom            = patient_data.get('prenom', ''),
            code_visite       = self.code_visite,
            code_consultation = self.code_consultation
        )

        self.form_component.activer_formulaire()

        # Recharger les lignes dÃ©jÃ  prescrites pour cette consultation
        self._reinitialiser_lignes()
        if self.code_consultation:
            self.data_loader.charger_panier_existant(
                self.prescription_ctrl,
                self.code_consultation,
                self._ajouter_ligne_visuelle
            )

        self._recalculer_total()

        print(f"[PrescriptionWidget] Consultation sÃ©lectionnÃ©e: "
              f"{patient_data.get('prenom')} {patient_data.get('nom')} "
              f"| visite={self.code_visite} | consultation={self.code_consultation}")

    # =========================================================================
    # Ã‰VÃ‰NEMENTS FORMULAIRE
    # =========================================================================

    def _on_produit_change(self, index: int) -> None:
        """
        Auto-remplissage dÃ©signation + prix Ã  la sÃ©lection du produit.
        Lit directement depuis currentData() â€” dict complet stockÃ© par data_loader.
        MÃªme pattern que PanierForm._on_produit_change.
        """
        produit_data = self.combo_produit.currentData()

        if not produit_data:
            self.input_designation.clear()
            self.input_designation.setStyleSheet(PrescriptionStyles.input_readonly())
            self.input_prix.clear()
            return

        # âœ… Lecture directe depuis le dict â€” pas de lazy import ProduitControleur
        designation = produit_data.get('libelle', '')
        prix        = float(produit_data.get('prix_vente_unitaire', 0) or 0)

        # Auto-remplir dÃ©signation
        self.input_designation.setText(designation)
        self.input_designation.setStyleSheet(PrescriptionStyles.input_readonly())

        # Auto-remplir prix (readonly)
        if prix > 0:
            self.input_prix.blockSignals(True)
            self.input_prix.clear()
            self.input_prix.setText(
                str(int(prix)) if prix == int(prix) else str(prix)
            )
            self.input_prix.blockSignals(False)

    # =========================================================================
    # PRESCRIRE (AJOUTER)
    # =========================================================================

    def _prescrire(self) -> None:
        """
        Ajoute un produit au panier prescription.
        AppelÃ© par le clic sur btn_prescrire.
        """
        if not self.code_consultation:
            self._afficher_message(
                "Attention", "Veuillez sÃ©lectionner un patient d'abord.", False
            )
            return

        # PrÃ©parer les donnÃ©es du formulaire
        produit_data = self.combo_produit.currentData()
        form_data = {
            'code_produit'     : produit_data.get('code_produit') if produit_data else None,
            'code_session'     : self.code_session,
            'code_visite'      : self.code_visite,
            'code_consultation': self.code_consultation,
            'designation'      : self.input_designation.text().strip(),
            'quantite'         : self.input_quantite.text(),
            'prix'             : self.input_prix.text(),
        }

        # DÃ©lÃ©guer au handler opÃ©rations
        ok, msg = self.operations.ajouter_ligne_prescription(form_data)

        if ok:
            allocations = form_data.get('allocations')
            if allocations:
                for alloc in allocations:
                    self._ajouter_ligne_visuelle(alloc)
            else:
                self._ajouter_ligne_visuelle(form_data)
            self.form_component.vider_formulaire()
            self._recalculer_total()
            self._afficher_message("SuccÃ¨s", msg, True)
        else:
            self._afficher_message("Erreur", msg, False)

    # =========================================================================
    # GESTION VISUELLE DES LIGNES
    # =========================================================================

    def _ajouter_ligne_visuelle(self, form_data: Dict[str, Any]) -> None:
        """
        Ajoute une ligne visuelle dans le panier.

        Args:
            form_data: Dict avec designation, quantite, prix,
                       date_expiration, code_prescription
        """
        ligne_widget = self.ligne_item_factory.create(
            designation       = form_data.get('designation', ''),
            quantite          = int(form_data.get('quantite', 1)),
            prix              = float(str(form_data.get('prix', '0')).replace(" ", "") or 0),
            date_expiration   = form_data.get('date_expiration'),
            code_prescription = form_data.get('code_prescription', 'PRS_TEMP'),
            on_delete_callback= self._supprimer_ligne
        )

        self.lignes_panier.append(ligne_widget)

        # InsÃ©rer avant le stretch
        count = self.layout_lignes_panier.count()
        self.layout_lignes_panier.insertWidget(count - 1, ligne_widget)

        # Mettre Ã  jour le badge
        self.badge_panier.setText(str(len(self.lignes_panier)))

    def _supprimer_ligne(self, ligne_widget: Any) -> None:
        """
        Supprime une ligne du panier (BDD + visuel) avec confirmation.

        Args:
            ligne_widget: Widget QFrame de la ligne Ã  supprimer
        """
        if not hasattr(ligne_widget, 'code_prescription'):
            return

        ok, msg = self.operations.supprimer_ligne_prescription(
            ligne_widget.code_prescription, self
        )

        if ok:
            self.lignes_panier.remove(ligne_widget)
            ligne_widget.deleteLater()
            self.badge_panier.setText(str(len(self.lignes_panier)))
            self._recalculer_total()
            self._afficher_message("SuccÃ¨s", msg, True)
        else:
            if msg != "Suppression annulÃ©e":
                self._afficher_message("Erreur", msg, False)

    # =========================================================================
    # VALIDER / ANNULER
    # =========================================================================

    def _valider_prescription(self) -> None:
        """
        Valide la prescription en cours.
        Le statut_patient passe Ã  'Attente payement' au moment de la validation.
        """
        if not self.lignes_panier:
            self._afficher_message(
                "Attention", "La prescription est vide.", False
            )
            return

        ok, msg = self.operations.valider_prescription(
            self.code_consultation, self.code_visite, self
        )

        if ok:
            self._afficher_message("SuccÃ¨s", msg, True)
            self._reinitialiser_complet()
            self.prescription_validee.emit()
        else:
            if msg != "Validation annulÃ©e":
                self._afficher_message("Erreur", msg, False)

    def _annuler_prescription(self) -> None:
        """Annule la prescription en cours avec confirmation."""
        if not self.lignes_panier and not self.code_consultation:
            return

        ok, msg = self.operations.annuler_prescription(self.lignes_panier, self)

        if ok:
            self._reinitialiser_complet()
            self._afficher_message("SuccÃ¨s", msg, True)
        else:
            if msg != "Annulation annulÃ©e":
                self._afficher_message("Erreur", msg, False)

    # =========================================================================
    # CALCULS
    # =========================================================================

    def _recalculer_total(self) -> None:
        """Recalcule et affiche le total du panier prescription."""
        if self.prescription_ctrl and self.code_consultation:
            # Source de vÃ©ritÃ© : BDD (via contrÃ´leur)
            total = self.prescription_ctrl.obtenir_montant_total_consultation(
                self.code_consultation
            )
        else:
            # Fallback local
            total = sum(
                getattr(l, 'quantite', 0) * getattr(l, 'prix', 0.0)
                for l in self.lignes_panier
            )

        self.footer_component.update_total(total)

    # =========================================================================
    # RÃ‰INITIALISATION
    # =========================================================================

    def _reinitialiser_lignes(self) -> None:
        """
        Supprime uniquement les lignes visuelles (sans toucher au combo patient).
        AppelÃ© lors d'un changement de patient pour repartir d'un panier vide.
        """
        for ligne in self.lignes_panier:
            ligne.deleteLater()
        self.lignes_panier.clear()
        self.badge_panier.setText("0")
        self.footer_component.update_total(0)

    def _reinitialiser_complet(self) -> None:
        """
        RÃ©initialise complÃ¨tement le widget aprÃ¨s validation ou annulation.
        Recharge le combo patient pour reflÃ©ter les nouvelles attentes.
        """
        self._reinitialiser_lignes()

        self.code_visite       = None
        self.code_consultation = None

        self.form_component.vider_formulaire()
        self.form_component.vider_patient()
        self.form_component.desactiver_formulaire()

        # Recharger le combo consultation â€” patient servi, disparaÃ®t de la liste
        if self.prescription_ctrl and self.code_session:
            self.data_loader.charger_patients_en_attente(
                self.prescription_ctrl,
                self.combo_consultation,
                self.code_session
            )

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _appliquer_style_scrollbar(self, widget: Any) -> None:
        """
        Applique le style personnalisÃ© Ã  la scrollbar verticale.

        Args:
            widget: QScrollArea Ã  styler
        """
        widget.verticalScrollBar().setStyleSheet(PrescriptionStyles.scrollbar())

    def _afficher_message(self, titre: str, message: str, succes: bool) -> None:
        """
        Affiche un message Ã  l'utilisateur via CustomMessageBox.

        Args:
            titre  : Titre du dialogue
            message: Contenu du message
            succes : True â†’ vert (succÃ¨s), False â†’ rouge (erreur)
        """
        if succes:
            CustomMessageBox.success(
                self, titre, message, theme_manager.colors()['primary']
            )
        else:
            CustomMessageBox.error(
                self, titre, message, theme_manager.colors()['primary']
            )

