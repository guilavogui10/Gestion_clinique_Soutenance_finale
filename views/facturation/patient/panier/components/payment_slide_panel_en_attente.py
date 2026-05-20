"""
Composant PaymentSlidePanel - Interface de paiement fournisseur glissante.
Responsabilité : Affichage des produits et formulaire de paiement.
Design fidèle à l'image de référence. Fond transparent, thème dynamique.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QButtonGroup, QRadioButton, QSizePolicy
)
from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox


# =============================================================================
# CARD RÉSEAU MOBILE — logo coloré + nom + radio centré en bas
# =============================================================================

class NetworkCard(QFrame):
    """Card cliquable pour chaque réseau mobile (logo + nom + radio)."""

    def __init__(self, name: str, bg_color: str, text_color: str = "white", parent=None):
        super().__init__(parent)
        self.name = name
        self._bg_color = bg_color
        self._text_color = text_color
        self._selected = False

        self.setFixedSize(90, 90)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._apply_style()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 8, 6, 6)
        lay.setSpacing(3)
        lay.setAlignment(Qt.AlignCenter)

        # Icône réseau (carré coloré avec initiales)
        self.icon_frame = QFrame()
        self.icon_frame.setFixedSize(40, 30)
        self.icon_frame.setStyleSheet(
            f"background: {bg_color}; border-radius: 8px;"
        )
        icon_lay = QHBoxLayout(self.icon_frame)
        icon_lay.setContentsMargins(0, 0, 0, 0)
        abbr = QLabel(name[:2].upper())
        abbr.setAlignment(Qt.AlignCenter)
        abbr.setStyleSheet(
            f"color: {text_color}; font-weight: 800; font-size: 11px; background: transparent;"
        )
        icon_lay.addWidget(abbr)
        lay.addWidget(self.icon_frame, 0, Qt.AlignCenter)

        # Nom court
        short = name.split()[0]
        name_lbl = QLabel(short)
        name_lbl.setAlignment(Qt.AlignCenter)
        c = theme_manager.colors()
        name_lbl.setStyleSheet(
            f"font-size: 10px; font-weight: 600; color: {c['text_primary']}; background: transparent;"
        )
        lay.addWidget(name_lbl)

        # Radio
        self.radio = QRadioButton()
        self.radio.setStyleSheet("QRadioButton::indicator { width: 14px; height: 14px; }")
        self.radio.toggled.connect(self._on_toggle)
        lay.addWidget(self.radio, 0, Qt.AlignCenter)

    def _apply_style(self):
        c = theme_manager.colors()
        if self._selected:
            self.setStyleSheet(
                f"QFrame {{ background: {c['bg_card']}; border: 2px solid {self._bg_color};"
                f" border-radius: 12px; }}"
            )
        else:
            self.setStyleSheet(
                f"QFrame {{ background: {c['bg_card']}; border: 1px solid {c['border']};"
                f" border-radius: 12px; }}"
            )

    def _on_toggle(self, checked):
        self._selected = checked
        self._apply_style()

    def mousePressEvent(self, event):
        self.radio.setChecked(True)
        super().mousePressEvent(event)

    def set_checked(self, val: bool):
        self.radio.setChecked(val)


# =============================================================================
# PANNEAU PRINCIPAL
# =============================================================================

class PaymentSlidePanel(QFrame):
    """
    Panneau de paiement fournisseur — fond transparent, thème dynamique.
    S'intègre dans le panel_payment_overlay de GestionProduitsView.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.facture_data = None
        self.produits_data = []
        self.fournisseur_data = None
        self._visible = False
        self._animation = None

        self.setAttribute(Qt.WA_StyledBackground, True)
        # Fond entièrement transparent — hérite du parent
        self.setStyleSheet("QFrame { background: transparent; border: none; }")

        self._init_ui()
        self.hide()

    # -------------------------------------------------------------------------
    # CONSTRUCTION UI
    # -------------------------------------------------------------------------

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)   # marges réduites
        root.setSpacing(8)

        # ── Header compact
        self._build_header(root)

        # ── Corps : colonne gauche (70 %) + droite (30 %)
        body = QHBoxLayout()
        body.setSpacing(12)

        left_scroll = self._build_left_section()
        body.addWidget(left_scroll, 7)

        right_widget = self._build_right_section()
        body.addWidget(right_widget, 3)

        root.addLayout(body, 1)   # stretch=1 → prend tout l'espace restant

    # ── Header ───────────────────────────────────────────────────────────────

    def _build_header(self, layout):
        c = theme_manager.colors()
        header = QFrame()
        header.setFixedHeight(46)          # compact
        header.setAttribute(Qt.WA_StyledBackground, True)
        header.setStyleSheet(
            f"QFrame {{ background: {c['bg_card']}; border-radius: 12px;"
            f" border: 1px solid {c['border']}; }}"
        )

        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(10, 6, 10, 6)
        hlay.setSpacing(10)

        # Bouton retour
        btn_back = QPushButton(qta.icon("fa5s.arrow-left", color=c['primary']), "")
        btn_back.setFixedSize(32, 32)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(
            f"QPushButton {{ background: {c['bg_card']}; border: 1px solid {c['border']};"
            f" border-radius: 8px; }}"
            f"QPushButton:hover {{ background: {c['primary']}20; border: 1px solid {c['primary']}; }}"
        )
        btn_back.clicked.connect(self.close_panel)
        hlay.addWidget(btn_back)

        # Titre + sous-titre
        title_col = QVBoxLayout()
        title_col.setSpacing(0)

        title = QLabel("Paiement Fournisseur")
        title.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {c['text_primary']};"
            " background: transparent; border: none;"
        )
        subtitle = QLabel("Régler la facture d'un fournisseur")
        subtitle.setStyleSheet(
            f"font-size: 10px; color: {c['text_muted']};"
            " background: transparent; border: none;"
        )
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        hlay.addLayout(title_col)

        hlay.addStretch()

        # Badge référence (dynamique)
        self.lbl_reference = self._badge_label(
            qta.icon("fa5s.file-invoice", color=c['text_muted']), ""
        )
        hlay.addWidget(self.lbl_reference)

        # Badge date (dynamique)
        self.lbl_date = self._badge_label(
            qta.icon("fa5s.calendar-alt", color=c['text_muted']), ""
        )
        hlay.addWidget(self.lbl_date)

        layout.addWidget(header)

    def _badge_label(self, icon, text: str) -> QWidget:
        """Badge icône + texte pour l'en-tête."""
        c = theme_manager.colors()
        frame = QFrame()
        frame.setAttribute(Qt.WA_StyledBackground, True)
        frame.setStyleSheet(
            f"QFrame {{ background: {c['bg_card']}; border: 1px solid {c['border']};"
            f" border-radius: 8px; }}"
        )
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(6)

        ico_lbl = QLabel()
        ico_lbl.setPixmap(icon.pixmap(14, 14))
        ico_lbl.setStyleSheet("background: transparent; border: none;")

        txt_lbl = QLabel(text)
        txt_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_primary']};"
            " background: transparent; border: none;"
        )
        txt_lbl.setObjectName("badge_text")

        lay.addWidget(ico_lbl)
        lay.addWidget(txt_lbl)
        return frame

    # ── Section gauche ────────────────────────────────────────────────────────

    def _build_left_section(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.verticalScrollBar().setStyleSheet(self._scrollbar_style())

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(10)

        # Card fournisseur
        self.fournisseur_card = self._build_fournisseur_card()
        lay.addWidget(self.fournisseur_card)

        # Tableau produits
        lay.addWidget(self._build_products_table(), 1)

        # Note info
        lay.addWidget(self._build_note())

        scroll.setWidget(container)
        return scroll

    def _build_fournisseur_card(self) -> QFrame:
        c = theme_manager.colors()
        card = QFrame()
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setStyleSheet(
            f"QFrame {{ background: {c['bg_card']}; border: 1px solid {c['border']};"
            f" border-radius: 12px; }}"
        )

        lay = QHBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(14)

        # Icône fournisseur
        icon_frame = QFrame()
        icon_frame.setFixedSize(54, 54)
        icon_frame.setAttribute(Qt.WA_StyledBackground, True)
        icon_frame.setStyleSheet(
            f"background: {c['primary']}15; border-radius: 12px;"
        )
        icon_lay = QVBoxLayout(icon_frame)
        icon_lay.setContentsMargins(0, 0, 0, 0)
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.store", color=c['primary']).pixmap(28, 28))
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet("background: transparent;")
        icon_lay.addWidget(ico)
        lay.addWidget(icon_frame)

        # Infos fournisseur
        info = QVBoxLayout()
        info.setSpacing(3)

        hint = QLabel("Nom du fournisseur")
        hint.setStyleSheet(
            f"font-size: 10px; color: {c['text_muted']}; background: transparent;"
        )

        self.lbl_fournisseur_nom = QLabel("")
        self.lbl_fournisseur_nom.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {c['primary']}; background: transparent;"
        )

        self.lbl_fournisseur_num = QLabel("")
        self.lbl_fournisseur_num.setStyleSheet(
            f"font-size: 10px; color: {c['text_muted']}; background: transparent;"
        )

        # Badge code fournisseur
        self.badge_code = QLabel("")
        self.badge_code.setStyleSheet(
            f"background: {c['primary']}15; color: {c['primary']}; font-weight: 700;"
            f" font-size: 10px; border-radius: 6px; padding: 2px 8px;"
        )

        info.addWidget(hint)
        info.addWidget(self.lbl_fournisseur_nom)
        info.addWidget(self.badge_code)
        lay.addLayout(info)

        lay.addStretch()

        # Contact
        contact = QVBoxLayout()
        contact.setSpacing(4)
        self._row_tel    = self._info_row("fa5s.phone",          "")
        self._row_email  = self._info_row("fa5s.envelope",       "")
        self._row_addr   = self._info_row("fa5s.map-marker-alt", "")
        contact.addWidget(self._row_tel)
        contact.addWidget(self._row_email)
        contact.addWidget(self._row_addr)
        lay.addLayout(contact)

        return card

    def _info_row(self, icon_name: str, text: str) -> QWidget:
        c = theme_manager.colors()
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        ico = QLabel()
        ico.setPixmap(qta.icon(icon_name, color=c['text_muted']).pixmap(12, 12))
        ico.setStyleSheet("background: transparent;")

        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 11px; color: {c['text_secondary']}; background: transparent;")
        lbl.setObjectName("val")

        lay.addWidget(ico)
        lay.addWidget(lbl)
        lay.addStretch()
        return w

    def _build_products_table(self) -> QFrame:
        c = theme_manager.colors()
        frame = QFrame()
        frame.setAttribute(Qt.WA_StyledBackground, True)
        frame.setStyleSheet(
            f"QFrame {{ background: {c['bg_card']}; border: 1px solid {c['border']};"
            f" border-radius: 12px; }}"
        )

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        title = QLabel("Produits de la facture")
        title.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {c['text_primary']}; background: transparent;"
        )
        lay.addWidget(title)

        self.table_produits = QTableWidget(0, 5)
        self.table_produits.setHorizontalHeaderLabels(
            ["#", "Produit", "Quantité", "Prix unitaire", "Montant"]
        )
        self.table_produits.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_produits.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_produits.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_produits.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_produits.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_produits.verticalHeader().setVisible(False)
        self.table_produits.setAlternatingRowColors(True)
        self.table_produits.setSelectionMode(QTableWidget.NoSelection)
        self.table_produits.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_produits.setStyleSheet(f"""
            QTableWidget {{
                background: transparent;
                border: 1px solid {c['border']};
                border-radius: 8px;
                gridline-color: {c['border']};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background: {c['bg_main']};
                color: {c['text_muted']};
                font-weight: 600;
                font-size: 10px;
                text-transform: uppercase;
                padding: 6px;
                border: none;
                border-bottom: 1px solid {c['border']};
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                color: {c['text_primary']};
            }}
            QTableWidget::item:alternate {{
                background: {c['bg_main']};
            }}
        """)
        lay.addWidget(self.table_produits, 1)

        # Total
        tot_lay = QHBoxLayout()
        tot_lay.setContentsMargins(4, 4, 4, 0)
        lbl_tot = QLabel("Total des produits")
        lbl_tot.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {c['text_primary']}; background: transparent;"
        )
        self.lbl_total_produits = QLabel("0 XOF")
        self.lbl_total_produits.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {c['primary']}; background: transparent;"
        )
        tot_lay.addWidget(lbl_tot)
        tot_lay.addStretch()
        tot_lay.addWidget(self.lbl_total_produits)
        lay.addLayout(tot_lay)

        return frame

    def _build_note(self) -> QFrame:
        c = theme_manager.colors()
        note = QFrame()
        note.setAttribute(Qt.WA_StyledBackground, True)
        note.setStyleSheet(
            f"QFrame {{ background: {c['info']}15; border: 1px solid {c['info']};"
            f" border-radius: 8px; }}"
        )
        lay = QHBoxLayout(note)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)

        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.info-circle", color=c['info']).pixmap(16, 16))
        ico.setStyleSheet("background: transparent;")

        txt = QLabel("Note : Veuillez vérifier les informations avant de confirmer le paiement.")
        txt.setStyleSheet(
            f"font-size: 11px; color: {c['info']}; font-weight: 500; background: transparent;"
        )
        txt.setWordWrap(True)

        lay.addWidget(ico)
        lay.addWidget(txt, 1)
        return note

    # ── Section droite ────────────────────────────────────────────────────────

    def _build_right_section(self) -> QFrame:
        c = theme_manager.colors()
        frame = QFrame()
        frame.setAttribute(Qt.WA_StyledBackground, True)
        frame.setStyleSheet(
            f"QFrame {{ background: {c['bg_card']}; border: 1px solid {c['border']};"
            f" border-radius: 12px; }}"
        )

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)

        # Titre
        title = QLabel("Détails du paiement")
        title.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {c['text_primary']}; background: transparent;"
        )
        lay.addWidget(title)

        # Devise
        self._add_field_label(lay, "Devise")
        self.combo_devise = QComboBox()
        self.combo_devise.addItems(["XOF – GNF", "EUR – Euro", "USD – Dollar"])
        self.combo_devise.setFixedHeight(34)
        self.combo_devise.setStyleSheet(self._combo_style())
        lay.addWidget(self.combo_devise)

        # Montant total
        self._add_field_label(lay, "Montant total à payer")
        self.lbl_montant_total = QLabel("0 XOF")
        self.lbl_montant_total.setStyleSheet(
            f"font-size: 22px; font-weight: 700; color: {c['primary']}; background: transparent;"
        )
        lay.addWidget(self.lbl_montant_total)

        # Type de paiement
        self._add_field_label(lay, "Type de paiement")
        self._build_payment_tabs(lay)

        # Réseaux mobiles
        self._add_field_label(lay, "Réseaux mobiles disponibles")
        self._build_network_cards(lay)

        # Numéro de paiement
        self._add_field_label(lay, "Numéro de paiement")
        self._build_phone_input(lay)

        # Référence
        self._add_field_label(lay, "Référence / Motif (optionnel)")
        self.input_reference = QLineEdit()
        self.input_reference.setPlaceholderText("Référence paiement…")
        self.input_reference.setFixedHeight(34)
        self.input_reference.setStyleSheet(self._input_style())
        lay.addWidget(self.input_reference)

        lay.addStretch()

        # Bouton Payer
        self.btn_pay = QPushButton(qta.icon("fa5s.lock", color="white"), "  Payer")
        self.btn_pay.setFixedHeight(44)
        self.btn_pay.setCursor(Qt.PointingHandCursor)
        self.btn_pay.setStyleSheet(f"""
            QPushButton {{
                background: {c['primary']};
                color: white;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
                border: none;
            }}
            QPushButton:hover {{ background: {c['primary_light']}; }}
        """)
        self.btn_pay.clicked.connect(self.process_payment)
        lay.addWidget(self.btn_pay)

        return frame

    def _add_field_label(self, layout, text: str):
        c = theme_manager.colors()
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_muted']}; background: transparent;"
        )
        layout.addWidget(lbl)

    def _build_payment_tabs(self, layout):
        c = theme_manager.colors()
        tabs = QHBoxLayout()
        tabs.setSpacing(8)

        self.btn_mobile = QPushButton(
            qta.icon("fa5s.mobile-alt", color=c['primary']), " Réseaux mobiles"
        )
        self.btn_mobile.setCheckable(True)
        self.btn_mobile.setChecked(True)
        self.btn_mobile.setFixedHeight(34)
        self.btn_mobile.setCursor(Qt.PointingHandCursor)

        self.btn_bank = QPushButton(
            qta.icon("fa5s.university", color=c['text_muted']), " Bancaire"
        )
        self.btn_bank.setCheckable(True)
        self.btn_bank.setFixedHeight(34)
        self.btn_bank.setCursor(Qt.PointingHandCursor)

        _tab_qss = f"""
            QPushButton {{
                background: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
                color: {c['text_secondary']};
            }}
            QPushButton:checked {{
                background: {c['primary']}15;
                border: 2px solid {c['primary']};
                color: {c['primary']};
            }}
        """
        self.btn_mobile.setStyleSheet(_tab_qss)
        self.btn_bank.setStyleSheet(_tab_qss)

        tabs.addWidget(self.btn_mobile)
        tabs.addWidget(self.btn_bank)
        layout.addLayout(tabs)

    def _build_network_cards(self, layout):
        c = theme_manager.colors()
        self.network_group = QButtonGroup(self)

        networks = [
            ("Orange Money", "#FF6600", "white"),
            ("MTN Mobile",   "#FFCC00", "#333333"),
            ("Moov Money",   "#E30613", "white"),
            ("Wari",         "#1B8B40", "white"),
        ]

        nets_lay = QHBoxLayout()
        nets_lay.setSpacing(8)

        for i, (name, color, txt_color) in enumerate(networks):
            card = NetworkCard(name, color, txt_color)
            if i == 0:
                card.set_checked(True)
            self.network_group.addButton(card.radio, i)
            nets_lay.addWidget(card)

        layout.addLayout(nets_lay)

    def _build_phone_input(self, layout):
        c = theme_manager.colors()
        row = QHBoxLayout()
        row.setSpacing(8)

        self.combo_indicatif = QComboBox()
        self.combo_indicatif.addItems(["+224", "+225", "+33", "+1"])
        self.combo_indicatif.setFixedWidth(75)
        self.combo_indicatif.setFixedHeight(34)
        self.combo_indicatif.setStyleSheet(self._combo_style())

        self.input_phone = QLineEdit()
        self.input_phone.setPlaceholderText("6XX XX XX XX")
        self.input_phone.setFixedHeight(34)
        self.input_phone.setStyleSheet(self._input_style())

        row.addWidget(self.combo_indicatif)
        row.addWidget(self.input_phone)
        layout.addLayout(row)

    # ── Styles partagés ───────────────────────────────────────────────────────

    def _combo_style(self) -> str:
        c = theme_manager.colors()
        return f"""
            QComboBox {{
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding-left: 10px;
                background: {c['bg_main']};
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QComboBox:focus {{ border: 2px solid {c['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 22px; }}
            QComboBox QAbstractItemView {{
                background: {c['bg_card']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
            }}
        """

    def _input_style(self) -> str:
        c = theme_manager.colors()
        return f"""
            QLineEdit {{
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding-left: 10px;
                background: {c['bg_main']};
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QLineEdit:focus {{ border: 2px solid {c['primary']}; }}
        """

    def _scrollbar_style(self) -> str:
        c = theme_manager.colors()
        return f"""
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 5px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['text_muted']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

    # =========================================================================
    # CHARGEMENT DES DONNÉES
    # =========================================================================

    def load_data(self, facture_data, produits_data, fournisseur_data):
        self.facture_data    = facture_data
        self.produits_data   = produits_data
        self.fournisseur_data = fournisseur_data
        self._update_ui()

    def _update_ui(self):
        if not self.facture_data or not self.produits_data:
            return

        c = theme_manager.colors()

        # ── En-tête : référence et date
        ref_lbl = self.lbl_reference.findChild(QLabel, "badge_text")
        dat_lbl = self.lbl_date.findChild(QLabel, "badge_text")

        if ref_lbl and hasattr(self.facture_data, 'code_facture_four'):
            ref_lbl.setText(f"Réf : {self.facture_data.code_facture_four}")

        if dat_lbl and hasattr(self.facture_data, 'date_facture_four'):
            d = self.facture_data.date_facture_four
            date_str = d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d)
            dat_lbl.setText(f"Date : {date_str}")

        # ── Fournisseur
        if self.fournisseur_data:
            nom = getattr(self.fournisseur_data, 'nom', '') or ''
            prenom = getattr(self.fournisseur_data, 'prenom', '') or ''
            self.lbl_fournisseur_nom.setText(f"{nom} {prenom}".strip())

            code = getattr(self.fournisseur_data, 'code_fournisseur', '')
            self.badge_code.setText(code or '')

            # Contact
            self._set_info_row(self._row_tel,   getattr(self.fournisseur_data, 'telephone', '') or '')
            self._set_info_row(self._row_email,  getattr(self.fournisseur_data, 'email',     '') or '')
            self._set_info_row(self._row_addr,   getattr(self.fournisseur_data, 'adresse',   '') or '')

        # ── Tableau produits
        self.table_produits.setRowCount(0)
        total = 0.0

        for i, produit in enumerate(self.produits_data, 1):
            row = self.table_produits.rowCount()
            self.table_produits.insertRow(row)

            # #
            num_item = QTableWidgetItem(str(i))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.table_produits.setItem(row, 0, num_item)

            # Produit
            designation = (
                getattr(produit, 'libelle', None)
                or getattr(produit, 'designation', None)
                or "Produit"
            )
            type_prod = getattr(produit, 'type', '') or ''
            produit_text = f"{designation}\n{type_prod}" if type_prod else designation
            self.table_produits.setItem(row, 1, QTableWidgetItem(produit_text))

            # Quantité
            quantite = getattr(produit, 'quantite_four', 0) or 0
            qte_item = QTableWidgetItem(str(quantite))
            qte_item.setTextAlignment(Qt.AlignCenter)
            self.table_produits.setItem(row, 2, qte_item)

            # Prix unitaire
            prix = getattr(produit, 'prix_unitaire', 0.0) or 0.0
            self.table_produits.setItem(
                row, 3, QTableWidgetItem(f"{int(prix):,} XOF".replace(',', ' '))
            )

            # Montant (coloré)
            montant = quantite * prix
            total += montant
            montant_item = QTableWidgetItem(f"{int(montant):,} XOF".replace(',', ' '))
            montant_item.setForeground(
                __import__('PySide6.QtGui', fromlist=['QColor']).QColor(c['primary'])
            )
            montant_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_produits.setItem(row, 4, montant_item)

        # ── Totaux
        total_str = f"{int(total):,} XOF".replace(',', ' ')
        self.lbl_total_produits.setText(total_str)
        self.lbl_montant_total.setText(total_str)
        self.btn_pay.setText(f"  Payer {total_str}")

        # ── Référence pré-remplie
        if hasattr(self.facture_data, 'code_facture_four') and self.fournisseur_data:
            nom_f = getattr(self.fournisseur_data, 'nom', 'Fournisseur') or 'Fournisseur'
            self.input_reference.setText(
                f"Paiement {self.facture_data.code_facture_four} - {nom_f}"
            )

    def _set_info_row(self, row_widget: QWidget, text: str):
        """Met à jour le label 'val' d'une ligne d'info."""
        lbl = row_widget.findChild(QLabel, "val")
        if lbl:
            lbl.setText(text)

    # =========================================================================
    # ANIMATION / AFFICHAGE
    # =========================================================================

    def show_panel(self):
        if self._visible:
            return
        self.raise_()
        self.show()
        self._visible = True

    def close_panel(self):
        """Ferme le panneau — délègue à la vue parente si possible."""
        self._visible = False
        # Demande au parent (GestionProduitsView) de fermer l'overlay
        p = self.parent()
        while p:
            if hasattr(p, '_fermer_payment_overlay'):
                p._fermer_payment_overlay()
                return
            p = p.parent() if hasattr(p, 'parent') else None
        self.hide()

    # =========================================================================
    # TRAITEMENT DU PAIEMENT
    # =========================================================================

    def process_payment(self):
        if not self.facture_data:
            CustomMessageBox.error(
                self, "Erreur", "Aucune facture à finaliser",
                theme_manager.colors()['primary']
            )
            return

        telephone = self.input_phone.text().strip()
        if not telephone:
            CustomMessageBox.warning(
                self, "Attention", "Veuillez entrer un numéro de téléphone.",
                theme_manager.colors()['primary']
            )
            return

        # Mode de paiement
        mode_paiement = "especes"
        if self.btn_mobile.isChecked():
            networks = ["orange money", "mtn mobile money", "moov money", "wari"]
            sid = self.network_group.checkedId()
            if 0 <= sid < len(networks):
                mode_paiement = networks[sid]
        elif self.btn_bank.isChecked():
            mode_paiement = "virement"

        confirmed = CustomMessageBox.question(
            self, "Confirmation",
            f"Confirmer le paiement de {self.lbl_montant_total.text()} ?\n\n"
            f"Mode : {mode_paiement.title()}\n"
            f"Téléphone : {self.combo_indicatif.currentText()} {telephone}"
        )
        if not confirmed:
            return

        from controllers.controleur_factureFournisseur import FactureFournisseurControleur
        from models.modele_factureFournisseur import FactureFournisseur
        from datetime import datetime

        facture_ctrl = FactureFournisseurControleur()
        facture = FactureFournisseur(
            code_facture_four=self.facture_data.code_facture_four,
            code_fournisseur=self.facture_data.code_fournisseur,
            code_session=self.facture_data.code_session,
            date_facture_four=datetime.now(),
            montant_total=0,
            mode_payement=mode_paiement,
            telephone=telephone
        )

        ok, msg = facture_ctrl.finaliser_facture(facture)

        if ok:
            CustomMessageBox.success(
                self, "Succès", "Facture finalisée avec succès !",
                theme_manager.colors()['primary']
            )
            self.close_panel()
            p = self.parent()
            while p:
                if hasattr(p, 'actualiser'):
                    p.actualiser()
                    break
                p = p.parent() if hasattr(p, 'parent') else None
        else:
            CustomMessageBox.error(
                self, "Erreur", f"Erreur lors de la finalisation : {msg}",
                theme_manager.colors()['primary']
            )