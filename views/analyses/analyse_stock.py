"""
Dashboard d'analyse du stock pour l'interface administrateur.
"""

from datetime import datetime

import qtawesome as qta
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from controllers.controleur_factureFournisseur import FactureFournisseurControleur
from views.shared.theme_manager import theme_manager


def _clean_text(value) -> str:
    text = str(value or "").strip()
    replacements = {
        "ExpirÃ©": "Expire",
        "ExpirÃ©s": "Expires",
        "Ã€ Expirer": "A expirer",
        "ComprimÃ©": "Comprime",
        "ComprimÃ©s": "Comprimes",
        "BientÃ´t": "Bientot",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = (
        text.replace("Expiré", "Expire")
        .replace("Expirés", "Expires")
        .replace("À Expirer", "A expirer")
        .replace("à Expirer", "A expirer")
        .replace("à expirer", "A expirer")
        .replace("Comprimé", "Comprime")
        .replace("Comprimés", "Comprimes")
        .replace("Bientôt", "Bientot")
    )
    return text


def _format_int(value) -> str:
    try:
        return f"{int(value):,}".replace(",", " ")
    except Exception:
        return "0"


def _format_currency(value) -> str:
    try:
        return f"{float(value):,.0f}".replace(",", " ") + " FCFA"
    except Exception:
        return "0 FCFA"


def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, "strftime"):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


class StockKpiCard(QFrame):
    def __init__(self, title: str, icon_name: str, accent_color: str, suffix: str = ""):
        super().__init__()
        self._title = title
        self._icon_name = icon_name
        self._accent_color = accent_color
        self._suffix = suffix

        self.setMinimumHeight(92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 24))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.icon_wrap = QLabel()
        self.icon_wrap.setFixedSize(52, 52)
        self.icon_wrap.setAlignment(Qt.AlignCenter)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.lbl_title = QLabel(title)
        self.lbl_title.setWordWrap(True)
        self.lbl_value = QLabel("0")
        self.lbl_suffix = QLabel(suffix)

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_value)
        text_layout.addWidget(self.lbl_suffix)

        layout.addWidget(self.icon_wrap, 0, Qt.AlignTop)
        layout.addLayout(text_layout, 1)

        self.apply_theme()

    def update_value(self, value: str, suffix: str | None = None):
        self.lbl_value.setText(value)
        if suffix is not None:
            self.lbl_suffix.setText(suffix)

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"QFrame {{ background:{c['bg_card']}; border:1px solid {c['border']}; border-radius:14px; }}"
        )
        self.icon_wrap.setStyleSheet(
            f"background:{self._accent_color}22; border:1px solid {self._accent_color}55; border-radius:26px;"
        )
        self.icon_wrap.setPixmap(
            qta.icon(self._icon_name, color=self._accent_color).pixmap(QSize(28, 28))
        )
        self.lbl_title.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:10px; font-weight:700; border:none;"
        )
        self.lbl_value.setStyleSheet(
            f"color:{self._accent_color}; font-size:22px; font-weight:800; border:none;"
        )
        self.lbl_suffix.setStyleSheet(
            f"color:{c['text_muted']}; font-size:11px; font-weight:600; border:none;"
        )


class SectionCard(QFrame):
    def __init__(self, title: str, icon_name: str):
        super().__init__()
        self._title = title
        self._icon_name = icon_name

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 22))
        self.setGraphicsEffect(shadow)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(14, 14, 14, 14)
        self.root.setSpacing(10)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(22, 22)
        self.title_lbl = QLabel(title)
        self.title_lbl.setWordWrap(True)
        self.sep = QFrame()
        self.sep.setFixedHeight(1)

        header.addWidget(self.icon_lbl)
        header.addWidget(self.title_lbl, 1)

        self.root.addLayout(header)
        self.root.addWidget(self.sep)

        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        self.root.addLayout(self.content_layout, 1)

        self.apply_theme()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"QFrame {{ background:{c['bg_card']}; border:1px solid {c['border']}; border-radius:16px; }}"
        )
        self.icon_lbl.setPixmap(
            qta.icon(self._icon_name, color=c["primary"]).pixmap(QSize(18, 18))
        )
        self.title_lbl.setStyleSheet(
            f"color:{c['text_primary']}; font-size:12px; font-weight:800; border:none;"
        )
        self.sep.setStyleSheet(f"background:{c['border']}; border:none;")


class DonutCanvas(FigureCanvas):
    def __init__(self):
        self.figure = Figure(figsize=(3, 2.1), dpi=100, facecolor="none")
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)
        self.setStyleSheet("background: transparent;")

    def draw_chart(self, labels, values, colors, center_text: str):
        c = theme_manager.colors()
        self.figure.clear()
        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor("none")

        positive = [(lab, val, col) for lab, val, col in zip(labels, values, colors) if val > 0]
        if not positive:
            self.axes.text(
                0.5,
                0.5,
                "Aucune donnee",
                ha="center",
                va="center",
                color=c["text_muted"],
                fontsize=11,
                fontweight="600",
                transform=self.axes.transAxes,
            )
            self.axes.axis("off")
            self.draw()
            return

        labs, vals, cols = zip(*positive)
        self.axes.pie(
            vals,
            colors=cols,
            startangle=90,
            counterclock=False,
            wedgeprops={"width": 0.45, "edgecolor": c["bg_card"]},
        )
        self.axes.text(
            0,
            0,
            center_text,
            ha="center",
            va="center",
            color=c["text_primary"],
            fontsize=11,
            fontweight="700",
        )
        self.axes.axis("equal")
        self.axes.axis("off")
        self.figure.tight_layout(pad=0.2)
        self.draw()


class BarCanvas(FigureCanvas):
    def __init__(self):
        self.figure = Figure(figsize=(5.8, 2.2), dpi=100, facecolor="none")
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)
        self.setStyleSheet("background: transparent;")

    def draw_chart(self, stats_par_mois: dict):
        c = theme_manager.colors()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("none")

        months = ["Jan", "Fev", "Mar", "Avr", "Mai", "Juin", "Juil", "Aout", "Sep", "Oct", "Nov", "Dec"]
        entries = [int((stats_par_mois.get(m) or {}).get("entrees", 0) or 0) for m in months]
        exits = [int((stats_par_mois.get(m) or {}).get("sorties", 0) or 0) for m in months]
        x_positions = list(range(len(months)))
        width = 0.34

        ax.bar(
            [x - width / 2 for x in x_positions],
            entries,
            width=width,
            color=c["info"],
            label="Entrees",
            edgecolor=c["info"],
            alpha=0.9,
        )
        ax.bar(
            [x + width / 2 for x in x_positions],
            exits,
            width=width,
            color=c["danger"],
            label="Sorties",
            edgecolor=c["danger"],
            alpha=0.9,
        )

        ax.set_xticks(x_positions)
        ax.set_xticklabels(months, fontsize=8, color=c["text_secondary"])
        ax.tick_params(axis="y", labelsize=8, colors=c["text_secondary"])
        ax.grid(True, axis="y", alpha=0.18, linestyle="--", color=c["border"])

        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color(c["border"])
        ax.spines["bottom"].set_color(c["border"])

        legend = ax.legend(loc="upper left", frameon=False, fontsize=8)
        for txt in legend.get_texts():
            txt.set_color(c["text_secondary"])

        self.figure.tight_layout(pad=0.8)
        self.draw()


class AnalyseStockView(QWidget):
    def __init__(self, stock_ctrl, code_session):
        super().__init__()
        self.ctrl = stock_ctrl
        self.facture_ctrl = FactureFournisseurControleur()
        self.code_session = code_session

        self._init_ui()
        self.rafraichir()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.scroll.setWidget(self.container)
        self.root_layout.addWidget(self.scroll)

        self.page_layout = QVBoxLayout(self.container)
        self.page_layout.setContentsMargins(12, 12, 12, 16)
        self.page_layout.setSpacing(12)

        self.title_lbl = QLabel("Analyse du stock pharmaceutique")
        self.subtitle_lbl = QLabel(
            "Fonctionnalites exploitables a afficher sur l'interface administrateur"
        )

        self.page_layout.addWidget(self.title_lbl)
        self.page_layout.addWidget(self.subtitle_lbl)

        self.main_content = QHBoxLayout()
        self.main_content.setSpacing(12)
        self.page_layout.addLayout(self.main_content, 1)

        self.left_panel = self._create_panel(
            "1. Fonctionnalites utiles a integrer", fixed_width=365
        )
        self.right_panel = self._create_panel(
            "2. Fonctionnalites a afficher sur l'interface administrateur"
        )

        self.main_content.addWidget(self.left_panel["frame"], 0)
        self.main_content.addWidget(self.right_panel["frame"], 1)

        self._build_left_column(self.left_panel["body"])
        self._build_left_overlay()
        self._build_right_column(self.right_panel["body"])

        self.apply_theme()

    def _create_panel(self, title: str, fixed_width: int | None = None):
        frame = QFrame()
        if fixed_width:
            frame.setFixedWidth(fixed_width)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 20))
        frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(title)
        header.setFixedHeight(38)
        header.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(12)

        layout.addWidget(header)
        layout.addWidget(body, 1)

        return {"frame": frame, "header": header, "body": body_layout, "body_widget": body}

    def _build_left_column(self, layout: QVBoxLayout):
        self.utility_cards = []
        tools = [
            {
                "key": "search",
                "icon": "fa5s.search",
                "title": "Recherche avancee",
                "desc": "Retrouver rapidement un produit, un fournisseur, un lot ou une date d'approvisionnement.",
                "color": "#3178e0",
                "badge": "Prioritaire",
                "chips": ["Produit", "Lot", "Fournisseur", "Date"],
                "action_text": "Ouvrir la recherche",
            },
            {
                "key": "filters",
                "icon": "fa5s.filter",
                "title": "Filtres intelligents",
                "desc": "Filtrer le stock par session, statut d'expiration, periode ou niveau d'alerte.",
                "color": "#f38b1f",
                "badge": "Utile",
                "chips": ["Session", "Statut", "Periode", "Seuil"],
                "action_text": "Afficher les filtres",
            },
            {
                "key": "lot_detail",
                "icon": "fa5s.box-open",
                "title": "Detail d'un lot",
                "desc": "Afficher les entrees, prescriptions utilisees et le stock restant du lot prioritaire.",
                "color": "#7a5acb",
                "badge": "Donnees live",
                "chips": ["FEFO", "Tracabilite", "Stock restant"],
                "action_text": "Voir les lots",
            },
        ]

        for tool in tools:
            card = QFrame()
            card.setMinimumHeight(118)
            root = QVBoxLayout(card)
            root.setContentsMargins(12, 12, 12, 12)
            root.setSpacing(8)

            top = QHBoxLayout()
            top.setContentsMargins(0, 0, 0, 0)
            top.setSpacing(10)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(46, 46)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setPixmap(qta.icon(tool["icon"], color="white").pixmap(QSize(20, 20)))
            icon_lbl.setStyleSheet(
                f"background:{tool['color']}; border-radius:23px; border:none;"
            )

            title_wrap = QVBoxLayout()
            title_wrap.setContentsMargins(0, 0, 0, 0)
            title_wrap.setSpacing(3)

            title_lbl = QLabel(tool["title"])
            title_lbl.setWordWrap(True)
            desc_lbl = QLabel(tool["desc"])
            desc_lbl.setWordWrap(True)

            title_wrap.addWidget(title_lbl)
            title_wrap.addWidget(desc_lbl)
            top.addWidget(icon_lbl, 0, Qt.AlignTop)
            top.addLayout(title_wrap, 1)

            badge_lbl = QLabel(tool["badge"])
            badge_lbl.setAlignment(Qt.AlignCenter)
            badge_lbl.setMinimumWidth(82)
            top.addWidget(badge_lbl, 0, Qt.AlignTop)
            root.addLayout(top)

            chips_row = QHBoxLayout()
            chips_row.setContentsMargins(0, 0, 0, 0)
            chips_row.setSpacing(6)
            chip_labels = []
            for chip in tool["chips"]:
                chip_lbl = QLabel(chip)
                chip_lbl.setAlignment(Qt.AlignCenter)
                chip_lbl.setMinimumHeight(24)
                chip_labels.append(chip_lbl)
                chips_row.addWidget(chip_lbl)
            root.addLayout(chips_row)

            detail_lbl = QLabel("")
            detail_lbl.setWordWrap(True)
            root.addWidget(detail_lbl)

            action_btn = QPushButton(tool["action_text"])
            action_btn.clicked.connect(
                lambda checked=False, key=tool["key"]: self._handle_utility_action(key)
            )
            root.addWidget(action_btn, 0, Qt.AlignLeft)

            layout.addWidget(card)
            self.utility_cards.append({
                "key": tool["key"],
                "card": card,
                "title": title_lbl,
                "desc": desc_lbl,
                "badge": badge_lbl,
                "detail": detail_lbl,
                "action": action_btn,
                "chips": chip_labels,
                "color": tool["color"],
            })

        layout.addStretch()

    def _build_left_overlay(self):
        self.left_overlay = QFrame(self.left_panel["body_widget"])
        self.left_overlay.hide()

        root = QVBoxLayout(self.left_overlay)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)

        self.left_overlay_icon = QLabel()
        self.left_overlay_icon.setFixedSize(42, 42)
        self.left_overlay_icon.setAlignment(Qt.AlignCenter)

        title_wrap = QVBoxLayout()
        title_wrap.setContentsMargins(0, 0, 0, 0)
        title_wrap.setSpacing(2)
        self.left_overlay_title = QLabel("")
        self.left_overlay_title.setWordWrap(True)
        self.left_overlay_subtitle = QLabel("")
        self.left_overlay_subtitle.setWordWrap(True)
        title_wrap.addWidget(self.left_overlay_title)
        title_wrap.addWidget(self.left_overlay_subtitle)

        self.left_overlay_close = QPushButton("Fermer")
        self.left_overlay_close.clicked.connect(self._close_left_overlay)

        header_row.addWidget(self.left_overlay_icon, 0, Qt.AlignTop)
        header_row.addLayout(title_wrap, 1)
        header_row.addWidget(self.left_overlay_close, 0, Qt.AlignTop)
        root.addLayout(header_row)

        self.left_overlay_summary = QLabel("")
        self.left_overlay_summary.setWordWrap(True)
        root.addWidget(self.left_overlay_summary)

        self.left_overlay_content = QVBoxLayout()
        self.left_overlay_content.setContentsMargins(0, 0, 0, 0)
        self.left_overlay_content.setSpacing(10)
        root.addLayout(self.left_overlay_content, 1)

        self.left_overlay_animation = QPropertyAnimation(self.left_overlay, b"geometry", self)
        self.left_overlay_animation.setDuration(280)
        self.left_overlay_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._left_overlay_should_hide = False
        self.left_overlay_animation.finished.connect(self._on_left_overlay_animation_finished)

    def _clear_layout(self, layout: QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout(child_layout)

    def _update_left_overlay_geometry(self, hidden: bool = False):
        if not hasattr(self, "left_overlay"):
            return
        body_widget = self.left_panel["body_widget"]
        width = body_widget.width()
        height = body_widget.height()
        y = height if hidden else 0
        self.left_overlay.setGeometry(0, y, width, height)

    def _create_overlay_table(self, headers: list[str], minimum_height: int = 170) -> QTableWidget:
        table = QTableWidget(3, len(headers))
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(minimum_height)
        for idx, text in enumerate(headers):
            table.setHorizontalHeaderItem(idx, QTableWidgetItem(text))
        hdr = table.horizontalHeader()
        for idx in range(len(headers)):
            hdr.setSectionResizeMode(idx, QHeaderView.Stretch if idx == 1 else QHeaderView.ResizeToContents)
        return table

    def _open_left_overlay(self, key: str):
        configs = {
            "search": {
                "icon": "fa5s.search",
                "color": "#3178e0",
                "title": "Recherche avancee",
                "subtitle": "Retrouver rapidement un produit, un lot ou une facture fournisseur.",
                "summary": "Cette zone vient se superposer aux cartes de gauche pour garder l'utilisateur dans le meme contexte visuel.",
            },
            "filters": {
                "icon": "fa5s.filter",
                "color": "#f38b1f",
                "title": "Filtres intelligents",
                "subtitle": "Combiner les filtres essentiels sans quitter l'analyse stock.",
                "summary": "L'interface privilegie des controles simples, lisibles et directement relies aux alertes de stock.",
            },
            "lot_detail": {
                "icon": "fa5s.box-open",
                "color": "#7a5acb",
                "title": "Detail d'un lot",
                "subtitle": "Consulter le lot prioritaire, son expiration et sa tracabilite.",
                "summary": "Le panneau met en avant une lecture FEFO avec un resume clair et une zone de details structurée.",
            },
        }
        config = configs.get(key)
        if not config:
            return

        self._clear_layout(self.left_overlay_content)
        self.left_overlay_title.setText(config["title"])
        self.left_overlay_subtitle.setText(config["subtitle"])
        self.left_overlay_summary.setText(config["summary"])
        self.left_overlay_icon.setPixmap(
            qta.icon(config["icon"], color="white").pixmap(QSize(18, 18))
        )
        self.left_overlay_icon.setStyleSheet(
            f"background:{config['color']}; border-radius:21px; border:none;"
        )

        if key == "search":
            self._populate_search_overlay()
        elif key == "filters":
            self._populate_filters_overlay()
        elif key == "lot_detail":
            self._populate_lot_overlay()

        self._update_left_overlay_geometry(hidden=True)
        self.left_overlay.show()
        self.left_overlay.raise_()
        end_rect = QRect(0, 0, self.left_panel["body_widget"].width(), self.left_panel["body_widget"].height())
        start_rect = QRect(0, self.left_panel["body_widget"].height(), end_rect.width(), end_rect.height())
        self.left_overlay_animation.stop()
        self._left_overlay_should_hide = False
        self.left_overlay_animation.setStartValue(start_rect)
        self.left_overlay_animation.setEndValue(end_rect)
        self.left_overlay_animation.start()

    def _close_left_overlay(self):
        if not hasattr(self, "left_overlay") or not self.left_overlay.isVisible():
            return
        start_rect = self.left_overlay.geometry()
        end_rect = QRect(0, self.left_panel["body_widget"].height(), start_rect.width(), start_rect.height())
        self.left_overlay_animation.stop()
        self._left_overlay_should_hide = True
        self.left_overlay_animation.setStartValue(start_rect)
        self.left_overlay_animation.setEndValue(end_rect)
        self.left_overlay_animation.start()

    def _on_left_overlay_animation_finished(self):
        if getattr(self, "_left_overlay_should_hide", False):
            self.left_overlay.hide()

    def _populate_search_overlay(self):
        type_row = QHBoxLayout()
        type_row.setContentsMargins(0, 0, 0, 0)
        type_row.setSpacing(8)

        type_combo = QComboBox()
        type_combo.addItems(["Comprime", "Liquide", "Pommade"])
        type_combo.setMinimumHeight(36)

        search_btn = QPushButton("Afficher")
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.setMinimumHeight(36)

        type_row.addWidget(type_combo, 1)
        type_row.addWidget(search_btn)
        self.left_overlay_content.addLayout(type_row)

        summary = QLabel("")
        summary.setWordWrap(True)
        self.left_overlay_content.addWidget(summary)

        cards_scroll = QScrollArea()
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setFrameShape(QFrame.NoFrame)
        cards_scroll.setMinimumHeight(400)

        cards_host = QWidget()
        cards_grid = QGridLayout(cards_host)
        cards_grid.setContentsMargins(0, 0, 0, 0)
        cards_grid.setHorizontalSpacing(12)
        cards_grid.setVerticalSpacing(12)
        cards_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        cards_scroll.setWidget(cards_host)
        self.left_overlay_content.addWidget(cards_scroll, 1)

        def collect_products():
            produits = {}
            for ligne in self.ctrl.lister_par_session(self.code_session) or []:
                code = getattr(ligne, "code_produit", None)
                if not code or code in produits:
                    continue
                
                # Récupérer le type et le nettoyer
                produit_type = _clean_text(getattr(ligne, "type", "") or "Comprime")
                
                # Récupérer le stock global
                stock = self.ctrl.obtenir_stock(code, self.code_session) or {}
                qte_globale = int(stock.get("quantite_actuelle") or 0)
                
                # Récupérer les lots pour calculer les quantités par statut
                lots = self.ctrl.lister_lots_par_produit(code, self.code_session) or []
                qte_expire = 0
                qte_bientot = 0
                qte_valide = 0
                
                for lot in lots:
                    stock_lot = int(lot.get("stock_lot") or 0)
                    statut = _clean_text(lot.get("statut_lot") or "")
                    if statut == "Expire":
                        qte_expire += stock_lot
                    elif statut == "A expirer":
                        qte_bientot += stock_lot
                    else:
                        qte_valide += stock_lot

                produits[code] = {
                    "code": code,
                    "designation": _clean_text(getattr(ligne, "libelle", None) or getattr(ligne, "designation", "") or code),
                    "type": produit_type,
                    "qte_globale": qte_globale,
                    "qte_expire": qte_expire,
                    "qte_bientot": qte_bientot,
                    "qte_valide": qte_valide,
                }
            return list(produits.values())

        def clear_cards():
            while cards_grid.count():
                item = cards_grid.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        def add_product_card(row_data: dict, index: int):
            card = QFrame()
            card.setObjectName("searchProductCard")
            card.setFixedSize(110, 80)
            
            # Ombre portée
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(6)
            shadow.setOffset(0, 1)
            shadow.setColor(QColor(0, 0, 0, 15))
            card.setGraphicsEffect(shadow)

            layout = QVBoxLayout(card)
            layout.setContentsMargins(6, 6, 6, 6)
            layout.setSpacing(3)

            # En-tête : Icône + Nom du produit
            header = QHBoxLayout()
            header.setContentsMargins(0, 0, 0, 0)
            header.setSpacing(4)
            
            # Icône selon le type
            icon_map = {
                "Liquide": ("fa5s.tint", "#3498db"),
                "Pommade": ("fa5s.prescription-bottle", "#9b59b6"),
                "Comprime": ("fa5s.pills", "#2ecc71")
            }
            icon_name, icon_color = icon_map.get(row_data["type"], ("fa5s.capsules", "#95a5a6"))
            
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(18, 18)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setPixmap(qta.icon(icon_name, color="white").pixmap(QSize(11, 11)))
            icon_lbl.setStyleSheet(f"background:{icon_color}; border-radius:9px; border:none;")
            
            title = QLabel(row_data["designation"][:12] + ".." if len(row_data["designation"]) > 12 else row_data["designation"])
            title.setStyleSheet("font-weight:700; font-size:9px; border:none; color:#2c3e50;")
            
            header.addWidget(icon_lbl)
            header.addWidget(title, 1)
            layout.addLayout(header)

            # Séparateur
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet("background:#ecf0f1; border:none;")
            layout.addWidget(sep)

            # Quantité globale
            global_row = QHBoxLayout()
            global_row.setContentsMargins(0, 0, 0, 0)
            global_row.setSpacing(3)
            
            global_icon = QLabel()
            global_icon.setFixedSize(10, 10)
            global_icon.setPixmap(qta.icon("fa5s.database", color="#34495e").pixmap(QSize(8, 8)))
            
            global_label = QLabel("Glob")
            global_label.setStyleSheet("font-size:8px; font-weight:600; color:#34495e; border:none;")
            
            global_value = QLabel(f"{_format_int(row_data['qte_globale'])}")
            global_value.setStyleSheet("font-size:9px; font-weight:800; color:#2c3e50; border:none;")
            
            global_row.addWidget(global_icon)
            global_row.addWidget(global_label)
            global_row.addWidget(global_value)
            global_row.addStretch()
            layout.addLayout(global_row)
            
            # Quantité valide
            valide_row = QHBoxLayout()
            valide_row.setContentsMargins(0, 0, 0, 0)
            valide_row.setSpacing(3)
            
            valide_icon = QLabel()
            valide_icon.setFixedSize(10, 10)
            valide_icon.setPixmap(qta.icon("fa5s.check-circle", color="#27ae60").pixmap(QSize(8, 8)))
            
            valide_label = QLabel("Val")
            valide_label.setStyleSheet("font-size:8px; font-weight:600; color:#27ae60; border:none;")
            
            valide_value = QLabel(f"{_format_int(row_data['qte_valide'])}")
            valide_value.setStyleSheet("font-size:9px; font-weight:800; color:#27ae60; border:none;")
            
            valide_row.addWidget(valide_icon)
            valide_row.addWidget(valide_label)
            valide_row.addWidget(valide_value)
            valide_row.addStretch()
            layout.addLayout(valide_row)
            
            # Quantité à expirer
            bientot_row = QHBoxLayout()
            bientot_row.setContentsMargins(0, 0, 0, 0)
            bientot_row.setSpacing(3)
            
            bientot_icon = QLabel()
            bientot_icon.setFixedSize(10, 10)
            bientot_icon.setPixmap(qta.icon("fa5s.exclamation-triangle", color="#f39c12").pixmap(QSize(8, 8)))
            
            bientot_label = QLabel("Exp")
            bientot_label.setStyleSheet("font-size:8px; font-weight:600; color:#f39c12; border:none;")
            
            bientot_value = QLabel(f"{_format_int(row_data['qte_bientot'])}")
            bientot_value.setStyleSheet("font-size:9px; font-weight:800; color:#f39c12; border:none;")
            
            bientot_row.addWidget(bientot_icon)
            bientot_row.addWidget(bientot_label)
            bientot_row.addWidget(bientot_value)
            bientot_row.addStretch()
            layout.addLayout(bientot_row)
            
            # Quantité expirée
            expire_row = QHBoxLayout()
            expire_row.setContentsMargins(0, 0, 0, 0)
            expire_row.setSpacing(3)
            
            expire_icon = QLabel()
            expire_icon.setFixedSize(10, 10)
            expire_icon.setPixmap(qta.icon("fa5s.times-circle", color="#e74c3c").pixmap(QSize(8, 8)))
            
            expire_label = QLabel("Exp")
            expire_label.setStyleSheet("font-size:8px; font-weight:600; color:#e74c3c; border:none;")
            
            expire_value = QLabel(f"{_format_int(row_data['qte_expire'])}")
            expire_value.setStyleSheet("font-size:9px; font-weight:800; color:#e74c3c; border:none;")
            
            expire_row.addWidget(expire_icon)
            expire_row.addWidget(expire_label)
            expire_row.addWidget(expire_value)
            expire_row.addStretch()
            layout.addLayout(expire_row)
            
            layout.addStretch()

            # Calculer la position dans la grille (6 colonnes pour plus de cartes)
            row_pos = index // 6
            col_pos = index % 6
            cards_grid.addWidget(card, row_pos, col_pos)

        def run_search():
            selected_type = _clean_text(type_combo.currentText())
            all_products = collect_products()
            
            # Debug: afficher les types disponibles
            types_disponibles = set(_clean_text(item["type"]) for item in all_products)
            print(f"[DEBUG] Types disponibles: {types_disponibles}")
            print(f"[DEBUG] Type recherché: {selected_type}")
            print(f"[DEBUG] Nombre total de produits: {len(all_products)}")
            
            # Filtrer par type (comparaison insensible à la casse)
            filtered = [
                item for item in all_products
                if _clean_text(item["type"]).lower() == selected_type.lower()
            ]
            
            print(f"[DEBUG] Produits filtrés: {len(filtered)}")
            
            filtered.sort(key=lambda item: item["designation"].lower())

            clear_cards()
            if not filtered:
                summary.setText(f"Aucun produit trouve pour le type {selected_type}.")
                empty = QLabel(f"Aucun produit disponible pour ce type dans la session active.\n\nTypes disponibles: {', '.join(types_disponibles)}")
                empty.setWordWrap(True)
                empty.setAlignment(Qt.AlignCenter)
                empty.setStyleSheet("padding:20px; font-size:11px;")
                cards_grid.addWidget(empty, 0, 0, 1, 2)
                return

            summary.setText(f"{len(filtered)} produit(s) de type {selected_type} affiches.")
            for index, row_data in enumerate(filtered):
                add_product_card(row_data, index)

        search_btn.clicked.connect(run_search)
        type_combo.currentIndexChanged.connect(run_search)
        run_search()

    def _populate_filters_overlay(self):
        filters_card = QFrame()
        filters_layout = QVBoxLayout(filters_card)
        filters_layout.setContentsMargins(12, 12, 12, 12)
        filters_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)
        status_combo = QComboBox()
        status_combo.addItems(["Tous", "Rupture", "Stock faible", "A expirer", "Expire", "Valide"])
        type_combo = QComboBox()
        type_combo.addItems(["Tous les types", "Liquide", "Pommade", "Comprime"])
        top_row.addWidget(status_combo)
        top_row.addWidget(type_combo)
        filters_layout.addLayout(top_row)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Filtrer par designation ou code produit")
        filters_layout.addWidget(search_input)

        apply_btn = QPushButton("Appliquer les filtres")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setMinimumHeight(36)
        filters_layout.addWidget(apply_btn)

        summary = QLabel("")
        summary.setWordWrap(True)
        filters_layout.addWidget(summary)
        filters_layout.addWidget(QLabel("Apercu des resultats filtres"))
        results_table = self._create_overlay_table(["Code", "Designation", "Type", "Statut"], 240)
        filters_layout.addWidget(results_table)
        self.left_overlay_content.addWidget(filters_card)

        def build_rows():
            lignes = self.ctrl.lister_par_session(self.code_session) or []
            ruptures = {row.get("code_produit") for row in (self.ctrl.obtenir_ruptures_stock(self.code_session) or [])}
            stock_faible = {row.get("code_produit") for row in (self.ctrl.obtenir_stock_faible(self.code_session, seuil=10) or [])}
            a_expirer = {row.get("code_produit") for row in (self.ctrl.obtenir_lots_a_expirer(self.code_session) or [])}
            expires = {row.get("code_produit") for row in (self.ctrl.obtenir_lots_expires(self.code_session) or [])}

            rows = []
            seen = set()
            for ligne in lignes:
                code = getattr(ligne, "code_produit", None)
                if not code or code in seen:
                    continue
                seen.add(code)
                stock = self.ctrl.obtenir_stock(code, self.code_session) or {}
                quantite = int(stock.get("quantite_actuelle") or 0)
                if quantite <= 0 or code in ruptures:
                    statut = "Rupture"
                elif code in expires:
                    statut = "Expire"
                elif code in a_expirer:
                    statut = "A expirer"
                elif code in stock_faible:
                    statut = "Stock faible"
                else:
                    statut = "Valide"

                rows.append({
                    "code_produit": code,
                    "designation": _clean_text(getattr(ligne, "libelle", None) or getattr(ligne, "designation", "") or code),
                    "type": _clean_text(getattr(ligne, "type", "") or "Comprime"),
                    "quantite": quantite,
                    "statut": statut,
                })
            return rows

        def apply_filters():
            status = status_combo.currentText()
            type_value = type_combo.currentText()
            critere = _clean_text(search_input.text()).lower()
            filtered = []
            for row in build_rows():
                if status != "Tous" and row["statut"] != status:
                    continue
                if type_value != "Tous les types" and row["type"] != type_value:
                    continue
                if critere and critere not in row["designation"].lower() and critere not in row["code_produit"].lower():
                    continue
                filtered.append(row)

            summary.setText(f"{len(filtered)} resultat(s) pour statut={status} et type={type_value}.")
            self._populate_table(
                results_table,
                [
                    [row["code_produit"], row["designation"], row["type"], row["statut"]]
                    for row in sorted(filtered, key=lambda item: (item["statut"], item["designation"]))
                ],
            )

        apply_btn.clicked.connect(apply_filters)
        search_input.returnPressed.connect(apply_filters)
        apply_filters()

    def _populate_lot_overlay(self):
        lot_card = QFrame()
        lot_layout = QVBoxLayout(lot_card)
        lot_layout.setContentsMargins(12, 12, 12, 12)
        lot_layout.setSpacing(10)

        product_combo = QComboBox()
        product_combo.addItem("Choisir un produit", None)
        lot_layout.addWidget(product_combo)

        summary = QTextEdit()
        summary.setReadOnly(True)
        summary.setPlainText(
            "Produit :\nCode produit :\nStock global :\nLot FEFO prioritaire :\nStatut :"
        )
        summary.setMinimumHeight(120)
        lot_layout.addWidget(summary)

        detail_btn = QPushButton("Voir les details complets")
        detail_btn.setCursor(Qt.PointingHandCursor)
        detail_btn.setMinimumHeight(36)
        lot_layout.addWidget(detail_btn)

        lot_layout.addWidget(QLabel("Historique des lots"))
        lots_table = self._create_overlay_table(["Expiration", "Stock lot", "Jours restants", "Statut"], 220)
        lot_layout.addWidget(lots_table)
        self.left_overlay_content.addWidget(lot_card)

        produits = {}
        for ligne in self.ctrl.lister_par_session(self.code_session) or []:
            code = getattr(ligne, "code_produit", None)
            if not code or code in produits:
                continue
            produits[code] = _clean_text(getattr(ligne, "libelle", None) or getattr(ligne, "designation", "") or code)

        for code, libelle in sorted(produits.items(), key=lambda item: item[1].lower()):
            product_combo.addItem(f"{libelle} ({code})", code)

        def refresh_detail():
            code_produit = product_combo.currentData()
            if not code_produit:
                summary.setPlainText("Aucun produit disponible pour afficher le detail d'un lot.")
                self._set_table_message(lots_table, "Aucun lot disponible.")
                return

            lots = self.ctrl.lister_lots_par_produit(code_produit, self.code_session) or []
            stock = self.ctrl.obtenir_stock(code_produit, self.code_session) or {}
            fefo = self.ctrl.obtenir_date_fefo(code_produit, self.code_session, 1)

            nb_valides = self.ctrl.obtenir_lots_valides_par_produit(code_produit, self.code_session)
            nb_expirer = self.ctrl.obtenir_lots_a_expirer_par_produit(code_produit, self.code_session)
            nb_expires = self.ctrl.obtenir_lots_expires_par_produit(code_produit, self.code_session)

            designation = produits.get(code_produit, code_produit)
            summary.setPlainText(
                "\n".join(
                    [
                        f"Produit : {designation}",
                        f"Code produit : {code_produit}",
                        f"Stock global : {_format_int(stock.get('quantite_actuelle', 0))}",
                        f"Lot FEFO prioritaire : {self._format_date(fefo) if fefo else 'Aucun'}",
                        f"Lots valides : {_format_int(nb_valides)}",
                        f"Lots a expirer : {_format_int(nb_expirer)}",
                        f"Lots expires : {_format_int(nb_expires)}",
                    ]
                )
            )

            self._populate_table(
                lots_table,
                [
                    [
                        self._format_date(row.get("date_expiration")),
                        _format_int(row.get("stock_lot", 0)),
                        _format_int(row.get("jours_restants", 0)),
                        _clean_text(row.get("statut_lot") or "-"),
                    ]
                    for row in lots
                ],
            )

        detail_btn.clicked.connect(refresh_detail)
        product_combo.currentIndexChanged.connect(refresh_detail)
        if product_combo.count() > 1:
            product_combo.setCurrentIndex(1)
        refresh_detail()

    def _build_right_column(self, layout: QVBoxLayout):
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)
        self.kpi_ruptures = StockKpiCard("Ruptures de stock", "fa5s.exclamation-circle", "#e74c3c", "produits")
        self.kpi_expirer = StockKpiCard("Lots a expirer (-30 jours)", "fa5s.calendar-alt", "#f28c28", "lots")
        self.kpi_expires = StockKpiCard("Lots expires", "fa5s.calendar-times", "#7a5acb", "lots")
        self.kpi_valeur = StockKpiCard("Valeur totale du stock", "fa5s.database", "#2d7be5", "FCFA")
        self.kpi_perte = StockKpiCard("Valeur a perdre (-30 jours)", "fa5s.money-bill-wave", "#1f9d55", "FCFA")
        for card in (
            self.kpi_ruptures,
            self.kpi_expirer,
            self.kpi_expires,
            self.kpi_valeur,
            self.kpi_perte,
        ):
            kpi_row.addWidget(card, 1)
        layout.addLayout(kpi_row)

        chart_row = QHBoxLayout()
        chart_row.setSpacing(10)

        self.card_status = SectionCard("Repartition des quantites par statut d'expiration", "fa5s.chart-pie")
        self.card_types = SectionCard("Repartition des quantites par type de produit", "fa5s.chart-pie")
        self.card_alerts = SectionCard("Alertes & notifications", "fa5s.bell")

        self.status_canvas = DonutCanvas()
        self.type_canvas = DonutCanvas()
        self.status_legend = QVBoxLayout()
        self.type_legend = QVBoxLayout()

        self._build_donut_section(self.card_status, self.status_canvas, self.status_legend)
        self._build_donut_section(self.card_types, self.type_canvas, self.type_legend)
        self._build_alert_section()

        chart_row.addWidget(self.card_status, 3)
        chart_row.addWidget(self.card_types, 3)
        chart_row.addWidget(self.card_alerts, 3)
        layout.addLayout(chart_row)

        table_row = QHBoxLayout()
        table_row.setSpacing(10)
        self.card_stock = SectionCard("Stock detaille par produit (apercu)", "fa5s.boxes")
        self.card_top = SectionCard("Top 10 produits les plus consommes", "fa5s.chart-line")
        self.stock_table = self._create_table(4)
        self.top_table = self._create_table(4)
        self._setup_stock_table()
        self._setup_top_table()
        self.card_stock.content_layout.addWidget(self.stock_table)
        self.card_top.content_layout.addWidget(self.top_table)
        self.stock_link = QPushButton("Voir tous les produits")
        self.top_link = QPushButton("Voir le top complet")
        self.card_stock.content_layout.addWidget(self.stock_link, 0, Qt.AlignLeft)
        self.card_top.content_layout.addWidget(self.top_link, 0, Qt.AlignLeft)
        table_row.addWidget(self.card_stock, 1)
        table_row.addWidget(self.card_top, 1)
        layout.addLayout(table_row)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)
        self.card_compare = SectionCard("Comparaison entrees / sorties par mois", "fa5s.exchange-alt")
        self.card_history = SectionCard("Historique des approvisionnements par fournisseur (apercu)", "fa5s.truck-loading")
        self.compare_canvas = BarCanvas()
        self.history_table = self._create_table(5)
        self._setup_history_table()
        self.card_compare.content_layout.addWidget(self.compare_canvas)
        self.card_history.content_layout.addWidget(self.history_table)
        self.history_link = QPushButton("Voir tout l'historique")
        self.card_history.content_layout.addWidget(self.history_link, 0, Qt.AlignLeft)
        bottom_row.addWidget(self.card_compare, 1)
        bottom_row.addWidget(self.card_history, 1)
        layout.addLayout(bottom_row)

        self.card_extra = QFrame()
        extra_layout = QHBoxLayout(self.card_extra)
        extra_layout.setContentsMargins(16, 12, 16, 12)
        extra_layout.setSpacing(18)

        self.extra_icon = QLabel()
        self.extra_icon.setFixedSize(42, 42)
        self.extra_icon.setAlignment(Qt.AlignCenter)
        self.extra_icon.setPixmap(qta.icon("fa5s.lightbulb", color="#f2a51f").pixmap(QSize(22, 22)))

        extra_text_wrap = QVBoxLayout()
        extra_text_wrap.setContentsMargins(0, 0, 0, 0)
        extra_text_wrap.setSpacing(6)
        self.extra_title = QLabel("Autres fonctionnalites utiles a integrer")
        extra_text_wrap.addWidget(self.extra_title)

        extra_grid = QHBoxLayout()
        extra_grid.setSpacing(20)
        columns = [
            [
                "Recherche avancee (produit, fournisseur, lot, date...)",
                "Filtres : session, fournisseur, statut, periode",
                "Detail d'un lot : entrees, prescriptions utilisees, stock restant",
            ],
            [
                "Detail d'un lot : entrees, prescriptions utilisees, stock restant produits",
            ],
            [
                "Impression des rapports et des historiques",
                "Tableau de bord personnalisable",
            ],
        ]
        self.extra_labels = []
        for items in columns:
            col = QVBoxLayout()
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(4)
            for text in items:
                lbl = QLabel(f"✓  {text}")
                lbl.setWordWrap(True)
                self.extra_labels.append(lbl)
                col.addWidget(lbl)
            col.addStretch()
            extra_grid.addLayout(col, 1)

        extra_text_wrap.addLayout(extra_grid)
        extra_layout.addWidget(self.extra_icon, 0, Qt.AlignTop)
        extra_layout.addLayout(extra_text_wrap, 1)
        layout.addWidget(self.card_extra)
        self.card_extra.hide()
        layout.addStretch()

    def _refresh_left_utilities(self):
        try:
            ruptures = self.ctrl.obtenir_nombre_ruptures(self.code_session)
            lots_expirer = self.ctrl.obtenir_lots_a_expirer(self.code_session) or []
            lots_expires = self.ctrl.obtenir_lots_expires(self.code_session) or []
            stock_faible = self.ctrl.obtenir_stock_faible(self.code_session, seuil=10) or []
        except Exception:
            ruptures = 0
            lots_expirer = []
            lots_expires = []
            stock_faible = []

        lot_focus = lots_expirer[0] if lots_expirer else (lots_expires[0] if lots_expires else None)

        details = {
            "search": (
                f"Session active : {self.code_session or '-'}\n"
                f"Recherche ciblee sur les produits, fournisseurs et lots critiques."
            ),
            "filters": (
                f"{ruptures} rupture(s), {len(stock_faible)} stock(s) faible(s), "
                f"{len(lots_expirer)} lot(s) a expirer."
            ),
            "lot_detail": self._build_lot_focus_text(lot_focus),
        }

        for card in getattr(self, "utility_cards", []):
            card["detail"].setText(details.get(card["key"], ""))

    def _build_lot_focus_text(self, lot_focus: dict | None) -> str:
        if not lot_focus:
            return "Aucun lot critique detecte pour le moment sur la session active."

        designation = _clean_text(lot_focus.get("libelle") or lot_focus.get("code_produit") or "Lot")
        expiration = self._format_date(lot_focus.get("date_expiration"))
        stock_lot = _format_int(lot_focus.get("stock_lot", 0))
        jours = lot_focus.get("jours_restants")

        if jours is None:
            timing = "Statut a surveiller"
        elif int(jours) < 0:
            timing = "Lot deja expire"
        else:
            timing = f"Expire dans {int(jours)} jour(s)"

        return f"{designation} • expiration {expiration}\n{timing} • stock lot: {stock_lot}"

    def _handle_utility_action(self, key: str):
        self._open_left_overlay(key)

    def _set_table_message(self, table: QTableWidget, message: str):
        table.clearContents()
        table.setRowCount(1)
        table.setSpan(0, 0, 1, table.columnCount())
        table.setItem(0, 0, QTableWidgetItem(message))

    def _populate_table(self, table: QTableWidget, rows: list[list[str]]):
        table.clearContents()
        table.setRowCount(0)
        if not rows:
            self._set_table_message(table, "Aucun resultat disponible.")
            return
        for row_data in rows:
            row = table.rowCount()
            table.insertRow(row)
            for col, value in enumerate(row_data):
                table.setItem(row, col, QTableWidgetItem(str(value)))

    def _build_donut_section(self, card: SectionCard, canvas: DonutCanvas, legend_layout: QVBoxLayout):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        legend_widget = QWidget()
        legend_widget.setLayout(legend_layout)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(10)

        row.addWidget(canvas, 3)
        row.addWidget(legend_widget, 2)
        card.content_layout.addLayout(row)

    def _build_alert_section(self):
        self.alert_rows = []
        for color in ("#e74c3c", "#f28c28", "#7a5acb", "#ef5350"):
            row = QFrame()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 4, 0, 4)
            layout.setSpacing(10)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(34, 34)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet(
                f"background:{color}22; border:1px solid {color}55; border-radius:17px;"
            )

            text_wrap = QVBoxLayout()
            text_wrap.setContentsMargins(0, 0, 0, 0)
            text_wrap.setSpacing(1)
            title_lbl = QLabel()
            title_lbl.setWordWrap(True)
            link_lbl = QLabel("Voir la liste")
            text_wrap.addWidget(title_lbl)
            text_wrap.addWidget(link_lbl)

            layout.addWidget(icon_lbl, 0, Qt.AlignTop)
            layout.addLayout(text_wrap, 1)
            self.card_alerts.content_layout.addWidget(row)
            self.alert_rows.append((row, icon_lbl, title_lbl, link_lbl))
        self.card_alerts.content_layout.addStretch()

    def _create_table(self, columns: int) -> QTableWidget:
        table = QTableWidget(0, columns)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)
        table.setMinimumHeight(190)
        return table

    def _setup_stock_table(self):
        headers = ["Designation", "Type", "Quantite totale", "Statut principal"]
        for idx, text in enumerate(headers):
            self.stock_table.setHorizontalHeaderItem(idx, QTableWidgetItem(text))
        hdr = self.stock_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)

    def _setup_top_table(self):
        headers = ["#", "Produit", "Total consomme", "Stock restant"]
        for idx, text in enumerate(headers):
            self.top_table.setHorizontalHeaderItem(idx, QTableWidgetItem(text))
        hdr = self.top_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)

    def _setup_history_table(self):
        headers = ["Date facture", "Fournisseur", "Montant total", "Nb lignes", "Action"]
        for idx, text in enumerate(headers):
            self.history_table.setHorizontalHeaderItem(idx, QTableWidgetItem(text))
        hdr = self.history_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)

    def rafraichir(self):
        if not self.code_session:
            return
        self._refresh_left_utilities()
        self._charger_kpis()
        self._charger_graphique_statut()
        self._charger_graphique_types()
        self._charger_alertes()
        self._charger_table_stock()
        self._charger_table_top()
        self._charger_comparaison()
        self._charger_historique()

    def _charger_kpis(self):
        try:
            ruptures = self.ctrl.obtenir_nombre_ruptures(self.code_session)
            expirer = self.ctrl.obtenir_nombre_lots_a_expirer(self.code_session)
            expires = self.ctrl.obtenir_nombre_lots_expires(self.code_session)
            valeur = self.ctrl.obtenir_valeur_stock(self.code_session)
            perte = self.ctrl.obtenir_valeur_lots_a_expirer(self.code_session)

            self.kpi_ruptures.update_value(_format_int(ruptures), "produits")
            self.kpi_expirer.update_value(_format_int(expirer), "lots")
            self.kpi_expires.update_value(_format_int(expires), "lots")
            self.kpi_valeur.update_value(_format_currency(valeur), "")
            self.kpi_perte.update_value(_format_currency(perte), "")
        except Exception:
            pass

    def _charger_graphique_statut(self):
        c = theme_manager.colors()
        stats = self.ctrl.obtenir_quantites_par_statut_expiration(self.code_session) or {}
        items = [
            ("Expires", int(stats.get("qte_expire", 0) or 0), "#ef5350"),
            ("Bientot (-30j)", int(stats.get("qte_bientot", 0) or 0), "#ff9d2e"),
            ("Valides", int(stats.get("qte_valide", 0) or 0), "#66bb6a"),
        ]
        total = sum(value for _, value, _ in items)
        self.status_canvas.draw_chart(
            [label for label, _, _ in items],
            [value for _, value, _ in items],
            [color for _, _, color in items],
            f"Total\nquantite\n{_format_int(total)}",
        )
        self._fill_legend(self.status_legend, items, total, c["text_primary"])

    def _charger_graphique_types(self):
        c = theme_manager.colors()
        raw = self.ctrl.obtenir_quantites_par_type_produit(self.code_session) or {}
        items = [
            ("Liquide", int(raw.get("Liquide", 0) or 0), "#4a86d1"),
            ("Pommade", int(raw.get("Pommade", 0) or 0), "#7c64c5"),
            ("Comprime", int(raw.get("Comprime", raw.get("ComprimÃ©", 0)) or 0), "#66b36b"),
        ]
        total = sum(value for _, value, _ in items)
        self.type_canvas.draw_chart(
            [label for label, _, _ in items],
            [value for _, value, _ in items],
            [color for _, _, color in items],
            "",
        )
        self._fill_legend(self.type_legend, items, total, c["text_primary"])

    def _fill_legend(self, layout: QVBoxLayout, items, total: int, primary_color: str):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for label, value, color in items:
            pct = (value / total * 100) if total else 0
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"background:{color}; border-radius:6px;")

            text = QLabel(f"{label}\n{_format_int(value)} ({pct:.1f}%)")
            text.setStyleSheet(
                f"color:{primary_color}; font-size:11px; font-weight:600; border:none;"
            )
            text.setWordWrap(True)

            row_layout.addWidget(dot, 0, Qt.AlignTop)
            row_layout.addWidget(text, 1)
            layout.addWidget(row)

        layout.addStretch()

    def _charger_alertes(self):
        ruptures = self.ctrl.obtenir_ruptures_stock(self.code_session) or []
        lots_expirer = self.ctrl.obtenir_lots_a_expirer(self.code_session) or []
        lots_expires = self.ctrl.obtenir_lots_expires(self.code_session) or []
        stock_faible = self.ctrl.obtenir_stock_faible(self.code_session, seuil=10) or []

        data = [
            ("fa5s.exclamation-triangle", f"{len(ruptures)} produit(s) en rupture de stock"),
            ("fa5s.calendar-alt", f"{len(lots_expirer)} lot(s) a expirer dans les 30 jours"),
            ("fa5s.calendar-times", f"{len(lots_expires)} lot(s) deja expires"),
            ("fa5s.prescription-bottle", f"Stock faible (< 10 unites) : {len(stock_faible)} produit(s)"),
        ]
        c = theme_manager.colors()
        colors = [c["danger"], c["warning"], "#7a5acb", "#ef6c63"]

        for (row, icon_lbl, title_lbl, link_lbl), (icon_name, text), color in zip(self.alert_rows, data, colors):
            icon_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(QSize(18, 18)))
            title_lbl.setText(text)
            title_lbl.setStyleSheet(
                f"color:{c['text_primary']}; font-size:12px; font-weight:700; border:none;"
            )
            link_lbl.setStyleSheet(
                f"color:{c['primary']}; font-size:11px; font-weight:600; border:none;"
            )

    def _charger_table_stock(self):
        preview = self._build_stock_preview()
        self.stock_table.setRowCount(0)
        c = theme_manager.colors()
        for item in preview[:5]:
            row = self.stock_table.rowCount()
            self.stock_table.insertRow(row)
            self.stock_table.setItem(row, 0, QTableWidgetItem(item["designation"]))
            self.stock_table.setItem(row, 1, QTableWidgetItem(item["type"]))
            self.stock_table.setItem(row, 2, QTableWidgetItem(_format_int(item["quantite_totale"])))
            status_item = QTableWidgetItem(item["statut"])
            self.stock_table.setItem(row, 3, status_item)
            status_color = {
                "Valide": c["success"],
                "A expirer": c["warning"],
                "Expire": c["danger"],
                "Rupture": c["danger"],
            }.get(item["statut"], c["text_secondary"])
            status_item.setForeground(QColor(status_color))

    def _build_stock_preview(self):
        try:
            lignes = self.ctrl.lister_par_session(self.code_session) or []
            ruptures = {row.get("code_produit") for row in (self.ctrl.obtenir_ruptures_stock(self.code_session) or [])}
            a_expirer = {row.get("code_produit") for row in (self.ctrl.obtenir_lots_a_expirer(self.code_session) or [])}
            expires = {row.get("code_produit") for row in (self.ctrl.obtenir_lots_expires(self.code_session) or [])}
            produits = {}
            for ligne in lignes:
                code = getattr(ligne, "code_produit", None)
                if not code or code in produits:
                    continue
                stock = self.ctrl.obtenir_stock(code, self.code_session) or {}
                quantite = int(stock.get("quantite_actuelle") or 0)
                if quantite <= 0 or code in ruptures:
                    statut = "Rupture"
                elif code in expires:
                    statut = "Expire"
                elif code in a_expirer:
                    statut = "A expirer"
                else:
                    statut = "Valide"

                produits[code] = {
                    "designation": _clean_text(getattr(ligne, "libelle", None) or getattr(ligne, "designation", "") or code),
                    "type": _clean_text(getattr(ligne, "type", "") or "Comprime"),
                    "quantite_totale": quantite,
                    "statut": statut,
                }
            return sorted(
                produits.values(),
                key=lambda item: (-item["quantite_totale"], item["designation"].lower()),
            )
        except Exception:
            return []

    def _charger_table_top(self):
        rows = self.ctrl.obtenir_top_produits_consommes(self.code_session, limite=10) or []
        self.top_table.setRowCount(0)
        c = theme_manager.colors()
        for index, row_data in enumerate(rows, start=1):
            row = self.top_table.rowCount()
            self.top_table.insertRow(row)
            self.top_table.setItem(row, 0, QTableWidgetItem(str(index)))
            self.top_table.setItem(row, 1, QTableWidgetItem(_clean_text(row_data.get("libelle") or row_data.get("code_produit"))))
            self.top_table.setItem(row, 2, QTableWidgetItem(_format_int(row_data.get("total_consomme", 0))))
            stock_item = QTableWidgetItem(_format_int(row_data.get("stock_restant", 0)))
            if int(row_data.get("stock_restant", 0) or 0) <= 0:
                stock_item.setForeground(QColor(c["danger"]))
            self.top_table.setItem(row, 3, stock_item)

    def _charger_comparaison(self):
        stats = self.ctrl.obtenir_comparaison_entrees_sorties(self.code_session) or {}
        self.compare_canvas.draw_chart(stats)

    def _charger_historique(self):
        rows = self._build_history_preview()
        self.history_table.setRowCount(0)
        c = theme_manager.colors()
        for item in rows[:5]:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QTableWidgetItem(item["date_facture"]))
            self.history_table.setItem(row, 1, QTableWidgetItem(item["fournisseur"]))
            self.history_table.setItem(row, 2, QTableWidgetItem(item["montant_total"]))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(item["nb_lignes"])))
            action = QTableWidgetItem("Voir")
            action.setForeground(QColor(c["primary"]))
            self.history_table.setItem(row, 4, action)

    def _build_history_preview(self):
        try:
            lignes = self.ctrl.lister_par_session(self.code_session) or []
            fournisseurs = sorted(
                {getattr(ligne, "code_fournisseur", None) for ligne in lignes if getattr(ligne, "code_fournisseur", None)}
            )
            factures = {}
            for code_fournisseur in fournisseurs:
                historique = self.ctrl.obtenir_historique_fournisseur(code_fournisseur, self.code_session) or []
                for row in historique:
                    code_facture = row.get("code_facture_four")
                    if not code_facture:
                        continue
                    factures.setdefault(
                        code_facture,
                        {
                            "date_obj": _to_date(row.get("date_facture_four")),
                            "date_facture": self._format_date(row.get("date_facture_four")),
                            "fournisseur": self._build_fournisseur_label(row),
                            "montant_total": _format_currency(row.get("montant_total", 0)),
                            "nb_lignes": 0,
                        },
                    )
                    factures[code_facture]["nb_lignes"] += 1
            return sorted(
                factures.values(),
                key=lambda item: item["date_obj"] or datetime.min.date(),
                reverse=True,
            )
        except Exception:
            return []

    def _build_fournisseur_label(self, row: dict) -> str:
        nom = _clean_text(row.get("fournisseur_nom") or "")
        prenom = _clean_text(row.get("fournisseur_prenom") or "")
        label = f"{nom} {prenom}".strip()
        return label or _clean_text(row.get("code_fournisseur") or "Fournisseur")

    def _format_date(self, value) -> str:
        dt = _to_date(value)
        if not dt:
            return str(value or "-")
        return dt.strftime("%d/%m/%Y")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "left_overlay"):
            self._update_left_overlay_geometry(hidden=not self.left_overlay.isVisible())

    def apply_theme(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"background:{c['bg_main']};")
        self.scroll.setStyleSheet(f"background:{c['bg_main']}; border:none;")

        self.title_lbl.setStyleSheet(
            f"color:{c['text_primary']}; font-size:28px; font-weight:900; border:none;"
        )
        self.subtitle_lbl.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:15px; font-weight:600; border:none;"
        )

        for panel in (self.left_panel, self.right_panel):
            panel["frame"].setStyleSheet(
                f"QFrame {{ background:{c['bg_card']}; border:1px solid {c['border']}; border-radius:16px; }}"
            )
            panel["header"].setStyleSheet(
                f"background:{c['primary']}; color:{c['text_inverse']};"
                "font-size:12px; font-weight:900; padding-left:16px; border-top-left-radius:16px; border-top-right-radius:16px;"
            )

        for item in getattr(self, "utility_cards", []):
            item["card"].setStyleSheet(
                f"QFrame {{ background:{c['bg_card']}; border:1px solid {c['border_light']}; border-radius:14px; }}"
            )
            item["title"].setStyleSheet(
                f"color:{c['text_primary']}; font-size:12px; font-weight:800; border:none;"
            )
            item["desc"].setStyleSheet(
                f"color:{c['text_secondary']}; font-size:11px; font-weight:500; border:none;"
            )
            item["badge"].setStyleSheet(
                f"background:{item['color']}22; color:{item['color']}; border:1px solid {item['color']}55; "
                "border-radius:10px; font-size:10px; font-weight:800; padding:4px 8px;"
            )
            item["detail"].setStyleSheet(
                f"color:{c['text_primary']}; font-size:11px; font-weight:600; border:none;"
            )
            item["action"].setStyleSheet(
                f"QPushButton {{ background-color:{item['color']}; color:{c['text_inverse']}; "
                f"border:0px; border-radius:10px; padding:6px 10px; font-size:11px; font-weight:700; }}"
                f"QPushButton:hover {{ background-color:{c['primary_hover']}; }}"
            )
            item["action"].setCursor(Qt.PointingHandCursor)
            for chip in item["chips"]:
                chip.setStyleSheet(
                    f"background:{c['bg_table_alt']}; color:{c['text_secondary']}; border:1px solid {c['border']}; "
                    "border-radius:10px; font-size:10px; font-weight:700; padding:3px 8px;"
                )

        if hasattr(self, "left_overlay"):
            self.left_overlay.setStyleSheet(
                f"QFrame {{ background:{c['bg_card']}; border:1px solid {c['border']}; border-radius:16px; }}"
                f"QFrame#searchProductCard {{ background:white; border:1px solid {c['border_light']}; border-radius:12px; }}"
                f"QLabel {{ color:{c['text_primary']}; border:none; }}"
                f"QLineEdit, QComboBox, QTextEdit {{ background:{c['bg_main']}; color:{c['text_primary']}; "
                f"border:1px solid {c['border']}; border-radius:10px; padding:8px; font-size:11px; }}"
                f"QPushButton {{ background:{c['primary']}; color:{c['text_inverse']}; border:none; "
                f"border-radius:10px; padding:8px 16px; font-size:11px; font-weight:700; }}"
                f"QPushButton:hover {{ background:{c['primary_hover']}; }}"
                f"QTableWidget {{ border:1px solid {c['border_light']}; background:{c['bg_card']}; "
                f"alternate-background-color:{c['bg_table_alt']}; gridline-color:{c['border_light']}; color:{c['text_primary']}; font-size:11px; }}"
                f"QHeaderView::section {{ background:{c['primary']}; color:{c['text_inverse']}; border:none; padding:8px; font-size:11px; font-weight:800; }}"
            )
            self.left_overlay_title.setStyleSheet(
                f"color:{c['text_primary']}; font-size:15px; font-weight:900; border:none;"
            )
            self.left_overlay_subtitle.setStyleSheet(
                f"color:{c['text_secondary']}; font-size:11px; font-weight:600; border:none;"
            )
            self.left_overlay_summary.setStyleSheet(
                f"background:{c['bg_table_alt']}; color:{c['text_primary']}; border:1px solid {c['border_light']}; "
                "border-radius:12px; padding:10px; font-size:11px; font-weight:600;"
            )
            self.left_overlay_close.setStyleSheet(
                f"QPushButton {{ background-color:{c['hover']}; color:{c['text_primary']}; "
                f"border:1px solid {c['border']}; border-radius:10px; padding:7px 12px; "
                f"font-size:11px; font-weight:700; }}"
                f"QPushButton:hover {{ background-color:{c['bg_table_alt']}; }}"
            )
            self.left_overlay_close.setCursor(Qt.PointingHandCursor)
            self._update_left_overlay_geometry(hidden=not self.left_overlay.isVisible())

        for card in (
            self.kpi_ruptures,
            self.kpi_expirer,
            self.kpi_expires,
            self.kpi_valeur,
            self.kpi_perte,
        ):
            card.apply_theme()

        for card in (
            self.card_status,
            self.card_types,
            self.card_alerts,
            self.card_stock,
            self.card_top,
            self.card_compare,
            self.card_history,
        ):
            card.apply_theme()

        table_style = (
            f"QTableWidget {{ border:none; background:{c['bg_card']}; alternate-background-color:{c['bg_table_alt']};"
            f" gridline-color:{c['border_light']}; color:{c['text_primary']}; font-size:11px; }}"
            f"QHeaderView::section {{ background:{c['primary']}; color:{c['text_inverse']}; border:none; padding:8px; font-size:11px; font-weight:800; }}"
            f"QTableWidget::item {{ padding:6px; }}"
            f"QTableWidget::item:selected {{ background:{c['primary_light']}; color:{c['text_primary']}; }}"
        )
        for table in (self.stock_table, self.top_table, self.history_table):
            table.setStyleSheet(table_style)

        link_style = (
            f"QPushButton {{ background-color:transparent; border:0px; color:{c['primary']}; font-size:11px; font-weight:700; padding:0px; }}"
            f"QPushButton:hover {{ color:{c['primary_hover']}; }}"
        )
        for btn in (self.stock_link, self.top_link, self.history_link):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(link_style)

        self.rafraichir()
