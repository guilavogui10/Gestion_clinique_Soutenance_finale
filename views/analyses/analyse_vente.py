"""
Dashboard d'analyse des ventes base sur panier_facture.

Cette vue affiche uniquement la partie utile de la maquette:
- KPI de la session
- graphes de repartition / top revenus / volume vs revenus
- detail d'une facture, top volume et evolution mensuelle
- alertes et insights
"""

from __future__ import annotations

from typing import List, Dict

import qtawesome as qta
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from views.shared.theme_manager import theme_manager


EXPECTED_SERVICES = [
    "Consultation",
    "Examen",
    "Chirurgie",
    "Lunettes",
    "Pharmacie",
]

SERVICE_COLORS = {
    "Consultation": "#3B82F6",
    "Examen": "#22C55E",
    "Chirurgie": "#F97316",
    "Lunettes": "#8B5CF6",
    "Pharmacie": "#EF4444",
}


def _fmt_int(value) -> str:
    try:
        return f"{int(value):,}".replace(",", " ")
    except Exception:
        return "0"


def _fmt_money(value, decimals: int = 0) -> str:
    try:
        amount = float(value or 0)
        if decimals > 0:
            return f"{amount:,.{decimals}f}".replace(",", " ") + " GNF"
        return f"{amount:,.0f}".replace(",", " ") + " GNF"
    except Exception:
        return "0 GNF"


def _safe_ratio(part, total) -> float:
    try:
        part = float(part or 0)
        total = float(total or 0)
        return round((part / total) * 100, 1) if total > 0 else 0.0
    except Exception:
        return 0.0


class VenteKpiCard(QFrame):
    def __init__(self, title: str, icon_name: str, accent_color: str, subtitle: str = ""):
        super().__init__()
        self._title = title
        self._icon_name = icon_name
        self._accent_color = accent_color

        self.setMinimumHeight(92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 24))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.icon_wrap = QLabel()
        self.icon_wrap.setFixedSize(44, 44)
        self.icon_wrap.setAlignment(Qt.AlignCenter)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        self.lbl_title = QLabel(title)
        self.lbl_title.setWordWrap(True)
        self.lbl_value = QLabel("0")
        self.lbl_subtitle = QLabel(subtitle)
        self.lbl_subtitle.setWordWrap(True)

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_value)
        text_layout.addWidget(self.lbl_subtitle)

        layout.addWidget(self.icon_wrap, 0, Qt.AlignTop)
        layout.addLayout(text_layout, 1)

        self.apply_theme()

    def update_content(self, value: str, subtitle: str = ""):
        self.lbl_value.setText(value)
        self.lbl_subtitle.setText(subtitle)

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"QFrame {{ background:{c['bg_card']}; border:1px solid {c['border']}; border-radius:16px; }}"
        )
        self.icon_wrap.setStyleSheet(
            f"background:{self._accent_color}22; border:1px solid {self._accent_color}55; border-radius:22px;"
        )
        self.icon_wrap.setPixmap(
            qta.icon(self._icon_name, color=self._accent_color).pixmap(QSize(22, 22))
        )
        self.lbl_title.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:9px; font-weight:800; border:none;"
        )
        self.lbl_value.setStyleSheet(
            f"color:{self._accent_color}; font-size:18px; font-weight:900; border:none;"
        )
        self.lbl_subtitle.setStyleSheet(
            f"color:{c['text_muted']}; font-size:9px; font-weight:600; border:none;"
        )


class VenteSectionCard(QFrame):
    def __init__(self, title: str, icon_name: str):
        super().__init__()
        self._title = title
        self._icon_name = icon_name
        self.setObjectName("vente_section_card")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(10, 10, 10, 10)
        self.root.setSpacing(3)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(18, 18)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl = QLabel(title)
        self.title_lbl.setWordWrap(False)
        self.sep = QFrame()
        self.sep.setObjectName("vente_section_sep")
        self.sep.setFixedHeight(1)

        header.addWidget(self.icon_lbl)
        header.addWidget(self.title_lbl, 1)

        self.root.addLayout(header)
        self.root.addWidget(self.sep)

        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(3)
        self.root.addLayout(self.content_layout, 1)

        self.apply_theme()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"QFrame#vente_section_card {{"
            f" background:{c['bg_card']};"
            f" border:1px solid {c['border']};"
            f" border-radius:18px;"
            f"}}"
            f"QFrame#vente_section_sep {{"
            f" background:{c['border']};"
            f" border:none;"
            f" border-radius:0px;"
            f"}}"
        )
        self.icon_lbl.setPixmap(
            qta.icon(self._icon_name, color=c["primary"]).pixmap(QSize(15, 15))
        )
        self.icon_lbl.setStyleSheet("background:transparent; border:none; padding:0px; margin:0px;")
        self.title_lbl.setStyleSheet(
            f"color:{c['text_primary']}; font-size:11px; font-weight:900; border:none; background:transparent; padding:0px; margin:0px;"
        )


class SimpleFigureCanvas(FigureCanvas):
    def __init__(self, width=4, height=3):
        self.figure = Figure(figsize=(width, height), dpi=100, facecolor="none")
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(150)
        self.setMaximumHeight(180)

    def clear(self):
        self.figure.clear()
        self.axes = self.figure.add_subplot(111)


class InsightMiniCard(QFrame):
    def __init__(self, icon_name: str, accent_color: str):
        super().__init__()
        self._icon_name = icon_name
        self._accent_color = accent_color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        self.icon_wrap = QLabel()
        self.icon_wrap.setFixedSize(34, 34)
        self.icon_wrap.setAlignment(Qt.AlignCenter)

        self.title_lbl = QLabel("-")
        self.title_lbl.setWordWrap(True)
        self.desc_lbl = QLabel("-")
        self.desc_lbl.setWordWrap(True)

        layout.addWidget(self.icon_wrap, 0, Qt.AlignLeft)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.desc_lbl)
        layout.addStretch()

        self.apply_theme()

    def update_content(self, title: str, description: str):
        self.title_lbl.setText(title)
        self.desc_lbl.setText(description)

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"QFrame {{ background:{c['bg_card']}; border:1px solid {c['border_light']}; border-radius:14px; }}"
        )
        self.icon_wrap.setStyleSheet(
            f"background:{self._accent_color}22; border:1px solid {self._accent_color}55; border-radius:17px;"
        )
        self.icon_wrap.setPixmap(
            qta.icon(self._icon_name, color=self._accent_color).pixmap(QSize(18, 18))
        )
        self.title_lbl.setStyleSheet(
            f"color:{c['text_primary']}; font-size:10px; font-weight:800; border:none;"
        )
        self.desc_lbl.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:9px; font-weight:600; border:none;"
        )


class AnalyseVenteView(QWidget):
    def __init__(self, vente_ctrl, code_session):
        super().__init__()
        self.ctrl = vente_ctrl
        self.code_session = code_session

        self.resume = {}
        self.repartition = []
        self.top_revenus = []
        self.volume_revenus = []
        self.apercu_facture = {}
        self.top_volume = []
        self.evolution = {}

        self._init_ui()
        self.rafraichir()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.scroll.setWidget(self.container)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        self._build_header()
        self._build_kpis()
        self._build_graphs()
        self._build_bottom()

        root.addWidget(self.scroll)
        self.apply_theme()

    def _build_header(self):
        self.header_card = QFrame()
        self.header_layout = QVBoxLayout(self.header_card)
        self.header_layout.setContentsMargins(12, 12, 12, 12)
        self.header_layout.setSpacing(2)

        self.title_lbl = QLabel("Dashboard facturation - panier_facture")
        self.subtitle_lbl = QLabel(
            "Vue d'ensemble des revenus generes par les services factures aux patients"
        )

        self.header_layout.addWidget(self.title_lbl)
        self.header_layout.addWidget(self.subtitle_lbl)
        self.main_layout.addWidget(self.header_card)

    def _build_kpis(self):
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setContentsMargins(0, 0, 0, 0)
        self.kpi_grid.setHorizontalSpacing(8)
        self.kpi_grid.setVerticalSpacing(8)

        self.card_ca = VenteKpiCard("Chiffre d'affaires total", "fa5s.wallet", "#16A34A")
        self.card_services = VenteKpiCard("Nombre total de services", "fa5s.receipt", "#2563EB")
        self.card_factures = VenteKpiCard("Nombre total de factures", "fa5s.file-invoice", "#EA580C")
        self.card_panier = VenteKpiCard("Panier moyen par facture", "fa5s.shopping-bag", "#7C3AED")
        self.card_top = VenteKpiCard("Service le plus rentable", "fa5s.trophy", "#E11D48")

        cards = [
            self.card_ca,
            self.card_services,
            self.card_factures,
            self.card_panier,
            self.card_top,
        ]
        for index, card in enumerate(cards):
            self.kpi_grid.addWidget(card, 0, index)

        self.main_layout.addLayout(self.kpi_grid)

    def _build_graphs(self):
        self.graphs_grid = QGridLayout()
        self.graphs_grid.setContentsMargins(0, 0, 0, 0)
        self.graphs_grid.setHorizontalSpacing(10)
        self.graphs_grid.setVerticalSpacing(10)

        self.section_repartition = VenteSectionCard("Repartition des revenus par service", "fa5s.chart-pie")
        self.canvas_repartition = SimpleFigureCanvas(width=3.3, height=1.8)
        self.legend_repartition = QLabel()
        self.legend_repartition.setWordWrap(True)
        self.legend_repartition.setMaximumHeight(40)
        self.section_repartition.content_layout.addWidget(self.canvas_repartition)
        self.section_repartition.content_layout.addWidget(self.legend_repartition)
        self.section_repartition.setMinimumHeight(245)
        self.section_repartition.setMaximumHeight(270)

        self.section_top_revenus = VenteSectionCard("Top 5 services", "fa5s.chart-bar")
        self.canvas_top_revenus = SimpleFigureCanvas(width=3.2, height=1.8)
        self.section_top_revenus.content_layout.addWidget(self.canvas_top_revenus)
        self.section_top_revenus.setMinimumHeight(245)
        self.section_top_revenus.setMaximumHeight(270)

        self.section_volume_revenus = VenteSectionCard("Volume vs revenus", "fa5s.chart-area")
        self.canvas_volume_revenus = SimpleFigureCanvas(width=3.6, height=1.8)
        self.section_volume_revenus.content_layout.addWidget(self.canvas_volume_revenus)
        self.section_volume_revenus.setMinimumHeight(245)
        self.section_volume_revenus.setMaximumHeight(270)

        self.graphs_grid.addWidget(self.section_repartition, 0, 0)
        self.graphs_grid.addWidget(self.section_top_revenus, 0, 1)
        self.graphs_grid.addWidget(self.section_volume_revenus, 0, 2)

        self.main_layout.addLayout(self.graphs_grid)

    def _build_bottom(self):
        self.bottom_grid = QGridLayout()
        self.bottom_grid.setContentsMargins(0, 0, 0, 0)
        self.bottom_grid.setHorizontalSpacing(10)
        self.bottom_grid.setVerticalSpacing(10)

        self.section_facture = VenteSectionCard("Detail des lignes d'une facture", "fa5s.table")
        self.tbl_facture = self._create_table(
            ["#", "Designation", "Ref. source", "Quantite", "Prix applique", "Total ligne"],
            stretch_columns={1},
        )
        self.lbl_total_facture = QLabel("Total facture : 0 GNF")
        self.section_facture.content_layout.addWidget(self.tbl_facture)
        self.section_facture.content_layout.addWidget(self.lbl_total_facture)
        self.section_facture.setMinimumHeight(255)
        self.section_facture.setMaximumHeight(285)

        self.section_top_volume = VenteSectionCard("Top 10 services", "fa5s.list-ol")
        self.tbl_top_volume = self._create_table(
            ["#", "Service", "Nombre", "% du total"],
            stretch_columns={1},
        )
        self.section_top_volume.content_layout.addWidget(self.tbl_top_volume)
        self.section_top_volume.setMinimumHeight(255)
        self.section_top_volume.setMaximumHeight(285)

        self.section_evolution = VenteSectionCard("Evolution du chiffre", "fa5s.chart-line")
        self.canvas_evolution = SimpleFigureCanvas(width=3.6, height=1.8)
        self.section_evolution.content_layout.addWidget(self.canvas_evolution)
        self.section_evolution.setMinimumHeight(255)
        self.section_evolution.setMaximumHeight(285)

        self.bottom_grid.addWidget(self.section_facture, 0, 0)
        self.bottom_grid.addWidget(self.section_top_volume, 0, 1)
        self.bottom_grid.addWidget(self.section_evolution, 0, 2)

        self.main_layout.addLayout(self.bottom_grid)

        self.final_grid = QGridLayout()
        self.final_grid.setContentsMargins(0, 0, 0, 0)
        self.final_grid.setHorizontalSpacing(10)
        self.final_grid.setVerticalSpacing(10)

        self.alert_section = VenteSectionCard("Alertes et anomalies", "fa5s.exclamation-triangle")
        self.alert_cards_layout = QHBoxLayout()
        self.alert_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.alert_cards_layout.setSpacing(8)
        self.alert_card_1 = InsightMiniCard("fa5s.bell", "#EF4444")
        self.alert_card_2 = InsightMiniCard("fa5s.chart-line", "#F59E0B")
        self.alert_card_3 = InsightMiniCard("fa5s.file-invoice-dollar", "#F97316")
        self.alert_cards_layout.addWidget(self.alert_card_1)
        self.alert_cards_layout.addWidget(self.alert_card_2)
        self.alert_cards_layout.addWidget(self.alert_card_3)
        self.alert_section.content_layout.addLayout(self.alert_cards_layout)
        self.alert_section.setMinimumHeight(145)
        self.alert_section.setMaximumHeight(170)

        self.insight_section = VenteSectionCard("Analyses et insights", "fa5s.lightbulb")
        self.insight_cards_layout = QHBoxLayout()
        self.insight_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.insight_cards_layout.setSpacing(8)
        self.insight_card_1 = InsightMiniCard("fa5s.chart-pie", "#16A34A")
        self.insight_card_2 = InsightMiniCard("fa5s.rocket", "#2563EB")
        self.insight_card_3 = InsightMiniCard("fa5s.bullseye", "#EA580C")
        self.insight_card_4 = InsightMiniCard("fa5s.calendar-alt", "#7C3AED")
        self.insight_cards_layout.addWidget(self.insight_card_1)
        self.insight_cards_layout.addWidget(self.insight_card_2)
        self.insight_cards_layout.addWidget(self.insight_card_3)
        self.insight_cards_layout.addWidget(self.insight_card_4)
        self.insight_section.content_layout.addLayout(self.insight_cards_layout)
        self.insight_section.setMinimumHeight(145)
        self.insight_section.setMaximumHeight(170)

        self.final_grid.addWidget(self.alert_section, 0, 0)
        self.final_grid.addWidget(self.insight_section, 0, 1)
        self.final_grid.setColumnStretch(0, 1)
        self.final_grid.setColumnStretch(1, 2)

        self.main_layout.addLayout(self.final_grid)

    def _create_table(self, headers: List[str], stretch_columns=None) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setMinimumHeight(150)
        table.setMaximumHeight(170)

        header = table.horizontalHeader()
        stretch_columns = stretch_columns or set()
        for idx in range(len(headers)):
            mode = QHeaderView.Stretch if idx in stretch_columns else QHeaderView.ResizeToContents
            header.setSectionResizeMode(idx, mode)
        return table

    def rafraichir(self):
        self._charger_donnees()
        self._mettre_a_jour_kpis()
        self._dessiner_repartition()
        self._dessiner_top_revenus()
        self._dessiner_volume_vs_revenus()
        self._remplir_facture()
        self._remplir_top_volume()
        self._dessiner_evolution()
        self._mettre_a_jour_alertes_insights()

    def _charger_donnees(self):
        self.resume = self.ctrl.obtenir_resume_economie_session(self.code_session) or {}
        self.repartition = self.ctrl.obtenir_repartition_par_service(self.code_session) or []
        self.top_revenus = self.ctrl.obtenir_top_services_par_revenus(self.code_session, 5) or []
        self.volume_revenus = self.ctrl.obtenir_volume_vs_revenus_par_service(self.code_session) or []
        self.apercu_facture = self.ctrl.obtenir_derniere_facture_payee_apercu(self.code_session) or {}
        self.top_volume = self.ctrl.obtenir_top_services_par_volume(self.code_session, 10) or []
        self.evolution = self.ctrl.obtenir_evolution_chiffre_affaires_par_mois(self.code_session) or {}

    def _mettre_a_jour_kpis(self):
        self.card_ca.update_content(
            _fmt_money(self.resume.get("chiffre_affaires_total", 0)),
            "Toutes factures payees",
        )
        self.card_services.update_content(
            _fmt_int(self.resume.get("nombre_services_factures", 0)),
            "Lignes de services",
        )
        self.card_factures.update_content(
            _fmt_int(self.resume.get("nombre_factures_payees", 0)),
            "Factures payees",
        )
        self.card_panier.update_content(
            _fmt_money(self.resume.get("panier_moyen_facture", 0)),
            "Montant moyen",
        )

        top_service = self.resume.get("service_plus_rentable") or "Aucun service"
        top_total = self.resume.get("montant_service_plus_rentable", 0)
        self.card_top.update_content(top_service, _fmt_money(top_total))

    def _dessiner_repartition(self):
        self.canvas_repartition.clear()
        ax = self.canvas_repartition.axes
        c = theme_manager.colors()

        if not self.repartition:
            self._draw_empty(ax, "Aucune donnee de repartition")
            self.legend_repartition.setText("Aucune donnee disponible pour la session.")
            self.canvas_repartition.draw()
            return

        labels = [row.get("designation", "-") for row in self.repartition]
        values = [float(row.get("total", 0) or 0) for row in self.repartition]
        colors = [SERVICE_COLORS.get(label, c["primary"]) for label in labels]

        total = sum(values)
        ax.pie(
            values,
            startangle=90,
            counterclock=False,
            colors=colors,
            radius=1.08,
            wedgeprops={"width": 0.48, "edgecolor": c["bg_card"]},
        )
        ax.text(
            0, 0,
            "Total\n" + _fmt_money(total).replace(" GNF", "\nGNF"),
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=c["text_primary"],
        )
        ax.set_aspect("equal")
        ax.set_xlim(-1.16, 1.16)
        ax.set_ylim(-1.12, 1.12)

        legend_lines = []
        for row in self.repartition:
            legend_lines.append(
                f"{row.get('designation', '-')}: {_fmt_money(row.get('total', 0))} ({row.get('pourcentage', 0)}%)"
            )
        self.legend_repartition.setText("   |   ".join(legend_lines))
        self.canvas_repartition.figure.subplots_adjust(left=0.04, right=0.96, top=0.96, bottom=0.06)
        self.canvas_repartition.draw()

    def _dessiner_top_revenus(self):
        self.canvas_top_revenus.clear()
        ax = self.canvas_top_revenus.axes
        c = theme_manager.colors()

        if not self.top_revenus:
            self._draw_empty(ax, "Aucun revenu a afficher")
            self.canvas_top_revenus.draw()
            return

        rows = list(reversed(self.top_revenus))
        labels = [row.get("designation", "-") for row in rows]
        values = [float(row.get("total", 0) or 0) for row in rows]
        colors = [SERVICE_COLORS.get(label, c["primary"]) for label in labels]

        bars = ax.barh(labels, values, height=0.42, color=colors, alpha=0.9)
        ax.grid(True, axis="x", linestyle="--", linewidth=0.6, alpha=0.25, color=c["border"])
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", colors=c["text_secondary"], labelsize=7)
        ax.tick_params(axis="y", colors=c["text_primary"], labelsize=8)
        for spine in ax.spines.values():
            spine.set_visible(False)

        for bar, value in zip(bars, values):
            ax.text(
                bar.get_width() + max(values) * 0.02 if max(values) else 0.2,
                bar.get_y() + bar.get_height() / 2,
                _fmt_money(value),
                va="center",
                ha="left",
                fontsize=7,
                color=c["text_primary"],
            )

        self.canvas_top_revenus.figure.subplots_adjust(left=0.28, right=0.94, top=0.90, bottom=0.18)
        self.canvas_top_revenus.draw()

    def _dessiner_volume_vs_revenus(self):
        self.canvas_volume_revenus.clear()
        c = theme_manager.colors()

        if not self.volume_revenus:
            self._draw_empty(self.canvas_volume_revenus.axes, "Aucune comparaison disponible")
            self.canvas_volume_revenus.draw()
            return

        ax = self.canvas_volume_revenus.axes
        ax2 = ax.twinx()

        labels = [row.get("designation", "-") for row in self.volume_revenus]
        volumes = [int(row.get("nombre", 0) or 0) for row in self.volume_revenus]
        revenues = [float(row.get("total", 0) or 0) for row in self.volume_revenus]
        x_positions = list(range(len(labels)))

        bars_vol = ax.bar(
            [x - 0.13 for x in x_positions],
            volumes,
            width=0.22,
            color=c["info"],
            alpha=0.85,
            label="Nombre de services",
        )
        bars_rev = ax2.bar(
            [x + 0.13 for x in x_positions],
            revenues,
            width=0.22,
            color=c["success"],
            alpha=0.72,
            label="Revenus",
        )

        ax.set_xticks(x_positions)
        ax.set_xticklabels(labels, fontsize=7, color=c["text_primary"])
        ax.tick_params(axis="y", colors=c["text_secondary"], labelsize=7)
        ax2.tick_params(axis="y", colors=c["success"], labelsize=7)
        ax.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.2, color=c["border"])
        ax.set_axisbelow(True)

        for spine in ax.spines.values():
            spine.set_visible(False)
        for spine in ax2.spines.values():
            spine.set_visible(False)

        for bar, value in zip(bars_vol, volumes):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                _fmt_int(value),
                ha="center",
                va="bottom",
                fontsize=6,
                color=c["info"],
            )
        for bar, value in zip(bars_rev, revenues):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                self._compact_money(value),
                ha="center",
                va="bottom",
                fontsize=6,
                color=c["success"],
            )

        handles = [bars_vol, bars_rev]
        labels_leg = ["Nombre de services", "Revenus (GNF)"]
        ax.legend(handles, labels_leg, loc="upper left", frameon=False, fontsize=7, handlelength=1.4)
        self.canvas_volume_revenus.figure.subplots_adjust(left=0.08, right=0.91, top=0.88, bottom=0.24)
        self.canvas_volume_revenus.draw()

    def _remplir_facture(self):
        lignes = self.apercu_facture.get("lignes", []) or []
        self.tbl_facture.setRowCount(0)

        for index, row in enumerate(lignes, start=1):
            table_row = self.tbl_facture.rowCount()
            self.tbl_facture.insertRow(table_row)
            values = [
                str(index),
                str(row.get("designation", "-")),
                str(row.get("numero_reference", "-")),
                _fmt_int(row.get("quantite_facture", 0)),
                _fmt_money(row.get("prix_applique", 0)),
                _fmt_money(row.get("total_ligne", 0)),
            ]
            for col, value in enumerate(values):
                self.tbl_facture.setItem(table_row, col, QTableWidgetItem(value))

        code_facture = self.apercu_facture.get("code_facture") or "Aucune facture"
        total = self.apercu_facture.get("total_facture", 0)
        self.lbl_total_facture.setText(
            f"{code_facture}  |  Total facture : {_fmt_money(total)}"
        )

    def _remplir_top_volume(self):
        self.tbl_top_volume.setRowCount(0)
        for index, row in enumerate(self.top_volume, start=1):
            table_row = self.tbl_top_volume.rowCount()
            self.tbl_top_volume.insertRow(table_row)
            values = [
                str(index),
                str(row.get("designation", "-")),
                _fmt_int(row.get("nombre", 0)),
                f"{float(row.get('pourcentage', 0) or 0):.1f} %",
            ]
            for col, value in enumerate(values):
                self.tbl_top_volume.setItem(table_row, col, QTableWidgetItem(value))

    def _dessiner_evolution(self):
        self.canvas_evolution.clear()
        ax = self.canvas_evolution.axes
        c = theme_manager.colors()

        if not self.evolution:
            self._draw_empty(ax, "Aucune evolution disponible")
            self.canvas_evolution.draw()
            return

        months = list(self.evolution.keys())
        values = [float(self.evolution.get(month, 0) or 0) for month in months]
        x_positions = list(range(len(months)))

        ax.plot(
            x_positions,
            values,
            color=c["primary"],
            linewidth=2.0,
            marker="o",
            markersize=4,
        )
        ax.fill_between(x_positions, values, color=c["primary"], alpha=0.12)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(months, fontsize=7, color=c["text_primary"])
        ax.tick_params(axis="y", colors=c["text_secondary"], labelsize=7)
        ax.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.24, color=c["border"])
        ax.set_axisbelow(True)

        for spine in ax.spines.values():
            spine.set_visible(False)

        for x_pos, value in zip(x_positions, values):
            if value > 0:
                ax.text(
                    x_pos,
                    value,
                    self._compact_money(value),
                    ha="center",
                    va="bottom",
                    fontsize=6,
                    color=c["text_primary"],
                )

        self.canvas_evolution.figure.subplots_adjust(left=0.08, right=0.96, top=0.88, bottom=0.22)
        self.canvas_evolution.draw()

    def _mettre_a_jour_alertes_insights(self):
        total_ca = float(self.resume.get("chiffre_affaires_total", 0) or 0)
        top_name = self.resume.get("service_plus_rentable") or "Aucun service"
        top_total = float(self.resume.get("montant_service_plus_rentable", 0) or 0)
        top_share = _safe_ratio(top_total, total_ca)

        services_presents = {row.get("designation", "") for row in self.repartition}
        services_absents = [service for service in EXPECTED_SERVICES if service not in services_presents]

        bascule = 0.0
        if len(self.evolution or {}) >= 2:
            values = [float(v or 0) for v in self.evolution.values()]
            previous_non_zero = next((v for v in reversed(values[:-1]) if v > 0), 0)
            last_value = values[-1] if values else 0
            bascule = round(((last_value - previous_non_zero) / previous_non_zero) * 100, 1) if previous_non_zero > 0 else 0.0

        if services_absents:
            self.alert_card_1.update_content(
                "Services sans revenu",
                f"{len(services_absents)} service(s) sans revenu sur la session : {', '.join(services_absents[:3])}.",
            )
        else:
            self.alert_card_1.update_content(
                "Couverture complete",
                "Tous les services attendus ont genere au moins un revenu sur la session.",
            )

        if bascule < 0:
            self.alert_card_2.update_content(
                "Tendance en baisse",
                f"Le dernier mois actif est en retrait de {abs(bascule):.1f}% par rapport au mois precedent actif.",
            )
        else:
            self.alert_card_2.update_content(
                "Tendance stable/hausse",
                "La courbe mensuelle ne montre pas de baisse recente significative.",
            )

        pending_count = max(
            0,
            int(self.resume.get("nombre_factures_payees", 0) or 0) - len(self.apercu_facture.get("lignes", []) or []),
        )
        self.alert_card_3.update_content(
            "Controle de factures",
            f"{pending_count} element(s) a verifier dans l'aperu courant apres agregration panier.",
        )

        self.insight_card_1.update_content(
            "Contribution majeure",
            f"{top_name} represente environ {top_share:.1f}% du chiffre d'affaires total.",
        )

        potentiel = self._best_potential_service()
        self.insight_card_2.update_content(
            "Fort potentiel",
            potentiel,
        )

        optimisation = self._optimisation_message()
        self.insight_card_3.update_content(
            "Optimisation",
            optimisation,
        )

        if bascule > 0:
            forecast = f"Tendance haussiere recente : +{bascule:.1f}% sur le dernier mois actif."
        elif bascule < 0:
            forecast = f"Tendance baissiere recente : {bascule:.1f}% sur le dernier mois actif."
        else:
            forecast = "Tendance encore neutre : pas assez d'ecart pour projeter un signal fort."
        self.insight_card_4.update_content("Previsionnel", forecast)

    def _best_potential_service(self) -> str:
        if not self.volume_revenus:
            return "Pas assez de donnees pour degager un potentiel clair."

        ranked = []
        for row in self.volume_revenus:
            volume = float(row.get("nombre", 0) or 0)
            revenu = float(row.get("total", 0) or 0)
            if volume <= 0:
                continue
            rendement = revenu / volume
            ranked.append((volume, rendement, row.get("designation", "-"), revenu))

        if not ranked:
            return "Pas assez de donnees pour degager un potentiel clair."

        ranked.sort(key=lambda item: (-item[0], item[1]))
        volume, rendement, designation, revenu = ranked[0]
        return (
            f"{designation} combine un volume de {_fmt_int(volume)} avec un rendement moyen de "
            f"{_fmt_money(rendement)} par ligne."
        )

    def _optimisation_message(self) -> str:
        if not self.top_volume:
            return "Aucune piste d'optimisation detectee."

        low_margin = min(
            self.top_volume,
            key=lambda row: float(row.get("total", 0) or 0) / max(float(row.get("nombre", 1) or 1), 1),
        )
        designation = low_margin.get("designation", "-")
        avg = float(low_margin.get("total", 0) or 0) / max(float(low_margin.get("nombre", 1) or 1), 1)
        return f"{designation} semble avoir le revenu unitaire le plus faible parmi les services les plus frequents ({_fmt_money(avg)} par ligne)."

    def _draw_empty(self, ax, message: str):
        c = theme_manager.colors()
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            fontsize=11,
            color=c["text_muted"],
            transform=ax.transAxes,
        )

    def _compact_money(self, value: float) -> str:
        try:
            value = float(value or 0)
            if value >= 1_000_000:
                return f"{value / 1_000_000:.2f}M"
            if value >= 1_000:
                return f"{value / 1_000:.0f}K"
            return f"{value:.0f}"
        except Exception:
            return "0"

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background:{c['bg_main']};")
        self.scroll.setStyleSheet(
            f"QScrollArea {{ background:{c['bg_main']}; border:none; }}"
        )
        self.container.setStyleSheet(f"background:{c['bg_main']};")

        self.header_card.setStyleSheet(
            f"QFrame {{ background:{c['bg_card']}; border:1px solid {c['border']}; border-radius:18px; }}"
        )
        self.title_lbl.setStyleSheet(
            f"color:{c['primary']}; font-size:22px; font-weight:900; border:none;"
        )
        self.subtitle_lbl.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:10px; font-weight:600; border:none;"
        )
        self.legend_repartition.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:9px; font-weight:700; border:none;"
        )
        self.lbl_total_facture.setStyleSheet(
            f"color:{c['success']}; font-size:10px; font-weight:900; border:none;"
        )

        for card in (
            self.card_ca,
            self.card_services,
            self.card_factures,
            self.card_panier,
            self.card_top,
        ):
            card.apply_theme()

        for section in (
            self.section_repartition,
            self.section_top_revenus,
            self.section_volume_revenus,
            self.section_facture,
            self.section_top_volume,
            self.section_evolution,
            self.alert_section,
            self.insight_section,
        ):
            section.apply_theme()

        for mini in (
            self.alert_card_1,
            self.alert_card_2,
            self.alert_card_3,
            self.insight_card_1,
            self.insight_card_2,
            self.insight_card_3,
            self.insight_card_4,
        ):
            mini.apply_theme()

        self._apply_table_theme(self.tbl_facture)
        self._apply_table_theme(self.tbl_top_volume)

        self.rafraichir()

    def _apply_table_theme(self, table: QTableWidget):
        c = theme_manager.colors()
        table.setStyleSheet(
            f"QTableWidget {{"
            f" background:{c['bg_card']};"
            f" alternate-background-color:{c['bg_table_alt']};"
            f" color:{c['text_primary']};"
            f" border:none;"
            f" gridline-color:{c['border_light']};"
            f"}}"
            f"QHeaderView::section {{"
            f" background:{c['table_header_bg']};"
            f" color:{c['text_primary']};"
            f" border:none;"
            f" border-bottom:1px solid {c['table_header_border']};"
            f" padding:5px;"
            f" font-size:9px;"
            f" font-weight:800;"
            f"}}"
            f"QTableWidget::item {{ padding:5px; border:none; font-size:9px; }}"
            f"QTableWidget::item:selected {{ background:{c['table_selection']}; }}"
        )
