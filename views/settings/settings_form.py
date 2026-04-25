import qtawesome as qta
from PySide6.QtCore import Qt, QSize, Signal, QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QLabel, QGraphicsDropShadowEffect,
    QLineEdit, QTextEdit, QComboBox, QSizePolicy,
    QGridLayout, QFileDialog, QMessageBox, QDateEdit
)
from views.shared.theme_manager import theme_manager
from parametre.controleur_param import CabinetController


class SettingsForm(QWidget):
    """
    Formulaire de paramètres généraux du cabinet.
    Contient : formulaire 2 colonnes + panel aperçu.
    """
    
    # Signal émis quand les données sont sauvegardées avec succès
    donnees_sauvegardees = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #FFFFFF;")
        self.controller = CabinetController()
        self.chemin_logo_selectionne = None
        self._init_ui()
        self._charger_donnees()
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def _init_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 6, 0, 0)
        outer.setSpacing(14)
        
        # Formulaire (2 colonnes)
        form_widget = self._creer_formulaire()
        outer.addWidget(form_widget, 0)
        
        # Panel Aperçu
        self.apercu_panel = self._creer_apercu_panel()
        outer.addWidget(self.apercu_panel, 1, Qt.AlignTop)
    
    def _creer_formulaire(self) -> QWidget:
        """Crée le formulaire avec 2 colonnes."""
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: #FFFFFF;")
        form_widget.setMaximumWidth(580)
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)
        
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(3)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        
        # ── Colonne gauche ────────────────────────────────────────────────────
        row = 0
        
        # Nom du cabinet
        grid.addWidget(self._mk_label("Nom du cabinet"), row, 0)
        row += 1
        self.inp_nom = self._mk_input("Cabinet Ophtalmologique Vision Plus")
        grid.addWidget(self.inp_nom, row, 0)
        row += 1
        
        # Email
        grid.addWidget(self._mk_label("Email"), row, 0)
        row += 1
        self.inp_email = self._mk_input("contact@visionplus.com")
        grid.addWidget(self.inp_email, row, 0)
        row += 1
        
        # Téléphone
        grid.addWidget(self._mk_label("Téléphone"), row, 0)
        row += 1
        self.inp_tel = self._mk_input("+224 612 34 56 78")
        grid.addWidget(self.inp_tel, row, 0)
        row += 1
        
        # Devise principale
        grid.addWidget(self._mk_label("Devise principale"), row, 0)
        row += 1
        self.cb_devise = self._mk_combo([
            "GNF - Franc guinéen (GNF)", "EUR - Euro (€)", "USD - Dollar ($)"
        ])
        grid.addWidget(self.cb_devise, row, 0)
        row += 1
        
        # Logo du cabinet
        grid.addWidget(self._mk_label("Logo du cabinet"), row, 0)
        row += 1
        logo_w = self._creer_logo_widget()
        grid.addWidget(logo_w, row, 0)
        row += 1
        
        # ── Colonne droite ────────────────────────────────────────────────────
        row_r = 0
        
        # Adresse
        grid.addWidget(self._mk_label("Adresse"), row_r, 1)
        row_r += 1
        self.inp_adresse = QTextEdit()
        self.inp_adresse.setPlainText("Rue KA 123, Quartier Kaloum\nConakry, Guinée")
        self.inp_adresse.setFixedHeight(46)
        self.inp_adresse.setStyleSheet(self._css_input())
        grid.addWidget(self.inp_adresse, row_r, 1)
        row_r += 1
        
        # Fuseau horaire
        grid.addWidget(self._mk_label("Fuseau horaire"), row_r, 1)
        row_r += 1
        self.cb_fuseau = self._mk_combo([
            "(GMT) Afrique/Conakry", "(GMT+1) Europe/Paris", "(GMT-5) America/New_York"
        ])
        grid.addWidget(self.cb_fuseau, row_r, 1)
        row_r += 1
        
        # Format de date
        grid.addWidget(self._mk_label("Format de date"), row_r, 1)
        row_r += 1
        self.cb_date_fmt = self._mk_combo(["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
        grid.addWidget(self.cb_date_fmt, row_r, 1)
        row_r += 1
        
        # Format d'heure
        grid.addWidget(self._mk_label("Format d'heure"), row_r, 1)
        row_r += 1
        self.cb_heure_fmt = self._mk_combo(["24 heures (HH:mm)", "12 heures (AM/PM)"])
        grid.addWidget(self.cb_heure_fmt, row_r, 1)
        row_r += 1
        
        # Date de création
        grid.addWidget(self._mk_label("Date de création"), row_r, 1)
        row_r += 1
        self.date_creation = self._creer_date_input()
        grid.addWidget(self.date_creation, row_r, 1)
        row_r += 1
        
        # Notes
        grid.addWidget(self._mk_label("Notes (optionnel)"), row_r, 1)
        row_r += 1
        self.inp_notes = QTextEdit()
        self.inp_notes.setPlainText("Cabinet spécialisé en ophtalmologie ouvert depuis 2020.")
        self.inp_notes.setFixedHeight(52)
        self.inp_notes.setStyleSheet(self._css_input())
        grid.addWidget(self.inp_notes, row_r, 1)
        row_r += 1
        
        form_layout.addLayout(grid)
        form_layout.addSpacing(6)
        
        # Boutons Annuler / Enregistrer
        form_layout.addLayout(self._creer_boutons_action())
        
        # Connecter les boutons APRÈS leur création
        self.btn_annuler.clicked.connect(self._annuler)
        self.btn_enregistrer.clicked.connect(self._enregistrer)
        
        return form_widget
    
    def _creer_boutons_action(self) -> QHBoxLayout:
        """Crée les boutons Annuler et Enregistrer."""
        c = theme_manager.colors()
        layout = QHBoxLayout()
        layout.addStretch()
        
        # Bouton Annuler
        self.btn_annuler = QPushButton()
        self.btn_annuler.setCursor(Qt.PointingHandCursor)
        self.btn_annuler.setFixedHeight(32)
        self.btn_annuler.setIcon(qta.icon("fa5s.times", color=c['text_primary']))
        self.btn_annuler.setIconSize(QSize(12, 12))
        self.btn_annuler.setText("Annuler")
        self.btn_annuler.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
            }}
        """)
        
        # Bouton Enregistrer
        self.btn_enregistrer = QPushButton()
        self.btn_enregistrer.setCursor(Qt.PointingHandCursor)
        self.btn_enregistrer.setFixedHeight(32)
        self.btn_enregistrer.setIcon(qta.icon("fa5s.save", color=c['text_inverse']))
        self.btn_enregistrer.setIconSize(QSize(12, 12))
        self.btn_enregistrer.setText("Enregistrer")
        self.btn_enregistrer.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 10px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        
        layout.addWidget(self.btn_annuler)
        layout.addSpacing(10)
        layout.addWidget(self.btn_enregistrer)
        return layout
    
    def _creer_apercu_panel(self) -> QFrame:
        """Crée le panel d'aperçu à droite."""
        c = theme_manager.colors()
        
        frame = QFrame()
        frame.setMinimumWidth(240)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 16px;
                border: 1px solid {c['border']};
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 25))
        frame.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        
        # Titre
        lbl_apercu = QLabel("Aperçu")
        lbl_apercu.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 15px; font-weight: 700; border: none;"
        )
        layout.addWidget(lbl_apercu)
        
        # Logo preview (conteneur dynamique)
        self.logo_preview_frame = QFrame()
        self.logo_preview_frame.setFixedHeight(85)
        self.logo_preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid {c['border']};
            }}
        """)
        self.logo_preview_layout = QVBoxLayout(self.logo_preview_frame)
        self.logo_preview_layout.setAlignment(Qt.AlignCenter)
        self.logo_preview_layout.setSpacing(3)
        
        layout.addWidget(self.logo_preview_frame)
        
        # Séparateur
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['border']}; border: none;")
        layout.addWidget(sep)
        
        # Conteneur pour les champs d'aperçu (pour mise à jour dynamique)
        self.apercu_container = QWidget()
        self.apercu_container.setStyleSheet("background-color: transparent;")
        self.apercu_layout = QVBoxLayout(self.apercu_container)
        self.apercu_layout.setContentsMargins(0, 0, 0, 0)
        self.apercu_layout.setSpacing(8)
        
        layout.addWidget(self.apercu_container)
        
        # Initialiser les champs d'aperçu
        self._mettre_a_jour_apercu()
        
        layout.addSpacing(4)
        
        # Bouton Modifier
        self.btn_modifier_apercu = QPushButton()
        self.btn_modifier_apercu.setCursor(Qt.PointingHandCursor)
        self.btn_modifier_apercu.setFixedHeight(36)
        self.btn_modifier_apercu.setIcon(qta.icon("fa5s.pen", color=c['primary']))
        self.btn_modifier_apercu.setIconSize(QSize(11, 11))
        self.btn_modifier_apercu.setText("Modifier")
        self.btn_modifier_apercu.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {c['primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
            }}
        """)
        layout.addWidget(self.btn_modifier_apercu)
        
        return frame
    
    def _mettre_a_jour_apercu(self):
        """Met à jour le panel d'aperçu avec les données actuelles."""
        c = theme_manager.colors()
        
        # Récupérer les données depuis la base
        info = self.controller.obtenir_informations_cabinet()
        
        # Mettre à jour le logo et le nom
        self._mettre_a_jour_logo_preview(info)
        
        # Vider le conteneur des informations
        while self.apercu_layout.count():
            child = self.apercu_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if info:
            apercu_data = [
                ("Nom", info.get('nom_cabinet', 'N/A')),
                ("Téléphone", info.get('telephone', 'N/A')),
                ("Email", info.get('email', 'N/A')),
                ("Devise", info.get('devise', 'N/A')),
                ("Fuseau horaire", info.get('fuseau_horaire', 'N/A').replace('(GMT) ', '')),
                ("Format date", info.get('format_date', 'N/A')),
                ("Format heure", info.get('format_heure', 'N/A')),
            ]
        else:
            apercu_data = [
                ("Nom", "Aucune donnée"),
                ("Téléphone", "N/A"),
                ("Email", "N/A"),
                ("Devise", "N/A"),
                ("Fuseau horaire", "N/A"),
                ("Format date", "N/A"),
                ("Format heure", "N/A"),
            ]
        
        for cle, val in apercu_data:
            row_w = QWidget()
            row_w.setStyleSheet("background-color: #FFFFFF;")
            row_l = QVBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(1)
            
            lbl_cle = QLabel(cle)
            lbl_cle.setStyleSheet(
                f"color: {c['text_muted']}; font-size: 11px; font-weight: 600; border: none;"
            )
            
            lbl_val = QLabel(val)
            lbl_val.setWordWrap(True)
            lbl_val.setStyleSheet(
                f"color: {c['text_primary']}; font-size: 12px; border: none;"
            )
            
            row_l.addWidget(lbl_cle)
            row_l.addWidget(lbl_val)
            self.apercu_layout.addWidget(row_w)
    
    def _mettre_a_jour_logo_preview(self, info):
        """Met à jour le logo et le nom dans le preview."""
        from PySide6.QtGui import QPixmap
        import os
        c = theme_manager.colors()
        
        # Vider le layout du logo
        while self.logo_preview_layout.count():
            child = self.logo_preview_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if info:
            nom_cabinet = info.get('nom_cabinet', 'Cabinet')
            logo_filename = info.get('logo', '')
            
            print(f"[DEBUG] Nom cabinet: {nom_cabinet}")
            print(f"[DEBUG] Logo filename: {logo_filename}")
            
            # Afficher le logo si disponible
            if logo_filename:
                # Construire le chemin du logo - plusieurs tentatives
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
                # Tentative 1: connexion/image/
                logo_path1 = os.path.join(script_dir, 'connexion', 'image', logo_filename)
                # Tentative 2: projetSoutenance/connexion/image/
                logo_path2 = os.path.join(os.path.dirname(script_dir), 'connexion', 'image', logo_filename)
                # Tentative 3: chemin absolu si le logo_filename contient déjà un chemin
                logo_path3 = logo_filename if os.path.isabs(logo_filename) else None
                
                print(f"[DEBUG] Script dir: {script_dir}")
                print(f"[DEBUG] Tentative 1: {logo_path1}")
                print(f"[DEBUG] Existe 1: {os.path.exists(logo_path1)}")
                print(f"[DEBUG] Tentative 2: {logo_path2}")
                print(f"[DEBUG] Existe 2: {os.path.exists(logo_path2)}")
                if logo_path3:
                    print(f"[DEBUG] Tentative 3: {logo_path3}")
                    print(f"[DEBUG] Existe 3: {os.path.exists(logo_path3)}")
                
                # Essayer les différents chemins
                logo_path = None
                if os.path.exists(logo_path1):
                    logo_path = logo_path1
                elif os.path.exists(logo_path2):
                    logo_path = logo_path2
                elif logo_path3 and os.path.exists(logo_path3):
                    logo_path = logo_path3
                
                if logo_path:
                    print(f"[DEBUG] Logo trouvé: {logo_path}")
                    lbl_logo = QLabel()
                    pixmap = QPixmap(logo_path)
                    print(f"[DEBUG] Pixmap null: {pixmap.isNull()}")
                    print(f"[DEBUG] Pixmap size: {pixmap.size()}")
                    
                    if not pixmap.isNull():
                        # Redimensionner le logo
                        scaled_pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        lbl_logo.setPixmap(scaled_pixmap)
                        lbl_logo.setAlignment(Qt.AlignCenter)
                        lbl_logo.setStyleSheet("border: none; background: transparent;")
                        self.logo_preview_layout.addWidget(lbl_logo)
                        print(f"[DEBUG] Logo affiché avec succès")
                    else:
                        print(f"[DEBUG] Pixmap null, affichage logo par défaut")
                        self._afficher_logo_defaut()
                else:
                    print(f"[DEBUG] Aucun chemin valide trouvé, affichage logo par défaut")
                    self._afficher_logo_defaut()
            else:
                print(f"[DEBUG] Pas de logo filename, affichage logo par défaut")
                self._afficher_logo_defaut()
            
            # Afficher le nom du cabinet
            # Extraire les mots principaux du nom (max 2 lignes)
            mots = nom_cabinet.split()
            if len(mots) > 2:
                ligne1 = ' '.join(mots[:2])
                ligne2 = ' '.join(mots[2:4]) if len(mots) > 2 else ''
            else:
                ligne1 = nom_cabinet
                ligne2 = ''
            
            lbl_nom1 = QLabel(ligne1.upper())
            lbl_nom1.setAlignment(Qt.AlignCenter)
            lbl_nom1.setStyleSheet(
                f"color: {c['primary']}; font-size: 11px; font-weight: 800; "
                "border: none; background: transparent;"
            )
            self.logo_preview_layout.addWidget(lbl_nom1)
            
            if ligne2:
                lbl_nom2 = QLabel(ligne2.upper())
                lbl_nom2.setAlignment(Qt.AlignCenter)
                lbl_nom2.setStyleSheet(
                    f"color: {c['text_muted']}; font-size: 9px; "
                    "border: none; background: transparent;"
                )
                self.logo_preview_layout.addWidget(lbl_nom2)
        else:
            print(f"[DEBUG] Aucune info disponible")
            # Aucune donnée, afficher le logo par défaut
            self._afficher_logo_defaut()
            lbl_nom = QLabel("AUCUNE DONNÉE")
            lbl_nom.setAlignment(Qt.AlignCenter)
            lbl_nom.setStyleSheet(
                f"color: {c['text_muted']}; font-size: 11px; font-weight: 800; "
                "border: none; background: transparent;"
            )
            self.logo_preview_layout.addWidget(lbl_nom)
    
    def _afficher_logo_defaut(self):
        """Affiche l'icône par défaut (oeil)."""
        c = theme_manager.colors()
        lbl_eye = QLabel()
        lbl_eye.setPixmap(qta.icon("fa5s.eye", color=c['primary']).pixmap(QSize(28, 28)))
        lbl_eye.setAlignment(Qt.AlignCenter)
        lbl_eye.setStyleSheet("border: none; background: transparent;")
        self.logo_preview_layout.addWidget(lbl_eye)
    
    def _creer_logo_widget(self) -> QWidget:
        """Crée le widget de sélection de logo."""
        c = theme_manager.colors()
        
        w = QWidget()
        w.setStyleSheet("background-color: #FFFFFF;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        
        # Preview
        preview = QFrame()
        preview.setFixedSize(80, 68)
        preview.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid {c['border']};
            }}
        """)
        pl = QVBoxLayout(preview)
        pl.setAlignment(Qt.AlignCenter)
        pl.setSpacing(2)
        
        lbl_eye2 = QLabel()
        lbl_eye2.setPixmap(qta.icon("fa5s.eye", color=c['primary']).pixmap(QSize(22, 22)))
        lbl_eye2.setAlignment(Qt.AlignCenter)
        lbl_eye2.setStyleSheet("border: none; background: transparent;")
        
        lbl_vp2 = QLabel("VISION PLUS")
        lbl_vp2.setAlignment(Qt.AlignCenter)
        lbl_vp2.setStyleSheet(
            f"color: {c['primary']}; font-size: 6px; font-weight: 700; "
            "border: none; background: transparent;"
        )
        
        pl.addWidget(lbl_eye2)
        pl.addWidget(lbl_vp2)
        
        # Droite
        right = QWidget()
        right.setStyleSheet("background-color: #FFFFFF;")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(5)
        
        self.btn_changer_logo = QPushButton()
        self.btn_changer_logo.setCursor(Qt.PointingHandCursor)
        self.btn_changer_logo.setFixedHeight(30)
        self.btn_changer_logo.setIcon(qta.icon("fa5s.upload", color=c['primary']))
        self.btn_changer_logo.setIconSize(QSize(11, 11))
        self.btn_changer_logo.setText("Changer le logo")
        self.btn_changer_logo.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {c['primary']};
                border: 1px solid {c['primary']};
                border-radius: 7px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
            }}
        """)
        self.btn_changer_logo.clicked.connect(self._choisir_logo)
        
        lbl_fmt = QLabel("Formats acceptés : PNG, JPG")
        lbl_fmt.setStyleSheet(f"color: {c['text_muted']}; font-size: 10px; border: none;")
        lbl_size = QLabel("Taille max : 2 Mo")
        lbl_size.setStyleSheet(f"color: {c['text_muted']}; font-size: 10px; border: none;")
        
        rl.addWidget(self.btn_changer_logo)
        rl.addWidget(lbl_fmt)
        rl.addWidget(lbl_size)
        
        layout.addWidget(preview)
        layout.addWidget(right)
        layout.addStretch()
        return w
    
    def _choisir_logo(self):
        """Ouvre un sélecteur de fichier pour changer le logo."""
        fichier, _ = QFileDialog.getOpenFileName(
            self, "Choisir un logo", "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if fichier:
            self.chemin_logo_selectionne = fichier
            print(f"[SettingsForm] Logo sélectionné : {fichier}")
            # TODO: Afficher un aperçu du logo sélectionné
    
    def _charger_donnees(self):
        """Charge les données depuis la base de données."""
        try:
            info = self.controller.obtenir_informations_cabinet()
            if info:
                # Remplir les champs
                self.inp_nom.setText(info.get('nom_cabinet', ''))
                self.inp_email.setText(info.get('email', ''))
                self.inp_tel.setText(info.get('telephone', ''))
                self.inp_adresse.setPlainText(info.get('adresse', ''))
                self.inp_notes.setPlainText(info.get('notes', ''))
                
                # Sélectionner la devise
                devise = info.get('devise', 'GNF - Franc guinéen (GNF)')
                index = self.cb_devise.findText(devise)
                if index >= 0:
                    self.cb_devise.setCurrentIndex(index)
                
                # Sélectionner le fuseau horaire
                fuseau = info.get('fuseau_horaire', '(GMT) Afrique/Conakry')
                index = self.cb_fuseau.findText(fuseau)
                if index >= 0:
                    self.cb_fuseau.setCurrentIndex(index)
                
                # Sélectionner le format de date
                format_date = info.get('format_date', 'DD/MM/YYYY')
                index = self.cb_date_fmt.findText(format_date)
                if index >= 0:
                    self.cb_date_fmt.setCurrentIndex(index)
                
                # Sélectionner le format d'heure
                format_heure = info.get('format_heure', '24 heures (HH:mm)')
                index = self.cb_heure_fmt.findText(format_heure)
                if index >= 0:
                    self.cb_heure_fmt.setCurrentIndex(index)
                
                # Date de création
                date_creation = info.get('date_creation')
                if date_creation:
                    from datetime import datetime
                    if isinstance(date_creation, str):
                        date_obj = datetime.strptime(date_creation, '%Y-%m-%d')
                        self.date_creation.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
                    else:
                        self.date_creation.setDate(QDate(date_creation.year, date_creation.month, date_creation.day))
                
                # Mettre à jour l'aperçu
                self._mettre_a_jour_apercu()
                
                print("[SettingsForm] Données chargées avec succès")
            else:
                print("[SettingsForm] Aucune donnée trouvée")
        except Exception as e:
            print(f"[SettingsForm] Erreur chargement : {e}")
            import traceback
            traceback.print_exc()
    
    def _annuler(self):
        """Annule les modifications et recharge les données."""
        reponse = QMessageBox.question(
            self,
            "Annuler les modifications",
            "Voulez-vous vraiment annuler les modifications ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reponse == QMessageBox.Yes:
            self._charger_donnees()
            self.chemin_logo_selectionne = None
            print("[SettingsForm] Modifications annulées")
    
    def _enregistrer(self):
        """Enregistre les paramètres dans la base de données."""
        try:
            # Récupérer les valeurs
            nom_cabinet = self.inp_nom.text().strip()
            email = self.inp_email.text().strip()
            telephone = self.inp_tel.text().strip()
            adresse = self.inp_adresse.toPlainText().strip()
            devise = self.cb_devise.currentText()
            fuseau_horaire = self.cb_fuseau.currentText()
            format_date = self.cb_date_fmt.currentText()
            format_heure = self.cb_heure_fmt.currentText()
            notes = self.inp_notes.toPlainText().strip()
            date_creation_qdate = self.date_creation.date()
            date_creation_str = date_creation_qdate.toString("yyyy-MM-dd")
            
            # Validation basique
            if not nom_cabinet:
                QMessageBox.warning(self, "Erreur", "Le nom du cabinet est obligatoire")
                return
            
            if not adresse:
                QMessageBox.warning(self, "Erreur", "L'adresse est obligatoire")
                return
            
            # Appeler le contrôleur
            result = self.controller.enregistrer_informations_cabinet(
                nom_cabinet=nom_cabinet,
                chemin_logo=self.chemin_logo_selectionne,
                adresse=adresse,
                email=email,
                telephone=telephone,
                devise=devise,
                fuseau_horaire=fuseau_horaire,
                format_date=format_date,
                format_heure=format_heure,
                notes=notes,
                date_creation=date_creation_str
            )
            
            if result['status'] == 'success':
                QMessageBox.information(self, "Succès", result['message'])
                self.chemin_logo_selectionne = None
                self._charger_donnees()
                self._mettre_a_jour_apercu()
                self.donnees_sauvegardees.emit()
            else:
                QMessageBox.critical(self, "Erreur", result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {e}")
            print(f"[SettingsForm] Erreur enregistrement : {e}")
            import traceback
            traceback.print_exc()
    
    # ── HELPERS CSS / WIDGETS ─────────────────────────────────────────────────
    
    def _mk_label(self, texte: str) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel(texte)
        lbl.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 11px; font-weight: 600; border: none;"
        )
        return lbl
    
    def _mk_input(self, valeur: str = "") -> QLineEdit:
        inp = QLineEdit(valeur)
        inp.setFixedHeight(28)
        inp.setStyleSheet(self._css_input())
        return inp
    
    def _mk_combo(self, options: list) -> QComboBox:
        c = theme_manager.colors()
        cb = QComboBox()
        cb.addItems(options)
        cb.setFixedHeight(28)
        cb.setStyleSheet(f"""
            QComboBox {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 26px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }}
            QComboBox QAbstractItemView {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                outline: none;
                selection-background-color: {c['primary']};
                selection-color: {c['text_inverse']};
                padding: 4px;
            }}
        """)
        return cb
    
    def _creer_date_input(self) -> QDateEdit:
        """Crée un champ de date avec calendrier."""
        c = theme_manager.colors()
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        date_edit.setDisplayFormat("dd/MM/yyyy")
        date_edit.setFixedHeight(28)
        date_edit.setStyleSheet(f"""
            QDateEdit {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 12px;
            }}
            QDateEdit:focus {{
                border: 1.5px solid {c['primary']};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 26px;
            }}
        """)
        return date_edit
    
    def _css_input(self) -> str:
        c = theme_manager.colors()
        return f"""
            QLineEdit, QTextEdit {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1.5px solid {c['primary']};
            }}
        """
    
    def apply_theme(self):
        """Ré-applique les couleurs sur tous les composants."""
        c = theme_manager.colors()
        
        # Inputs
        for inp in self.findChildren(QLineEdit):
            inp.setStyleSheet(self._css_input())
        for ta in self.findChildren(QTextEdit):
            ta.setStyleSheet(self._css_input())
        
        # Combos
        for cb in self.findChildren(QComboBox):
            cb.setStyleSheet(f"""
                QComboBox {{
                    background-color: #FFFFFF;
                    color: {c['text_primary']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                    padding: 0 12px;
                    font-size: 12px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: #ffffff;
                    color: {c['text_primary']};
                    border: 1px solid {c['border']};
                    selection-background-color: {c['primary']};
                    selection-color: {c['text_inverse']};
                }}
            """)
