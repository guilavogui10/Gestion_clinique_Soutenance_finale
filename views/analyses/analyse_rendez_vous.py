"""
Dashboard d'analyse des rendez-vous pour l'interface administrateur.
Vue d'ensemble de la session active avec KPI, graphes, tableaux et alertes.
"""

from collections import Counter
from datetime import datetime

import qtawesome as qta
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from views.shared.theme_manager import theme_manager


class _TC:
    def __init__(self, key):
        self._key = key

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype=None):
        return theme_manager.colors()[self._key]


class ModernTheme:
    primary = _TC("primary")
    success = _TC("success")
    warning = _TC("warning")
    danger = _TC("danger")
    info = _TC("info")
    accent = _TC("accent")
    text = _TC("text_primary")
    subtext = _TC("text_secondary")
    muted = _TC("text_muted")
    inverse = _TC("text_inverse")
    surface = _TC("bg_card")
    surface_alt = _TC("bg_input")
    bg_main = _TC("bg_main")
    border = _TC("border")
    border_light = _TC("border_light")
    hover = _TC("hover")


class BaseCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rdv_card")
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(18)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 28))
        self.setGraphicsEffect(self._shadow)
        self.apply_theme()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"""
            QFrame#rdv_card {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 18px;
            }}
            """
        )


class HeaderInfoCard(BaseCard):
    def __init__(self, titre: str, valeur: str, icone: str, parent=None):
        self._icone_nom = icone
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        self.lbl_titre = QLabel(titre)
        self.lbl_icone = QLabel()
        self.lbl_icone.setFixedSize(18, 18)
        top.addWidget(self.lbl_titre)
        top.addStretch()
        top.addWidget(self.lbl_icone)
        layout.addLayout(top)

        self.lbl_valeur = QLabel(valeur)
        layout.addWidget(self.lbl_valeur)
        self.apply_theme()

    def set_value(self, valeur: str):
        self.lbl_valeur.setText(valeur)

    def apply_theme(self):
        super().apply_theme()
        c = theme_manager.colors()
        if hasattr(self, 'lbl_titre') and self.lbl_titre:
            self.lbl_titre.setStyleSheet(
                f"color:{c['text_secondary']}; font-size:12px; font-weight:600; border:none;"
            )
        if hasattr(self, 'lbl_valeur') and self.lbl_valeur:
            self.lbl_valeur.setStyleSheet(
                f"color:{c['text_primary']}; font-size:22px; font-weight:700; border:none;"
            )
        if hasattr(self, 'lbl_icone') and self.lbl_icone and hasattr(self, '_icone_nom'):
            self.lbl_icone.setPixmap(qta.icon(self._icone_nom, color=c["text_secondary"]).pixmap(QSize(16, 16)))


class FeatureItem(BaseCard):
    def __init__(self, titre: str, description: str, icone: str, couleur: str, parent=None):
        self._icone_nom = icone
        self._couleur = couleur
        
        # Créer les widgets AVANT d'appeler super().__init__()
        # car BaseCard.apply_theme() sera appelé et a besoin de ces attributs
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.icon_wrap = QLabel()
        self.icon_wrap.setFixedSize(38, 38)
        self.icon_wrap.setAlignment(Qt.AlignCenter)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)
        self.lbl_titre = QLabel(titre)
        self.lbl_desc = QLabel(description)
        self.lbl_desc.setWordWrap(True)
        text_col.addWidget(self.lbl_titre)
        text_col.addWidget(self.lbl_desc)

        layout.addWidget(self.icon_wrap, 0, Qt.AlignTop)
        layout.addLayout(text_col, 1)
        
        # Appliquer le thème après avoir créé tous les widgets
        self.apply_theme()

    def apply_theme(self):
        super().apply_theme()
        c = theme_manager.colors()
        
        # Vérifier que les widgets existent avant de les styliser
        if hasattr(self, 'icon_wrap') and self.icon_wrap:
            self.icon_wrap.setStyleSheet(
                f"background:{self._couleur}; border:none; border-radius:19px;"
            )
            self.icon_wrap.setPixmap(qta.icon(self._icone_nom, color=c["text_inverse"]).pixmap(QSize(18, 18)))
        
        if hasattr(self, 'lbl_titre') and self.lbl_titre:
            self.lbl_titre.setStyleSheet(
                f"color:{c['text_primary']}; font-size:13px; font-weight:700; border:none;"
            )
        
        if hasattr(self, 'lbl_desc') and self.lbl_desc:
            self.lbl_desc.setStyleSheet(
                f"color:{c['text_secondary']}; font-size:12px; line-height:1.4; border:none;"
            )


class KPIBox(BaseCard):
    def __init__(self, titre: str, valeur: str, sous_titre: str, icone: str, couleur: str, parent=None):
        self._icone_nom = icone
        self._couleur = couleur
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(0)

        self.icon_wrap = QLabel()
        self.icon_wrap.setFixedSize(54, 54)
        self.icon_wrap.setAlignment(Qt.AlignCenter)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(2)
        self.lbl_titre = QLabel(titre)
        self.lbl_valeur = QLabel(valeur)
        self.lbl_sous_titre = QLabel(sous_titre)
        self.lbl_sous_titre.setWordWrap(True)
        content.addWidget(self.lbl_titre)
        content.addWidget(self.lbl_valeur)
        content.addWidget(self.lbl_sous_titre)

        layout.addWidget(self.icon_wrap, 0, Qt.AlignTop)
        layout.addLayout(content, 1)
        self.apply_theme()

    def update_values(self, valeur: str, sous_titre: str = None):
        self.lbl_valeur.setText(valeur)
        if sous_titre is not None:
            self.lbl_sous_titre.setText(sous_titre)

    def apply_theme(self):
        super().apply_theme()
        c = theme_manager.colors()
        if hasattr(self, 'icon_wrap') and self.icon_wrap and hasattr(self, '_couleur') and hasattr(self, '_icone_nom'):
            self.icon_wrap.setStyleSheet(
                f"background:{self._couleur}; border:none; border-radius:27px;"
            )
            self.icon_wrap.setPixmap(qta.icon(self._icone_nom, color=c["text_inverse"]).pixmap(QSize(24, 24)))
        if hasattr(self, 'lbl_titre') and self.lbl_titre and hasattr(self, '_couleur'):
            self.lbl_titre.setStyleSheet(
                f"color:{self._couleur}; font-size:12px; font-weight:800; border:none; text-transform:uppercase;"
            )
        if hasattr(self, 'lbl_valeur') and self.lbl_valeur:
            self.lbl_valeur.setStyleSheet(
                f"color:{c['text_primary']}; font-size:20px; font-weight:800; border:none;"
            )
        if hasattr(self, 'lbl_sous_titre') and self.lbl_sous_titre:
            self.lbl_sous_titre.setStyleSheet(
                f"color:{c['text_secondary']}; font-size:12px; font-weight:500; border:none;"
            )


class SectionFrame(BaseCard):
    def __init__(self, titre: str, parent=None):
        self._titre = titre
        super().__init__(parent)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(14, 12, 14, 12)
        self.main_layout.setSpacing(10)

        self.lbl_titre = QLabel(titre)
        self.main_layout.addWidget(self.lbl_titre)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(8)
        self.main_layout.addWidget(self.body, 1)
        self.apply_theme()

    def apply_theme(self):
        super().apply_theme()
        c = theme_manager.colors()
        if hasattr(self, 'lbl_titre') and self.lbl_titre:
            self.lbl_titre.setStyleSheet(
                f"color:{c['primary']}; font-size:13px; font-weight:800; border:none;"
            )


class StatusBadge(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(80)
        self.setFixedHeight(24)

    def set_status(self, statut: str):
        couleur = AnalyseRendezVousView.status_color(statut)
        texte = AnalyseRendezVousView.pretty_status(statut)
        self.setText(texte)
        self.setStyleSheet(
            f"""
            QLabel {{
                background:{couleur}22;
                color:{couleur};
                border:none;
                border-radius:12px;
                padding:2px 10px;
                font-size:11px;
                font-weight:700;
            }}
            """
        )


class StyledTable(QTableWidget):
    def __init__(self, columns, parent=None):
        super().__init__(0, len(columns), parent)
        self.setHorizontalHeaderLabels(columns)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setMinimumSectionSize(64)
        self.setAlternatingRowColors(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.apply_theme()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"""
            QTableWidget {{
                background: transparent;
                color: {c['text_primary']};
                border: none;
                gridline-color: {c['border_light']};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background: transparent;
                color: {c['text_primary']};
                border: none;
                border-bottom: 1px solid {c['border_light']};
                padding: 8px 6px;
                font-size: 11px;
                font-weight: 800;
                text-align: left;
            }}
            QTableWidget::item {{
                border: none;
                border-bottom: 1px solid {c['border_light']};
                padding: 8px 6px;
            }}
            """
        )


class RankBarRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.lbl_rank = QLabel("-")
        self.lbl_name = QLabel("--")
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(10)
        self.lbl_value = QLabel("0")
        layout.addWidget(self.lbl_rank, 0)
        layout.addWidget(self.lbl_name, 1)
        layout.addWidget(self.bar, 3)
        layout.addWidget(self.lbl_value, 0)
        self.apply_theme()

    def update_row(self, rank: int, name: str, total: int, max_value: int):
        self.lbl_rank.setText(str(rank))
        self.lbl_name.setText(name)
        self.lbl_value.setText(str(total))
        self.bar.setMaximum(max(max_value, 1))
        self.bar.setValue(total)

    def apply_theme(self):
        c = theme_manager.colors()
        self.lbl_rank.setStyleSheet(
            f"color:{c['text_primary']}; font-size:12px; font-weight:800; border:none;"
        )
        self.lbl_name.setStyleSheet(
            f"color:{c['text_primary']}; font-size:12px; font-weight:600; border:none;"
        )
        self.lbl_value.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:12px; font-weight:700; border:none;"
        )
        self.bar.setStyleSheet(
            f"""
            QProgressBar {{
                background:{c['bg_input']};
                border:none;
                border-radius:5px;
            }}
            QProgressBar::chunk {{
                background:{c['accent']};
                border-radius:5px;
            }}
            """
        )


class AlertBox(QFrame):
    def __init__(self, titre: str, description: str, icone: str, couleur: str, parent=None):
        self._icone_nom = icone
        self._couleur = couleur
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.icon_wrap = QLabel()
        self.icon_wrap.setFixedSize(42, 42)
        self.icon_wrap.setAlignment(Qt.AlignCenter)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(3)
        self.lbl_titre = QLabel(titre)
        self.lbl_desc = QLabel(description)
        self.lbl_desc.setWordWrap(True)
        self.lbl_link = QLabel("Voir la liste ->")
        content.addWidget(self.lbl_titre)
        content.addWidget(self.lbl_desc)
        content.addWidget(self.lbl_link)

        layout.addWidget(self.icon_wrap, 0, Qt.AlignTop)
        layout.addLayout(content, 1)
        self.apply_theme()

    def set_texts(self, titre: str, description: str):
        self.lbl_titre.setText(titre)
        self.lbl_desc.setText(description)

    def apply_theme(self):
        c = theme_manager.colors()
        if hasattr(self, '_couleur'):
            self.setStyleSheet(
                f"""
                QFrame {{
                    background:{self._couleur}10;
                    border:1px solid {self._couleur}33;
                    border-radius:16px;
                }}
                """
            )
        if hasattr(self, 'icon_wrap') and self.icon_wrap and hasattr(self, '_couleur') and hasattr(self, '_icone_nom'):
            self.icon_wrap.setStyleSheet(
                f"background:{self._couleur}; border:none; border-radius:21px;"
            )
            self.icon_wrap.setPixmap(qta.icon(self._icone_nom, color=c["text_inverse"]).pixmap(QSize(18, 18)))
        if hasattr(self, 'lbl_titre') and self.lbl_titre:
            self.lbl_titre.setStyleSheet(
                f"color:{c['text_primary']}; font-size:18px; font-weight:800; border:none;"
            )
        if hasattr(self, 'lbl_desc') and self.lbl_desc:
            self.lbl_desc.setStyleSheet(
                f"color:{c['text_secondary']}; font-size:12px; font-weight:500; border:none;"
            )
        if hasattr(self, 'lbl_link') and self.lbl_link:
            self.lbl_link.setStyleSheet(
                f"color:{c['primary']}; font-size:12px; font-weight:700; border:none;"
            )


class DonutChart(FigureCanvas):
    ORDER = [
        ("attente", "Attente"),
        ("confirme", "Confirme"),
        ("en_cours", "En cours"),
        ("termine", "Termine"),
        ("annule", "Annule"),
        ("absent", "Absent"),
        ("reporte", "Reporte"),
    ]

    def __init__(self, parent=None):
        self.theme = ModernTheme()
        self.fig = Figure(figsize=(3.3, 2.35), dpi=100, facecolor="none")
        self.ax_pie = self.fig.add_subplot(121)
        self.ax_legend = self.fig.add_subplot(122)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background:transparent;")

    def draw_chart(self, data: dict, total: int):
        self.ax_pie.clear()
        self.ax_legend.clear()
        self.ax_pie.set_facecolor("none")
        self.ax_legend.set_facecolor("none")
        colors = {
            "attente": theme_manager.color("info"),
            "confirme": theme_manager.color("success"),
            "en_cours": theme_manager.color("warning"),
            "termine": theme_manager.color("accent"),
            "annule": theme_manager.color("danger"),
            "absent": "#B7791F",
            "reporte": "#EC4899",
        }
        values = []
        labels = []
        cols = []
        for key, label in self.ORDER:
            value = int((data or {}).get(key, 0) or 0)
            if value > 0:
                values.append(value)
                labels.append((key, label))
                cols.append(colors.get(key, theme_manager.color("text_muted")))

        if not values:
            values = [1]
            cols = [theme_manager.color("border_light")]

        self.ax_pie.pie(
            values,
            colors=cols,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.45, edgecolor=theme_manager.color("bg_card")),
        )
        self.ax_pie.text(
            0,
            0.08,
            "Total",
            ha="center",
            va="bottom",
            color=theme_manager.color("text_secondary"),
            fontsize=10,
            fontweight="600",
        )
        self.ax_pie.text(
            0,
            -0.02,
            f"{int(total):,}".replace(",", " "),
            ha="center",
            va="center",
            color=theme_manager.color("text_primary"),
            fontsize=17,
            fontweight="800",
        )
        self.ax_pie.text(
            0,
            -0.23,
            "RDV",
            ha="center",
            va="center",
            color=theme_manager.color("text_secondary"),
            fontsize=10,
            fontweight="600",
        )
        self.ax_pie.axis("equal")

        self.ax_legend.axis("off")
        y = 0.9
        for key, label in self.ORDER:
            value = int((data or {}).get(key, 0) or 0)
            pct = ((value / total) * 100.0) if total else 0.0
            self.ax_legend.text(0.02, y, "■", color=colors.get(key, "#999999"), fontsize=9, va="center")
            self.ax_legend.text(
                0.12, y, label, color=theme_manager.color("text_primary"),
                fontsize=10, va="center", fontweight="600"
            )
            self.ax_legend.text(
                0.98, y, f"{value} ({pct:.1f}%)".replace(".", ","),
                color=theme_manager.color("text_secondary"), fontsize=9,
                va="center", ha="right"
            )
            y -= 0.12

        self.fig.subplots_adjust(left=0.03, right=0.98, top=0.95, bottom=0.05, wspace=0.04)
        self.draw()


class HourBarChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(3.3, 2.35), dpi=100, facecolor="none")
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background:transparent;")

    def draw_chart(self, hour_counts: dict):
        self.ax.clear()
        self.ax.set_facecolor("none")
        hours = list(range(8, 19))
        values = [int(hour_counts.get(h, 0)) for h in hours]
        bars = self.ax.bar(
            range(len(hours)),
            values,
            color=theme_manager.color("info"),
            width=0.42,
            edgecolor=theme_manager.color("info"),
            alpha=0.92,
        )
        for idx, bar in enumerate(bars):
            val = values[idx]
            self.ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + (0.3 if val > 0 else 0.15),
                str(val),
                ha="center",
                va="bottom",
                fontsize=9,
                color=theme_manager.color("text_primary"),
                fontweight="700",
            )
        self.ax.set_xticks(range(len(hours)))
        self.ax.set_xticklabels([f"{h:02d}h" for h in hours], color=theme_manager.color("text_secondary"), fontsize=9)
        self.ax.tick_params(axis="y", colors=theme_manager.color("text_secondary"), labelsize=9, length=0)
        self.ax.grid(True, axis="y", linestyle="-", alpha=0.08, color=theme_manager.color("border"))
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
        self.fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.12)
        self.draw()


class TrendLineChart(FigureCanvas):
    MONTHS = ["Jan", "Fev", "Mar", "Avr", "Mai", "Juin", "Juil", "Aout", "Sep", "Oct", "Nov", "Dec"]

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(3.3, 2.35), dpi=100, facecolor="none")
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background:transparent;")

    def draw_chart(self, data: dict):
        self.ax.clear()
        self.ax.set_facecolor("none")
        values = [int((data or {}).get(m, 0) or 0) for m in self.MONTHS]
        x = list(range(len(self.MONTHS)))
        self.ax.plot(
            x,
            values,
            color=theme_manager.color("info"),
            linewidth=2.4,
            marker="o",
            markersize=5,
            markerfacecolor=theme_manager.color("info"),
        )
        self.ax.fill_between(x, values, color=theme_manager.color("info"), alpha=0.12)
        for idx, value in enumerate(values):
            self.ax.text(
                idx,
                value + max(2, max(values or [0]) * 0.02),
                str(value),
                ha="center",
                va="bottom",
                fontsize=8.5,
                color=theme_manager.color("text_primary"),
                fontweight="700",
            )
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(self.MONTHS, fontsize=9, color=theme_manager.color("text_secondary"))
        self.ax.tick_params(axis="y", colors=theme_manager.color("text_secondary"), labelsize=9, length=0)
        self.ax.grid(True, axis="y", linestyle="-", alpha=0.08, color=theme_manager.color("border"))
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
        self.fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.14)
        self.draw()


class AnalyseRendezVousView(QWidget):
    FEATURES = [
        ("Gestion des rendez-vous", "Ajouter, modifier, supprimer un rendez-vous.", "fa5s.calendar-alt", "#2563EB"),
        ("Recherche & filtres", "Rechercher par patient, personnel, statut ou date.", "fa5s.search", "#0F8B8D"),
        ("Gestion des statuts", "Changer le statut d'un rendez-vous.", "fa5s.sync-alt", "#6D4CCB"),
        ("Disponibilites", "Verifier la disponibilite d'un personnel ou d'une visite.", "fa5s.user-md", "#2F9E64"),
        ("Suivi temps reel", "Vue temps reel, RDV proches, oublies et en retard.", "fa5s.chart-bar", "#F97316"),
        ("Statistiques & analyses", "Analyse par statut, par jour, par heure, par mois.", "fa5s.chart-pie", "#7C4DCC"),
        ("Charge du personnel", "Suivi de la charge et alertes de surcharge.", "fa5s.users", "#EF4444"),
        ("Alertes & notifications", "RDV proches, oublies, surcharge personnel.", "fa5s.bell", "#F59E0B"),
        ("Previsions", "Predictions d'affluence et d'absences.", "fa5s.chart-line", "#2563EB"),
    ]

    STATUS_LABELS = {
        "attente": "Attente",
        "confirme": "Confirme",
        "en_cours": "En cours",
        "termine": "Termine",
        "annule": "Annule",
        "absent": "Absent",
        "reporte": "Reporte",
    }

    STATUS_COLORS = {
        "attente": "#F59E0B",
        "confirme": "#16A34A",
        "en_cours": "#FB8C00",
        "termine": "#7C4DCC",
        "annule": "#EF4444",
        "absent": "#A16207",
        "reporte": "#EC4899",
    }

    def __init__(self, controleur, code_session: str, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.code_session = code_session
        self._build_ui()
        self.charger_donnees()
        theme_manager.theme_changed.connect(self.apply_theme)

    @classmethod
    def pretty_status(cls, statut: str) -> str:
        key = str(statut or "").strip().lower()
        return cls.STATUS_LABELS.get(key, str(statut or "-").title())

    @classmethod
    def status_color(cls, statut: str) -> str:
        key = str(statut or "").strip().lower()
        return cls.STATUS_COLORS.get(key, theme_manager.color("text_muted"))

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("background:transparent; border:none;")

        content = QWidget()
        content.setStyleSheet("background:transparent;")
        scroll.setWidget(content)

        layout = QHBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        self.main = QWidget()
        self.main.setMinimumWidth(0)
        self.main.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.main_layout = QVBoxLayout(self.main)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)
        layout.addWidget(self.main, 1)

        self.feature_items = []

        self._build_header()
        self._build_kpi_row()
        self._build_dashboard_rows()

        root.addWidget(scroll)

    def _build_feature_sidebar(self):
        card = BaseCard()
        card.setFixedWidth(260)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(46)
        header.setStyleSheet(
            "background:#203A7A; border:none; border-top-left-radius:18px; border-top-right-radius:18px;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 14, 0)
        lbl = QLabel("FONCTIONNALITES CLES")
        lbl.setStyleSheet("color:white; font-size:14px; font-weight:800; border:none;")
        header_layout.addWidget(lbl)
        layout.addWidget(header)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.setSpacing(8)
        self.feature_items = []
        for titre, desc, icon_name, color in self.FEATURES:
            item = FeatureItem(titre, desc, icon_name, color)
            self.feature_items.append(item)
            body_layout.addWidget(item)
        body_layout.addStretch()
        layout.addWidget(body, 1)
        return card

    def _build_header(self):
        header = QHBoxLayout()
        header.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.calendar-alt", color=theme_manager.color("primary")).pixmap(QSize(32, 32)))
        self.lbl_title = QLabel("DASHBOARD RENDEZ-VOUS - VUE D'ENSEMBLE")
        title_row.addWidget(icon)
        title_row.addWidget(self.lbl_title)
        title_row.addStretch()
        self.lbl_subtitle = QLabel("Tableau de bord administrateur - Analyse et suivi des rendez-vous (session active)")
        title_col.addLayout(title_row)
        title_col.addWidget(self.lbl_subtitle)

        header.addLayout(title_col, 1)

        self.info_session = HeaderInfoCard("Session active", self.code_session or "--", "fa5s.chevron-down")
        self.info_date = HeaderInfoCard("Aujourd'hui", datetime.now().strftime("%d/%m/%Y"), "fa5s.calendar-day")
        header.addWidget(self.info_session)
        header.addWidget(self.info_date)
        self.main_layout.addLayout(header)

        self.lbl_section = QLabel("INDICATEURS CLES - SESSION ACTIVE")
        self.main_layout.addWidget(self.lbl_section)

    def _build_kpi_row(self):
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        self.kpi_total = KPIBox("Total RDV", "0", "Tous statuts", "fa5s.calendar-alt", "#2563EB")
        self.kpi_today = KPIBox("Aujourd'hui", "0", "Rendez-vous", "fa5s.calendar-day", "#2F9E64")
        self.kpi_late = KPIBox("En retard", "0", "(en attente / confirme)", "fa5s.clock", "#F97316")
        self.kpi_presence = KPIBox("Taux de presence", "0%", "(venus / conclus)", "fa5s.check-circle", "#2F9E64")
        self.kpi_conversion = KPIBox("Taux conversion", "0%", "(venus / conclus)", "fa5s.users", "#7C4DCC")
        self.kpi_waiting = KPIBox("Patients en attente de RDV", "0", "Sans rendez-vous", "fa5s.user", "#E91E63")
        self.kpi_cards = [
            self.kpi_total,
            self.kpi_today,
            self.kpi_late,
            self.kpi_presence,
            self.kpi_conversion,
            self.kpi_waiting,
        ]
        for idx, card in enumerate(self.kpi_cards):
            grid.addWidget(card, idx // 3, idx % 3)
        self.main_layout.addLayout(grid)

    def _build_dashboard_rows(self):
        self.row1 = QHBoxLayout()
        self.row1.setSpacing(8)
        self.frame_donut = SectionFrame("REPARTITION DES RENDEZ-VOUS PAR STATUT")
        self.frame_donut.setMinimumHeight(220)
        self.donut = DonutChart()
        self.frame_donut.body_layout.addWidget(self.donut)

        self.frame_hours = SectionFrame("RENDEZ-VOUS AUJOURD'HUI PAR HEURE")
        self.frame_hours.setMinimumHeight(220)
        self.hours_chart = HourBarChart()
        self.frame_hours.body_layout.addWidget(self.hours_chart)

        self.frame_proches = SectionFrame("RDV PROCHES (PROCHAINE HEURE)")
        self.frame_proches.setMinimumHeight(220)
        self.table_proches = StyledTable(["Heure", "Patient", "Personnel", "Motif", "Statut"])
        self.frame_proches.body_layout.addWidget(self.table_proches)

        self.row1.addWidget(self.frame_donut, 1)
        self.row1.addWidget(self.frame_hours, 1)
        self.row1.addWidget(self.frame_proches, 1)
        self.main_layout.addLayout(self.row1)

        self.row2 = QHBoxLayout()
        self.row2.setSpacing(8)
        self.frame_trend = SectionFrame("TENDANCE DES RDV PAR MOIS (CETTE ANNEE)")
        self.frame_trend.setMinimumHeight(220)
        self.trend_chart = TrendLineChart()
        self.frame_trend.body_layout.addWidget(self.trend_chart)

        self.frame_staff = SectionFrame("TOP 5 PERSONNELS (CHARGE TOTALE)")
        self.frame_staff.setMinimumHeight(220)
        self.table_staff = StyledTable(["#", "Personnel", "Fonction", "Total RDV", "Aujourd'hui", "En retard", "Surcharge"])
        self.frame_staff.body_layout.addWidget(self.table_staff)

        self.frame_days = SectionFrame("TOP 5 JOURS LES PLUS CHARGES (GLOBAL)")
        self.frame_days.setMinimumHeight(220)
        self.days_rows = []
        for _ in range(5):
            row = RankBarRow()
            self.days_rows.append(row)
            self.frame_days.body_layout.addWidget(row)
        self.frame_days.body_layout.addStretch()

        self.row2.addWidget(self.frame_trend, 1)
        self.row2.addWidget(self.frame_staff, 1)
        self.row2.addWidget(self.frame_days, 1)
        self.main_layout.addLayout(self.row2)

        self.row3 = QHBoxLayout()
        self.row3.setSpacing(8)
        self.frame_alerts = SectionFrame("ALERTES & NOTIFICATIONS")
        self.frame_alerts.setMinimumHeight(220)
        self.alert_late = AlertBox("0 rendez-vous en retard", "Statut actif depasse", "fa5s.clock", "#EF4444")
        self.alert_close = AlertBox("0 RDV dans la prochaine heure", "A venir tres prochainement", "fa5s.bell", "#F97316")
        self.alert_overload = AlertBox("0 personnels en surcharge", "Depassement du seuil de charge", "fa5s.user-md", "#EF4444")
        self.frame_alerts.body_layout.addWidget(self.alert_late)
        self.frame_alerts.body_layout.addWidget(self.alert_close)
        self.frame_alerts.body_layout.addWidget(self.alert_overload)
        self.frame_alerts.body_layout.addStretch()

        self.frame_predictions = SectionFrame("PREVISIONS D'AFFLUENCE (7 PROCHAINS JOURS)")
        self.frame_predictions.setMinimumHeight(220)
        self.table_predictions = StyledTable(["Date", "Jour", "RDV prevus", "Absents prevus", "Taux absence prevu"])
        self.frame_predictions.body_layout.addWidget(self.table_predictions)
        self.lbl_predictions_link = QLabel("Voir toutes les previsions ->")
        self.frame_predictions.body_layout.addWidget(self.lbl_predictions_link)

        self.frame_oublies = SectionFrame("RDV OUBLIES (DEPASSES)")
        self.frame_oublies.setMinimumHeight(220)
        self.table_oublies = StyledTable(["Heure prevue", "Patient", "Personnel", "Statut", "Retard"])
        self.frame_oublies.body_layout.addWidget(self.table_oublies)
        self.lbl_oublies_link = QLabel("Voir tous les RDV oublies ->")
        self.frame_oublies.body_layout.addWidget(self.lbl_oublies_link)

        self.row3.addWidget(self.frame_alerts, 1)
        self.row3.addWidget(self.frame_predictions, 1)
        self.row3.addWidget(self.frame_oublies, 1)
        self.main_layout.addLayout(self.row3)

    def _safe_call(self, method_name: str, default=None, *args):
        fn = getattr(self.controleur, method_name, None)
        if callable(fn):
            try:
                return fn(self.code_session, *args)
            except TypeError:
                try:
                    return fn(*args)
                except Exception:
                    return default
            except Exception:
                return default
        return default

    def _safe_call_no_session(self, method_name: str, default=None, *args):
        fn = getattr(self.controleur, method_name, None)
        if callable(fn):
            try:
                return fn(*args)
            except Exception:
                return default
        return default

    def _value_from(self, item, *names, default=""):
        if item is None:
            return default
        for name in names:
            if isinstance(item, dict) and name in item:
                value = item.get(name)
                if value is not None:
                    return value
            if hasattr(item, name):
                value = getattr(item, name)
                if value is not None:
                    return value
        return default

    def _patient_name(self, item):
        nom = str(self._value_from(item, "patient_nom", "nom", default="")).strip()
        prenom = str(self._value_from(item, "patient_prenom", "prenom", default="")).strip()
        full = f"{nom} {prenom}".strip()
        return full if full else "-"

    def _personnel_name(self, item):
        nom = str(self._value_from(item, "personnel_nom", "nom", default="")).strip()
        prenom = str(self._value_from(item, "personnel_prenom", "prenom", default="")).strip()
        if nom or prenom:
            return f"{nom} {prenom}".strip()
        code = str(self._value_from(item, "code_personnel", default="")).strip()
        return code or "-"

    def _format_datetime(self, valeur, fmt="%H:%M"):
        if isinstance(valeur, datetime):
            return valeur.strftime(fmt)
        if isinstance(valeur, str):
            for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
                try:
                    return datetime.strptime(valeur, pattern).strftime(fmt)
                except ValueError:
                    continue
            return valeur
        return "-"

    def _to_datetime(self, valeur):
        if isinstance(valeur, datetime):
            return valeur
        if isinstance(valeur, str):
            for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
                try:
                    return datetime.strptime(valeur, pattern)
                except ValueError:
                    continue
        return None

    def _format_percent(self, value) -> str:
        try:
            return f"{float(value):.1f} %".replace(".", ",")
        except Exception:
            return "0,0 %"

    def _aggregate_today_by_hour(self, rdvs):
        counts = {h: 0 for h in range(8, 19)}
        for item in rdvs or []:
            dt = self._to_datetime(self._value_from(item, "date_rendez_vous", default=None))
            if dt:
                counts[dt.hour] = counts.get(dt.hour, 0) + 1
        return counts

    def _translate_day(self, day_value: str) -> str:
        mapping = {
            "Monday": "Lundi",
            "Tuesday": "Mardi",
            "Wednesday": "Mercredi",
            "Thursday": "Jeudi",
            "Friday": "Vendredi",
            "Saturday": "Samedi",
            "Sunday": "Dimanche",
        }
        return mapping.get(str(day_value), str(day_value))

    def _compute_delay_label(self, item):
        dt = self._to_datetime(self._value_from(item, "date_rendez_vous", default=None))
        if not dt:
            return "-"
        delta = datetime.now() - dt
        total_minutes = max(int(delta.total_seconds() // 60), 0)
        heures = total_minutes // 60
        minutes = total_minutes % 60
        if heures > 0:
            return f"{heures}h {minutes:02d}m"
        return f"{minutes} min"

    def _set_table_item(self, table: QTableWidget, row: int, col: int, text: str, color: str = None, align=Qt.AlignLeft | Qt.AlignVCenter):
        item = QTableWidgetItem(text)
        item.setTextAlignment(int(align))
        if color:
            item.setForeground(QColor(color))
        table.setItem(row, col, item)

    def _populate_proches_table(self, rows):
        rows = list(rows or [])[:5]
        self.table_proches.setRowCount(max(len(rows), 1))
        if not rows:
            self._set_table_item(self.table_proches, 0, 0, "--")
            self._set_table_item(self.table_proches, 0, 1, "Aucun rendez-vous proche")
            for col in range(2, 5):
                self._set_table_item(self.table_proches, 0, col, "-")
            return

        for row_idx, item in enumerate(rows):
            self.table_proches.setRowHeight(row_idx, 42)
            self._set_table_item(self.table_proches, row_idx, 0, self._format_datetime(self._value_from(item, "date_rendez_vous")))
            self._set_table_item(self.table_proches, row_idx, 1, self._patient_name(item))
            self._set_table_item(self.table_proches, row_idx, 2, self._personnel_name(item))
            motif = str(self._value_from(item, "type_visite", default="-")).replace("_", " ").title()
            self._set_table_item(self.table_proches, row_idx, 3, motif if motif.strip() else "-")
            badge = StatusBadge()
            badge.set_status(str(self._value_from(item, "statut_rendez_vous", default="-")))
            self.table_proches.setCellWidget(row_idx, 4, badge)

    def _populate_staff_table(self, rows, today_rows, late_rows, overload_rows):
        rows = list(rows or [])[:5]
        self.table_staff.setRowCount(max(len(rows), 1))
        today_counter = Counter()
        late_counter = Counter()
        overload_set = set()

        for item in today_rows or []:
            today_counter[str(self._value_from(item, "code_personnel", default=""))] += 1
        for item in late_rows or []:
            late_counter[str(self._value_from(item, "code_personnel", default=""))] += 1
        for item in overload_rows or []:
            overload_set.add(str(self._value_from(item, "code_personnel", default="")))

        if not rows:
            self._set_table_item(self.table_staff, 0, 0, "1")
            self._set_table_item(self.table_staff, 0, 1, "Aucune donnee")
            for col in range(2, 7):
                self._set_table_item(self.table_staff, 0, col, "-")
            return

        for row_idx, item in enumerate(rows):
            code = str(self._value_from(item, "code_personnel", default=""))
            self.table_staff.setRowHeight(row_idx, 40)
            self._set_table_item(self.table_staff, row_idx, 0, str(row_idx + 1), align=Qt.AlignCenter)
            self._set_table_item(self.table_staff, row_idx, 1, self._personnel_name(item))
            self._set_table_item(self.table_staff, row_idx, 2, str(self._value_from(item, "fonction", "personnel_fonction", default="-")))
            self._set_table_item(self.table_staff, row_idx, 3, str(self._value_from(item, "nombre_rendez_vous", default=0)), align=Qt.AlignCenter)
            self._set_table_item(self.table_staff, row_idx, 4, str(today_counter.get(code, 0)), align=Qt.AlignCenter)
            self._set_table_item(self.table_staff, row_idx, 5, str(late_counter.get(code, 0)), align=Qt.AlignCenter)
            surcharge_text = "!" if code in overload_set else "-"
            surcharge_color = theme_manager.color("danger") if code in overload_set else theme_manager.color("text_secondary")
            self._set_table_item(self.table_staff, row_idx, 6, surcharge_text, color=surcharge_color, align=Qt.AlignCenter)

    def _populate_days_rows(self, rows):
        rows = list(rows or [])[:5]
        max_value = max([int(self._value_from(r, "total", default=0) or 0) for r in rows], default=1)
        for idx, row_widget in enumerate(self.days_rows):
            if idx < len(rows):
                item = rows[idx]
                jour = str(self._value_from(item, "jour", default="-"))
                total = int(self._value_from(item, "total", default=0) or 0)
                row_widget.update_row(idx + 1, jour, total, max_value)
                row_widget.show()
            else:
                row_widget.update_row(idx + 1, "-", 0, 1)
                row_widget.show()

    def _populate_predictions_table(self, rows):
        rows = list(rows or [])[:7]
        self.table_predictions.setRowCount(max(len(rows), 1))
        if not rows:
            self._set_table_item(self.table_predictions, 0, 0, "--")
            self._set_table_item(self.table_predictions, 0, 1, "Aucune prediction")
            for col in range(2, 5):
                self._set_table_item(self.table_predictions, 0, col, "-")
            return

        for row_idx, item in enumerate(rows):
            self.table_predictions.setRowHeight(row_idx, 38)
            date_value = self._value_from(item, "date", default="-")
            if isinstance(date_value, datetime):
                date_txt = date_value.strftime("%d/%m/%Y")
            else:
                date_txt = str(date_value)
            self._set_table_item(self.table_predictions, row_idx, 0, date_txt)
            self._set_table_item(self.table_predictions, row_idx, 1, self._translate_day(str(self._value_from(item, "jour", default="-"))))
            self._set_table_item(self.table_predictions, row_idx, 2, str(self._value_from(item, "rendez_vous_prevus", default=0)), align=Qt.AlignCenter)
            self._set_table_item(self.table_predictions, row_idx, 3, str(self._value_from(item, "absents_prevus", default=0)), align=Qt.AlignCenter)
            self._set_table_item(
                self.table_predictions,
                row_idx,
                4,
                self._format_percent(self._value_from(item, "taux_absence_prevu", default=0.0)),
                align=Qt.AlignCenter,
            )

    def _populate_oublies_table(self, rows):
        rows = list(rows or [])[:5]
        self.table_oublies.setRowCount(max(len(rows), 1))
        if not rows:
            self._set_table_item(self.table_oublies, 0, 0, "--")
            self._set_table_item(self.table_oublies, 0, 1, "Aucun RDV oublie")
            for col in range(2, 5):
                self._set_table_item(self.table_oublies, 0, col, "-")
            return

        for row_idx, item in enumerate(rows):
            self.table_oublies.setRowHeight(row_idx, 40)
            self._set_table_item(self.table_oublies, row_idx, 0, self._format_datetime(self._value_from(item, "date_rendez_vous")))
            self._set_table_item(self.table_oublies, row_idx, 1, self._patient_name(item))
            self._set_table_item(self.table_oublies, row_idx, 2, self._personnel_name(item))
            statut = str(self._value_from(item, "statut_rendez_vous", default="-"))
            self._set_table_item(self.table_oublies, row_idx, 3, self.pretty_status(statut), color=self.status_color(statut), align=Qt.AlignCenter)
            self._set_table_item(self.table_oublies, row_idx, 4, self._compute_delay_label(item), color=theme_manager.color("danger"), align=Qt.AlignCenter)

    def charger_donnees(self):
        if not self.code_session:
            return

        try:
            stats = self._safe_call("obtenir_statistiques_generales", {})
            by_status = self._safe_call("obtenir_rendez_vous_par_statut", {})
            patients_attente = self._safe_call("obtenir_patients_attente_rendez_vous", [])
            rdv_today = self._safe_call("obtenir_rendez_vous_du_jour", [])
            rdv_proches = self._safe_call("obtenir_rendez_vous_proches", [])
            rdv_oublies = self._safe_call("obtenir_rendez_vous_oublies", [])
            charge_personnel = self._safe_call("obtenir_charge_par_personnel", [])
            jours_charges = self._safe_call("obtenir_jours_plus_charges", [])
            predictions = self._safe_call("predire_affluence", [])
            trend_months = self._safe_call("obtenir_rendez_vous_par_mois", {})
            alerts = self._safe_call("obtenir_alertes_rendez_vous", {})
            taux_conversion = self._safe_call("obtenir_taux_conversion", 0.0)

            total = int((stats or {}).get("total", 0) or 0)
            today_total = int((stats or {}).get("aujourd_hui", 0) or 0)
            late_total = int((stats or {}).get("en_retard", 0) or 0)
            presence = float((stats or {}).get("taux_presence", 0.0) or 0.0)
            waiting_total = len(patients_attente or [])

            self.info_session.set_value(self.code_session or "--")
            self.info_date.set_value(datetime.now().strftime("%d/%m/%Y"))

            self.kpi_total.update_values(f"{total:,}".replace(",", " "), "Tous statuts")
            self.kpi_today.update_values(f"{today_total:,}".replace(",", " "), "Rendez-vous")
            self.kpi_late.update_values(f"{late_total:,}".replace(",", " "), "(en attente / confirme)")
            self.kpi_presence.update_values(self._format_percent(presence), "(venus / conclus)")
            self.kpi_conversion.update_values(self._format_percent(taux_conversion), "(venus / conclus)")
            self.kpi_waiting.update_values(f"{waiting_total:,}".replace(",", " "), "Sans rendez-vous")

            self.donut.draw_chart(by_status or {}, total)
            self.hours_chart.draw_chart(self._aggregate_today_by_hour(rdv_today))
            self.trend_chart.draw_chart(trend_months or {})

            self._populate_proches_table(rdv_proches)
            self._populate_staff_table(
                charge_personnel,
                rdv_today,
                rdv_oublies,
                (alerts or {}).get("surcharge_personnel", []),
            )
            self._populate_days_rows(jours_charges)
            self._populate_predictions_table(predictions)
            self._populate_oublies_table(rdv_oublies)

            self.alert_late.set_texts(
                f"{late_total} rendez-vous en retard",
                "Statut actif depasse"
            )
            self.alert_close.set_texts(
                f"{len((alerts or {}).get('proches', []) or [])} RDV dans la prochaine heure",
                "A venir tres prochainement"
            )
            self.alert_overload.set_texts(
                f"{len((alerts or {}).get('surcharge_personnel', []) or [])} personnels en surcharge",
                "Depassement du seuil (>= 12)"
            )
        except Exception as e:
            print(f"[AnalyseRendezVousView] Erreur chargement donnees: {e}")
            import traceback
            traceback.print_exc()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background:{c['bg_main']};")
        self.main.setStyleSheet("background:transparent;")
        self.lbl_title.setStyleSheet(
            f"color:{c['text_primary']}; font-size:24px; font-weight:900; border:none;"
        )
        self.lbl_subtitle.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:13px; font-weight:500; border:none;"
        )
        self.lbl_section.setStyleSheet(
            f"color:{c['primary']}; font-size:14px; font-weight:900; border:none; padding:2px 4px;"
        )
        self.lbl_predictions_link.setStyleSheet(
            f"color:{c['primary']}; font-size:12px; font-weight:700; border:none;"
        )
        self.lbl_oublies_link.setStyleSheet(
            f"color:{c['primary']}; font-size:12px; font-weight:700; border:none;"
        )

        if hasattr(self, "sidebar"):
            self.sidebar.apply_theme()
        for item in self.feature_items:
            item.apply_theme()
        self.info_session.apply_theme()
        self.info_date.apply_theme()
        for card in self.kpi_cards:
            card.apply_theme()
        for frame in [
            self.frame_donut,
            self.frame_hours,
            self.frame_proches,
            self.frame_trend,
            self.frame_staff,
            self.frame_days,
            self.frame_alerts,
            self.frame_predictions,
            self.frame_oublies,
        ]:
            frame.apply_theme()
        for table in [
            self.table_proches,
            self.table_staff,
            self.table_predictions,
            self.table_oublies,
        ]:
            table.apply_theme()
        for row in self.days_rows:
            row.apply_theme()
        self.alert_late.apply_theme()
        self.alert_close.apply_theme()
        self.alert_overload.apply_theme()
        self.charger_donnees()

    def rafraichir(self):
        self.charger_donnees()
