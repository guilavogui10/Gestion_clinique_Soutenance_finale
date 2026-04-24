"""
Vue VueDetailFacture - Vue détaillée d'une facture fournisseur.
Responsabilité : Afficher toutes les informations d'une facture + actions.
Pattern : Component, Composite.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QMessageBox
)

from ..styles.facture_styles import FactureStyles


class VueDetailFacture(QWidget):
    """
    Vue détaillée d'une facture fournisseur.

    Sections :
    1. En-tête avec bouton retour
    2. Informations facture (code, date, montant, mode, téléphone)
    3. Informations fournisseur (nom entreprise, téléphone, adresse)
    4. Liste des produits (designation, qté, prix, sous-total, expiration)
    5. Actions (Imprimer, Supprimer)
    """

    def __init__(self, facture_ctrl: Any, panier_ctrl: Any,
                 on_retour: Callable,
                 parent: Optional[QWidget] = None):
        """
        Args:
            facture_ctrl: Contrôleur facture fournisseur
            panier_ctrl:  Contrôleur panier
            on_retour:    Callback pour retourner à la liste
            parent:       Widget parent Qt
        """
        super().__init__(parent)
        self.facture_ctrl = facture_ctrl
        self.panier_ctrl  = panier_ctrl
        self.on_retour    = on_retour
        self.logger       = logging.getLogger(__name__)

        self.code_facture  = None
        self.data_facture  = None

        self.setStyleSheet("background:transparent;")
        self._setup_ui()

    # =========================================================================
    # CONSTRUCTION UI
    # =========================================================================

    def _setup_ui(self) -> None:
        """Construit le squelette de l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)

        layout.addLayout(self._construire_header())

        self.container = QWidget()
        self.container.setStyleSheet(
            f"background:{FactureStyles.BLANC}; border-radius:12px;"
        )
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(16, 16, 16, 16)
        self.container_layout.setSpacing(12)

        layout.addWidget(self.container)
        layout.addStretch()

    def _construire_header(self) -> QHBoxLayout:
        """Construit l'en-tête avec bouton retour et titre."""
        lay = QHBoxLayout()

        btn_retour = QPushButton(
            qta.icon("fa5s.arrow-left", color=FactureStyles.VERT_PRINCIPAL),
            "  Retour"
        )
        btn_retour.setFixedHeight(32)
        btn_retour.setCursor(Qt.PointingHandCursor)
        btn_retour.setStyleSheet(
            f"QPushButton{{background:{FactureStyles.BLANC};"
            f"color:{FactureStyles.VERT_PRINCIPAL};"
            f"border:1px solid {FactureStyles.VERT_PRINCIPAL};"
            f"border-radius:8px; font-size:11px; font-weight:600; padding:0 12px;}}"
            f"QPushButton:hover{{background:{FactureStyles.VERT_CLAIR};}}"
        )
        btn_retour.clicked.connect(self.on_retour)

        titre = QLabel("Détail de la facture")
        titre.setStyleSheet(
            f"color:#1F2937; font-size:14px; font-weight:700; background:transparent;"
        )

        lay.addWidget(btn_retour)
        lay.addSpacing(10)
        lay.addWidget(titre)
        lay.addStretch()
        return lay

    # =========================================================================
    # CHARGEMENT
    # =========================================================================

    def charger(self, code_facture: str) -> None:
        """
        Charge et affiche les données complètes d'une facture.

        Args:
            code_facture: Code de la facture à afficher
        """
        self.code_facture = code_facture
        self.logger.info(f"Chargement facture {code_facture}")

        self._vider_container()

        try:
            self.data_facture = self.facture_ctrl.obtenir_facture_complete(
                code_facture
            )

            if not self.data_facture:
                self._afficher_erreur("Facture introuvable")
                return

            entete = self.data_facture.get('entete', {})
            lignes = self.data_facture.get('lignes', [])

            self._creer_section_facture(entete)
            self._creer_section_fournisseur(entete)
            self._creer_section_produits(lignes)
            self._creer_section_actions()

        except Exception as e:
            self.logger.error(f"Erreur chargement facture: {e}", exc_info=True)
            self._afficher_erreur(f"Erreur : {e}")

    # =========================================================================
    # SECTIONS
    # =========================================================================

    def _creer_section_facture(self, entete: Dict[str, Any]) -> None:
        """Section 1 : informations de la facture."""
        section = self._creer_cadre("Informations Facture", "fa5s.file-invoice")

        # Code
        self._ajouter_ligne_info(
            section, "Code",
            entete.get('code_facture_four', '—'),
            "fa5s.hashtag"
        )

        # Date
        date_val = entete.get('date_facture_four')
        if isinstance(date_val, datetime):
            date_str = date_val.strftime("%d/%m/%Y à %H:%M")
        else:
            date_str = str(date_val) if date_val else "—"
        self._ajouter_ligne_info(section, "Date", date_str, "fa5s.calendar-alt")

        # Montant — insensible à la casse BDD (Montant_total vs montant_total)
        montant = entete.get('Montant_total') or entete.get('montant_total') or 0
        montant_fmt = f"{int(montant):,}".replace(",", " ") + " GNF"
        self._ajouter_ligne_info(
            section, "Montant Total", montant_fmt, "fa5s.coins",
            couleur=FactureStyles.VERT_PRINCIPAL, gras=True
        )

        # Mode de paiement
        mode = entete.get('mode_payement') or '—'
        self._ajouter_ligne_info(
            section, "Mode de paiement",
            mode.capitalize(),
            "fa5s.credit-card"
        )

        # Téléphone
        self._ajouter_ligne_info(
            section, "Téléphone",
            entete.get('telephone', '—'),
            "fa5s.phone"
        )

        self.container_layout.addWidget(section)

    def _creer_section_fournisseur(self, entete: Dict[str, Any]) -> None:
        """Section 2 : informations du fournisseur."""
        section = self._creer_cadre("Fournisseur", "fa5s.truck")

        # Nom entreprise — la table fournisseurs utilise nom_entreprise
        nom = entete.get('fournisseur_nom', '—')
        self._ajouter_ligne_info(
            section, "Entreprise", nom,
            "fa5s.building", gras=True
        )

        # Téléphone fournisseur
        self._ajouter_ligne_info(
            section, "Téléphone",
            entete.get('fournisseur_telephone', '—'),
            "fa5s.phone"
        )

        # Adresse
        self._ajouter_ligne_info(
            section, "Adresse",
            entete.get('fournisseur_adresse', '—'),
            "fa5s.map-marker-alt"
        )

        self.container_layout.addWidget(section)

    def _creer_section_produits(self, lignes: list) -> None:
        """Section 3 : liste des produits de la facture."""
        section = self._creer_cadre(
            f"Produits ({len(lignes)})", "fa5s.boxes"
        )

        if not lignes:
            lbl = QLabel("Aucun produit dans cette facture")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"color:{FactureStyles.GRIS_TEXTE}; font-size:11px; padding:20px;"
            )
            section.layout().addWidget(lbl)
        else:
            for ligne in lignes:
                section.layout().addWidget(
                    self._creer_carte_produit(ligne)
                )

        self.container_layout.addWidget(section)

    def _creer_section_actions(self) -> None:
        """Section 4 : boutons Imprimer et Supprimer."""
        lay = QHBoxLayout()
        lay.setSpacing(10)

        btn_imprimer = QPushButton(
            qta.icon("fa5s.print", color=FactureStyles.BLANC), "  Imprimer"
        )
        btn_imprimer.setFixedHeight(40)
        btn_imprimer.setCursor(Qt.PointingHandCursor)
        btn_imprimer.setStyleSheet(
            f"QPushButton{{background:{FactureStyles.BLEU_SOFT};"
            f"color:{FactureStyles.BLANC}; border-radius:10px;"
            f"font-size:12px; font-weight:600; border:none;}}"
            f"QPushButton:hover{{background:#2563EB;}}"
        )
        btn_imprimer.clicked.connect(self._imprimer_facture)

        btn_supprimer = QPushButton(
            qta.icon("fa5s.trash", color=FactureStyles.BLANC), "  Supprimer"
        )
        btn_supprimer.setFixedHeight(40)
        btn_supprimer.setCursor(Qt.PointingHandCursor)
        btn_supprimer.setStyleSheet(
            f"QPushButton{{background:{FactureStyles.ROUGE_SOFT};"
            f"color:{FactureStyles.BLANC}; border-radius:10px;"
            f"font-size:12px; font-weight:600; border:none;}}"
            f"QPushButton:hover{{background:#DC2626;}}"
        )
        btn_supprimer.clicked.connect(self._supprimer_facture)

        lay.addWidget(btn_imprimer)
        lay.addWidget(btn_supprimer)
        self.container_layout.addLayout(lay)

    # =========================================================================
    # COMPOSANTS RÉUTILISABLES
    # =========================================================================

    def _creer_cadre(self, titre: str, icone: str) -> QFrame:
        """
        Crée un cadre avec titre + icône.

        Args:
            titre: Texte du titre
            icone: Nom de l'icône qtawesome

        Returns:
            QFrame: Cadre configuré avec layout vertical
        """
        cadre = QFrame()
        cadre.setStyleSheet(
            f"QFrame{{background:{FactureStyles.GRIS_FOND}; border-radius:10px;"
            f"border:1px solid {FactureStyles.GRIS_CLAIR};}}"
        )
        layout = QVBoxLayout(cadre)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Titre
        titre_lay = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(
            qta.icon(icone, color=FactureStyles.VERT_PRINCIPAL).pixmap(QSize(14, 14))
        )
        ic.setStyleSheet("background:transparent;")

        lbl_titre = QLabel(titre)
        lbl_titre.setStyleSheet(
            f"color:#1F2937; font-size:12px; font-weight:700; background:transparent;"
        )

        titre_lay.addWidget(ic)
        titre_lay.addSpacing(6)
        titre_lay.addWidget(lbl_titre)
        titre_lay.addStretch()
        layout.addLayout(titre_lay)

        return cadre

    def _ajouter_ligne_info(self, parent: QFrame, label: str, valeur: str,
                            icone: str,
                            couleur: str = FactureStyles.GRIS_TEXTE,
                            gras: bool = False) -> None:
        """
        Ajoute une ligne [icône | label | valeur] dans un cadre.

        Args:
            parent:  Cadre cible
            label:   Texte du label
            valeur:  Valeur à afficher
            icone:   Icône qtawesome
            couleur: Couleur icône + valeur
            gras:    Si True, valeur en gras
        """
        ligne = QHBoxLayout()
        ligne.setSpacing(8)

        ic = QLabel()
        ic.setPixmap(qta.icon(icone, color=couleur).pixmap(QSize(11, 11)))
        ic.setStyleSheet("background:transparent;")

        lbl = QLabel(f"{label} :")
        lbl.setFixedWidth(130)
        lbl.setStyleSheet(
            f"color:{FactureStyles.GRIS_TEXTE}; font-size:11px; background:transparent;"
        )

        val = QLabel(str(valeur) if valeur else "—")
        val.setWordWrap(True)
        val.setStyleSheet(
            f"color:{couleur}; font-size:11px; "
            f"font-weight:{'700' if gras else '400'}; background:transparent;"
        )

        ligne.addWidget(ic)
        ligne.addWidget(lbl)
        ligne.addWidget(val, 1)
        parent.layout().addLayout(ligne)

    def _creer_carte_produit(self, ligne: Dict[str, Any]) -> QFrame:
        """
        Crée une carte produit à hauteur dynamique.

        ✅ Correction : suppression du setFixedHeight(90) qui tronquait
        le contenu quand la désignation était longue.

        Args:
            ligne: Dictionnaire données d'une ligne panier
        """
        carte = QFrame()
        carte.setStyleSheet(
            f"QFrame{{background:{FactureStyles.BLANC}; border-radius:8px;"
            f"border:1px solid {FactureStyles.GRIS_CLAIR};}}"
        )

        layout = QVBoxLayout(carte)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Ligne 1 : Désignation
        designation = ligne.get('designation', '—')
        lbl_desig = QLabel(designation)
        lbl_desig.setWordWrap(True)
        lbl_desig.setStyleSheet(
            f"color:#1F2937; font-size:11px; font-weight:700; background:transparent;"
        )
        layout.addWidget(lbl_desig)

        # Ligne 2 : Qté | Prix | Sous-total
        # Note : le calcul sous_total est présentatif uniquement
        # (la valeur métier vient de la BDD via le contrôleur)
        quantite   = ligne.get('quantite_four', 0) or 0
        prix       = ligne.get('prix_unitaire', 0) or 0
        sous_total = quantite * prix

        info_lay = QHBoxLayout()
        info_lay.setSpacing(10)

        for ic_nom, texte, couleur in [
            ("fa5s.sort-numeric-up", f"Qté : {quantite}",
             FactureStyles.GRIS_TEXTE),
            ("fa5s.tag", f"PU : {int(prix):,}".replace(",", " ") + " GNF",
             FactureStyles.GRIS_TEXTE),
        ]:
            ic = QLabel()
            ic.setPixmap(
                qta.icon(ic_nom, color=couleur).pixmap(QSize(10, 10))
            )
            ic.setStyleSheet("background:transparent;")
            lbl = QLabel(texte)
            lbl.setStyleSheet(
                f"color:{couleur}; font-size:10px; background:transparent;"
            )
            info_lay.addWidget(ic)
            info_lay.addWidget(lbl)

        info_lay.addStretch()

        # Sous-total mis en évidence
        ic_total = QLabel()
        ic_total.setPixmap(
            qta.icon("fa5s.coins",
                     color=FactureStyles.VERT_PRINCIPAL).pixmap(QSize(10, 10))
        )
        ic_total.setStyleSheet("background:transparent;")
        lbl_total = QLabel(f"{int(sous_total):,}".replace(",", " ") + " GNF")
        lbl_total.setStyleSheet(
            f"color:{FactureStyles.VERT_PRINCIPAL}; font-size:10px; "
            f"font-weight:700; background:transparent;"
        )
        info_lay.addWidget(ic_total)
        info_lay.addWidget(lbl_total)

        layout.addLayout(info_lay)

        # Ligne 3 : Date expiration (optionnelle)
        date_exp = ligne.get('date_expiration')
        if date_exp:
            date_str = (
                date_exp.strftime("%d/%m/%Y")
                if isinstance(date_exp, datetime)
                else str(date_exp)
            )
            exp_lay = QHBoxLayout()
            exp_lay.setSpacing(5)

            ic_exp = QLabel()
            ic_exp.setPixmap(
                qta.icon("fa5s.calendar-times",
                         color=FactureStyles.ORANGE_SOFT).pixmap(QSize(10, 10))
            )
            ic_exp.setStyleSheet("background:transparent;")

            lbl_exp = QLabel(f"Expire le {date_str}")
            lbl_exp.setStyleSheet(
                f"color:{FactureStyles.ORANGE_SOFT}; font-size:9px; "
                f"background:transparent;"
            )
            exp_lay.addWidget(ic_exp)
            exp_lay.addWidget(lbl_exp)
            exp_lay.addStretch()
            layout.addLayout(exp_lay)

        return carte

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def _imprimer_facture(self) -> None:
        """
        Génère un aperçu d'impression HTML de la facture.
        Utilise QTextDocument + QPrinter pour une impression native.
        """
        if not self.data_facture:
            QMessageBox.warning(self, "Impression", "Aucune facture chargée.")
            return

        try:
            from PySide6.QtGui import QTextDocument
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog

            entete = self.data_facture.get('entete', {})
            lignes = self.data_facture.get('lignes', [])

            montant = (entete.get('Montant_total')
                       or entete.get('montant_total') or 0)
            date_val = entete.get('date_facture_four')
            date_str = (
                date_val.strftime("%d/%m/%Y à %H:%M")
                if isinstance(date_val, datetime) else str(date_val or "—")
            )

            # Construction du HTML
            lignes_html = "".join([
                f"<tr>"
                f"<td>{l.get('designation', '—')}</td>"
                f"<td align='center'>{l.get('quantite_four', 0)}</td>"
                f"<td align='right'>{int(l.get('prix_unitaire', 0)):,} GNF</td>"
                f"<td align='right'><b>{int((l.get('quantite_four', 0) or 0) * (l.get('prix_unitaire', 0) or 0)):,} GNF</b></td>"
                f"</tr>"
                for l in lignes
            ])

            html = f"""
            <html><body style='font-family:Arial; font-size:12px;'>
            <h2 style='color:#003f20;'>Facture Fournisseur — {entete.get('code_facture_four','')}</h2>
            <p><b>Fournisseur :</b> {entete.get('fournisseur_nom','—')}</p>
            <p><b>Date :</b> {date_str} &nbsp;&nbsp;
               <b>Mode :</b> {(entete.get('mode_payement') or '—').capitalize()}</p>
            <hr/>
            <table width='100%' border='1' cellspacing='0' cellpadding='6'
                   style='border-collapse:collapse;'>
              <thead style='background:#e8f5ee;'>
                <tr>
                  <th align='left'>Produit</th>
                  <th>Qté</th>
                  <th align='right'>Prix unit.</th>
                  <th align='right'>Sous-total</th>
                </tr>
              </thead>
              <tbody>{lignes_html}</tbody>
            </table>
            <p align='right' style='font-size:14px;'>
              <b>Total : {int(montant):,} GNF</b>
            </p>
            </body></html>
            """

            printer = QPrinter(QPrinter.HighResolution)
            dlg = QPrintDialog(printer, self)
            if dlg.exec() == QPrintDialog.Accepted:
                doc = QTextDocument()
                doc.setHtml(html)
                doc.print_(printer)
                self.logger.info(f"Facture {self.code_facture} imprimée")

        except Exception as e:
            self.logger.error(f"Erreur impression: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur impression", str(e))

    def _supprimer_facture(self) -> None:
        """Supprime la facture après confirmation de l'utilisateur."""
        reponse = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Voulez-vous vraiment supprimer la facture {self.code_facture} ?\n\n"
            f"Toutes les lignes seront supprimées et le stock sera ajusté.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reponse != QMessageBox.Yes:
            return

        try:
            ok, msg = self.facture_ctrl.supprimer_facture(self.code_facture)
            if ok:
                self.logger.info(f"Facture {self.code_facture} supprimée")
                QMessageBox.information(self, "Succès", msg)
                self.on_retour()
            else:
                QMessageBox.warning(self, "Erreur", msg)
        except Exception as e:
            self.logger.error(f"Erreur suppression facture: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Erreur inattendue : {e}")

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _vider_container(self) -> None:
        """Vide le conteneur principal avant rechargement."""
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _afficher_erreur(self, message: str) -> None:
        """Affiche un message d'erreur centré dans le conteneur."""
        lay = QHBoxLayout()
        lay.setSpacing(8)

        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.exclamation-circle",
                     color=FactureStyles.ROUGE_SOFT).pixmap(QSize(16, 16))
        )
        ic.setStyleSheet("background:transparent;")

        lbl = QLabel(message)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"color:{FactureStyles.ROUGE_SOFT}; font-size:12px; padding:40px;"
        )

        lay.addStretch()
        lay.addWidget(ic)
        lay.addWidget(lbl)
        lay.addStretch()
        self.container_layout.addLayout(lay)