"""
Tableau consultation:
- filtre par recherche, date, service
- bouton imprimer
- tableau des consultations avec alternance de lignes
- zone graphique par patient (placeholder)
"""

from datetime import datetime, date, timedelta
import re

import qtawesome as qta
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTableWidget, QHeaderView,
    QTableWidgetItem, QFrame, QSizePolicy, QAbstractItemView, QCheckBox
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from views.shared.modal_theme import MC
from views.shared.theme_manager import theme_manager


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

        self.graph_canvas = FigureCanvas(Figure(figsize=(3, 2), dpi=100, facecolor=MC.BG_CARD))
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

        self.graph_patient_canvas = FigureCanvas(Figure(figsize=(3, 2), dpi=100, facecolor=MC.BG_CARD))
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
        """Met à jour le graphique des consultations par mois avec barres horizontales adaptatives."""
        try:
            data = self.ctrl.obtenir_nombre_par_mois_filtre(
                self.code_session,
                examen=self.graph_service_filters['examen'],
                chirurgie=self.graph_service_filters['chirurgie'],
                commandelunette=self.graph_service_filters['commandelunette'],
                prescription=self.graph_service_filters['prescription']
            )
            
            if not data:
                self.graph_canvas.figure.clear()
                self.graph_canvas.draw()
                return

            self.graph_canvas.figure.clear()
            ax = self.graph_canvas.figure.add_subplot(111)
            ax.set_facecolor(MC.BG_CARD)
            ax.grid(True, axis="x", alpha=0.3, linestyle="--", color=MC.BORDER)

            # Mapping mois 1-12 au lieu des noms
            mois_labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
            mois_ordre = {str(i): i-1 for i in range(1, 13)}  # "1"->0, "2"->1, etc.
            
            mois_sorted = sorted(data.keys(), key=lambda x: mois_ordre.get(x, 100))
            values = [data[m] for m in mois_sorted]

            # Calculer l'échelle adaptative plus compacte
            max_val = max(values) if values else 0
            if max_val <= 3:
                step = 1
                max_limit = max(3, max_val + 0.5)
            elif max_val <= 10:
                step = 2
                max_limit = max(10, max_val + 1)
            elif max_val <= 50:
                step = 5
                max_limit = max(50, max_val + 5)
            elif max_val <= 200:
                step = 20
                max_limit = max(200, max_val + 20)
            else:
                step = 50
                max_limit = max(500, max_val + 50)

            colors = [MC.PRIMARY if v > 0 else MC.BG_MAIN for v in values]
            bars = ax.barh(mois_sorted, values, color=colors, edgecolor=MC.PRIMARY, linewidth=1, height=0.8)

            for i, (bar, val) in enumerate(zip(bars, values)):
                if val > 0:
                    # Positionnement compact du texte
                    if val < max_limit * 0.15:
                        text_x = val + (max_limit * 0.02)
                        ha = "left"
                    else:
                        text_x = val - (max_limit * 0.02)
                        ha = "right"
                    
                    ax.text(text_x, bar.get_y() + bar.get_height() / 2,
                           f"{int(val)}", ha=ha, va="center", fontsize=8, 
                           fontweight="bold", color=MC.PRIMARY if ha == "right" else MC.TEXT_SECONDARY)

            ax.set_xlim(0, max_limit)
            ax.set_xticks(range(0, int(max_limit) + step, step))
            ax.set_xlabel("Consultations", fontsize=9, fontweight="bold", color=MC.TEXT_PRIMARY)
            ax.set_ylabel("Mois", fontsize=9, fontweight="bold", color=MC.TEXT_PRIMARY)
            ax.tick_params(labelsize=8, colors=MC.TEXT_SECONDARY)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(MC.BORDER)
            ax.spines["bottom"].set_color(MC.BORDER)

            # Layout plus compact
            self.graph_canvas.figure.subplots_adjust(left=0.12, right=0.98, top=0.95, bottom=0.12)
            self.graph_canvas.draw()
        except Exception as e:
            print(f"[TableauConsultationView] Erreur actualiser_graphique: {e}")

    def _actualiser_graphique_patient(self):
        """Met à jour le graphique des consultations du patient sélectionné avec échelle adaptative."""
        try:
            patient_code = self.patient_combo.currentData()
            if not patient_code:
                self.graph_patient_canvas.figure.clear()
                self.graph_patient_canvas.draw()
                return

            data = self.ctrl.obtenir_consultations_par_patient_par_mois(self.code_session, patient_code)
            
            if not data:
                self.graph_patient_canvas.figure.clear()
                self.graph_patient_canvas.draw()
                return

            self.graph_patient_canvas.figure.clear()
            ax = self.graph_patient_canvas.figure.add_subplot(111)
            ax.set_facecolor(MC.BG_CARD)
            ax.grid(True, axis="x", alpha=0.3, linestyle="--", color=MC.BORDER)

            # Mapping mois 1-12 au lieu des noms
            mois_labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
            mois_ordre = {str(i): i-1 for i in range(1, 13)}  # "1"->0, "2"->1, etc.
            
            mois_sorted = sorted(data.keys(), key=lambda x: mois_ordre.get(x, 100))
            values = [data[m] for m in mois_sorted]

            # Calculer l'échelle adaptative plus compacte
            max_val = max(values) if values else 0
            if max_val <= 3:
                step = 1
                max_limit = max(3, max_val + 0.5)
            elif max_val <= 10:
                step = 2
                max_limit = max(10, max_val + 1)
            elif max_val <= 50:
                step = 5
                max_limit = max(50, max_val + 5)
            elif max_val <= 200:
                step = 20
                max_limit = max(200, max_val + 20)
            else:
                step = 50
                max_limit = max(500, max_val + 50)

            colors = [MC.ACCENT if v > 0 else MC.BG_MAIN for v in values]  # Couleur violette pour différencier
            bars = ax.barh(mois_sorted, values, color=colors, edgecolor=MC.ACCENT, linewidth=1, height=0.8)

            for i, (bar, val) in enumerate(zip(bars, values)):
                if val > 0:
                    # Positionnement compact du texte
                    if val < max_limit * 0.15:
                        text_x = val + (max_limit * 0.02)
                        ha = "left"
                    else:
                        text_x = val - (max_limit * 0.02)
                        ha = "right"
                    
                    ax.text(text_x, bar.get_y() + bar.get_height() / 2,
                           f"{int(val)}", ha=ha, va="center", fontsize=8, 
                           fontweight="bold", color=MC.ACCENT if ha == "right" else MC.TEXT_SECONDARY)

            ax.set_xlim(0, max_limit)
            ax.set_xticks(range(0, int(max_limit) + step, step))
            ax.set_xlabel("Consultations", fontsize=9, fontweight="bold", color=MC.TEXT_PRIMARY)
            ax.set_ylabel("Mois", fontsize=9, fontweight="bold", color=MC.TEXT_PRIMARY)
            ax.tick_params(labelsize=8, colors=MC.TEXT_SECONDARY)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(MC.BORDER)
            ax.spines["bottom"].set_color(MC.BORDER)

            # Layout plus compact
            self.graph_patient_canvas.figure.subplots_adjust(left=0.12, right=0.98, top=0.95, bottom=0.12)
            self.graph_patient_canvas.draw()
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
            from services.consultation_pdf_service import ConsultationPDFService
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
