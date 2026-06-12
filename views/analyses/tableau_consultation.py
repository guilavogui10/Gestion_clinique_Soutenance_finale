"""
Tableau consultation:
- filtre par recherche, date, service
- bouton imprimer
- tableau des consultations avec alternance de lignes
- zone graphique par patient (placeholder)
"""

from datetime import datetime, date, timedelta
import re
import numpy as np

import qtawesome as qta
from PySide6.QtCore import QSize, Qt, QPropertyAnimation, QRect, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTableWidget, QHeaderView,
    QTableWidgetItem, QFrame, QSizePolicy, QAbstractItemView, QCheckBox,
    QGraphicsDropShadowEffect, QScrollArea
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from views.shared.modal_theme import MC
from views.shared.theme_manager import theme_manager


class MiniLinearGraph(FigureCanvas):
    MONTH_LABELS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]

    def __init__(self, parent=None, width=3, height=2, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("none")
        self.hover_text = self.fig.text(0.5, 0.95, '', ha='center', va='top', fontsize=9, fontweight='bold')
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background: transparent;")
        self.scatters = []
        self.mpl_connect("motion_notify_event", self._on_hover)
        self.mpl_connect("axes_leave_event", lambda e: self._clear_hover_text())
        self.mpl_connect("figure_leave_event", lambda e: self._clear_hover_text())

    def update_graph(self, data_dict, color, label_text):
        self.axes.clear()
        self.scatters.clear()
        
        # Style
        for spine in self.axes.spines.values():
            spine.set_visible(False)
        self.axes.grid(True, axis="both", linestyle="--", alpha=0.3, color=MC.BORDER, linewidth=0.8)
        self.axes.tick_params(colors=MC.TEXT_SECONDARY, labelsize=7, length=0, pad=4)
        if hasattr(self, 'hover_text'):
            self.hover_text.set_text('')
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.8, bottom=0.2)

        if not data_dict:
            self.fig.tight_layout()
            self.draw()
            return

        x = np.arange(12)
        y = np.zeros(12)
        for k, v in data_dict.items():
            try:
                idx = int(k) - 1
                if 0 <= idx < 12:
                    y[idx] = v
            except ValueError:
                if k in self.MONTH_LABELS:
                    y[self.MONTH_LABELS.index(k)] = v

        if sum(y) == 0:
            self.axes.set_ylim(0, 10)
        else:
            self.axes.set_ylim(0, max(y) * 1.25)
            self.axes.plot(x, y, color=color, linewidth=2.0, alpha=0.9, antialiased=True, zorder=5)
            sc = self.axes.scatter(x, y, color=color, edgecolor=MC.BG_CARD, s=40, zorder=10, linewidth=1.5, alpha=1.0)
            self.scatters.append({'scatter': sc, 'label': label_text, 'x': x, 'y': y})

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.MONTH_LABELS, rotation=45, ha='right')
        self.axes.yaxis.set_visible(False)
        self.draw()

    def _on_hover(self, event):
        if not event.inaxes:
            self._clear_hover_text()
            return
        found = False
        for item in self.scatters:
            cont, ind = item['scatter'].contains(event)
            if cont:
                idx = ind["ind"][0]
                value = item['y'][idx]
                label = item['label']
                month = self.MONTH_LABELS[idx]
                txt = f"{label} en {month} : {int(value)}"
                if self.hover_text.get_text() != txt:
                    self.hover_text.set_text(txt)
                    self.hover_text.set_color(MC.TEXT_PRIMARY)
                    self.fig.canvas.draw_idle()
                found = True
                break
        if not found and self.hover_text.get_text() != '':
            self._clear_hover_text()

    def _clear_hover_text(self):
        self.hover_text.set_text('')
        self.fig.canvas.draw_idle()


class TableauConsultationView(QWidget):
    def __init__(self, consultation_ctrl, code_session):
        super().__init__()
        self.ctrl = consultation_ctrl
        self.code_session = code_session
        self.consultations = []
        self.filtered_consultations = []
        self.graph_service_filters = {
            'examen': None,
            'chirurgie': None,
            'commandelunette': None,
            'prescription': None
        }
        self._init_ui()
        self.charger_consultations(code_session)
        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {MC.BG_MAIN};")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        # Panel gauche : tableau (plus de poids)
        self.left_panel = self._creer_panel_tableau()

        # Panel droit : 2 frames graphiques empilés
        self.right_panel = self._creer_panel_graphique()

        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        content_layout.addWidget(self.left_panel, 6)
        content_layout.addWidget(self.right_panel, 4)

        self.main_layout.addLayout(content_layout)

    def _creer_panel_tableau(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet(
            f"background: {MC.BG_CARD}; border-radius: 18px; border: 1px solid {MC.BORDER_LIGHT};"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tbl_header = self._creer_header("Tableau consultation", "fa5s.table")
        self._tbl_filter = self._creer_zone_filtre()
        self._tbl_table_frame = self._creer_table_frame()
        layout.addWidget(self._tbl_header)
        layout.addWidget(self._tbl_filter)
        layout.addWidget(self._tbl_table_frame, 1)

        return panel

    def _creer_header(self, titre: str, icone: str) -> QWidget:
        header = QFrame()
        header.setStyleSheet(
            f"background: {MC.BG_CARD}; border-top-left-radius: 18px; border-top-right-radius: 18px;"
            f" border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"
            f" border-bottom: 1px solid {MC.BORDER_LIGHT};"
        )
        header.setFixedHeight(44)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6)

        self._header_icon = QLabel()
        self._header_icon.setPixmap(qta.icon(icone, color=MC.PRIMARY).pixmap(QSize(18, 18)))
        self._header_title = QLabel(titre)
        self._header_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {MC.TEXT_PRIMARY};")
        self._header_icone = icone

        layout.addWidget(self._header_icon)
        layout.addWidget(self._header_title)
        layout.addStretch()

        return header

    def _creer_zone_filtre(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"background: {MC.BG_CARD}; border: none; border-bottom: 1px solid {MC.BORDER_LIGHT};")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher ou saisir une date (dd/mm/yyyy)...")
        self.search_input.setFixedHeight(28)
        self.search_input.setMaximumWidth(220)
        self.search_input.setStyleSheet(
            f"border: 1px solid {MC.BORDER}; border-radius: 12px; padding-left: 12px;"
        )
        self.search_input.textChanged.connect(self._actualiser_filtrage)

        self.filter_combo = QComboBox()
        self.filter_combo.setIconSize(QSize(16, 16))
        self._FILTER_ITEMS = [
            ("fa5s.list", "Tous"),
            ("fa5s.calendar-alt", "Date"),
            ("fa5s.stethoscope", "Consultation"),
            ("fa5s.notes-medical", "Consultation avec examen"),
            ("fa5s.user-md", "Chirurgie"),
            ("fa5s.glasses", "Lunette"),
            ("fa5s.pills", "Prescription"),
            ("fa5s.filter", "Entre"),
        ]
        for ico_name, label in self._FILTER_ITEMS:
            self.filter_combo.addItem(qta.icon(ico_name, color=MC.PRIMARY), label)
        self.filter_combo.setFixedHeight(28)
        self.filter_combo.setStyleSheet(
            f"border: 1px solid {MC.BORDER}; border-radius: 10px; padding-left: 8px; font-size: 11px;"
        )
        self.filter_combo.currentIndexChanged.connect(self._on_filter_mode_changed)

        self.btn_print = QPushButton(qta.icon("fa5s.print", color=MC.TEXT_INVERSE), "Imprimer")
        self.btn_print.setFixedHeight(28)
        self.btn_print.setCursor(Qt.PointingHandCursor)
        self.btn_print.setStyleSheet(
            f"background-color: {MC.PRIMARY}; color: {MC.TEXT_INVERSE}; border-radius: 10px; font-weight: 600; font-size: 11px; padding: 0 10px;"
        )
        self.btn_print.clicked.connect(self._imprimer_filtre)

        layout.addWidget(self.search_input, 0, Qt.AlignVCenter)
        layout.addWidget(self.filter_combo, 0, Qt.AlignVCenter)
        layout.addStretch()
        layout.addWidget(self.btn_print, 0, Qt.AlignVCenter)

        return frame

    def _creer_table_frame(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {MC.BG_CARD}; border-bottom-left-radius: 18px; border-bottom-right-radius: 18px;"
        )
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        self.table = QTableWidget(0, 4)
        
        # Créer les en-têtes avec icônes et couleurs
        header_item_0 = QTableWidgetItem()
        icon_code = qta.icon("fa5s.barcode", color=MC.TEXT_INVERSE)
        header_item_0.setIcon(icon_code)
        header_item_0.setText("Code")
        self.table.setHorizontalHeaderItem(0, header_item_0)
        
        header_item_1 = QTableWidgetItem()
        icon_patient = qta.icon("fa5s.user", color=MC.TEXT_INVERSE)
        header_item_1.setIcon(icon_patient)
        header_item_1.setText("Patient")
        self.table.setHorizontalHeaderItem(1, header_item_1)
        
        header_item_2 = QTableWidgetItem()
        icon_service = qta.icon("fa5s.stethoscope", color=MC.TEXT_INVERSE)
        header_item_2.setIcon(icon_service)
        header_item_2.setText("Service")
        self.table.setHorizontalHeaderItem(2, header_item_2)
        
        header_item_3 = QTableWidgetItem()
        icon_date = qta.icon("fa5s.calendar-alt", color=MC.TEXT_INVERSE)
        header_item_3.setIcon(icon_date)
        header_item_3.setText("Date")
        self.table.setHorizontalHeaderItem(3, header_item_3)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            f"QTableWidget {{ border: none; background-color: {MC.BG_CARD}; alternate-background-color: {MC.BG_MAIN}; gridline-color: {MC.BORDER_LIGHT}; }}"
            f"QHeaderView::section {{ background-color: {MC.PRIMARY}; padding: 10px; border: none;"
            f" font-weight: 700; color: {MC.TEXT_INVERSE}; font-size: 11px; }}"
            f"QTableWidget::item {{ padding: 10px; color: {MC.TEXT_PRIMARY}; }}"
            f"QTableWidget::item:selected {{ background: {MC.PRIMARY_LIGHT}; color: {MC.TEXT_PRIMARY}; }}"
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        frame_layout.addWidget(self.table)
        return frame

    def _creer_panel_graphique(self) -> QFrame:
        """Panel droit : un seul QFrame blanc arrondi, 2 graphes empilés dedans."""
        frame = QFrame()
        frame.setStyleSheet(f"background: {MC.BG_CARD}; border-radius: 18px; border: 1px solid {MC.BORDER_LIGHT};")
        frame.setMinimumWidth(200)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(6, 4, 6, 4)
        frame_layout.setSpacing(2)

        # Graphe 1 : Consultations par mois
        self._graph_title1 = QLabel("Consultations par mois")
        self._graph_title1.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {MC.TEXT_PRIMARY};"
        )
        frame_layout.addWidget(self._graph_title1)

        self._filters_frame = self._creer_filtres_graphique()
        frame_layout.addWidget(self._filters_frame)

        self.graph_canvas = MiniLinearGraph(width=3, height=2, dpi=100)
        self.graph_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_canvas.setMinimumHeight(0)
        frame_layout.addWidget(self.graph_canvas, 1)

        # Graphe 2 : Consultations du patient
        self._graph_title2 = QLabel("Consultations du patient")
        self._graph_title2.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {MC.TEXT_PRIMARY};"
        )
        frame_layout.addWidget(self._graph_title2)

        self._patient_frame = self._creer_selecteur_patient()
        frame_layout.addWidget(self._patient_frame)

        self.graph_patient_canvas = MiniLinearGraph(width=3, height=2, dpi=100)
        self.graph_patient_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_patient_canvas.setMinimumHeight(0)
        frame_layout.addWidget(self.graph_patient_canvas, 1)

        return frame

    def _creer_filtres_graphique(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"background: {MC.BG_MAIN}; border-radius: 10px;")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(3)

        self._filters_label = QLabel("Filtrer:")
        self._filters_label.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {MC.TEXT_PRIMARY};")
        layout.addWidget(self._filters_label)

        # Examen
        self.check_examen = QCheckBox("Examen")
        self.check_examen.setIcon(qta.icon("fa5s.stethoscope", color="#0f766e"))
        self.check_examen.setStyleSheet(
            f"QCheckBox {{ color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }} "
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 2px solid {MC.BORDER}; background: {MC.BG_CARD}; }} "
            f"QCheckBox::indicator:checked {{ background: #0f766e; border-color: #0f766e; }} "
            f"QCheckBox::indicator:checked:hover {{ background: #0d5f5f; }}"
        )
        self.check_examen.stateChanged.connect(self._on_graph_filter_changed)

        # Chirurgie
        self.check_chirurgie = QCheckBox("Chirurgie")
        self.check_chirurgie.setIcon(qta.icon("fa5s.user-md", color="#dc2626"))
        self.check_chirurgie.setStyleSheet(
            f"QCheckBox {{ color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }} "
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 2px solid {MC.BORDER}; background: {MC.BG_CARD}; }} "
            f"QCheckBox::indicator:checked {{ background: #dc2626; border-color: #dc2626; }} "
            f"QCheckBox::indicator:checked:hover {{ background: #b91c1c; }}"
        )
        self.check_chirurgie.stateChanged.connect(self._on_graph_filter_changed)

        # Lunette
        self.check_lunette = QCheckBox("Lunette")
        self.check_lunette.setIcon(qta.icon("fa5s.glasses", color="#7c3aed"))
        self.check_lunette.setStyleSheet(
            f"QCheckBox {{ color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }} "
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 2px solid {MC.BORDER}; background: {MC.BG_CARD}; }} "
            f"QCheckBox::indicator:checked {{ background: #7c3aed; border-color: #7c3aed; }} "
            f"QCheckBox::indicator:checked:hover {{ background: #6d28d9; }}"
        )
        self.check_lunette.stateChanged.connect(self._on_graph_filter_changed)

        # Prescription
        self.check_prescription = QCheckBox("Prescription")
        self.check_prescription.setIcon(qta.icon("fa5s.pills", color="#ea580c"))
        self.check_prescription.setStyleSheet(
            f"QCheckBox {{ color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }} "
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 2px solid {MC.BORDER}; background: {MC.BG_CARD}; }} "
            f"QCheckBox::indicator:checked {{ background: #ea580c; border-color: #ea580c; }} "
            f"QCheckBox::indicator:checked:hover {{ background: #c2410c; }}"
        )
        self.check_prescription.stateChanged.connect(self._on_graph_filter_changed)

        for checkbox in [self.check_examen, self.check_chirurgie, self.check_lunette, self.check_prescription]:
            layout.addWidget(checkbox)

        layout.addStretch()
        return frame

    def _creer_selecteur_patient(self) -> QFrame:
        """Crée un sélecteur de patient pour visualiser ses consultations."""
        frame = QFrame()
        frame.setStyleSheet(f"background: {MC.BG_MAIN}; border-radius: 10px;")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        self._patient_label = QLabel("Sélectionner patient:")
        self._patient_label.setPixmap(qta.icon("fa5s.user-friends", color=MC.PRIMARY).pixmap(16, 16))
        self._patient_label.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {MC.TEXT_PRIMARY};")
        layout.addWidget(self._patient_label)

        self.patient_combo = QComboBox()
        self.patient_combo.setStyleSheet(
            f"QComboBox {{ border: 2px solid {MC.BORDER}; border-radius: 8px; padding: 8px 12px; "
            f"background: {MC.BG_CARD}; color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }} "
            f"QComboBox::drop-down {{ border: none; padding-right: 8px; }} "
            f"QComboBox::down-arrow {{ image: url(none); border-left: 4px solid transparent; "
            f"border-right: 4px solid transparent; border-top: 4px solid {MC.TEXT_SECONDARY}; margin-top: 2px; }} "
            f"QComboBox:hover {{ border-color: {MC.PRIMARY}; }} "
            f"QComboBox:focus {{ border-color: {MC.PRIMARY}; }} "
            f"QComboBox QAbstractItemView {{ border: 1px solid {MC.BORDER}; border-radius: 4px; "
            f"background: {MC.BG_CARD}; selection-background-color: {MC.HOVER}; }}"
        )
        self.patient_combo.setFixedHeight(28)
        self.patient_combo.currentIndexChanged.connect(self._actualiser_graphique_patient)
        layout.addWidget(self.patient_combo, 1)

        layout.addStretch()
        return frame

    def apply_theme(self):
        # Main background
        self.setStyleSheet(f"background-color: {MC.BG_MAIN};")
        # Panels
        self.left_panel.setStyleSheet(f"background: {MC.BG_CARD}; border-radius: 18px; border: 1px solid {MC.BORDER_LIGHT};")
        self.right_panel.setStyleSheet(f"background: {MC.BG_CARD}; border-radius: 18px; border: 1px solid {MC.BORDER_LIGHT};")
        # Header
        self._tbl_header.setStyleSheet(
            f"background: {MC.BG_CARD}; border-top-left-radius: 18px; border-top-right-radius: 18px;"
            f" border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"
            f" border-bottom: 1px solid {MC.BORDER_LIGHT};"
        )
        self._header_icon.setPixmap(qta.icon(self._header_icone, color=MC.PRIMARY).pixmap(QSize(18, 18)))
        self._header_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {MC.TEXT_PRIMARY};")
        # Filter zone
        self._tbl_filter.setStyleSheet(f"background: {MC.BG_CARD}; border: none; border-bottom: 1px solid {MC.BORDER_LIGHT};")
        self.search_input.setStyleSheet(f"border: 1px solid {MC.BORDER}; border-radius: 10px; padding-left: 10px; font-size: 11px;")
        self.filter_combo.setStyleSheet(f"border: 1px solid {MC.BORDER}; border-radius: 10px; padding-left: 8px; font-size: 11px;")
        self.btn_print.setStyleSheet(f"background-color: {MC.PRIMARY}; color: {MC.TEXT_INVERSE}; border-radius: 10px; font-weight: 600; font-size: 11px; padding: 0 10px;")
        self.btn_print.setIcon(qta.icon("fa5s.print", color=MC.TEXT_INVERSE))
        # Rebuild filter_combo icons
        for i, (ico_name, _label) in enumerate(self._FILTER_ITEMS):
            self.filter_combo.setItemIcon(i, qta.icon(ico_name, color=MC.PRIMARY))
        # Table
        self._tbl_table_frame.setStyleSheet(
            f"background: {MC.BG_CARD}; border-bottom-left-radius: 18px; border-bottom-right-radius: 18px;"
        )
        self.table.setStyleSheet(
            f"QTableWidget {{ border: none; background-color: {MC.BG_CARD}; alternate-background-color: {MC.BG_MAIN}; gridline-color: {MC.BORDER_LIGHT}; }}"
            f"QHeaderView::section {{ background-color: {MC.PRIMARY}; padding: 6px; border: none;"
            f" font-weight: 700; color: {MC.TEXT_INVERSE}; font-size: 10px; }}"
            f"QTableWidget::item {{ padding: 6px; color: {MC.TEXT_PRIMARY}; font-size: 11px; }}"
            f"QTableWidget::item:selected {{ background: {MC.PRIMARY_LIGHT}; color: {MC.TEXT_PRIMARY}; }}"
        )
        # Graph panel titles
        self._graph_title1.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {MC.TEXT_PRIMARY}; border: none;")
        self._graph_title2.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {MC.TEXT_PRIMARY}; border: none;")
        # Filters frame
        self._filters_frame.setStyleSheet(f"background: {MC.BG_MAIN}; border-radius: 10px;")
        self._filters_label.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {MC.TEXT_PRIMARY};")
        # Checkboxes
        self.check_examen.setStyleSheet(
            f"QCheckBox {{ color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }} "
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 2px solid {MC.BORDER}; background: {MC.BG_CARD}; }} "
            f"QCheckBox::indicator:checked {{ background: #0f766e; border-color: #0f766e; }} "
            f"QCheckBox::indicator:checked:hover {{ background: #0d5f5f; }}"
        )
        self.check_chirurgie.setStyleSheet(
            f"QCheckBox {{ color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }} "
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 2px solid {MC.BORDER}; background: {MC.BG_CARD}; }} "
            f"QCheckBox::indicator:checked {{ background: #dc2626; border-color: #dc2626; }} "
            f"QCheckBox::indicator:checked:hover {{ background: #b91c1c; }}"
        )
        self.check_lunette.setStyleSheet(
            f"QCheckBox {{ color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }} "
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 2px solid {MC.BORDER}; background: {MC.BG_CARD}; }} "
            f"QCheckBox::indicator:checked {{ background: #7c3aed; border-color: #7c3aed; }} "
            f"QCheckBox::indicator:checked:hover {{ background: #6d28d9; }}"
        )
        self.check_prescription.setStyleSheet(
            f"QCheckBox {{ color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }} "
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 2px solid {MC.BORDER}; background: {MC.BG_CARD}; }} "
            f"QCheckBox::indicator:checked {{ background: #ea580c; border-color: #ea580c; }} "
            f"QCheckBox::indicator:checked:hover {{ background: #c2410c; }}"
        )
        # Patient selector
        self._patient_frame.setStyleSheet(f"background: {MC.BG_MAIN}; border-radius: 10px;")
        self._patient_label.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {MC.TEXT_PRIMARY};")
        self._patient_label.setPixmap(qta.icon("fa5s.user-friends", color=MC.PRIMARY).pixmap(16, 16))
        self.patient_combo.setStyleSheet(
            f"QComboBox {{ border: 2px solid {MC.BORDER}; border-radius: 8px; padding: 8px 12px; "
            f"background: {MC.BG_CARD}; color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }} "
            f"QComboBox::drop-down {{ border: none; padding-right: 8px; }} "
            f"QComboBox::down-arrow {{ image: url(none); border-left: 4px solid transparent; "
            f"border-right: 4px solid transparent; border-top: 4px solid {MC.TEXT_SECONDARY}; margin-top: 2px; }} "
            f"QComboBox:hover {{ border-color: {MC.PRIMARY}; }} "
            f"QComboBox:focus {{ border-color: {MC.PRIMARY}; }} "
            f"QComboBox QAbstractItemView {{ border: 1px solid {MC.BORDER}; border-radius: 4px; "
            f"background: {MC.BG_CARD}; selection-background-color: {MC.HOVER}; }}"
        )
        # Graph canvases
        self.graph_canvas.figure.set_facecolor(MC.BG_CARD)
        self.graph_patient_canvas.figure.set_facecolor(MC.BG_CARD)
        # Table header icons (white on PRIMARY bg = text_inverse)
        self.table.horizontalHeaderItem(0).setIcon(qta.icon("fa5s.barcode", color=MC.TEXT_INVERSE))
        self.table.horizontalHeaderItem(1).setIcon(qta.icon("fa5s.user", color=MC.TEXT_INVERSE))
        self.table.horizontalHeaderItem(2).setIcon(qta.icon("fa5s.stethoscope", color=MC.TEXT_INVERSE))
        self.table.horizontalHeaderItem(3).setIcon(qta.icon("fa5s.calendar-alt", color=MC.TEXT_INVERSE))
        # Rebuild patient combo icons
        self._remplir_combo_patients()
        # Redraw graphs
        self._actualiser_graphique()
        self._actualiser_graphique_patient()

    def charger_consultations(self, code_session: str):
        self.code_session = code_session
        try:
            self.consultations = self.ctrl.lister_consultations(code_session) or []
        except Exception:
            self.consultations = []
        
        # Remplir le combo de sélection des patients
        self._remplir_combo_patients()
        self._actualiser_filtrage()

    def _remplir_combo_patients(self):
        """Remplit le combo de sélection des patients."""
        self.patient_combo.blockSignals(True)
        self.patient_combo.clear()
        
        try:
            patients = self.ctrl.obtenir_codes_patients_session(self.code_session)
            if patients:
                self.patient_combo.addItem(qta.icon("fa5s.user-plus", color=MC.TEXT_SECONDARY), "-- Sélectionnez un patient --", None)
                for patient in patients:
                    code = patient.get('code_patient')
                    nom = patient.get('nom', '')
                    prenom = patient.get('prenom', '')
                    a_consulte = patient.get('a_consulte', 0)
                    
                    # Icône différente selon si le patient a consulté
                    if a_consulte:
                        icon = qta.icon("fa5s.user-check", color=MC.PRIMARY)
                        label = f"{code} - {prenom} {nom} ✓"
                    else:
                        icon = qta.icon("fa5s.user", color=MC.TEXT_SECONDARY)
                        label = f"{code} - {prenom} {nom}"
                    
                    self.patient_combo.addItem(icon, label, code)
        except Exception as e:
            print(f"[TableauConsultationView] Erreur remplir_combo_patients: {e}")
        
        self.patient_combo.blockSignals(False)

    def _on_filter_mode_changed(self):
        """Change le placeholder selon le mode de filtrage sélectionné."""
        mode = self.filter_combo.currentText()
        if mode == "Date":
            self.search_input.setPlaceholderText("Saisir une date (dd/mm/yyyy ou yyyy-mm-dd)")
        elif mode == "Entre":
            self.search_input.setPlaceholderText("Saisir un intervalle: dd/mm/yyyy - dd/mm/yyyy")
        else:
            self.search_input.setPlaceholderText("Rechercher par nom, code ou service...")
        
        # Relancer le filtrage avec le nouveau mode
        self._actualiser_filtrage()

    def _actualiser_filtrage(self):
        texte = self.search_input.text().strip()
        filtre = self.filter_combo.currentText()

        self.filtered_consultations = []

        if filtre == "Tous":
            if texte:
                self.filtered_consultations = self._filtrer_par_texte(self.consultations, texte)
            else:
                self.filtered_consultations = self.consultations
        elif filtre == "Date":
            if texte:
                date_obj = self._parse_date(texte)
                if date_obj:
                    result = self.ctrl.rechercher_entre_dates(self.code_session, date_obj, date_obj)
                    self.filtered_consultations = result if result else []
        elif filtre == "Entre":
            if texte:
                dates = self._parse_date_range(texte)
                if dates:
                    date_debut, date_fin = dates
                    print(f"[DEBUG] Filtrage entre dates: {date_debut} - {date_fin}")
                    result = self.ctrl.rechercher_entre_dates(self.code_session, date_debut, date_fin)
                    self.filtered_consultations = result if result else []
                    print(f"[DEBUG] Résultat: {len(self.filtered_consultations)} consultations trouvées")
                else:
                    print(f"[DEBUG] Format de dates invalide: '{texte}'. Utilisez: dd/mm/yyyy - dd/mm/yyyy")
                    self.filtered_consultations = []
        else:
            # Filtrage par service
            service_map = {
                "Consultation avec examen": {"examen": "Oui"},
                "Chirurgie": {"chirurgie": "Oui"},
                "Lunette": {"commandelunette": "Oui"},
                "Prescription": {"prescription": "Oui"},
                "Consultation": {}
            }
            if filtre in service_map:
                params = service_map[filtre]
                result = self.ctrl.rechercher_par_services(
                    self.code_session,
                    examen=params.get('examen'),
                    chirurgie=params.get('chirurgie'),
                    commandelunette=params.get('commandelunette'),
                    prescription=params.get('prescription')
                )
                self.filtered_consultations = result if result else []

        self._remplir_table(self.filtered_consultations)
        self._actualiser_graphique()

    def _filtrer_par_texte(self, consultations, texte: str) -> list:
        """Filtre les consultations par texte de recherche simple."""
        texte_lower = texte.lower()
        result = []
        for consultation in consultations:
            values = [
                str(getattr(consultation, 'code', '')),
                self._get_nom_patient(getattr(consultation, 'code', '')),
                self._get_service_label(consultation),
                self._format_date(getattr(consultation, 'date_consultation', '')),
            ]
            combined = " ".join(v.lower() for v in values if isinstance(v, str))
            if texte_lower in combined:
                result.append(consultation)
        return result

    def _parse_date(self, texte: str):
        """Parse une seule date au format dd/mm/yyyy ou yyyy-mm-dd."""
        texte = texte.strip()
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
            try:
                return datetime.strptime(texte, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_date_range(self, texte: str):
        """Parse un intervalle de dates avec plusieurs formats supportés."""
        texte = texte.strip()
        
        # Essayer différents séparateurs
        separators = [' - ', ' au ', ' à ', ' et ', ' jusqu\'au ', ' jusqu\'à ', ' to ', ';', ',']
        
        for sep in separators:
            if sep in texte:
                parts = texte.split(sep)
                if len(parts) == 2:
                    date_debut = self._parse_date(parts[0].strip())
                    date_fin = self._parse_date(parts[1].strip())
                    if date_debut and date_fin:
                        return (date_debut, date_fin) if date_debut <= date_fin else (date_fin, date_debut)
        
        # Essayer de détecter deux dates sans séparateur explicite (format: "01/01/2024 31/01/2024")
        import re
        # Chercher des patterns de dates
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}'
        dates_found = re.findall(date_pattern, texte)
        
        if len(dates_found) == 2:
            date_debut = self._parse_date(dates_found[0])
            date_fin = self._parse_date(dates_found[1])
            if date_debut and date_fin:
                return (date_debut, date_fin) if date_debut <= date_fin else (date_fin, date_debut)
        
        return None

    def _on_graph_filter_changed(self):
        """Appelé quand un filtre de service du graphique change."""
        self.graph_service_filters['examen'] = "Oui" if self.check_examen.isChecked() else None
        self.graph_service_filters['chirurgie'] = "Oui" if self.check_chirurgie.isChecked() else None
        self.graph_service_filters['commandelunette'] = "Oui" if self.check_lunette.isChecked() else None
        self.graph_service_filters['prescription'] = "Oui" if self.check_prescription.isChecked() else None
        self._actualiser_graphique()

    def _actualiser_graphique(self):
        """Met à jour le graphique des consultations par mois avec courbes linéaires."""
        try:
            data = self.ctrl.obtenir_nombre_par_mois_filtre(
                self.code_session,
                examen=self.graph_service_filters['examen'],
                chirurgie=self.graph_service_filters['chirurgie'],
                commandelunette=self.graph_service_filters['commandelunette'],
                prescription=self.graph_service_filters['prescription']
            )
            self.graph_canvas.update_graph(data or {}, MC.PRIMARY, "Consultations")
        except Exception as e:
            print(f"[TableauConsultationView] Erreur actualiser_graphique: {e}")

    def _actualiser_graphique_patient(self):
        """Met à jour le graphique des consultations du patient sélectionné avec courbes linéaires."""
        try:
            patient_code = self.patient_combo.currentData()
            if not patient_code:
                self.graph_patient_canvas.update_graph({}, MC.ACCENT, "Consultations")
                return

            data = self.ctrl.obtenir_consultations_par_patient_par_mois(self.code_session, patient_code)
            self.graph_patient_canvas.update_graph(data or {}, MC.ACCENT, "Consultations")
        except Exception as e:
            print(f"[TableauConsultationView] Erreur actualiser_graphique_patient: {e}")

    def _to_date(self, value):
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    def _get_service_label(self, consultation) -> str:
        label = "Consultation"
        if hasattr(consultation, 'service_type') and getattr(consultation, 'service_type'):
            return str(getattr(consultation, 'service_type'))
        if hasattr(consultation, 'type') and getattr(consultation, 'type'):
            return str(getattr(consultation, 'type'))
        if hasattr(consultation, 'examen') and getattr(consultation, 'examen'):
            return "Consultation avec examen"
        if hasattr(consultation, 'is_examen') and getattr(consultation, 'is_examen'):
            return "Consultation avec examen"
        if hasattr(consultation, 'chirurgie') and getattr(consultation, 'chirurgie'):
            return "Chirurgie"
        if hasattr(consultation, 'is_chirurgie') and getattr(consultation, 'is_chirurgie'):
            return "Chirurgie"
        if hasattr(consultation, 'lunette') and getattr(consultation, 'lunette'):
            return "Lunette"
        if hasattr(consultation, 'is_lunette') and getattr(consultation, 'is_lunette'):
            return "Lunette"
        if hasattr(consultation, 'prescription') and getattr(consultation, 'prescription'):
            return "Prescription"
        if hasattr(consultation, 'is_prescription') and getattr(consultation, 'is_prescription'):
            return "Prescription"
        return label

    def _remplir_table(self, consultations):
        self.table.setRowCount(0)
        for consultation in consultations:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(getattr(consultation, 'code', '—'))))
            self.table.setItem(row, 1, QTableWidgetItem(self._get_nom_patient(getattr(consultation, 'code', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(self._get_service_label(consultation)))
            date_str = self._format_date(getattr(consultation, 'date_consultation', '—'))
            self.table.setItem(row, 3, QTableWidgetItem(date_str))

    def _format_date(self, value):
        date_val = self._to_date(value)
        if not date_val:
            return str(value or "—")
        return date_val.strftime("%d/%m/%Y")

    def _get_nom_patient(self, code_consultation: str) -> str:
        try:
            data = self.ctrl.obtenir_consultation_complete(code_consultation)
            if not data:
                return "—"
            nom = data.get('patient_nom', '') or data.get('nom_patient', '') or ''
            prenom = data.get('patient_prenom', '') or data.get('prenom_patient', '') or ''
            return f"{nom} {prenom}".strip() or "—"
        except Exception:
            return "—"

    def _imprimer_filtre(self):
        """Imprime les consultations filtrées au format PDF."""
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            from services.pdf_rapports.consultation_analyses_pdf import ConsultationPDFService
            import os
            from datetime import datetime

            # Récupérer les consultations filtrées actuelles
            consultations_filtrees = self.filtered_consultations if hasattr(self, 'filtered_consultations') and self.filtered_consultations else self.consultations

            if not consultations_filtrees:
                QMessageBox.warning(self, "Aucune donnée", "Aucune consultation à imprimer avec les filtres actuels.")
                return

            # Collecter les filtres appliqués
            filtres_appliques = {}

            # Filtre de recherche
            recherche_texte = self.search_input.text().strip()
            if recherche_texte:
                filtres_appliques['recherche'] = recherche_texte

            # Filtre de dates (si applicable)
            filtre_selectionne = self.filter_combo.currentText()
            if filtre_selectionne in ["Date", "Entre"] and recherche_texte:
                if filtre_selectionne == "Date":
                    date_obj = self._parse_date(recherche_texte)
                    if date_obj:
                        filtres_appliques['date_debut'] = date_obj
                        filtres_appliques['date_fin'] = date_obj
                elif filtre_selectionne == "Entre":
                    dates = self._parse_date_range(recherche_texte)
                    if dates:
                        filtres_appliques['date_debut'], filtres_appliques['date_fin'] = dates

            # Filtres de services (checkboxes)
            if hasattr(self, 'check_examen') and self.check_examen.isChecked():
                filtres_appliques['examen'] = True
            if hasattr(self, 'check_chirurgie') and self.check_chirurgie.isChecked():
                filtres_appliques['chirurgie'] = True
            if hasattr(self, 'check_lunette') and self.check_lunette.isChecked():
                filtres_appliques['lunette'] = True
            if hasattr(self, 'check_prescription') and self.check_prescription.isChecked():
                filtres_appliques['prescription'] = True

            # Récupérer les informations du cabinet
            info_cabinet = self.ctrl.info_cabinet()
            if not info_cabinet:
                QMessageBox.warning(self, "Erreur", "Impossible de récupérer les informations du cabinet.")
                return

            # Ouvrir la boîte de dialogue de sauvegarde
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nom_fichier_defaut = f"consultations_filtrees_{timestamp}.pdf"

            chemin_pdf, _ = QFileDialog.getSaveFileName(
                self,
                "Sauvegarder le rapport PDF",
                nom_fichier_defaut,
                "Fichiers PDF (*.pdf)"
            )

            if not chemin_pdf:
                return  # L'utilisateur a annulé

            # Générer le PDF
            success = ConsultationPDFService.generer_pdf_consultations_filtrees(
                consultations_filtrees,
                filtres_appliques,
                chemin_pdf,
                info_cabinet
            )

            if success:
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Le rapport PDF a été généré avec succès :\n{chemin_pdf}"
                )
                # Ouvrir le PDF automatiquement
                os.startfile(chemin_pdf)
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    "Une erreur s'est produite lors de la génération du PDF."
                )

        except ImportError as e:
            QMessageBox.critical(
                self,
                "Erreur d'import",
                f"Module manquant pour la génération PDF : {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur inattendue s'est produite : {str(e)}"
            )


class TableauConsultationAdminView(QWidget):
    """
    Interface tableau consultation admin.
    - Tableau pleine largeur (ConsultationsTable) avec toutes les actions impression.
    - Panel glissant (drawer) déclenché au clic sur une ligne :
        • graphe consultations/mois du patient (tous les 12 mois)
        • détail de sa dernière consultation.
    """

    PANEL_WIDTH = 430

    def __init__(self, consultation_ctrl, code_session: str):
        super().__init__()
        self.ctrl          = consultation_ctrl
        self.code_session  = code_session
        self._code_patient = None
        self._nom_patient  = ""
        self._panel_open   = False
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    # ──────────────────────────────────────────────────────────────────
    # CONSTRUCTION
    # ──────────────────────────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Tableau pleine largeur
        from views.consultation.components.consultations_table import ConsultationsTable
        self.tbl = ConsultationsTable(self.ctrl)
        self.tbl.table.cellClicked.connect(self._on_cellule_cliquee)
        self.tbl.imprimer_info_clicked.connect(self._on_imprimer_info)
        self.tbl.imprimer_avec_resultat_clicked.connect(self._on_imprimer_avec_resultat)
        self.tbl.new_resultat_clicked.connect(self._on_new_resultat)
        root.addWidget(self.tbl)

        # Quick Actions en bas
        from views.consultation.components.quick_actions import QuickActions
        self.quick_actions = QuickActions()
        self.quick_actions.new_consultation_clicked.connect(self._naviguer_vers_consultation)
        self.quick_actions.imprimer_tous_rapports_clicked.connect(self._on_imprimer_tous_rapports)
        self.quick_actions.imprimer_rapport_date_clicked.connect(self._on_imprimer_rapport_par_date)
        self.quick_actions.advanced_search_clicked.connect(self._on_recherche_avancee)
        # Masquer les boutons non pertinents dans le contexte admin
        # Ordre : 0=Nouvelle consultation, 1=Patients en attente, 2=Recherche avancée,
        #         3=Rapports & exports, 4=Historique patient, 5=Imprimer rapport
        self.quick_actions.buttons[1].hide()  # Patients en attente
        self.quick_actions.buttons[4].hide()  # Historique patient
        root.addWidget(self.quick_actions)

        # Panel glissant (overlay — child de self, positionné en absolu)
        self._drawer = self._build_drawer()
        self._drawer.setParent(self)
        self._drawer.hide()

        self._anim = QPropertyAnimation(self._drawer, b"geometry")
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    # ── Drawer glissant ───────────────────────────────────────────────

    def _build_drawer(self) -> QFrame:
        c   = theme_manager.colors()
        frm = QFrame(self)
        frm.setObjectName("TCAdminDrawer")
        frm.setFixedWidth(self.PANEL_WIDTH)
        frm.setStyleSheet(f"""
            QFrame#TCAdminDrawer {{
                background:{c['bg_card']};
                border-left:2px solid {c['border']};
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(-5, 0)
        shadow.setColor(QColor(0, 0, 0, 70))
        frm.setGraphicsEffect(shadow)

        lay = QVBoxLayout(frm)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Barre titre du drawer
        title_bar = QFrame()
        title_bar.setFixedHeight(46)
        title_bar.setObjectName("DrawerTitleBar")
        tb_lay = QHBoxLayout(title_bar)
        tb_lay.setContentsMargins(14, 0, 10, 0)
        tb_lay.setSpacing(8)

        self._drawer_ico = QLabel()
        self._drawer_ico.setPixmap(qta.icon("fa5s.user-circle", color=c['primary']).pixmap(18, 18))
        self._drawer_ico.setStyleSheet("border:none; background:transparent;")
        self._drawer_title = QLabel("Détails patient")
        self._drawer_title.setStyleSheet(
            f"font-weight:700; font-size:13px; color:{c['text_primary']}; border:none;"
        )
        btn_close = QPushButton(qta.icon("fa5s.times", color=c['text_secondary']), "")
        btn_close.setObjectName("DrawerCloseBtn")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton#DrawerCloseBtn {{
                background:{c['hover']}; border:none; border-radius:14px;
            }}
            QPushButton#DrawerCloseBtn:hover {{
                background:{c['border']};
            }}
        """)
        btn_close.clicked.connect(self._fermer_drawer)

        tb_lay.addWidget(self._drawer_ico)
        tb_lay.addSpacing(4)
        tb_lay.addWidget(self._drawer_title, 1)
        tb_lay.addWidget(btn_close)
        lay.addWidget(title_bar)

        sep_top = QFrame()
        sep_top.setFixedHeight(1)
        sep_top.setObjectName("DrawerTopSep")
        sep_top.setStyleSheet(f"background:{c['border_light']}; border:none;")
        lay.addWidget(sep_top)

        # Contenu scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background:transparent; border:none;")

        content = QWidget()
        content.setStyleSheet("background:transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(10)

        self.frame_graphe = self._build_frame_graphe()
        self.frame_detail = self._build_frame_detail()
        cl.addWidget(self.frame_graphe)
        cl.addWidget(self.frame_detail)
        cl.addStretch()

        scroll.setWidget(content)
        lay.addWidget(scroll, 1)

        return frm

    # ── Frame graphe (dans le drawer) ────────────────────────────────

    def _build_frame_graphe(self) -> QFrame:
        c   = theme_manager.colors()
        frm = QFrame()
        frm.setObjectName("TCAdminGraph")
        self._appliquer_style_carte(frm, "TCAdminGraph")

        lay = QVBoxLayout(frm)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        hdr = QHBoxLayout()
        self._ico_graph = QLabel()
        self._ico_graph.setPixmap(qta.icon("fa5s.chart-bar", color=c['primary']).pixmap(16, 16))
        self._ico_graph.setStyleSheet("border:none; background:transparent;")
        self._title_graph = QLabel("Consultations du patient par mois")
        self._title_graph.setStyleSheet(
            f"font-weight:700; font-size:12px; color:{c['text_primary']}; border:none;"
        )
        hdr.addWidget(self._ico_graph)
        hdr.addSpacing(6)
        hdr.addWidget(self._title_graph, 1)
        lay.addLayout(hdr)

        self._sep_graph = QFrame()
        self._sep_graph.setFixedHeight(1)
        self._sep_graph.setStyleSheet(f"background:{c['border']}; border:none;")
        lay.addWidget(self._sep_graph)

        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as _Canvas
        from matplotlib.figure import Figure as _Figure
        self._fig_graph    = _Figure(figsize=(4, 2.8), dpi=90, facecolor="none")
        self._ax_graph     = self._fig_graph.add_subplot(111)
        self._ax_graph.set_facecolor("none")
        self._canvas_graph = _Canvas(self._fig_graph)
        self._canvas_graph.setStyleSheet("background:transparent;")
        self._canvas_graph.setFixedHeight(220)
        lay.addWidget(self._canvas_graph)

        self._dessiner_graphe_vide()
        return frm

    # ── Frame détail (dans le drawer) ────────────────────────────────

    def _build_frame_detail(self) -> QFrame:
        c   = theme_manager.colors()
        frm = QFrame()
        frm.setObjectName("TCAdminDetail")
        self._appliquer_style_carte(frm, "TCAdminDetail")

        lay = QVBoxLayout(frm)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        hdr = QHBoxLayout()
        self._ico_detail = QLabel()
        self._ico_detail.setPixmap(qta.icon("fa5s.file-medical", color=c['primary']).pixmap(16, 16))
        self._ico_detail.setStyleSheet("border:none; background:transparent;")
        self._title_detail = QLabel("Dernière consultation du patient")
        self._title_detail.setStyleSheet(
            f"font-weight:700; font-size:12px; color:{c['text_primary']}; border:none;"
        )
        hdr.addWidget(self._ico_detail)
        hdr.addSpacing(6)
        hdr.addWidget(self._title_detail, 1)
        lay.addLayout(hdr)

        self._sep_detail = QFrame()
        self._sep_detail.setFixedHeight(1)
        self._sep_detail.setStyleSheet(f"background:{c['border']}; border:none;")
        lay.addWidget(self._sep_detail)

        self._lbl_empty_det = QLabel("Cliquez sur une ligne du tableau\npour voir les détails")
        self._lbl_empty_det.setAlignment(Qt.AlignCenter)
        self._lbl_empty_det.setStyleSheet(
            f"color:{c['text_muted']}; font-size:11px; border:none;"
        )
        lay.addWidget(self._lbl_empty_det)

        self._detail_widget = QWidget()
        self._detail_widget.setStyleSheet("background:transparent;")
        dl = QGridLayout(self._detail_widget)
        dl.setContentsMargins(0, 4, 0, 4)
        dl.setSpacing(8)
        dl.setColumnStretch(2, 1)

        champs = [
            ("fa5s.user",            "Patient",        "_det_patient"),
            ("fa5s.calendar-alt",    "Date",           "_det_date"),
            ("fa5s.stethoscope",     "Diagnostic",     "_det_diag"),
            ("fa5s.money-bill-wave", "Frais",          "_det_frais"),
            ("fa5s.file-invoice",    "Statut facture", "_det_statut"),
            ("fa5s.user-md",         "Personnel",      "_det_personnel"),
        ]
        for i, (icon_name, libelle, attr) in enumerate(champs):
            ico = QLabel()
            ico.setPixmap(qta.icon(icon_name, color=c['primary']).pixmap(14, 14))
            ico.setStyleSheet("border:none; background:transparent;")
            ico.setFixedSize(20, 20)
            ico.setAlignment(Qt.AlignCenter)

            lbl = QLabel(libelle)
            lbl.setStyleSheet(
                f"color:{c['text_secondary']}; font-size:11px; font-weight:600; border:none;"
            )
            lbl.setFixedWidth(100)

            val = QLabel("—")
            val.setStyleSheet(
                f"color:{c['text_primary']}; font-size:12px; font-weight:700; border:none;"
            )
            val.setWordWrap(True)
            setattr(self, attr, val)

            dl.addWidget(ico, i, 0)
            dl.addWidget(lbl, i, 1)
            dl.addWidget(val, i, 2)

        lay.addWidget(self._detail_widget)
        self._detail_widget.hide()
        lay.addStretch()
        return frm

    @staticmethod
    def _appliquer_style_carte(frame: QFrame, obj_name: str):
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#{obj_name} {{
                background:{c['bg_card']};
                border:1px solid {c['border']};
                border-radius:14px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 20))
        frame.setGraphicsEffect(shadow)

    # ──────────────────────────────────────────────────────────────────
    # ANIMATION DRAWER
    # ──────────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        h = self.height()
        w = self.PANEL_WIDTH
        if self._panel_open:
            self._drawer.setGeometry(self.width() - w, 0, w, h)
        else:
            self._drawer.setGeometry(self.width(), 0, w, h)

    def _ouvrir_drawer(self):
        h = self.height()
        w = self.PANEL_WIDTH
        self._anim.stop()
        # Déconnecter le hide branché lors de la fermeture précédente
        try:
            self._anim.finished.disconnect()
        except Exception:
            pass
        if not self._drawer.isVisible():
            self._drawer.setGeometry(QRect(self.width(), 0, w, h))
            self._drawer.show()
            self._drawer.raise_()
        self._anim.setStartValue(QRect(self.width(), 0, w, h))
        self._anim.setEndValue(QRect(self.width() - w, 0, w, h))
        self._panel_open = True
        self._anim.start()

    def _fermer_drawer(self):
        h = self.height()
        w = self.PANEL_WIDTH
        self._anim.stop()
        self._anim.setStartValue(QRect(self.width() - w, 0, w, h))
        self._anim.setEndValue(QRect(self.width(), 0, w, h))
        self._panel_open = False
        try:
            self._anim.finished.disconnect()
        except Exception:
            pass
        self._anim.finished.connect(self._drawer.hide)
        self._anim.start()

    # ──────────────────────────────────────────────────────────────────
    # INTERACTIONS
    # ──────────────────────────────────────────────────────────────────

    def _on_cellule_cliquee(self, row: int, col: int):
        ct    = self.tbl
        start = (ct.current_page - 1) * ct.items_per_page
        idx   = start + row
        if 0 <= idx < len(ct.filtered_consultations):
            self._selectionner(ct.filtered_consultations[idx])

    def _selectionner(self, consultation):
        detail = self.tbl._get_detail(consultation)
        if not detail:
            return
        code_patient = detail.get('code_patient')
        if not code_patient:
            return
        nom = f"{detail.get('patient_nom','') or ''} {detail.get('patient_prenom','') or ''}".strip()
        self._code_patient = code_patient
        self._nom_patient  = nom or "Patient"
        self._drawer_title.setText(f"Détails — {self._nom_patient}")
        self._mettre_a_jour_graphe()
        self._mettre_a_jour_detail()
        self._ouvrir_drawer()

    # ──────────────────────────────────────────────────────────────────
    # GRAPHE — tous les 12 mois
    # ──────────────────────────────────────────────────────────────────

    _MOIS_ORDRE = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
                   "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]

    def _mettre_a_jour_graphe(self):
        try:
            data = self.ctrl.obtenir_consultations_par_patient_par_mois(
                self.code_session, self._code_patient
            ) or {}
        except Exception:
            data = {}

        self._title_graph.setText(f"Consultations de {self._nom_patient} par mois")

        # Tous les 12 mois — 0 pour les mois sans données
        vals = [float(data.get(m, 0) or 0) for m in self._MOIS_ORDRE]

        c_th = theme_manager.colors()
        self._ax_graph.clear()
        self._ax_graph.set_facecolor("none")

        x    = range(len(self._MOIS_ORDRE))
        colors = [c_th['primary'] if v > 0 else c_th['border_light'] for v in vals]
        bars = self._ax_graph.bar(x, vals, color=colors, width=0.55, alpha=0.88, zorder=3)

        self._ax_graph.set_xticks(list(x))
        self._ax_graph.set_xticklabels(
            self._MOIS_ORDRE, fontsize=7, color=c_th['text_secondary'], rotation=45, ha='right'
        )
        self._ax_graph.tick_params(colors=c_th['text_secondary'], labelsize=7, length=0, pad=4)
        self._ax_graph.set_ylabel("Consultations", fontsize=8, color=c_th['text_secondary'])
        for sp in self._ax_graph.spines.values():
            sp.set_visible(False)
        self._ax_graph.grid(True, axis='y', linestyle='-',
                            alpha=0.12, color=c_th['border'], linewidth=0.8)

        max_v = max(vals) if any(v > 0 for v in vals) else 1
        self._ax_graph.set_ylim(0, max_v * 1.35)

        for bar, val in zip(bars, vals):
            if val > 0:
                self._ax_graph.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max_v * 0.05,
                    f"{int(val)}", ha='center', va='bottom',
                    fontsize=8, fontweight='700', color=c_th['text_primary']
                )

        self._fig_graph.subplots_adjust(left=0.14, right=0.97, top=0.93, bottom=0.30)
        self._canvas_graph.draw()

    def _dessiner_graphe_vide(self):
        c_th = theme_manager.colors()
        self._ax_graph.clear()
        self._ax_graph.set_facecolor("none")
        self._ax_graph.text(
            0.5, 0.5,
            "Cliquez sur une ligne\npour voir les consultations du patient",
            ha='center', va='center', fontsize=9,
            color=c_th['text_muted'],
            transform=self._ax_graph.transAxes
        )
        for sp in self._ax_graph.spines.values():
            sp.set_visible(False)
        self._ax_graph.set_xticks([])
        self._ax_graph.set_yticks([])
        self._fig_graph.subplots_adjust(left=0.08, right=0.97, top=0.95, bottom=0.1)
        self._canvas_graph.draw()

    # ──────────────────────────────────────────────────────────────────
    # DÉTAIL DERNIÈRE CONSULTATION
    # ──────────────────────────────────────────────────────────────────

    def _mettre_a_jour_detail(self):
        try:
            historique = self.ctrl.obtenir_historique_patient(self._code_patient) or []
        except Exception:
            historique = []

        if not historique:
            self._detail_widget.hide()
            self._lbl_empty_det.show()
            return

        derniere = historique[0]  # trié DESC → index 0 = la plus récente

        def _g(key, fallback="—"):
            v = (derniere.get(key) if isinstance(derniere, dict)
                 else getattr(derniere, key, None))
            return str(v).strip() if v else fallback

        date_raw = (derniere.get('date_consultation') if isinstance(derniere, dict)
                    else getattr(derniere, 'date_consultation', None))
        try:
            if hasattr(date_raw, 'strftime'):
                date_str = date_raw.strftime('%d/%m/%Y')
            elif isinstance(date_raw, str):
                from datetime import datetime as _dt
                date_str = _dt.strptime(date_raw[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
            else:
                date_str = str(date_raw) if date_raw else "—"
        except Exception:
            date_str = str(date_raw) if date_raw else "—"

        frais_raw = (derniere.get('frais_consultation') if isinstance(derniere, dict)
                     else getattr(derniere, 'frais_consultation', 0)) or 0
        try:
            frais_str = f"{float(frais_raw):,.0f} GNF".replace(",", " ")
        except Exception:
            frais_str = "—"

        per_nom    = _g('personnel_nom',      "")
        per_prenom = _g('personnel_prenom',   "")
        per_fonc   = _g('personnel_fonction', "")
        dr_str = f"Dr. {per_nom} {per_prenom}".strip() if per_nom else "—"
        if per_fonc and per_fonc != "—":
            dr_str += f"  ({per_fonc})"

        self._det_patient.setText(self._nom_patient)
        self._det_date.setText(date_str)
        self._det_diag.setText(_g('diagnostique'))
        self._det_frais.setText(frais_str)
        self._det_statut.setText(_g('statut_facture'))
        self._det_personnel.setText(dr_str)

        self._lbl_empty_det.hide()
        self._detail_widget.show()

    # ──────────────────────────────────────────────────────────────────
    # IMPRESSION — réutilisation 100% des méthodes de VueConsultation
    # ──────────────────────────────────────────────────────────────────

    def _naviguer_vers_consultation(self):
        """Navigue vers la page consultation du dashboard."""
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == "DashboardView":
                if hasattr(parent, "show_consultation"):
                    parent.show_consultation()
                return
            parent = parent.parent()

    def _on_imprimer_info(self, consultation):
        from services.pdf_actes.consultation_pdf import ConsultationPDF
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from views.shared.message_box import CustomMessageBox
        code = consultation.code
        try:
            detail = self.ctrl.obtenir_consultation_complete(code)
            if not detail:
                CustomMessageBox("Erreur", f"Impossible de récupérer les détails de {code}.",
                                 "error", parent=self).exec()
                return
            try:
                info_cabinet = self.ctrl.get_cabinet_info()
            except Exception:
                info_cabinet = {}
            pdf_path = ConsultationPDF.generer_pdf_consultation(detail, info_cabinet, None)
            ApercuPDFDialog(pdf_path, f"Aperçu - Consultation {code}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}",
                             "error", parent=self).exec()

    def _on_imprimer_avec_resultat(self, consultation):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from services.pdf_actes.consultation_pdf import ConsultationPDF
        code = consultation.code
        try:
            detail = self.ctrl.obtenir_consultation_complete(code)
            if not detail:
                CustomMessageBox("Erreur", f"Impossible de récupérer les détails de {code}.",
                                 "error", parent=self).exec()
                return
            try:
                info_cabinet = self.ctrl.get_cabinet_info()
            except Exception:
                info_cabinet = {}

            resultat_data = {}
            try:
                from controllers.controleur_resultat import ResultatControleur
                res_ctrl = ResultatControleur()
                resultats = res_ctrl.lister_par_consultation(code) or []
                if resultats:
                    id_res = getattr(resultats[0], 'id_resultat', None)
                    if id_res:
                        resultat_data = res_ctrl.get_detail_resultat(id_res) or {}
            except Exception:
                pass

            if not resultat_data:
                CustomMessageBox("Information",
                                 "Aucun résultat médical trouvé pour cette consultation.",
                                 "info", parent=self).exec()
                return

            fichier_bytes    = None
            type_fichier_res = resultat_data.get('type_fichier', '') if isinstance(resultat_data, dict) else ''
            try:
                from controllers.controleur_resultat import ResultatControleur
                res_ctrl = ResultatControleur()
                id_res = resultat_data.get('id_resultat') if isinstance(resultat_data, dict) else None
                if id_res and type_fichier_res == 'image':
                    fichier_bytes = res_ctrl.lire_fichier_bytes(id_res)
            except Exception:
                pass

            pdf_path = ConsultationPDF.generer_pdf_consultation_avec_resultat(
                detail, resultat_data, info_cabinet, None,
                fichier_bytes=fichier_bytes, type_fichier_res=type_fichier_res
            )
            ApercuPDFDialog(pdf_path, f"Consultation avec résultat — {code}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}",
                             "error", parent=self).exec()

    def _on_new_resultat(self, consultation):
        from views.shared.message_box import CustomMessageBox
        CustomMessageBox(
            "Information",
            f"Pour ajouter un résultat à la consultation {consultation.code},\n"
            "veuillez naviguer vers la section Résultats.",
            "info", parent=self
        ).exec()

    def _on_imprimer_tous_rapports(self):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        if not self.code_session:
            CustomMessageBox("Information", "Aucune session active.", "info", parent=self).exec()
            return
        try:
            pdf_path = self.ctrl.generer_pdf_rapport_consultations_par_date(self.code_session)
            ApercuPDFDialog(pdf_path, "Rapport des consultations par date", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}",
                             "error", parent=self).exec()

    def _on_imprimer_rapport_par_date(self):
        from views.shared.message_box import CustomMessageBox
        if not self.code_session:
            CustomMessageBox("Information", "Aucune session active.", "info", parent=self).exec()
            return
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox
        from PySide6.QtCore import QDate
        from PySide6.QtWidgets import QDateEdit, QLabel as _QLabel
        dialog = QDialog(self)
        dialog.setWindowTitle("Sélectionner une date")
        dialog.setFixedSize(340, 150)
        c = theme_manager.colors()
        dialog.setStyleSheet(f"background:{c['bg_card']}; color:{c['text_primary']};")
        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(14)
        lay.addWidget(_QLabel("<b>Sélectionner une date pour le rapport</b>"))
        form = QFormLayout()
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        date_edit.setDisplayFormat("dd/MM/yyyy")
        date_edit.setFixedHeight(34)
        form.addRow("Date :", date_edit)
        lay.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        lay.addWidget(buttons)
        if dialog.exec():
            date_cible = date_edit.date().toPython()
            try:
                from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
                pdf_path = self.ctrl.generer_pdf_rapport_date_precise(self.code_session, date_cible)
                date_str = date_cible.strftime('%d/%m/%Y') if hasattr(date_cible, 'strftime') else str(date_cible)
                ApercuPDFDialog(pdf_path, f"Rapport du {date_str}", self).exec()
            except Exception as e:
                CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}",
                                 "error", parent=self).exec()

    def _on_recherche_avancee(self):
        if not self.code_session:
            return
        from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
                                        QDialogButtonBox, QDateEdit, QLabel as _QLabel)
        from PySide6.QtCore import QDate
        dialog = QDialog(self)
        dialog.setWindowTitle("Recherche entre deux dates")
        dialog.setFixedSize(400, 200)
        c = theme_manager.colors()
        dialog.setStyleSheet(f"background:{c['bg_card']}; color:{c['text_primary']};")
        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)
        lay.addWidget(_QLabel("<b>Rechercher des consultations entre deux dates</b>"))
        form = QFormLayout()
        form.setSpacing(10)
        today = QDate.currentDate()
        date_debut = QDateEdit()
        date_debut.setCalendarPopup(True)
        date_debut.setDate(today.addDays(-30))
        date_debut.setDisplayFormat("dd/MM/yyyy")
        date_fin = QDateEdit()
        date_fin.setCalendarPopup(True)
        date_fin.setDate(today)
        date_fin.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date début :", date_debut)
        form.addRow("Date fin :", date_fin)
        lay.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        lay.addWidget(buttons)
        if dialog.exec():
            debut = date_debut.date().toPython()
            fin   = date_fin.date().toPython()
            try:
                resultats = self.ctrl.rechercher_entre_dates(self.code_session, debut, fin) or []
            except Exception:
                resultats = []
            self.tbl.load_consultations(resultats, self.code_session)

    # ──────────────────────────────────────────────────────────────────
    # API PUBLIQUE
    # ──────────────────────────────────────────────────────────────────

    def charger_consultations(self, code_session: str):
        self.code_session = code_session
        try:
            consultations = self.ctrl.lister_consultations(code_session) or []
        except Exception:
            consultations = []
        self.tbl.load_consultations(consultations, code_session)

    def rafraichir(self):
        self.charger_consultations(self.code_session)

    # ──────────────────────────────────────────────────────────────────
    # THÈME
    # ──────────────────────────────────────────────────────────────────

    def apply_theme(self):
        c = theme_manager.colors()

        # Drawer
        self._drawer.setStyleSheet(f"""
            QFrame#TCAdminDrawer {{
                background:{c['bg_card']};
                border-left:2px solid {c['border']};
            }}
        """)
        self._drawer_ico.setPixmap(qta.icon("fa5s.user-circle", color=c['primary']).pixmap(18, 18))
        self._drawer_title.setStyleSheet(
            f"font-weight:700; font-size:13px; color:{c['text_primary']}; border:none;"
        )

        # Cartes
        for frm, name in [(self.frame_graphe, "TCAdminGraph"),
                          (self.frame_detail, "TCAdminDetail")]:
            frm.setStyleSheet(f"""
                QFrame#{name} {{
                    background:{c['bg_card']};
                    border:1px solid {c['border']};
                    border-radius:14px;
                }}
            """)

        self._ico_graph.setPixmap(qta.icon("fa5s.chart-bar",    color=c['primary']).pixmap(16, 16))
        self._ico_detail.setPixmap(qta.icon("fa5s.file-medical", color=c['primary']).pixmap(16, 16))
        for lbl in (self._title_graph, self._title_detail):
            lbl.setStyleSheet(
                f"font-weight:700; font-size:12px; color:{c['text_primary']}; border:none;"
            )
        for sep in (self._sep_graph, self._sep_detail):
            sep.setStyleSheet(f"background:{c['border']}; border:none;")
        self._lbl_empty_det.setStyleSheet(
            f"color:{c['text_muted']}; font-size:11px; border:none;"
        )

        if self._code_patient:
            self._mettre_a_jour_graphe()
        else:
            self._dessiner_graphe_vide()

        if hasattr(self, 'tbl') and hasattr(self.tbl, 'apply_theme'):
            try:
                self.tbl.apply_theme()
            except Exception:
                pass
