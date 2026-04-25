"""
Widget facture patient (panier services).
Architecture : MVC + composants + handlers.
Responsabilite : orchestrer UI et workflow facture patient.
"""

from typing import Any, Dict, List, Optional

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea, QWidget,
    QPushButton, QComboBox
)

from .components.animated_frame import AnimatedFrame
from .components.facture_patient_row import FacturePatientRowItem
from .components.facture_patient_line_dialog import FacturePatientLineDialog
from views.shared.message_box import CustomMessageBox
from .handlers.facture_patient_data_loader import FacturePatientDataLoader
from .handlers.facture_patient_operations import FacturePatientOperations
from .styles.facture_patient_styles import FacturePatientStyles
from views.shared.modal_theme import MC


class FacturePatientWidget(AnimatedFrame):
    """Widget principal facture patient."""

    paiement_effectue = Signal()
    facture_mise_a_jour = Signal()

    def __init__(self, facture_ctrl=None, panier_ctrl=None, parent=None):
        super().__init__(parent)

        self.facture_ctrl = facture_ctrl
        self.panier_ctrl = panier_ctrl

        self.code_session: Optional[str] = None
        self.code_visite: Optional[str] = None
        self.code_facture: Optional[str] = None
        self._patient_data: Dict[str, Any] = {}
        self._date_facture_str: str = "—"
        self.lignes_panier: List[Any] = []

        self.data_loader = FacturePatientDataLoader(FacturePatientStyles.BLEU_PRINCIPAL)
        self.operations = FacturePatientOperations(
            facture_ctrl, panier_ctrl, FacturePatientStyles.BLEU_PRINCIPAL
        )
        self.row_factory = FacturePatientRowItem(
            FacturePatientStyles.BLEU_PRINCIPAL, FacturePatientStyles.ROUGE
        )

        self._init_ui()
        self._connecter_signaux()

    # =========================================================================
    # UI
    # =========================================================================

    def _init_ui(self) -> None:
        self.setStyleSheet(
            f"background-color: {MC.BG_CARD}; border-radius: 18px; border: 1px solid {MC.BORDER};"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel("FACTURATION ET PAIEMENT DES SERVICES")
        title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {FacturePatientStyles.BLEU_PRINCIPAL};"
        )
        header.addWidget(title)
        header.addStretch()

        self.combo_visite = QComboBox()
        self.combo_visite.setFixedHeight(34)
        self.combo_visite.setMinimumWidth(280)
        self.combo_visite.setStyleSheet(
            f"border:1px solid {MC.BORDER}; border-radius:10px; padding-left:8px; font-size:12px;"
        )
        header.addWidget(self.combo_visite)
        layout.addLayout(header)

        # Top cards
        cards = QHBoxLayout()
        cards.setSpacing(10)

        self.card_patient = self._build_patient_card()
        self.card_resume = self._build_resume_card()

        cards.addWidget(self.card_patient, 3)
        cards.addWidget(self.card_resume, 2)
        layout.addLayout(cards)

        # Services de la visite (combo) + bouton ajouter
        tools = QHBoxLayout()
        self.combo_service = QComboBox()
        self.combo_service.setFixedHeight(36)
        self.combo_service.setStyleSheet(FacturePatientStyles.search_input())
        self._remplir_combo_services_visite([])

        self.btn_add_service = QPushButton(
            qta.icon("fa5s.plus", color="white"), " Ajouter un service"
        )
        self.btn_add_service.setFixedHeight(36)
        self.btn_add_service.setCursor(Qt.PointingHandCursor)
        self.btn_add_service.setStyleSheet(
            FacturePatientStyles.btn_add(FacturePatientStyles.BLEU_PRINCIPAL)
        )
        self.btn_add_service.setEnabled(False)

        self.btn_add_all = QPushButton(
            qta.icon("fa5s.layer-group", color=FacturePatientStyles.BLEU_PRINCIPAL),
            " Ajouter tous"
        )
        self.btn_add_all.setFixedHeight(36)
        self.btn_add_all.setCursor(Qt.PointingHandCursor)
        self.btn_add_all.setStyleSheet(
            f"background:{MC.BG_MAIN}; border:1px solid {MC.BORDER}; border-radius:12px; "
            "font-weight:bold; font-size:12px; padding:8px 14px;"
        )
        self.btn_add_all.setEnabled(False)

        tools.addWidget(self.combo_service, 1)
        tools.addWidget(self.btn_add_service)
        tools.addWidget(self.btn_add_all)
        layout.addLayout(tools)

        # Table header
        header_row = self._build_table_header()
        layout.addWidget(header_row)

        # Scroll area for lines
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll.verticalScrollBar().setStyleSheet(FacturePatientStyles.scrollbar())

        self.container_lignes = QWidget()
        self.container_lignes.setStyleSheet("background: transparent;")
        self.layout_lignes = QVBoxLayout(self.container_lignes)
        self.layout_lignes.setContentsMargins(0, 0, 0, 0)
        self.layout_lignes.setSpacing(6)
        self.layout_lignes.addStretch()

        self.scroll.setWidget(self.container_lignes)
        layout.addWidget(self.scroll, 1)

        # Footer buttons
        footer = QHBoxLayout()
        footer.addStretch()

        self.btn_annuler = QPushButton("ANNULER LA FACTURE")
        self.btn_annuler.setCursor(Qt.PointingHandCursor)
        self.btn_annuler.setStyleSheet(FacturePatientStyles.btn_cancel())
        self.btn_annuler.setFixedHeight(38)

        self.btn_payer = QPushButton("PROCEDER AU PAIEMENT")
        self.btn_payer.setCursor(Qt.PointingHandCursor)
        self.btn_payer.setStyleSheet(FacturePatientStyles.btn_pay())
        self.btn_payer.setFixedHeight(38)

        footer.addWidget(self.btn_annuler)
        footer.addWidget(self.btn_payer)
        layout.addLayout(footer)

    def _build_patient_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(FacturePatientStyles.card())
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        title = QLabel("Informations du patient")
        title.setStyleSheet(
            FacturePatientStyles.section_title("#0f172a") +
            " border: none; background: transparent;"
        )
        lay.addWidget(title)

        row = QHBoxLayout()
        avatar = QLabel()
        avatar.setPixmap(qta.icon("fa5s.user-circle", color=MC.TEXT_MUTED).pixmap(40, 40))
        avatar.setFixedSize(42, 42)
        row.addWidget(avatar)

        info = QVBoxLayout()
        self.lbl_patient_nom = QLabel("—")
        self.lbl_patient_nom.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{MC.TEXT_PRIMARY}; "
            "border: none; background: transparent;"
        )
        self.lbl_patient_id = QLabel("Patient ID: —")
        self.lbl_patient_id.setStyleSheet(
            f"font-size:10px; color:{MC.TEXT_SECONDARY}; border: none; background: transparent;"
        )
        info.addWidget(self.lbl_patient_nom)
        info.addWidget(self.lbl_patient_id)
        row.addLayout(info, 1)

        self.lbl_badge_urgent = QLabel("URGENT")
        self.lbl_badge_urgent.setStyleSheet(FacturePatientStyles.badge_urgent())
        self.lbl_badge_urgent.setVisible(False)
        row.addWidget(self.lbl_badge_urgent)

        lay.addLayout(row)

        meta = QHBoxLayout()
        self.lbl_code_visite = QLabel("Code visite: —")
        self.lbl_date_admission = QLabel("Date visite: —")
        self.lbl_telephone = QLabel("Telephone: —")
        for lbl in (self.lbl_code_visite, self.lbl_date_admission, self.lbl_telephone):
            lbl.setStyleSheet(
                f"font-size:10px; color:{MC.TEXT_SECONDARY}; border: none; background: transparent;"
            )
        meta.addWidget(self.lbl_code_visite)
        meta.addSpacing(12)
        meta.addWidget(self.lbl_date_admission)
        meta.addSpacing(12)
        meta.addWidget(self.lbl_telephone)
        meta.addStretch()
        lay.addLayout(meta)

        return card

    def _build_resume_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(FacturePatientStyles.card())
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        title = QLabel("Resume de la facture")
        title.setStyleSheet(
            FacturePatientStyles.section_title("#0f172a") +
            " border: none; background: transparent;"
        )
        lay.addWidget(title)

        self.lbl_total_facture = QLabel("Total facture: 0 GNF")
        self.lbl_total_facture.setStyleSheet(
            f"font-size:11px; color:{MC.TEXT_PRIMARY}; border: none; background: transparent;"
        )
        lay.addWidget(self.lbl_total_facture)

        self.lbl_nb_services = QLabel("Nombre de services: 0")
        self.lbl_nb_services.setStyleSheet(
            f"font-size:11px; color:{MC.TEXT_SECONDARY}; border: none; background: transparent;"
        )
        lay.addWidget(self.lbl_nb_services)

        self.lbl_date_facture = QLabel("Date: —")
        self.lbl_date_facture.setStyleSheet(
            f"font-size:11px; color:{MC.TEXT_SECONDARY}; border: none; background: transparent;"
        )
        lay.addWidget(self.lbl_date_facture)

        # Total a payer (valeur principale)
        self.lbl_total_a_payer = QLabel("TOTAL A PAYER: 0 GNF")
        self.lbl_total_a_payer.setStyleSheet(
            f"font-size:12px; font-weight:bold; color:{MC.TEXT_PRIMARY}; "
            "border: none; background: transparent;"
        )
        lay.addWidget(self.lbl_total_a_payer)

        return card

    def _build_table_header(self) -> QFrame:
        header = QFrame()
        header.setStyleSheet(FacturePatientStyles.table_header())
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)

        def _label(text, width, align=Qt.AlignLeft):
            lbl = QLabel(text)
            lbl.setFixedWidth(width)
            lbl.setAlignment(align)
            return lbl

        layout.addWidget(_label("#", 26, Qt.AlignCenter))
        layout.addWidget(_label("SERVICE", 140))
        layout.addWidget(_label("DESCRIPTION", 220))
        layout.addWidget(_label("QTE", 70, Qt.AlignCenter))
        layout.addWidget(_label("PRIX UNIT", 110, Qt.AlignRight))
        layout.addWidget(_label("TOTAL", 110, Qt.AlignRight))
        layout.addWidget(_label("ACTIONS", 170, Qt.AlignCenter))
        return header

    # =========================================================================
    # SIGNALS
    # =========================================================================

    def _connecter_signaux(self) -> None:
        self.combo_visite.currentIndexChanged.connect(self._on_visite_change)
        self.btn_add_service.clicked.connect(self._ajouter_service)
        self.btn_annuler.clicked.connect(self._annuler_facture)
        self.btn_payer.clicked.connect(self._payer_facture)
        self.combo_service.currentIndexChanged.connect(self._toggle_add_button)
        self.btn_add_all.clicked.connect(self._ajouter_tous_services)
        # pas de filtre: le combo sert a selectionner un service a ajouter

    # =========================================================================
    # CHARGEMENT DONNEES
    # =========================================================================

    def charger_donnees(self, code_session: str) -> None:
        self.code_session = code_session
        self.data_loader.charger_patients_en_attente(
            self.facture_ctrl, self.combo_visite, code_session
        )

    def _on_visite_change(self, index: int) -> None:
        patient = self.combo_visite.currentData()
        if not patient:
            self._reset_view()
            return

        self.code_visite = patient.get("code_visite")
        ok, msg, code_facture = self.operations.generer_facture(
            self.code_visite, patient.get("telephone", ""), creer_panier=False
        )
        if not ok:
            CustomMessageBox.error(self, "Erreur", msg, FacturePatientStyles.BLEU_PRINCIPAL)
            self._reset_view()
            return

        self.code_facture = code_facture
        self._charger_date_facture()
        self._patient_data = patient
        self._remplir_patient(patient)
        self._charger_services_visite()
        self._reinitialiser_lignes()
        self._recalculer_total()

    # =========================================================================
    # ACTIONS LIGNES
    # =========================================================================

    def _ajouter_service(self) -> None:
        if not self.code_facture:
            return
        data = self.combo_service.currentData()
        if not data:
            return
        ok, msg, code_panier = self.operations.ajouter_ligne(self.code_facture, data)
        if ok:
            data["code_paniere"] = code_panier
            self._ajouter_ligne_visuelle(data)
            # Retirer l'element du combo apres ajout
            current_index = self.combo_service.currentIndex()
            if current_index > 0:
                self.combo_service.removeItem(current_index)
            self._toggle_add_button()
            self._recalculer_total()

    def _ajouter_tous_services(self) -> None:
        if not self.code_facture:
            return
        if self.combo_service.count() <= 1:
            return

        total_ajoutes = 0
        erreurs = 0

        # Toujours ajouter l'item index 1 puis le retirer
        while self.combo_service.count() > 1:
            self.combo_service.setCurrentIndex(1)
            data = self.combo_service.currentData()
            if not data:
                break
            ok, msg, code_panier = self.operations.ajouter_ligne(self.code_facture, data)
            if ok:
                data["code_paniere"] = code_panier
                self._ajouter_ligne_visuelle(data)
                self.combo_service.removeItem(1)
                total_ajoutes += 1
            else:
                erreurs += 1
                # Eviter boucle infinie si un item echoue
                self.combo_service.removeItem(1)

        self._toggle_add_button()
        self._recalculer_total()

    def _ajouter_ligne_visuelle(self, data: Dict[str, Any]) -> None:
        index = len(self.lignes_panier) + 1
        ligne = self.row_factory.create(
            index=index,
            designation=data.get("designation", ""),
            description=data.get("description", ""),
            quantite=int(data.get("quantite", 1)),
            prix=float(data.get("prix", 0.0)),
            code_paniere=data.get("code_paniere", ""),
            on_delete_callback=self._supprimer_ligne,
            on_edit_callback=self._modifier_ligne
        )
        self.lignes_panier.append(ligne)
        count = self.layout_lignes.count()
        self.layout_lignes.insertWidget(count - 1, ligne)

    def _supprimer_ligne(self, ligne_widget) -> None:
        if not hasattr(ligne_widget, "code_paniere"):
            return
        ok, msg = self.operations.supprimer_ligne(ligne_widget.code_paniere, self)
        if ok:
            # Remettre le service dans le combo apres suppression
            self._restituer_service_au_combo(ligne_widget)
            self.lignes_panier.remove(ligne_widget)
            ligne_widget.deleteLater()
            self._reindexer_lignes()
            self._recalculer_total()
            if self.facture_ctrl and self.code_facture:
                self.facture_ctrl.recalculer_montant_facture(self.code_facture)
            CustomMessageBox.success(self, "Succes", msg, FacturePatientStyles.BLEU_PRINCIPAL)
        else:
            if msg != "Suppression annulee":
                CustomMessageBox.error(self, "Erreur", msg, FacturePatientStyles.BLEU_PRINCIPAL)

    def _modifier_ligne(self, ligne_widget) -> None:
        data = {
            "designation": getattr(ligne_widget, "designation", ""),
            "description": getattr(ligne_widget, "description", ""),
            "quantite": getattr(ligne_widget, "quantite", 1),
            "prix": getattr(ligne_widget, "prix", 0.0),
        }
        dialog = FacturePatientLineDialog(self, "Modifier un service", data)
        if dialog.exec() != dialog.Accepted:
            return
        new_data = dialog.get_data()
        ok, msg = self.operations.modifier_ligne(
            self.code_facture, ligne_widget.code_paniere, new_data
        )
        if ok:
            # Update widget data
            ligne_widget.designation = new_data["designation"]
            ligne_widget.description = new_data["description"]
            ligne_widget.quantite = new_data["quantite"]
            ligne_widget.prix = new_data["prix"]

            ligne_widget.lbl_service.setText(new_data["designation"])
            ligne_widget.lbl_desc.setText(new_data["description"] or "—")
            ligne_widget.lbl_qte.setText(str(new_data["quantite"]))
            ligne_widget.lbl_prix.setText(
                f"{new_data['prix']:,.0f} GNF".replace(",", " ")
            )
            total = new_data["quantite"] * new_data["prix"]
            ligne_widget.lbl_total.setText(f"{total:,.0f} GNF".replace(",", " "))
            self._recalculer_total()
            CustomMessageBox.success(self, "Succes", msg, FacturePatientStyles.BLEU_PRINCIPAL)
        else:
            CustomMessageBox.error(self, "Erreur", msg, FacturePatientStyles.BLEU_PRINCIPAL)

    # =========================================================================
    # FACTURE
    # =========================================================================

    def _payer_facture(self) -> None:
        if not self.code_facture:
            return
        ok, msg = self.operations.encaisser_facture(
            self.code_facture, self, patient_info=self._patient_data
        )
        if ok:
            CustomMessageBox.success(self, "Succes", msg, FacturePatientStyles.BLEU_PRINCIPAL)
            self._reset_view()
            if self.code_session:
                self.charger_donnees(self.code_session)
            self.paiement_effectue.emit()
            self.facture_mise_a_jour.emit()
        else:
            if msg != "Paiement annule":
                CustomMessageBox.error(self, "Erreur", msg, FacturePatientStyles.BLEU_PRINCIPAL)

    def _annuler_facture(self) -> None:
        if not self.code_facture:
            return
        ok, msg = self.operations.annuler_facture(self.code_facture, self)
        if ok:
            CustomMessageBox.success(self, "Succes", msg, FacturePatientStyles.BLEU_PRINCIPAL)
            self._reset_view()
            if self.code_session:
                self.charger_donnees(self.code_session)
            self.facture_mise_a_jour.emit()
        else:
            if msg != "Annulation annulee":
                CustomMessageBox.error(self, "Erreur", msg, FacturePatientStyles.BLEU_PRINCIPAL)

    # =========================================================================
    # UI HELPERS
    # =========================================================================

    def _remplir_patient(self, data: Dict[str, Any]) -> None:
        nom = data.get("nom", "")
        prenom = data.get("prenom", "")
        self.lbl_patient_nom.setText(f"{prenom} {nom}".strip() or "—")
        self.lbl_patient_id.setText(f"Patient ID: {data.get('code_patient', '—')}")
        date_visite = data.get("date_visite") or data.get("date_facture")
        if hasattr(date_visite, "strftime"):
            date_str = date_visite.strftime("%d/%m/%Y")
        else:
            date_str = str(date_visite) if date_visite else "—"
        self.lbl_code_visite.setText(f"Code visite: {data.get('code_visite', '—')}")
        self.lbl_date_admission.setText(f"Date visite: {date_str}")
        self.lbl_telephone.setText(f"Telephone: {data.get('telephone', '—')}")
        urgent = bool(data.get("urgent"))
        self.lbl_badge_urgent.setVisible(urgent)

    def _charger_date_facture(self) -> None:
        """Charge la date facture depuis le controleur si possible."""
        self._date_facture_str = "—"
        try:
            if self.facture_ctrl and self.code_facture:
                facture = self.facture_ctrl.obtenir_par_code(self.code_facture)
                if facture and facture.get_date_facture():
                    dt = facture.get_date_facture()
                    self._date_facture_str = (
                        dt.strftime("%d/%m/%Y") if hasattr(dt, "strftime") else str(dt)
                    )
        except Exception:
            self._date_facture_str = "—"

    def _reinitialiser_lignes(self) -> None:
        for ligne in self.lignes_panier:
            ligne.deleteLater()
        self.lignes_panier.clear()

    def _reset_view(self) -> None:
        self.code_visite = None
        self.code_facture = None
        self._patient_data = {}
        self._date_facture_str = "—"
        self._reinitialiser_lignes()
        self._recalculer_total()
        self.lbl_patient_nom.setText("—")
        self.lbl_patient_id.setText("Patient ID: —")
        self.lbl_code_visite.setText("Code visite: —")
        self.lbl_date_admission.setText("Date visite: —")
        self.lbl_telephone.setText("Telephone: —")
        self.lbl_badge_urgent.setVisible(False)
        self.combo_visite.blockSignals(True)
        self.combo_visite.setCurrentIndex(0)
        self.combo_visite.blockSignals(False)

    def _reindexer_lignes(self) -> None:
        for i, ligne in enumerate(self.lignes_panier, start=1):
            if hasattr(ligne, "lbl_index"):
                ligne.lbl_index.setText(f"{i}.")

    def _remplir_combo_services_visite(self, services: List[Dict[str, Any]]) -> None:
        """Remplit le combo avec les services lies a la visite selectionnee."""
        self.combo_service.clear()
        self.combo_service.addItem(
            qta.icon("fa5s.list", color=FacturePatientStyles.BLEU_PRINCIPAL),
            "  Selectionner un service...",
            None
        )
        for s in services:
            designation = s.get("designation", "")
            ref = s.get("numero_reference", "")
            prix = float(s.get("prix_applique", 0) or 0)
            label = f"  {designation}  •  {prix:,.0f} GNF".replace(",", " ")
            icon = self._icone_service(designation)
            # data pour ajout panier
            data = {
                "designation": designation,
                "description": ref,
                "quantite": int(s.get("quantite_facture", 1) or 1),
                "prix": prix,
            }
            self.combo_service.addItem(icon, label, data)

    def _restituer_service_au_combo(self, ligne_widget) -> None:
        """Reinjecte un service supprime dans le combo."""
        designation = getattr(ligne_widget, "designation", "")
        description = getattr(ligne_widget, "description", "")
        quantite = int(getattr(ligne_widget, "quantite", 1) or 1)
        prix = float(getattr(ligne_widget, "prix", 0.0) or 0.0)
        label = f"  {designation}  â€¢  {prix:,.0f} GNF".replace(",", " ")
        icon = self._icone_service(designation)
        data = {
            "designation": designation,
            "description": description,
            "quantite": quantite,
            "prix": prix,
        }
        self.combo_service.addItem(icon, label, data)
        self._toggle_add_button()

    def _icone_service(self, designation: str):
        d = (designation or "").lower()
        if "consult" in d:
            return qta.icon("fa5s.stethoscope", color=FacturePatientStyles.BLEU_PRINCIPAL)
        if "examen" in d or "exam" in d:
            return qta.icon("fa5s.microscope", color=FacturePatientStyles.BLEU_PRINCIPAL)
        if "chirurg" in d:
            return qta.icon("fa5s.procedures", color=FacturePatientStyles.BLEU_PRINCIPAL)
        if "lunette" in d:
            return qta.icon("fa5s.glasses", color=FacturePatientStyles.BLEU_PRINCIPAL)
        if "pharma" in d:
            return qta.icon("fa5s.pills", color=FacturePatientStyles.BLEU_PRINCIPAL)
        return qta.icon("fa5s.file-medical", color=FacturePatientStyles.BLEU_PRINCIPAL)

    def _charger_services_visite(self) -> None:
        """Charge depuis le controleur la liste des services de la visite."""
        services = []
        if self.facture_ctrl and self.code_visite:
            try:
                services = self.facture_ctrl.lister_services_visite(self.code_visite) or []
            except Exception:
                services = []
        self._remplir_combo_services_visite(services)
        self._toggle_add_button()

    def _toggle_add_button(self) -> None:
        """Active le bouton ajouter uniquement si un service est selectionne."""
        data = self.combo_service.currentData()
        can_add = bool(data) and bool(self.code_facture)
        self.btn_add_service.setEnabled(can_add)
        self.btn_add_all.setEnabled(self.combo_service.count() > 1 and bool(self.code_facture))

    def _recalculer_total(self) -> None:
        total = 0.0
        for ligne in self.lignes_panier:
            total += float(getattr(ligne, "quantite", 0)) * float(getattr(ligne, "prix", 0.0))
        self.lbl_total_facture.setText(f"Total facture: {total:,.0f} GNF".replace(",", " "))
        self.lbl_nb_services.setText(f"Nombre de services: {len(self.lignes_panier)}")
        self.lbl_date_facture.setText(f"Date: {self._date_facture_str}")
        self.lbl_total_a_payer.setText(
            f"TOTAL A PAYER: {total:,.0f} GNF".replace(",", " ")
        )
        self.btn_payer.setText(
            f"PROCEDER AU PAIEMENT  {total:,.0f} GNF".replace(",", " ")
        )

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================

    def selectionner_visite(self, code_visite: str) -> None:
        """Selectionne une visite dans le combo si disponible."""
        if not code_visite:
            return
        for i in range(self.combo_visite.count()):
            data = self.combo_visite.itemData(i)
            if isinstance(data, dict) and data.get("code_visite") == code_visite:
                self.combo_visite.setCurrentIndex(i)
                return
