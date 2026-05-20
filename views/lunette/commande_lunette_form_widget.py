"""
Widget formulaire commande lunette — même pattern que consultation/chirurgie/examen.
- Header avec boutons Annuler / Enregistrer (en haut à droite)
- Une seule carte, 2 rangées, pas de scroll
- Labels sans bordure ni fond
"""
import qtawesome as qta
from datetime import date as ddate

from PySide6.QtCore    import Qt, QDate, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDateEdit, QFrame,
)

from models.modeles_lunette   import CommandeLunette
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class CommandeLunetteFormWidget(QWidget):
    """
    Formulaire inline (non-dialog) pour créer/modifier une commande de lunettes.
    Pattern identique à ExamenFormWidget / ChirurgieFormWidget.
    """

    commande_saved = Signal()

    def __init__(self, controleur, code_session: str, parent=None):
        super().__init__(parent)
        self.ctrl          = controleur
        self.code_session  = code_session
        self._commande_obj = None   # None → création, sinon → modification

        self._consultations = []

        self._init_ui()
        self._charger_combos()
        self._connecter_validations()

        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # UI PRINCIPALE
    # =========================================================================

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 4, 20, 12)
        outer.setSpacing(10)

        self._setup_header(outer)
        self._section_infos(outer)
        self._section_info_bas(outer)
        outer.addStretch()

        self.apply_theme()

    # =========================================================================
    # HEADER
    # =========================================================================

    def _setup_header(self, parent_layout):
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(72)
        c = theme_manager.colors()
        self.header_frame.setStyleSheet(f"""
            background-color: {c['bg_card']};
            border-radius: 14px;
            border: none;
        """)

        layout = QHBoxLayout(self.header_frame)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(14)

        icon_box = QFrame()
        icon_box.setFixedSize(46, 46)
        icon_box.setStyleSheet(f"""
            background-color: {c['bg_main']};
            border-radius: 10px;
            border: 1px solid {c['border_light']};
        """)
        ib_layout = QHBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon("fa5s.glasses", color=c['primary']).pixmap(22, 22))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_main = QLabel("Commande de Lunettes")
        lbl_main.setStyleSheet(
            f"font-size: 17px; font-weight: bold; color: {c['text_primary']};"
            " background: transparent; border: none;"
        )
        lbl_sub = QLabel("Remplissez les informations de la commande")
        lbl_sub.setStyleSheet(
            f"font-size: 12px; color: {c['text_muted']};"
            " background: transparent; border: none;"
        )
        title_col.addWidget(lbl_main)
        title_col.addWidget(lbl_sub)

        layout.addWidget(icon_box)
        layout.addLayout(title_col)
        layout.addStretch()

        self.btn_cancel = QPushButton(
            qta.icon("fa5s.times", color=c['text_secondary']), " Annuler"
        )
        self.btn_cancel.setFixedSize(110, 40)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_main']};
                color: {c['text_secondary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {c['hover']}; }}
        """)
        self.btn_cancel.clicked.connect(self._annuler)

        self.btn_save = QPushButton(
            qta.icon("fa5s.save", color="#ffffff"), " Enregistrer"
        )
        self.btn_save.setFixedSize(150, 40)
        self.btn_save.setEnabled(False)
        self._apply_save_btn_style()
        self.btn_save.clicked.connect(self._soumettre)

        layout.addWidget(self.btn_cancel)
        layout.addWidget(self.btn_save)
        parent_layout.addWidget(self.header_frame)

    def _apply_save_btn_style(self):
        c = theme_manager.colors()
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['border']};
                color: {c['text_muted']};
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }}
            QPushButton:enabled {{
                background-color: {c['primary']};
                color: #ffffff;
            }}
            QPushButton:enabled:hover {{ background-color: {c['primary_hover']}; }}
        """)

    # =========================================================================
    # HELPERS — champ badge-icône
    # =========================================================================

    def _make_field(self, label_text: str, widget, icon_name: str, icon_color: str,
                    height: int = 42, align_top: bool = False):
        """Retourne (QVBoxLayout, wrapper_QFrame)."""
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )
        vbox.addWidget(lbl)

        wrapper = QFrame()
        wrapper.setObjectName("inputWrapper")
        wrapper.setFixedHeight(height)
        self._apply_wrapper_style(wrapper)

        hbox = QHBoxLayout(wrapper)
        hbox.setContentsMargins(8, 5, 8, 5)
        hbox.setSpacing(8)

        badge = QFrame()
        badge.setFixedSize(28, 28)
        badge.setStyleSheet(
            f"background-color: {icon_color}20; border-radius: 7px; border: none;"
        )
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        ic_lbl = QLabel()
        ic_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(14, 14))
        ic_lbl.setAlignment(Qt.AlignCenter)
        ic_lbl.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(ic_lbl, alignment=Qt.AlignCenter)

        self._clear_widget_style(widget, c)
        hbox.addWidget(badge, 0, Qt.AlignVCenter)
        hbox.addWidget(widget, 1)
        vbox.addWidget(wrapper)
        return vbox, wrapper

    def _apply_wrapper_style(self, wrapper: QFrame, border_color: str = None):
        c = theme_manager.colors()
        bc = border_color or c['border']
        wrapper.setStyleSheet(f"""
            QFrame#inputWrapper {{
                background-color: {c['bg_input']};
                border: 1.5px solid {bc};
                border-radius: 10px;
            }}
        """)

    def _clear_widget_style(self, widget, c):
        base = (
            f"border: none; background: transparent;"
            f" font-size: 12px; color: {c['text_primary']};"
        )
        if isinstance(widget, QComboBox):
            widget.setStyleSheet(f"""
                QComboBox {{ {base} padding: 0; min-height: 28px; }}
                QComboBox::drop-down {{ border: none; width: 20px; }}
                QComboBox QAbstractItemView {{
                    background-color: {c['bg_card']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                    color: {c['text_primary']};
                    selection-background-color: {c['primary_light']};
                    outline: none;
                }}
                QComboBox QAbstractItemView::item {{ padding: 6px 10px; min-height: 26px; }}
                QComboBox QAbstractItemView::item:hover {{ background-color: {c['hover']}; }}
                QComboBox QAbstractItemView::item:selected {{
                    background-color: {c['primary_light']}; color: {c['primary']};
                }}
            """)
        elif isinstance(widget, QDateEdit):
            widget.setStyleSheet(f"QDateEdit {{ {base} padding: 0; }}")
        else:
            widget.setStyleSheet(f"QLineEdit {{ {base} padding: 0; }}")

    def _field_widget(self, vbox: QVBoxLayout) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        w.setLayout(vbox)
        return w

    def _err_label(self) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel("")
        lbl.setStyleSheet(
            f"color: {c['danger']}; font-size: 10px; font-style: italic;"
            " background: transparent;"
        )
        lbl.setVisible(False)
        return lbl

    # =========================================================================
    # SECTION UNIQUE — 2 rangées dans une seule carte
    # =========================================================================

    def _section_infos(self, parent_layout):
        c = theme_manager.colors()
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(18, 14, 18, 14)
        vbox.setSpacing(12)

        # Titre de section
        hdr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.glasses", color=c['primary']).pixmap(16, 16))
        ico.setStyleSheet("border: none; background: transparent;")
        lbl_t = QLabel("Informations de la commande")
        lbl_t.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {c['primary']};"
            " background: transparent; border: none;"
        )
        hdr.addWidget(ico)
        hdr.addSpacing(8)
        hdr.addWidget(lbl_t)
        hdr.addStretch()
        vbox.addLayout(hdr)

        # ── Rangée 1 : Patient/Consultation | Code Visite | Numéro Cadre | Numéro Verre ──
        row1 = QHBoxLayout()
        row1.setSpacing(14)
        row1.setAlignment(Qt.AlignTop)

        self.combo_consultation = QComboBox()
        vb_c, self._wrap_consultation = self._make_field(
            "Patient / Consultation *", self.combo_consultation,
            "fa5s.file-medical", "#e74c3c"
        )
        self._err_consultation = self._err_label()
        vb_c.addWidget(self._err_consultation)
        row1.addWidget(self._field_widget(vb_c), 2, Qt.AlignTop)

        self.edit_code_visite = QLineEdit()
        self.edit_code_visite.setPlaceholderText("Auto")
        self.edit_code_visite.setReadOnly(True)
        vb_v, _ = self._make_field(
            "Code Visite", self.edit_code_visite, "fa5s.link", "#95a5a6"
        )
        row1.addWidget(self._field_widget(vb_v), 1, Qt.AlignTop)

        self.edit_numero_cadre = QLineEdit()
        self.edit_numero_cadre.setPlaceholderText("Ex : CAD-2024-001")
        vb_cad, _ = self._make_field(
            "Numéro Cadre", self.edit_numero_cadre, "fa5s.glasses", "#3498db"
        )
        row1.addWidget(self._field_widget(vb_cad), 1, Qt.AlignTop)

        self.edit_numero_verre = QLineEdit()
        self.edit_numero_verre.setPlaceholderText("Ex : +2.00 / -1.50")
        vb_ver, _ = self._make_field(
            "Numéro Verre", self.edit_numero_verre, "fa5s.eye", "#9b59b6"
        )
        row1.addWidget(self._field_widget(vb_ver), 1, Qt.AlignTop)

        vbox.addLayout(row1)

        # ── Rangée 2 : Date Livraison | Prix | Personnel | Statut Facture ──
        row2 = QHBoxLayout()
        row2.setSpacing(14)
        row2.setAlignment(Qt.AlignTop)

        self.edit_date_livraison = QDateEdit()
        self.edit_date_livraison.setCalendarPopup(True)
        self.edit_date_livraison.setDisplayFormat("dd/MM/yyyy")
        self.edit_date_livraison.setDate(QDate.currentDate().addDays(7))
        vb_date, _ = self._make_field(
            "Date Livraison Prévue", self.edit_date_livraison,
            "fa5s.calendar-alt", "#e67e22"
        )
        row2.addWidget(self._field_widget(vb_date), 1, Qt.AlignTop)

        self.edit_prix = QLineEdit()
        self.edit_prix.setPlaceholderText("Ex : 850000")
        vb_prix, self._wrap_prix = self._make_field(
            "Prix (GNF) *", self.edit_prix, "fa5s.money-bill-wave", "#27ae60"
        )
        self._err_prix = self._err_label()
        vb_prix.addWidget(self._err_prix)
        row2.addWidget(self._field_widget(vb_prix), 1, Qt.AlignTop)

        # Personnel (combo)
        self.combo_personnel = QComboBox()
        self.combo_personnel.addItem("-- Sélectionner le personnel --", "")
        # Charger la liste du personnel
        try:
            personnels = self.ctrl.lister_personnel() or []
            for personnel in personnels:
                nom = personnel.get('nom', '') if isinstance(personnel, dict) else getattr(personnel, 'nom', '')
                prenom = personnel.get('prenom', '') if isinstance(personnel, dict) else getattr(personnel, 'prenom', '')
                fonction = personnel.get('fonction', '') if isinstance(personnel, dict) else getattr(personnel, 'fonction', '')
                code = personnel.get('code', '') if isinstance(personnel, dict) else getattr(personnel, 'code', '')
                label = f"{nom} {prenom}  |  {fonction}"
                self.combo_personnel.addItem(label, code)
        except Exception as e:
            print(f"Erreur chargement personnel: {e}")
        vb_perso, self._wrap_personnel = self._make_field(
            "Personnel *", self.combo_personnel,
            "fa5s.user-md", "#1abc9c"
        )
        self._err_personnel = self._err_label()
        vb_perso.addWidget(self._err_personnel)
        row2.addWidget(self._field_widget(vb_perso), 1, Qt.AlignTop)

        self.combo_statut_facture = QComboBox()
        self.combo_statut_facture.addItems([
            "Attente payement", "Payée", "Partiellement payée"
        ])
        vb_stat, _ = self._make_field(
            "Statut Facture", self.combo_statut_facture,
            "fa5s.file-invoice", "#f39c12"
        )
        row2.addWidget(self._field_widget(vb_stat), 1, Qt.AlignTop)

        vbox.addLayout(row2)
        parent_layout.addWidget(card)

    # =========================================================================
    # SECTION INFO BAS
    # =========================================================================

    def _section_info_bas(self, parent_layout):
        c = theme_manager.colors()
        card = QFrame()
        card.setFixedHeight(70)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['primary_light']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
        """)
        hbox = QHBoxLayout(card)
        hbox.setContentsMargins(20, 0, 20, 0)
        hbox.setSpacing(14)

        ico_frame = QFrame()
        ico_frame.setFixedSize(36, 36)
        ico_frame.setStyleSheet(
            f"background-color: {c['primary']}; border-radius: 18px;"
        )
        ifi = QHBoxLayout(ico_frame)
        ifi.setContentsMargins(0, 0, 0, 0)
        il = QLabel()
        il.setPixmap(qta.icon("fa5s.info", color="#ffffff").pixmap(14, 14))
        il.setAlignment(Qt.AlignCenter)
        ifi.addWidget(il, alignment=Qt.AlignCenter)

        txt = QVBoxLayout()
        txt.setSpacing(2)
        t1 = QLabel("Informations")
        t1.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {c['primary']};"
            " background: transparent;"
        )
        t2 = QLabel(
            "Sélectionnez un patient et saisissez le prix avant d'enregistrer la commande."
        )
        t2.setStyleSheet(
            f"font-size: 11px; color: {c['text_secondary']}; background: transparent;"
        )
        txt.addWidget(t1)
        txt.addWidget(t2)

        hbox.addWidget(ico_frame)
        hbox.addLayout(txt)
        hbox.addStretch()
        parent_layout.addWidget(card)

    # =========================================================================
    # DONNÉES COMBOS
    # =========================================================================

    def _charger_combos(self):
        self.combo_consultation.blockSignals(True)
        self.combo_consultation.clear()
        self.combo_consultation.addItem("— Sélectionner un patient —", None)

        try:
            self._consultations = (
                self.ctrl.obtenir_patients_attente_lunette(self.code_session) or []
            )
        except Exception:
            self._consultations = []

        for row in self._consultations:
            label = (
                f"{row.get('code_consultation', '')}  |  "
                f"{row.get('nom', '')} {row.get('prenom', '')}  |  "
                f"{row.get('date_visite', '')}"
            )
            self.combo_consultation.addItem(label, {
                "code_consultation": row.get("code_consultation", ""),
                "code_visite":       row.get("code_visite", ""),
                "code_acte":         row.get("code_acte", ""),
            })

        self.combo_consultation.blockSignals(False)

    def _on_consultation_changed(self, idx: int):
        data = self.combo_consultation.itemData(idx)
        if data and isinstance(data, dict):
            self.edit_code_visite.setText(data.get("code_visite", ""))
        else:
            self.edit_code_visite.clear()
        self._valider_formulaire()

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def _connecter_validations(self):
        self.combo_consultation.currentIndexChanged.connect(self._on_consultation_changed)
        self.edit_prix.textChanged.connect(self._valider_formulaire)
        self.combo_personnel.currentIndexChanged.connect(self._valider_formulaire)

    def _valider_formulaire(self):
        tout_valide = True
        c = theme_manager.colors()

        # Validation consultation
        data = self.combo_consultation.currentData()
        if not data or not isinstance(data, dict):
            self._apply_wrapper_style(self._wrap_consultation, c['danger'])
            self._err_consultation.setText("Veuillez sélectionner un patient")
            self._err_consultation.setVisible(True)
            tout_valide = False
        else:
            self._apply_wrapper_style(self._wrap_consultation, c['border_focus'])
            self._err_consultation.setVisible(False)

        # Validation prix
        prix = self.edit_prix.text().strip()
        if not prix:
            self._apply_wrapper_style(self._wrap_prix, c['border'])
            self._err_prix.setVisible(False)
            tout_valide = False
        else:
            try:
                float(prix)
                self._apply_wrapper_style(self._wrap_prix, c['border_focus'])
                self._err_prix.setVisible(False)
            except ValueError:
                self._apply_wrapper_style(self._wrap_prix, c['danger'])
                self._err_prix.setText("Prix invalide (nombre attendu)")
                self._err_prix.setVisible(True)
                tout_valide = False

        # Validation personnel
        if not self.combo_personnel.currentData():
            self._apply_wrapper_style(self._wrap_personnel, c['danger'])
            self._err_personnel.setText("Veuillez sélectionner un personnel")
            self._err_personnel.setVisible(True)
            tout_valide = False
        else:
            self._apply_wrapper_style(self._wrap_personnel, c['border_focus'])
            self._err_personnel.setVisible(False)

        self.btn_save.setEnabled(tout_valide)
        self._apply_save_btn_style()

    # =========================================================================
    # RECHARGER POUR PATIENT
    # =========================================================================

    def recharger_pour_patient(self, code_consultation: str, code_session: str):
        self.code_session  = code_session
        self._commande_obj = None
        self._charger_combos()
        for i in range(self.combo_consultation.count()):
            d = self.combo_consultation.itemData(i)
            if isinstance(d, dict) and d.get("code_consultation") == code_consultation:
                self.combo_consultation.setCurrentIndex(i)
                break

    # =========================================================================
    # ACTIONS BOUTONS
    # =========================================================================

    def _annuler(self):
        self._reinitialiser()

    def _reinitialiser(self):
        self._commande_obj = None
        self.combo_consultation.setCurrentIndex(0)
        self.edit_code_visite.clear()
        self.edit_numero_cadre.clear()
        self.edit_numero_verre.clear()
        self.edit_prix.clear()
        self.combo_personnel.setCurrentIndex(0)
        self.edit_date_livraison.setDate(QDate.currentDate().addDays(7))
        self.combo_statut_facture.setCurrentIndex(0)
        self.btn_save.setEnabled(False)
        self._apply_save_btn_style()
        self._charger_combos()

    def _soumettre(self):
        data = self.combo_consultation.currentData()
        if not data or not isinstance(data, dict):
            CustomMessageBox("Validation", "Veuillez sélectionner un patient.", False, self).exec()
            return

        code_acte   = data.get("code_acte", "")
        code_visite = data.get("code_visite", "")

        qdate = self.edit_date_livraison.date()
        date_livraison = ddate(qdate.year(), qdate.month(), qdate.day())

        commande = CommandeLunette(
            code           = self._commande_obj.code if self._commande_obj else None,
            numero_cadre   = self.edit_numero_cadre.text().strip(),
            numero_verre   = self.edit_numero_verre.text().strip(),
            date_livraison = date_livraison,
            prix           = self.edit_prix.text().strip(),
            statut_facture = self.combo_statut_facture.currentText(),
            code_session   = self.code_session,
            code_personnel = self.combo_personnel.currentData(),
            code_acte      = code_acte,
        )

        if self._commande_obj:
            ok, msg = self.ctrl.modifier_commande(commande)
        else:
            ok, msg = self.ctrl.creer_commande(commande)

        if ok:
            CustomMessageBox("Succès", msg, True, self).exec()
            self.commande_saved.emit()
            self._reinitialiser()
        else:
            CustomMessageBox("Erreur", msg, False, self).exec()

    # =========================================================================
    # THÈME
    # =========================================================================

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"QWidget {{ background: {c['bg_main']}; }}")
        self.header_frame.setStyleSheet(f"""
            background-color: {c['bg_card']};
            border-radius: 14px;
            border: none;
        """)
        self._apply_save_btn_style()
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_main']};
                color: {c['text_secondary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {c['hover']}; }}
        """)
