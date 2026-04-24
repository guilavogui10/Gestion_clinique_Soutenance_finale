"""
vue_prescription_principale.py
--------------------------------
Vue principale Prescription.
Disposition : cards (3) â†’ bas : tableau gauche + panier droite.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QHeaderView, QFrame, QLabel, QGraphicsDropShadowEffect,
    QTableWidgetItem
)

# âœ… Import du widget prescription
from .vue_prescription_widget import PrescriptionWidget
from views.shared.theme_manager import theme_manager
from views.prescription.styles import PrescriptionStyles


# =============================================================================
# COMPOSANT : AnimatedFrame
# =============================================================================

class AnimatedFrame(QFrame):
    """Cadre arrondi avec effet d ombre et animation de survol."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_animation()

    def _setup_animation(self):
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self.shadow)

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(self.pos().x(), self.pos().y() - 5))
        self.shadow.setBlurRadius(25)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(self.pos().x(), self.pos().y() + 5))
        self.shadow.setBlurRadius(15)
        self.animation.start()
        super().leaveEvent(event)


# =============================================================================
# VUE PRINCIPALE
# =============================================================================

class PrescriptionView(QWidget):
    """
    Vue principale Prescription.

    Widgets publics :
        search_bar, btn_add, btn_notification, btn_export, btn_import

        card_jour.value_label     â†’ patients servis aujourd hui
        card_session.value_label  â†’ patients servis dans la session
        card_attente.value_label  â†’ patients en attente pharmacie

        frame_table               â†’ tableau gauche (stretch 3)
        table                     â†’ QTableWidget 5 colonnes
        widget_prescription       â†’ PrescriptionWidget droite (stretch 2)
    """

    VERT   = "#003f20"
    ORANGE = "#f39c12"
    BLEU   = "#3498db"

    def __init__(self, controleur=None, parent=None):
        super().__init__(parent)
        self.ctrl         = controleur
        self.code_session = None
        self._init_ui()
        self._connecter_signaux()

        # Appliquer le thème initial et écouter les changements
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # CONSTRUCTION
    # =========================================================================

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        self._setup_top_bar()
        self._setup_stats_section()
        self._setup_bottom_section()

    # =========================================================================
    # SIGNAUX
    # =========================================================================

    def _connecter_signaux(self):
        """Connecte les signaux de la vue."""
        # Recherche en temps rÃ©el
        self.search_bar.textChanged.connect(self._on_recherche)

        # SÃ©lection d'une ligne du tableau â†’ charger le patient dans le panier
        self.table.cellClicked.connect(self._on_ligne_selectionnee)

        # Validation prescription -> rafraichir cards + tableau
        if self.widget_prescription:
            self.widget_prescription.prescription_validee.connect(
                self._actualiser_apres_validation
            )

    # =========================================================================
    # BARRE DU HAUT
    # =========================================================================

    def apply_theme(self):
        """Applique le thème actif à tous les composants de la vue prescription."""
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_main']};")
        self.search_bar.setStyleSheet(PrescriptionStyles.search_bar())
        self.btn_add.setStyleSheet(PrescriptionStyles.button_primary())
        self.btn_add.setIcon(qta.icon("fa5s.plus-square", color=c['text_inverse']))
        round_btn = PrescriptionStyles.button_secondary()
        for btn, ico in [(self.btn_notification, "fa5s.bell"), (self.btn_export, "fa5s.file-export"), (self.btn_import, "fa5s.file-import")]:
            btn.setStyleSheet(round_btn)
            btn.setIcon(qta.icon(ico, color=c['primary']))
        for card, key in [(self.card_jour, 'primary'), (self.card_session, 'success'), (self.card_attente, 'warning')]:
            color = c[key]
            card.setStyleSheet(PrescriptionStyles.stat_card_style(color))
            card._icon_lbl.setPixmap(qta.icon(card._icon_name, color=color).pixmap(QSize(20, 20)))
            card._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;")
            card.value_label.setStyleSheet(f"font-size:28px; font-weight:bold; color:{color}; border:none;")
        self.frame_table.setStyleSheet(PrescriptionStyles.card())
        self.frame_table._icon_lbl.setPixmap(qta.icon(self.frame_table._icon_name, color=c['primary']).pixmap(QSize(16, 16)))
        self.frame_table._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;")
        self.frame_table._separator.setStyleSheet(f"background:{c['border_light']}; border:none;")
        self.table.setStyleSheet(PrescriptionStyles.table())
        self.table.verticalScrollBar().setStyleSheet(PrescriptionStyles.scrollbar())

    def _setup_top_bar(self):
        hbox = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(" Rechercher une prescription...")
        self.search_bar.setFixedHeight(45)

        self.btn_add = QPushButton(
            qta.icon("fa5s.plus-square", color="white"), " Nouvelle Prescription"
        )
        self.btn_add.setFixedHeight(45)
        self.btn_add.setMinimumWidth(180)
        self.btn_add.setCursor(Qt.PointingHandCursor)

        self.btn_notification = QPushButton(
            qta.icon("fa5s.bell", color=theme_manager.colors()['primary']), ""
        )
        self.btn_notification.setFixedSize(45, 45)
        self.btn_notification.setToolTip("Notifications")

        self.btn_export = QPushButton(
            qta.icon("fa5s.file-export", color=theme_manager.colors()['primary']), ""
        )
        self.btn_export.setFixedSize(45, 45)
        self.btn_export.setToolTip("Exporter")

        self.btn_import = QPushButton(
            qta.icon("fa5s.file-import", color=theme_manager.colors()['primary']), ""
        )
        self.btn_import.setFixedSize(45, 45)
        self.btn_import.setToolTip("Importer")

        hbox.addWidget(self.search_bar)
        hbox.addWidget(self.btn_add)
        hbox.addSpacing(10)
        hbox.addWidget(self.btn_notification)
        hbox.addWidget(self.btn_export)
        hbox.addWidget(self.btn_import)
        self.main_layout.addLayout(hbox)

    # =========================================================================
    # CARDS STATISTIQUES (3)
    # =========================================================================

    def _setup_stats_section(self):
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_jour = self._creer_stat_card(
            "Patients servis aujourd'hui", "0",
            "fa5s.calendar-day",          "primary"
        )
        self.card_session = self._creer_stat_card(
            "Total Session",              "0",
            "fa5s.prescription",          "success"
        )
        self.card_attente = self._creer_stat_card(
            "En Attente Pharmacie",       "0",
            "fa5s.hourglass-half",        "warning"
        )

        stats_layout.addWidget(self.card_jour)
        stats_layout.addWidget(self.card_session)
        stats_layout.addWidget(self.card_attente)
        self.main_layout.addLayout(stats_layout)

    def _creer_stat_card(self, titre: str, valeur: str,
                         icone: str, accent_key: str) -> AnimatedFrame:
        c = theme_manager.colors()
        couleur = c.get(accent_key, accent_key)
        card = AnimatedFrame()
        card.setFixedHeight(120)
        card._icon_name = icone
        card._accent_key = accent_key
        card.setStyleSheet(PrescriptionStyles.stat_card_style(couleur))
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icone, color=couleur).pixmap(QSize(20, 20)))
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        card._icon_lbl = icon_lbl
        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;")
        card._title_lbl = title_lbl
        header.addWidget(icon_lbl)
        header.addSpacing(8)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        value_lbl = QLabel(valeur)
        value_lbl.setStyleSheet(f"font-size:28px; font-weight:bold; color:{couleur}; border:none;")
        value_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_lbl)
        layout.addStretch()

        card.value_label = value_lbl
        return card

    # =========================================================================
    # SECTION BAS : TABLEAU (gauche) + PANIER PRESCRIPTION (droite)
    # =========================================================================

    def _setup_bottom_section(self):
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        # â”€â”€ Tableau â€” gauche stretch 3 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self.frame_table = self._creer_cadre_arrondi(
            "Liste des Prescriptions", "fa5s.prescription"
        )
        self._setup_table()

        # â”€â”€ PrescriptionWidget â€” droite stretch 2 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # âœ… Instanciation avec injection du contrÃ´leur (Architecture MVC)
        self.widget_prescription = PrescriptionWidget(
            prescription_ctrl=self.ctrl
        )
        # Le frame_panier du squelette est remplacÃ© directement par le widget
        self.frame_panier = self.widget_prescription

        bottom_layout.addWidget(self.frame_table,         3)
        bottom_layout.addWidget(self.widget_prescription, 2)
        self.main_layout.addLayout(bottom_layout)

    # â”€â”€â”€ Cadre gÃ©nÃ©rique arrondi â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _creer_cadre_arrondi(self, titre: str, icone_name: str) -> AnimatedFrame:
        c = theme_manager.colors()
        frame = AnimatedFrame()
        frame._icon_name = icone_name
        frame.setStyleSheet(PrescriptionStyles.card())
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icone_name, color=c['primary']).pixmap(QSize(16, 16)))
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        frame._icon_lbl = icon_lbl
        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;")
        frame._title_lbl = title_lbl
        header.addWidget(icon_lbl)
        header.addSpacing(6)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{c['border_light']}; border:none;")
        frame._separator = sep
        layout.addWidget(sep)

        return frame

    # â”€â”€â”€ Tableau prescriptions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _setup_table(self):
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Consultation", "Patient", "Nb produits", "Total", "Date"
        ])
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._apply_scrollbar_style(self.table)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.table.setStyleSheet(PrescriptionStyles.table())
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setAlternatingRowColors(True)
        self.frame_table.layout().addWidget(self.table)

    def _apply_scrollbar_style(self, widget):
        widget.verticalScrollBar().setStyleSheet(PrescriptionStyles.scrollbar())

    # =========================================================================
    # Ã‰VÃ‰NEMENTS
    # =========================================================================

    def _on_ligne_selectionnee(self, row: int, col: int) -> None:
        """
        SÃ©lection d'une ligne du tableau â†’ charge le patient
        dans le widget prescription.

        Les donnÃ©es patient sont stockÃ©es dans la colonne 0 (userData).
        """
        item = self.table.item(row, 0)
        if not item:
            return

        patient_data = item.data(Qt.UserRole)
        if not patient_data:
            return

        # âœ… Charger le patient dans le widget prescription
        self.widget_prescription.charger_patient(patient_data)

    def _on_recherche(self, texte: str) -> None:
        """Recherche en temps rÃ©el dans le tableau."""
        if not self.ctrl or not self.code_session:
            return

        resultats = self.ctrl.lister_groupes_par_consultation(self.code_session)
        filtre = texte.strip().lower()
        if len(filtre) >= 2:
            resultats = [
                r for r in resultats
                if filtre in str(r.get('code_consultation', '')).lower()
                or filtre in f"{r.get('patient_prenom', '')} {r.get('patient_nom', '')}".lower()
            ]

        self._remplir_tableau(resultats)

    def _actualiser_apres_validation(self) -> None:
        """Rafraichit cards + tableau apres validation d'une prescription."""
        if not self.ctrl or not self.code_session:
            return
        self.charger_donnees(self.code_session)

    # =========================================================================
    # REMPLISSAGE TABLEAU
    # =========================================================================

    def _remplir_tableau(self, prescriptions: list) -> None:
        """
        Remplit le tableau avec la liste des prescriptions.

        Chaque ligne stocke le dict patient complet en UserRole
        sur la cellule Code (col 0) pour pouvoir le rÃ©cupÃ©rer
        au clic et l'envoyer au widget_prescription.

        Args:
            prescriptions: Liste de dicts regroupÃ©s par consultation
        """
        self.table.setRowCount(0)

        for p in prescriptions:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Col 0 â€” Code consultation + userData patient
            item_code = QTableWidgetItem(
                str(p.get('code_consultation', '') or "")
            )
            # Stocker les donnÃ©es patient pour _on_ligne_selectionnee
            patient_data = {
                'nom'              : p.get('patient_nom', ''),
                'prenom'           : p.get('patient_prenom', ''),
                'code_visite'      : str(p.get('code_visite', '') or ''),
                'code_consultation': str(p.get('code_consultation', '') or ''),
                'code_session'     : str(self.code_session or ''),
            }
            item_code.setData(Qt.UserRole, patient_data)
            item_code.setFlags(item_code.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, item_code)

            # Col 1 â€” Patient
            nom_complet = f"{p.get('patient_prenom', '')} {p.get('patient_nom', '')}".strip()
            item_patient = QTableWidgetItem(nom_complet or "â€”")
            item_patient.setFlags(item_patient.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, item_patient)

            # Col 2 â€” Nb produits
            item_qte = QTableWidgetItem(str(p.get('nb_produits', '') or "â€”"))
            item_qte.setFlags(item_qte.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, item_qte)

            # Col 3 â€” Total
            total_val = p.get('total_montant', None)
            total_str = f"{float(total_val):.2f}" if isinstance(total_val, (int, float)) else str(total_val or "â€”")
            item_prix = QTableWidgetItem(total_str)
            item_prix.setFlags(item_prix.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, item_prix)

            # Col 4 â€” Date consultation
            date_val = p.get('date_consultation', None)
            date_str = (
                date_val.strftime("%d/%m/%Y")
                if hasattr(date_val, "strftime") and date_val
                else str(date_val or "â€”")
            )
            item_date = QTableWidgetItem(date_str)
            item_date.setFlags(item_date.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, item_date)

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================

    def charger_donnees(self, code_session: str) -> None:
        """
        Point d'entrÃ©e depuis le dashboard.
        Charge les donnÃ©es de la session dans toute la vue.

        Args:
            code_session: Code de la session active
        """
        self.code_session = code_session

        if not self.ctrl:
            return

        # â”€â”€ Cards statistiques â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self.card_jour.value_label.setText(
            str(self.ctrl.obtenir_nombre_prescriptions_aujourd_hui(code_session))
        )
        self.card_session.value_label.setText(
            str(self.ctrl.obtenir_nombre_total_session(code_session))
        )
        self.card_attente.value_label.setText(
            str(self.ctrl.obtenir_nombre_en_attente(code_session))
        )

        # â”€â”€ Tableau â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        prescriptions = self.ctrl.lister_groupes_par_consultation(code_session)
        self._remplir_tableau(prescriptions)

        # â”€â”€ Widget prescription (produits + session) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # âœ… Charger les produits disponibles dans le combo du widget
        self.widget_prescription.charger_donnees(code_session)



