# """
# Tableau examen :
# - filtre par recherche, date (simple et intervalle)
# - bouton imprimer
# - tableau des examens avec alternance de lignes
# - graphe bar  : examens par mois (global)
# - graphe bar  : examens du patient sélectionné
# """

# from datetime import datetime, date
# import re

# import qtawesome as qta
# from PySide6.QtCore import QSize, Qt
# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QLabel,
#     QLineEdit, QPushButton, QComboBox, QTableWidget, QHeaderView,
#     QTableWidgetItem, QFrame, QSizePolicy, QAbstractItemView
# )
# from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
# from views.shared.modal_theme import MC
# from views.shared.theme_manager import theme_manager


# class TableauExamenView(QWidget):
#     def __init__(self, examen_ctrl, code_session):
#         super().__init__()
#         self.ctrl             = examen_ctrl
#         self.code_session     = code_session
#         self.examens          = []
#         self.filtered_examens = []
#         self._init_ui()
#         self.charger_examens(code_session)
#         theme_manager.theme_changed.connect(self.apply_theme)

#     # =========================================================================
#     # CONSTRUCTION UI
#     # =========================================================================

#     def _init_ui(self):
#         self.setStyleSheet(f"background-color: {MC.BG_MAIN};")
#         self.main_layout = QVBoxLayout(self)
#         self.main_layout.setContentsMargins(0, 0, 0, 0)
#         self.main_layout.setSpacing(10)

#         self.left_panel  = self._creer_panel_tableau()
#         self.right_panel = self._creer_panel_graphique()

#         content_layout = QHBoxLayout()
#         content_layout.setSpacing(10)
#         content_layout.addWidget(self.left_panel,  6)
#         content_layout.addWidget(self.right_panel, 4)

#         self.main_layout.addLayout(content_layout)

#     # ------------------------------------------------------------------ left

#     def _creer_panel_tableau(self) -> QFrame:
#         panel = QFrame()
#         panel.setStyleSheet(
#             f"background: {MC.BG_CARD}; border-radius: 18px; border: 1px solid {MC.BORDER_LIGHT};"
#         )
#         layout = QVBoxLayout(panel)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(0)

#         self._tbl_header      = self._creer_header("Tableau examen", "fa5s.stethoscope")
#         self._tbl_filter      = self._creer_zone_filtre()
#         self._tbl_table_frame = self._creer_table_frame()

#         layout.addWidget(self._tbl_header)
#         layout.addWidget(self._tbl_filter)
#         layout.addWidget(self._tbl_table_frame, 1)
#         return panel

#     def _creer_header(self, titre: str, icone: str) -> QFrame:
#         header = QFrame()
#         header.setStyleSheet(
#             f"background: {MC.BG_CARD};"
#             f"border-top-left-radius: 18px; border-top-right-radius: 18px;"
#             f"border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"
#             f"border-bottom: 1px solid {MC.BORDER_LIGHT};"
#         )
#         header.setFixedHeight(44)
#         layout = QHBoxLayout(header)
#         layout.setContentsMargins(12, 6, 12, 6)
#         layout.setSpacing(6)

#         self._header_icone = icone
#         self._header_icon  = QLabel()
#         self._header_icon.setPixmap(qta.icon(icone, color=MC.PRIMARY).pixmap(QSize(18, 18)))
#         self._header_title = QLabel(titre)
#         self._header_title.setStyleSheet(
#             f"font-size: 12px; font-weight: 700; color: {MC.TEXT_PRIMARY};"
#         )

#         layout.addWidget(self._header_icon)
#         layout.addWidget(self._header_title)
#         layout.addStretch()
#         return header

#     def _creer_zone_filtre(self) -> QFrame:
#         frame = QFrame()
#         frame.setStyleSheet(
#             f"background: {MC.BG_CARD}; border: none; border-bottom: 1px solid {MC.BORDER_LIGHT};"
#         )
#         layout = QHBoxLayout(frame)
#         layout.setContentsMargins(10, 4, 10, 4)
#         layout.setSpacing(6)

#         self.search_input = QLineEdit()
#         self.search_input.setPlaceholderText("Rechercher ou saisir une date (dd/mm/yyyy)...")
#         self.search_input.setFixedHeight(28)
#         self.search_input.setMaximumWidth(220)
#         self.search_input.setStyleSheet(
#             f"border: 1px solid {MC.BORDER}; border-radius: 12px; padding-left: 12px;"
#         )
#         self.search_input.textChanged.connect(self._actualiser_filtrage)

#         self.filter_combo = QComboBox()
#         self.filter_combo.setIconSize(QSize(16, 16))
#         self._FILTER_ITEMS = [
#             ("fa5s.list",         "Tous"),
#             ("fa5s.calendar-alt", "Date"),
#             ("fa5s.filter",       "Entre"),
#         ]
#         for ico_name, label in self._FILTER_ITEMS:
#             self.filter_combo.addItem(qta.icon(ico_name, color=MC.PRIMARY), label)
#         self.filter_combo.setFixedHeight(28)
#         self.filter_combo.setStyleSheet(
#             f"border: 1px solid {MC.BORDER}; border-radius: 10px;"
#             f"padding-left: 8px; font-size: 11px;"
#         )
#         self.filter_combo.currentIndexChanged.connect(self._on_filter_mode_changed)

#         self.btn_print = QPushButton(qta.icon("fa5s.print", color=MC.TEXT_INVERSE), "Imprimer")
#         self.btn_print.setFixedHeight(28)
#         self.btn_print.setCursor(Qt.PointingHandCursor)
#         self.btn_print.setStyleSheet(
#             f"background-color: {MC.PRIMARY}; color: {MC.TEXT_INVERSE};"
#             f"border-radius: 10px; font-weight: 600; font-size: 11px; padding: 0 10px;"
#         )
#         self.btn_print.clicked.connect(self._imprimer_filtre)

#         layout.addWidget(self.search_input, 0, Qt.AlignVCenter)
#         layout.addWidget(self.filter_combo, 0, Qt.AlignVCenter)
#         layout.addStretch()
#         layout.addWidget(self.btn_print, 0, Qt.AlignVCenter)
#         return frame

#     def _creer_table_frame(self) -> QFrame:
#         frame = QFrame()
#         frame.setStyleSheet(
#             f"background: {MC.BG_CARD};"
#             f"border-bottom-left-radius: 18px; border-bottom-right-radius: 18px;"
#         )
#         frame_layout = QVBoxLayout(frame)
#         frame_layout.setContentsMargins(0, 0, 0, 0)
#         frame_layout.setSpacing(0)

#         self.table = QTableWidget(0, 4)

#         headers = [
#             ("fa5s.barcode",      "Code"),
#             ("fa5s.user",         "Patient"),
#             ("fa5s.stethoscope",  "Type examen"),
#             ("fa5s.calendar-alt", "Date"),
#         ]
#         for col, (ico, txt) in enumerate(headers):
#             item = QTableWidgetItem()
#             item.setIcon(qta.icon(ico, color=MC.TEXT_INVERSE))
#             item.setText(txt)
#             self.table.setHorizontalHeaderItem(col, item)

#         self.table.verticalHeader().setVisible(False)
#         self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
#         self.table.setSelectionMode(QAbstractItemView.SingleSelection)
#         self.table.setAlternatingRowColors(True)
#         self.table.setStyleSheet(
#             f"QTableWidget {{ border: none; background-color: {MC.BG_CARD};"
#             f"  alternate-background-color: {MC.BG_MAIN};"
#             f"  gridline-color: {MC.BORDER_LIGHT}; }}"
#             f"QHeaderView::section {{ background-color: {MC.PRIMARY}; padding: 10px;"
#             f"  border: none; font-weight: 700; color: {MC.TEXT_INVERSE}; font-size: 11px; }}"
#             f"QTableWidget::item {{ padding: 10px; color: {MC.TEXT_PRIMARY}; }}"
#             f"QTableWidget::item:selected {{ background: {MC.PRIMARY_LIGHT};"
#             f"  color: {MC.TEXT_PRIMARY}; }}"
#         )

#         hdr = self.table.horizontalHeader()
#         hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
#         hdr.setSectionResizeMode(1, QHeaderView.Stretch)
#         hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
#         hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)

#         frame_layout.addWidget(self.table)
#         return frame

#     # ------------------------------------------------------------------ right

#     def _creer_panel_graphique(self) -> QFrame:
#         frame = QFrame()
#         frame.setStyleSheet(
#             f"background: {MC.BG_CARD}; border-radius: 18px; border: 1px solid {MC.BORDER_LIGHT};"
#         )
#         frame.setMinimumWidth(200)
#         frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         layout = QVBoxLayout(frame)
#         layout.setContentsMargins(6, 4, 6, 4)
#         layout.setSpacing(2)

#         # Graphe 1 : Examens par mois
#         self._graph_title1 = QLabel("Examens par mois")
#         self._graph_title1.setStyleSheet(
#             f"font-size: 10px; font-weight: 700; color: {MC.TEXT_PRIMARY};"
#         )
#         layout.addWidget(self._graph_title1)

#         self.graph_canvas = FigureCanvas(
#             Figure(figsize=(3, 2), dpi=100, facecolor=MC.BG_CARD)
#         )
#         self.graph_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.graph_canvas.setMinimumHeight(0)
#         layout.addWidget(self.graph_canvas, 1)

#         # Graphe 2 : Examens du patient sélectionné
#         self._graph_title2 = QLabel("Examens du patient")
#         self._graph_title2.setStyleSheet(
#             f"font-size: 10px; font-weight: 700; color: {MC.TEXT_PRIMARY};"
#         )
#         layout.addWidget(self._graph_title2)

#         self._patient_frame = self._creer_selecteur_patient()
#         layout.addWidget(self._patient_frame)

#         self.graph_patient_canvas = FigureCanvas(
#             Figure(figsize=(3, 2), dpi=100, facecolor=MC.BG_CARD)
#         )
#         self.graph_patient_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.graph_patient_canvas.setMinimumHeight(0)
#         layout.addWidget(self.graph_patient_canvas, 1)

#         return frame

#     def _creer_selecteur_patient(self) -> QFrame:
#         frame = QFrame()
#         frame.setStyleSheet(f"background: {MC.BG_MAIN}; border-radius: 10px;")
#         layout = QHBoxLayout(frame)
#         layout.setContentsMargins(4, 2, 4, 2)
#         layout.setSpacing(4)

#         self._patient_label = QLabel()
#         self._patient_label.setPixmap(
#             qta.icon("fa5s.user-friends", color=MC.PRIMARY).pixmap(16, 16)
#         )
#         layout.addWidget(self._patient_label)

#         self.patient_combo = QComboBox()
#         self.patient_combo.setStyleSheet(
#             f"QComboBox {{ border: 2px solid {MC.BORDER}; border-radius: 8px;"
#             f"  padding: 8px 12px; background: {MC.BG_CARD};"
#             f"  color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }}"
#             f"QComboBox::drop-down {{ border: none; padding-right: 8px; }}"
#             f"QComboBox::down-arrow {{ image: url(none);"
#             f"  border-left: 4px solid transparent; border-right: 4px solid transparent;"
#             f"  border-top: 4px solid {MC.TEXT_SECONDARY}; margin-top: 2px; }}"
#             f"QComboBox:hover {{ border-color: {MC.PRIMARY}; }}"
#             f"QComboBox:focus {{ border-color: {MC.PRIMARY}; }}"
#             f"QComboBox QAbstractItemView {{ border: 1px solid {MC.BORDER};"
#             f"  border-radius: 4px; background: {MC.BG_CARD};"
#             f"  selection-background-color: {MC.HOVER}; }}"
#         )
#         self.patient_combo.setFixedHeight(28)
#         self.patient_combo.currentIndexChanged.connect(self._actualiser_graphique_patient)
#         layout.addWidget(self.patient_combo, 1)

#         layout.addStretch()
#         return frame

#     # =========================================================================
#     # THÈME
#     # =========================================================================

#     def apply_theme(self):
#         self.setStyleSheet(f"background-color: {MC.BG_MAIN};")

#         for panel in (self.left_panel, self.right_panel):
#             panel.setStyleSheet(
#                 f"background: {MC.BG_CARD}; border-radius: 18px;"
#                 f"border: 1px solid {MC.BORDER_LIGHT};"
#             )

#         self._tbl_header.setStyleSheet(
#             f"background: {MC.BG_CARD};"
#             f"border-top-left-radius: 18px; border-top-right-radius: 18px;"
#             f"border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"
#             f"border-bottom: 1px solid {MC.BORDER_LIGHT};"
#         )
#         self._header_icon.setPixmap(
#             qta.icon(self._header_icone, color=MC.PRIMARY).pixmap(QSize(18, 18))
#         )
#         self._header_title.setStyleSheet(
#             f"font-size: 12px; font-weight: 700; color: {MC.TEXT_PRIMARY};"
#         )

#         self._tbl_filter.setStyleSheet(
#             f"background: {MC.BG_CARD}; border: none;"
#             f"border-bottom: 1px solid {MC.BORDER_LIGHT};"
#         )
#         self.search_input.setStyleSheet(
#             f"border: 1px solid {MC.BORDER}; border-radius: 10px;"
#             f"padding-left: 10px; font-size: 11px;"
#         )
#         self.filter_combo.setStyleSheet(
#             f"border: 1px solid {MC.BORDER}; border-radius: 10px;"
#             f"padding-left: 8px; font-size: 11px;"
#         )
#         for i, (ico_name, _) in enumerate(self._FILTER_ITEMS):
#             self.filter_combo.setItemIcon(i, qta.icon(ico_name, color=MC.PRIMARY))

#         self.btn_print.setStyleSheet(
#             f"background-color: {MC.PRIMARY}; color: {MC.TEXT_INVERSE};"
#             f"border-radius: 10px; font-weight: 600; font-size: 11px; padding: 0 10px;"
#         )
#         self.btn_print.setIcon(qta.icon("fa5s.print", color=MC.TEXT_INVERSE))

#         self._tbl_table_frame.setStyleSheet(
#             f"background: {MC.BG_CARD};"
#             f"border-bottom-left-radius: 18px; border-bottom-right-radius: 18px;"
#         )
#         self.table.setStyleSheet(
#             f"QTableWidget {{ border: none; background-color: {MC.BG_CARD};"
#             f"  alternate-background-color: {MC.BG_MAIN};"
#             f"  gridline-color: {MC.BORDER_LIGHT}; }}"
#             f"QHeaderView::section {{ background-color: {MC.PRIMARY}; padding: 6px;"
#             f"  border: none; font-weight: 700; color: {MC.TEXT_INVERSE}; font-size: 10px; }}"
#             f"QTableWidget::item {{ padding: 6px; color: {MC.TEXT_PRIMARY}; font-size: 11px; }}"
#             f"QTableWidget::item:selected {{ background: {MC.PRIMARY_LIGHT};"
#             f"  color: {MC.TEXT_PRIMARY}; }}"
#         )

#         _header_icons = [
#             "fa5s.barcode", "fa5s.user",
#             "fa5s.stethoscope", "fa5s.calendar-alt"
#         ]
#         for col, ico in enumerate(_header_icons):
#             self.table.horizontalHeaderItem(col).setIcon(
#                 qta.icon(ico, color=MC.TEXT_INVERSE)
#             )

#         self._graph_title1.setStyleSheet(
#             f"font-size: 10px; font-weight: 700; color: {MC.TEXT_PRIMARY}; border: none;"
#         )
#         self._graph_title2.setStyleSheet(
#             f"font-size: 10px; font-weight: 700; color: {MC.TEXT_PRIMARY}; border: none;"
#         )

#         self._patient_frame.setStyleSheet(f"background: {MC.BG_MAIN}; border-radius: 10px;")
#         self._patient_label.setPixmap(
#             qta.icon("fa5s.user-friends", color=MC.PRIMARY).pixmap(16, 16)
#         )
#         self.patient_combo.setStyleSheet(
#             f"QComboBox {{ border: 2px solid {MC.BORDER}; border-radius: 8px;"
#             f"  padding: 8px 12px; background: {MC.BG_CARD};"
#             f"  color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; }}"
#             f"QComboBox::drop-down {{ border: none; padding-right: 8px; }}"
#             f"QComboBox::down-arrow {{ image: url(none);"
#             f"  border-left: 4px solid transparent; border-right: 4px solid transparent;"
#             f"  border-top: 4px solid {MC.TEXT_SECONDARY}; margin-top: 2px; }}"
#             f"QComboBox:hover {{ border-color: {MC.PRIMARY}; }}"
#             f"QComboBox:focus {{ border-color: {MC.PRIMARY}; }}"
#             f"QComboBox QAbstractItemView {{ border: 1px solid {MC.BORDER};"
#             f"  border-radius: 4px; background: {MC.BG_CARD};"
#             f"  selection-background-color: {MC.HOVER}; }}"
#         )

#         self.graph_canvas.figure.set_facecolor(MC.BG_CARD)
#         self.graph_patient_canvas.figure.set_facecolor(MC.BG_CARD)

#         self._remplir_combo_patients()
#         self._actualiser_graphique()
#         self._actualiser_graphique_patient()

#     # =========================================================================
#     # CHARGEMENT DES DONNÉES
#     # =========================================================================

#     def charger_examens(self, code_session: str):
#         self.code_session = code_session
#         try:
#             self.examens = self.ctrl.lister_examens(code_session) or []
#         except Exception:
#             self.examens = []

#         self._remplir_combo_patients()
#         self._actualiser_filtrage()

#     def _remplir_combo_patients(self):
#         self.patient_combo.blockSignals(True)
#         self.patient_combo.clear()
#         try:
#             patients = self.ctrl.obtenir_codes_patients_session(self.code_session)
#             if patients:
#                 self.patient_combo.addItem(
#                     qta.icon("fa5s.user-plus", color=MC.TEXT_SECONDARY),
#                     "-- Sélectionnez un patient --",
#                     None
#                 )
#                 for patient in patients:
#                     code      = patient.get('code_patient')
#                     nom       = patient.get('nom', '')
#                     prenom    = patient.get('prenom', '')
#                     a_examine = patient.get('a_consulte', 0)

#                     if a_examine:
#                         icon  = qta.icon("fa5s.user-check", color=MC.PRIMARY)
#                         label = f"{code} - {prenom} {nom} ✓"
#                     else:
#                         icon  = qta.icon("fa5s.user", color=MC.TEXT_SECONDARY)
#                         label = f"{code} - {prenom} {nom}"

#                     self.patient_combo.addItem(icon, label, code)
#         except Exception as e:
#             print(f"[TableauExamenView] Erreur _remplir_combo_patients: {e}")
#         self.patient_combo.blockSignals(False)

#     # =========================================================================
#     # FILTRAGE
#     # =========================================================================

#     def _on_filter_mode_changed(self):
#         mode = self.filter_combo.currentText()
#         if mode == "Date":
#             self.search_input.setPlaceholderText("Saisir une date (dd/mm/yyyy ou yyyy-mm-dd)")
#         elif mode == "Entre":
#             self.search_input.setPlaceholderText("Saisir un intervalle: dd/mm/yyyy - dd/mm/yyyy")
#         else:
#             self.search_input.setPlaceholderText("Rechercher par code, patient ou type...")
#         self._actualiser_filtrage()

#     def _actualiser_filtrage(self):
#         texte  = self.search_input.text().strip()
#         filtre = self.filter_combo.currentText()
#         self.filtered_examens = []

#         if filtre == "Tous":
#             self.filtered_examens = (
#                 self._filtrer_par_texte(self.examens, texte) if texte
#                 else self.examens
#             )

#         elif filtre == "Date":
#             if texte:
#                 date_obj = self._parse_date(texte)
#                 if date_obj:
#                     result = self.ctrl.rechercher_entre_dates(
#                         self.code_session, date_obj, date_obj
#                     )
#                     self.filtered_examens = result or []

#         elif filtre == "Entre":
#             if texte:
#                 dates = self._parse_date_range(texte)
#                 if dates:
#                     date_debut, date_fin = dates
#                     result = self.ctrl.rechercher_entre_dates(
#                         self.code_session, date_debut, date_fin
#                     )
#                     self.filtered_examens = result or []

#         self._remplir_table(self.filtered_examens)
#         self._actualiser_graphique()

#     def _filtrer_par_texte(self, examens, texte: str) -> list:
#         texte_lower = texte.lower()
#         result = []
#         for e in examens:
#             code = str(getattr(e, 'code', ''))
#             values = [
#                 code,
#                 self._get_nom_patient(code),
#                 self._get_type_examen(e),
#                 self._format_date(getattr(e, 'date_examen', '')),
#             ]
#             if texte_lower in " ".join(v.lower() for v in values):
#                 result.append(e)
#         return result

#     def _parse_date(self, texte: str):
#         texte = texte.strip()
#         for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
#             try:
#                 return datetime.strptime(texte, fmt).date()
#             except ValueError:
#                 continue
#         return None

#     def _parse_date_range(self, texte: str):
#         texte = texte.strip()
#         separators = [' - ', ' au ', ' à ', ' et ', ' to ', ';', ',']
#         for sep in separators:
#             if sep in texte:
#                 parts = texte.split(sep, 1)
#                 if len(parts) == 2:
#                     d1 = self._parse_date(parts[0].strip())
#                     d2 = self._parse_date(parts[1].strip())
#                     if d1 and d2:
#                         return (d1, d2) if d1 <= d2 else (d2, d1)

#         date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}'
#         found = re.findall(date_pattern, texte)
#         if len(found) == 2:
#             d1 = self._parse_date(found[0])
#             d2 = self._parse_date(found[1])
#             if d1 and d2:
#                 return (d1, d2) if d1 <= d2 else (d2, d1)
#         return None

#     # =========================================================================
#     # REMPLISSAGE TABLE
#     # =========================================================================

#     def _remplir_table(self, examens):
#         """
#         Remplit le tableau — utilise getattr sur les objets Examen,
#         jamais de notation dict examen['...'].
#         """
#         self.table.setRowCount(0)
#         for e in examens:
#             row = self.table.rowCount()
#             self.table.insertRow(row)
#             code = str(getattr(e, 'code', '—'))
#             self.table.setItem(row, 0, QTableWidgetItem(code))
#             self.table.setItem(row, 1, QTableWidgetItem(self._get_nom_patient(code)))
#             self.table.setItem(row, 2, QTableWidgetItem(self._get_type_examen(e)))
#             self.table.setItem(
#                 row, 3,
#                 QTableWidgetItem(self._format_date(getattr(e, 'date_examen', '—')))
#             )

#     # =========================================================================
#     # GRAPHE 1 : EXAMENS PAR MOIS (BAR HORIZONTAL)
#     # =========================================================================

#     def _actualiser_graphique(self):
#         try:
#             data = self.ctrl.obtenir_nombre_par_mois(self.code_session)
#             if not data:
#                 self.graph_canvas.figure.clear()
#                 self.graph_canvas.draw()
#                 return

#             self.graph_canvas.figure.clear()
#             ax = self.graph_canvas.figure.add_subplot(111)
#             ax.set_facecolor(MC.BG_CARD)
#             ax.grid(True, axis="x", alpha=0.3, linestyle="--", color=MC.BORDER)

#             mois_ordre  = {str(i): i - 1 for i in range(1, 13)}
#             mois_sorted = sorted(data.keys(), key=lambda x: mois_ordre.get(x, 100))
#             values      = [data[m] for m in mois_sorted]

#             max_val = max(values) if values else 0
#             if max_val <= 3:
#                 step, max_limit = 1, max(3, max_val + 0.5)
#             elif max_val <= 10:
#                 step, max_limit = 2, max(10, max_val + 1)
#             elif max_val <= 50:
#                 step, max_limit = 5, max(50, max_val + 5)
#             elif max_val <= 200:
#                 step, max_limit = 20, max(200, max_val + 20)
#             else:
#                 step, max_limit = 50, max(500, max_val + 50)

#             colors = [MC.PRIMARY if v > 0 else MC.BG_MAIN for v in values]
#             bars   = ax.barh(mois_sorted, values, color=colors,
#                              edgecolor=MC.PRIMARY, linewidth=1, height=0.8)

#             for bar, val in zip(bars, values):
#                 if val > 0:
#                     if val < max_limit * 0.15:
#                         text_x, ha = val + (max_limit * 0.02), "left"
#                     else:
#                         text_x, ha = val - (max_limit * 0.02), "right"
#                     ax.text(
#                         text_x, bar.get_y() + bar.get_height() / 2,
#                         f"{int(val)}", ha=ha, va="center", fontsize=8,
#                         fontweight="bold",
#                         color=MC.PRIMARY if ha == "right" else MC.TEXT_SECONDARY
#                     )

#             ax.set_xlim(0, max_limit)
#             ax.set_xticks(range(0, int(max_limit) + step, step))
#             ax.set_xlabel("Examens", fontsize=9, fontweight="bold", color=MC.TEXT_PRIMARY)
#             ax.set_ylabel("Mois",    fontsize=9, fontweight="bold", color=MC.TEXT_PRIMARY)
#             ax.tick_params(labelsize=8, colors=MC.TEXT_SECONDARY)
#             for spine in ("top", "right"):
#                 ax.spines[spine].set_visible(False)
#             ax.spines["left"].set_color(MC.BORDER)
#             ax.spines["bottom"].set_color(MC.BORDER)
#             self.graph_canvas.figure.subplots_adjust(
#                 left=0.12, right=0.98, top=0.95, bottom=0.12
#             )
#             self.graph_canvas.draw()
#         except Exception as e:
#             print(f"[TableauExamenView] Erreur _actualiser_graphique: {e}")

#     # =========================================================================
#     # GRAPHE 2 : EXAMENS DU PATIENT (BAR HORIZONTAL)
#     # =========================================================================

#     def _actualiser_graphique_patient(self):
#         try:
#             patient_code = self.patient_combo.currentData()
#             if not patient_code:
#                 self.graph_patient_canvas.figure.clear()
#                 self.graph_patient_canvas.draw()
#                 return

#             data = self.ctrl.obtenir_examens_par_patient_par_mois(
#                 self.code_session, patient_code
#             )
#             if not data:
#                 self.graph_patient_canvas.figure.clear()
#                 self.graph_patient_canvas.draw()
#                 return

#             self.graph_patient_canvas.figure.clear()
#             ax = self.graph_patient_canvas.figure.add_subplot(111)
#             ax.set_facecolor(MC.BG_CARD)
#             ax.grid(True, axis="x", alpha=0.3, linestyle="--", color=MC.BORDER)

#             mois_ordre  = {str(i): i - 1 for i in range(1, 13)}
#             mois_sorted = sorted(data.keys(), key=lambda x: mois_ordre.get(x, 100))
#             values      = [data[m] for m in mois_sorted]

#             max_val = max(values) if values else 0
#             if max_val <= 3:
#                 step, max_limit = 1, max(3, max_val + 0.5)
#             elif max_val <= 10:
#                 step, max_limit = 2, max(10, max_val + 1)
#             elif max_val <= 50:
#                 step, max_limit = 5, max(50, max_val + 5)
#             elif max_val <= 200:
#                 step, max_limit = 20, max(200, max_val + 20)
#             else:
#                 step, max_limit = 50, max(500, max_val + 50)

#             colors = [MC.ACCENT if v > 0 else MC.BG_MAIN for v in values]
#             bars   = ax.barh(mois_sorted, values, color=colors,
#                              edgecolor=MC.ACCENT, linewidth=1, height=0.8)

#             for bar, val in zip(bars, values):
#                 if val > 0:
#                     if val < max_limit * 0.15:
#                         text_x, ha = val + (max_limit * 0.02), "left"
#                     else:
#                         text_x, ha = val - (max_limit * 0.02), "right"
#                     ax.text(
#                         text_x, bar.get_y() + bar.get_height() / 2,
#                         f"{int(val)}", ha=ha, va="center", fontsize=8,
#                         fontweight="bold",
#                         color=MC.ACCENT if ha == "right" else MC.TEXT_SECONDARY
#                     )

#             ax.set_xlim(0, max_limit)
#             ax.set_xticks(range(0, int(max_limit) + step, step))
#             ax.set_xlabel("Examens", fontsize=9, fontweight="bold", color=MC.TEXT_PRIMARY)
#             ax.set_ylabel("Mois",    fontsize=9, fontweight="bold", color=MC.TEXT_PRIMARY)
#             ax.tick_params(labelsize=8, colors=MC.TEXT_SECONDARY)
#             for spine in ("top", "right"):
#                 ax.spines[spine].set_visible(False)
#             ax.spines["left"].set_color(MC.BORDER)
#             ax.spines["bottom"].set_color(MC.BORDER)
#             self.graph_patient_canvas.figure.subplots_adjust(
#                 left=0.12, right=0.98, top=0.95, bottom=0.12
#             )
#             self.graph_patient_canvas.draw()
#         except Exception as e:
#             print(f"[TableauExamenView] Erreur _actualiser_graphique_patient: {e}")

#     # =========================================================================
#     # UTILITAIRES
#     # =========================================================================

#     def _to_date(self, value):
#         if isinstance(value, date):
#             return value
#         if isinstance(value, datetime):
#             return value.date()
#         if isinstance(value, str):
#             for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
#                 try:
#                     return datetime.strptime(value, fmt).date()
#                 except ValueError:
#                     continue
#         return None

#     def _format_date(self, value) -> str:
#         date_val = self._to_date(value)
#         if not date_val:
#             return str(value or "—")
#         return date_val.strftime("%d/%m/%Y")

#     def _get_type_examen(self, examen) -> str:
#         """Retourne le type/libellé d'examen depuis l'objet Examen."""
#         for attr in ('type_examen', 'libelle_examen', 'libelle', 'type', 'service'):
#             val = getattr(examen, attr, None)
#             if val:
#                 return str(val)
#         return "Examen"

#     def _get_nom_patient(self, code_examen: str) -> str:
#         try:
#             data = self.ctrl.obtenir_examen_complet(code_examen)
#             if not data:
#                 return "—"
#             nom    = data.get('patient_nom',    '') or data.get('nom_patient',    '') or ''
#             prenom = data.get('patient_prenom', '') or data.get('prenom_patient', '') or ''
#             return f"{nom} {prenom}".strip() or "—"
#         except Exception:
#             return "—"

#     # =========================================================================
#     # IMPRESSION
#     # =========================================================================

#     def _imprimer_filtre(self):
#         try:
#             from PySide6.QtWidgets import QFileDialog, QMessageBox
#             from services.examen_pdf_service import ExamenPDFService
#             import os

#             examens_a_imprimer = (
#                 self.filtered_examens if self.filtered_examens else self.examens
#             )

#             if not examens_a_imprimer:
#                 QMessageBox.warning(
#                     self, "Aucune donnée",
#                     "Aucun examen à imprimer avec les filtres actuels."
#                 )
#                 return

#             filtres_appliques = {}
#             texte = self.search_input.text().strip()
#             if texte:
#                 filtres_appliques['recherche'] = texte

#             filtre_selectionne = self.filter_combo.currentText()
#             if filtre_selectionne == "Date" and texte:
#                 d = self._parse_date(texte)
#                 if d:
#                     filtres_appliques['date_debut'] = d
#                     filtres_appliques['date_fin']   = d
#             elif filtre_selectionne == "Entre" and texte:
#                 dates = self._parse_date_range(texte)
#                 if dates:
#                     filtres_appliques['date_debut'], filtres_appliques['date_fin'] = dates

#             info_cabinet = self.ctrl.info_cabinet()
#             if not info_cabinet:
#                 QMessageBox.warning(self, "Erreur",
#                                     "Impossible de récupérer les informations du cabinet.")
#                 return

#             timestamp       = datetime.now().strftime("%Y%m%d_%H%M%S")
#             nom_fichier_def = f"examens_filtres_{timestamp}.pdf"

#             chemin_pdf, _ = QFileDialog.getSaveFileName(
#                 self, "Sauvegarder le rapport PDF",
#                 nom_fichier_def, "Fichiers PDF (*.pdf)"
#             )
#             if not chemin_pdf:
#                 return

#             success = ExamenPDFService.generer_pdf_examens_filtres(
#                 examens_a_imprimer, filtres_appliques, chemin_pdf, info_cabinet
#             )

#             if success:
#                 QMessageBox.information(
#                     self, "Succès",
#                     f"Le rapport PDF a été généré avec succès :\n{chemin_pdf}"
#                 )
#                 os.startfile(chemin_pdf)
#             else:
#                 QMessageBox.critical(self, "Erreur",
#                                      "Erreur lors de la génération du PDF.")

#         except ImportError as e:
#             from PySide6.QtWidgets import QMessageBox
#             QMessageBox.critical(self, "Erreur d'import",
#                                  f"Module manquant : {str(e)}")
#         except Exception as e:
#             from PySide6.QtWidgets import QMessageBox
#             QMessageBox.critical(self, "Erreur inattendue",
#                                  f"{str(e)}")