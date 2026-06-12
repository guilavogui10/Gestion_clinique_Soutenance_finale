"""
VisitCardsPanel — Panneau de suivi en temps réel des visites actives.

Affiche chaque visite active dans un petit frame rectangulaire.
Les frames se placent côte à côte horizontalement et reviennent
à la ligne automatiquement (flow / wrap layout).

Chaque carte affiche :
  • Nom complet du patient  (+ icône urgence si urgent)
  • Type de visite
  • Statut courant (badge coloré)
  • Durée écoulée depuis la date d'entrée
  • Code visite (discret, en bas)
"""
from PySide6.QtWidgets import (QWidget, QScrollArea, QFrame, QVBoxLayout,
                               QHBoxLayout, QLabel, QLayout, QSizePolicy)
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtGui import QFont
import qtawesome as qta
from views.shared.theme_manager import theme_manager


# =============================================================================
# FlowLayout — wrapping horizontal layout (items côte à côte, retour à la ligne)
# =============================================================================

class FlowLayout(QLayout):
    """Layout qui place les items de gauche à droite et revient à la ligne."""

    def __init__(self, parent=None, h_spacing: int = 10, v_spacing: int = 10):
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items: list = []

    # ── QLayout interface ────────────────────────────────────────────────────

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    # ── Calcul de disposition ────────────────────────────────────────────────

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        m = self.contentsMargins()
        eff = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())

        x = eff.x()
        y = eff.y()
        line_height = 0

        for item in self._items:
            hint = item.sizeHint()
            next_x = x + hint.width() + self._h_spacing

            if next_x - self._h_spacing > eff.right() and line_height > 0:
                x = eff.x()
                y += line_height + self._v_spacing
                next_x = x + hint.width() + self._h_spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))

            x = next_x
            line_height = max(line_height, hint.height())

        return y + line_height - rect.y() + m.bottom()


# =============================================================================
# VisitCard — un frame rectangulaire = une visite active
# =============================================================================

def _status_colors(c: dict) -> dict:
    """Retourne la map statut → (txt_color, bg_color) avec les couleurs du thème actif."""
    return {
        'Attente consultation': (c['warning'],   c['warning_bg']),
        'Attente rendez-vous':  (c['warning'],   c['warning_bg']),
        'En consultation':      (c['info'],      c['info_bg']),
        'Examen en cours':      (c['accent'],    c['accent_light']),
        'Attente examen':       (c['accent'],    c['accent_light']),
        'Attente chirurgie':    (c['danger'],    c['danger_bg']),
        'Attente lunette':      (c['secondary'], c['primary_light']),
        'Attente prescription': (c['secondary'], c['primary_light']),
        'Attente paiement':     (c['warning'],   c['warning_bg']),
        'Accueil':              (c['success'],   c['success_bg']),
        'Libéré':               (c['success'],   c['success_bg']),
    }

def _type_icons(c: dict) -> dict:
    """Retourne la map type → (icon_name, color) avec les couleurs du thème actif."""
    return {
        'Immediat':    ('fa5s.bolt',           c['danger']),
        'Rendez vous': ('fa5s.calendar-check', c['primary']),
        'VIP':         ('fa5s.crown',          c['accent']),
        'Controle':    ('fa5s.redo',           c['success']),
    }


def _format_duree(minutes) -> str:
    try:
        minutes = int(minutes or 0)
    except (TypeError, ValueError):
        return "—"
    if minutes < 60:
        return f"{minutes} min"
    return f"{minutes // 60}h {minutes % 60:02d}min"


class VisitCard(QFrame):
    """Petit frame rectangulaire représentant une visite active."""

    CARD_W = 185
    CARD_H = 155

    def __init__(self, data: dict, parent=None):
        """
        Args:
            data (dict): {code_visite, nom, prenom, type_visite,
                           statut_patient, urgent, duree_minutes}
        """
        super().__init__(parent)
        self._data = data
        self._urgent = str(data.get('urgent', 'Non')).lower() in ('oui', '1', 'true')
        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setObjectName("VisitCard")
        self._build()
        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme()

    # ── Construction UI ──────────────────────────────────────────────────────

    def _build(self):
        d = self._data
        nom      = f"{d.get('nom', '')} {d.get('prenom', '')}".strip()
        self._statut = d.get('statut_patient', 'Accueil')
        self._type_v = d.get('type_visite', '')
        urgent   = self._urgent
        duree_totale   = _format_duree(d.get('duree_totale_minutes', d.get('duree_minutes')))
        duree_service  = _format_duree(d.get('duree_service_minutes')) if d.get('duree_service_minutes') is not None else None
        code_v   = d.get('code_visite', '')

        c = theme_manager.colors()
        sc = _status_colors(c)
        ti = _type_icons(c)
        txt_color, bg_color = sc.get(self._statut, (c['text_secondary'], c['hover']))
        icon_name, icon_color = ti.get(self._type_v, ('fa5s.hospital', c['text_muted']))

        main = QVBoxLayout(self)
        main.setContentsMargins(10, 8, 10, 8)
        main.setSpacing(5)

        # ── Ligne 1 : icône type + nom + urgence ────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self._ico_type = QLabel()
        self._ico_type.setFixedSize(16, 16)
        self._ico_type.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(14, 14))
        self._ico_type.setStyleSheet("border: none; background: transparent;")
        ico_type = self._ico_type

        lbl_nom = QLabel(nom or "—")
        lbl_nom.setObjectName("CardNom")
        font_nom = QFont()
        font_nom.setBold(True)
        font_nom.setPointSize(10)
        lbl_nom.setFont(font_nom)
        lbl_nom.setWordWrap(False)

        row1.addWidget(ico_type)
        row1.addWidget(lbl_nom, 1)

        if urgent:
            ico_urg = QLabel()
            ico_urg.setFixedSize(16, 16)
            ico_urg.setPixmap(
                qta.icon("fa5s.exclamation-circle", color="#e74c3c").pixmap(14, 14)
            )
            ico_urg.setToolTip("URGENT")
            ico_urg.setStyleSheet("border: none; background: transparent;")
            row1.addWidget(ico_urg)

        main.addLayout(row1)

        # ── Ligne 2 : badge statut ───────────────────────────────────────────
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        self._badge = QLabel(self._statut or "—")
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setWordWrap(False)
        badge = self._badge
        row2.addWidget(badge)
        row2.addStretch()
        main.addLayout(row2)

        # ── Ligne 3 : durée totale (depuis création) ───────────────────────────────────
        row3 = QHBoxLayout()
        row3.setSpacing(4)
        self._ico_total = QLabel()
        self._ico_total.setFixedSize(12, 12)
        self._ico_total.setObjectName("ClockIcon")
        self._ico_total.setStyleSheet("border: none; background: transparent;")
        lbl_total_hd = QLabel("Total :")
        lbl_total_hd.setObjectName("DureeLabel")
        self._lbl_total = QLabel(duree_totale)
        self._lbl_total.setObjectName("CardDuree")
        row3.addWidget(self._ico_total)
        row3.addWidget(lbl_total_hd)
        row3.addWidget(self._lbl_total)
        row3.addStretch()
        main.addLayout(row3)

        # ── Ligne 4 : durée dans le service courant (acte_visite) ───────────────
        row4 = QHBoxLayout()
        row4.setSpacing(4)
        self._ico_service = QLabel()
        self._ico_service.setFixedSize(12, 12)
        self._ico_service.setObjectName("ServiceIcon")
        self._ico_service.setStyleSheet("border: none; background: transparent;")
        lbl_service_hd = QLabel("Service :")
        lbl_service_hd.setObjectName("DureeLabel")
        self._lbl_service = QLabel(duree_service if duree_service else "—")
        self._lbl_service.setObjectName("CardDureeService")
        row4.addWidget(self._ico_service)
        row4.addWidget(lbl_service_hd)
        row4.addWidget(self._lbl_service)
        row4.addStretch()
        main.addLayout(row4)

        # ── Ligne 4 : code visite (discret) ─────────────────────────────────
        lbl_code = QLabel(code_v)
        lbl_code.setObjectName("CardCode")
        lbl_code.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        main.addWidget(lbl_code)

    # ── Thème ────────────────────────────────────────────────────────────────

    def _apply_theme(self):
        c = theme_manager.colors()
        if self._urgent:
            card_bg           = c['danger_bg']
            card_border       = c['danger']
            card_hover_bg     = c['danger_bg']
            card_hover_border = c['danger']
        else:
            card_bg           = c['bg_card']
            card_border       = c['border']
            card_hover_bg     = c['hover']
            card_hover_border = c['primary']

        # Rafraîchir badge statut
        if hasattr(self, '_badge') and hasattr(self, '_statut'):
            sc = _status_colors(c)
            txt_color, bg_color = sc.get(self._statut, (c['text_secondary'], c['hover']))
            self._badge.setStyleSheet(f"""
                background: {bg_color}; color: {txt_color};
                border-radius: 10px; padding: 3px 10px;
                font-size: 10px; font-weight: 700; border: none;
            """)

        # Rafraîchir icône type
        if hasattr(self, '_ico_type') and hasattr(self, '_type_v'):
            ti = _type_icons(c)
            icon_name, icon_color = ti.get(self._type_v, ('fa5s.hospital', c['text_muted']))
            self._ico_type.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(14, 14))

        self.setStyleSheet(f"""
            QFrame#VisitCard {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 12px;
            }}
            QFrame#VisitCard:hover {{
                border: 1px solid {card_hover_border};
                background: {card_hover_bg};
            }}
            QLabel#CardNom {{
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
            QLabel#DureeLabel {{
                color: {c['text_muted']};
                font-size: 10px;
                background: transparent;
                border: none;
            }}
            QLabel#CardDuree {{
                color: {c['text_secondary']};
                font-size: 10px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
            QLabel#CardDureeService {{
                color: {c['warning']};
                font-size: 10px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
            QLabel#CardCode {{
                color: {c['text_muted']};
                font-size: 9px;
                background: transparent;
                border: none;
            }}
        """)
        self._ico_total.setPixmap(
            qta.icon("fa5s.history", color=c['text_secondary']).pixmap(11, 11)
        )
        self._ico_service.setPixmap(
            qta.icon("fa5s.clock", color=c['warning']).pixmap(11, 11)
        )


# =============================================================================
# VisitCardsPanel — conteneur avec scroll + FlowLayout des cartes
# =============================================================================

class VisitCardsPanel(QWidget):
    """
    Panneau scrollable affichant les visites actives comme cartes en flow layout.
    Appeler update_cards(list[dict]) pour rafraîchir l'affichage.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme()

    # ── Construction ─────────────────────────────────────────────────────────

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # En-tête
        self._header = QFrame()
        self._header.setObjectName("CardsPanelHeader")
        self._header.setFixedHeight(42)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        header_layout.setSpacing(8)

        self._ico_header = QLabel()
        self._ico_header.setFixedSize(18, 18)
        self._ico_header.setStyleSheet("border: none; background: transparent;")

        self._lbl_title = QLabel("Visites en cours")
        self._lbl_title.setObjectName("CardsPanelTitle")

        self._lbl_count = QLabel("0")
        self._lbl_count.setObjectName("CardsPanelCount")
        self._lbl_count.setAlignment(Qt.AlignCenter)
        self._lbl_count.setFixedSize(24, 24)

        header_layout.addWidget(self._ico_header)
        header_layout.addWidget(self._lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self._lbl_count)

        outer.addWidget(self._header)

        # Zone scrollable
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._flow = FlowLayout(self._container, h_spacing=10, v_spacing=10)
        self._flow.setContentsMargins(10, 10, 10, 10)

        self._scroll.setWidget(self._container)
        outer.addWidget(self._scroll, 1)

        # Label affiché quand aucune visite
        self._lbl_empty = QLabel("Aucune visite active en ce moment.")
        self._lbl_empty.setObjectName("EmptyLabel")
        self._lbl_empty.setAlignment(Qt.AlignCenter)
        self._lbl_empty.setVisible(False)
        outer.addWidget(self._lbl_empty)

    # ── Données ──────────────────────────────────────────────────────────────

    def update_cards(self, visites: list):
        """
        Rafraîchit le panneau avec une nouvelle liste de visites.

        Args:
            visites (list[dict]): résultat de ctrl.obtenir_visites_actives_avec_duree()
        """
        # Vider le flow layout
        while self._flow.count():
            item = self._flow.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        if not visites:
            self._lbl_empty.setVisible(True)
            self._scroll.setVisible(False)
            self._lbl_count.setText("0")
            return

        self._lbl_empty.setVisible(False)
        self._scroll.setVisible(True)
        self._lbl_count.setText(str(len(visites)))

        for data in visites:
            card = VisitCard(data)
            self._flow.addWidget(card)

        # Forcer le recalcul de la hauteur
        self._container.updateGeometry()

    # ── Thème ────────────────────────────────────────────────────────────────

    def _apply_theme(self):
        c = theme_manager.colors()
        self._header.setStyleSheet(f"""
            QFrame#CardsPanelHeader {{
                background: {c['bg_card']};
                border-bottom: 1px solid {c['border_light']};
                border-radius: 0px;
            }}
        """)
        self._lbl_title.setStyleSheet(f"""
            color: {c['text_primary']};
            font-size: 13px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        self._lbl_count.setStyleSheet(f"""
            background: {c['primary']};
            color: {c['text_inverse']};
            border-radius: 12px;
            font-size: 10px;
            font-weight: 800;
            border: none;
        """)
        self._ico_header.setPixmap(
            qta.icon("fa5s.procedures", color=c['primary']).pixmap(16, 16)
        )
        self._lbl_empty.setStyleSheet(f"""
            color: {c['text_muted']};
            font-size: 12px;
            padding: 20px;
            background: transparent;
            border: none;
        """)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {c['bg_main']}; }}
            QScrollBar:vertical {{
                border: none; background: {c['bg_main']};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 3px; }}
            QScrollBar::handle:vertical:hover {{ background: {c['text_muted']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
