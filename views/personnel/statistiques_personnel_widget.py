from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import qtawesome as qta


class StatistiquesPersonnelWidget(QWidget):
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 10)
        layout.setSpacing(8)
        
        # En-tête
        header = self._create_header()
        layout.addWidget(header)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # KPI Cards
        kpi_section = self._create_kpi_section()
        content_layout.addWidget(kpi_section)
        
        # Responsables
        responsables_section = self._create_responsables_section()
        content_layout.addWidget(responsables_section)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
    
    def _create_header(self):
        frame = QFrame()
        frame.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Titre supprimé
        
        return frame
    
    def _create_kpi_section(self):
        frame = QFrame()
        frame.setStyleSheet("background: transparent;")
        self.kpi_layout = QHBoxLayout(frame)
        self.kpi_layout.setSpacing(10)
        self.kpi_layout.setContentsMargins(0, 0, 0, 0)
        
        return frame
    
    def _create_kpi_card(self, nom, nombre, pct, couleur, icon_name):
        card = QFrame()
        card.setMinimumWidth(160)
        card.setFixedHeight(85)
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Icône + Nom
        top = QHBoxLayout()
        top.setSpacing(6)
        icon_label = QLabel()
        icon = qta.icon(icon_name, color=couleur)
        icon_label.setPixmap(icon.pixmap(16, 16))
        top.addWidget(icon_label)
        
        nom_label = QLabel(nom)
        nom_label.setStyleSheet("font-size: 9px; color: #6B7280; font-weight: 500;")
        top.addWidget(nom_label)
        top.addStretch()
        layout.addLayout(top)
        
        # Nombre
        nombre_label = QLabel(nombre)
        nombre_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1F2937;")
        layout.addWidget(nombre_label)
        
        # Pourcentage
        pct_label = QLabel(pct)
        pct_label.setStyleSheet("font-size: 8px; color: #9CA3AF;")
        layout.addWidget(pct_label)
        
        layout.addStretch()
        
        # Barre
        barre = QFrame()
        barre.setFixedHeight(4)
        barre.setStyleSheet(f"background: {couleur}; border-radius: 2px;")
        layout.addWidget(barre)
        
        return card
    
    def _create_total_card(self):
        card = QFrame()
        card.setMinimumWidth(160)
        card.setFixedHeight(85)
        card.setStyleSheet("""
            QFrame {
                background: #F0F9FF;
                border: 2px solid #3B82F6;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)
        
        titre = QLabel("Total du personnel")
        titre.setStyleSheet("font-size: 8px; color: #6B7280; font-weight: 500;")
        layout.addWidget(titre)
        
        nombre = QLabel("31")
        nombre.setStyleSheet("font-size: 26px; font-weight: bold; color: #3B82F6;")
        layout.addWidget(nombre)
        
        pct = QLabel("100%")
        pct.setStyleSheet("font-size: 10px; color: #3B82F6; font-weight: 600;")
        layout.addWidget(pct)
        
        effectifs = QLabel("Effectifs totaux")
        effectifs.setStyleSheet("font-size: 8px; color: #9CA3AF;")
        layout.addWidget(effectifs)
        
        icon_label = QLabel()
        icon = qta.icon('fa5s.users', color='#3B82F6')
        icon_label.setPixmap(icon.pixmap(14, 14))
        icon_label.setAlignment(Qt.AlignRight)
        layout.addWidget(icon_label)
        
        return card
    
    def _create_responsables_section(self):
        frame = QFrame()
        frame.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        
        titre = QLabel("Responsables par service / fonction")
        titre.setStyleSheet("font-size: 14px; font-weight: bold; color: #1F2937;")
        layout.addWidget(titre)
        
        # Grid 3 colonnes
        self.responsables_grid = QGridLayout()
        self.responsables_grid.setSpacing(12)
        layout.addLayout(self.responsables_grid)
        
        return frame
    
    def _create_resp_medecins(self):
        return self._create_resp_card(
            "Médecins", "12 employés", "#3B82F6", "fa5s.user-md",
            "Dr. Moussa Diallo", "Responsable des Médecins",
            "m.diallo@visioncare.com", "+221 77 123 45 67",
            "15 Mars 2018", "Almadies, Dakar - Sénégal", None
        )
    
    def _create_resp_laborantins(self):
        return self._create_resp_card(
            "Laborantins", "8 employés", "#10B981", "fa5s.flask",
            "Dr. Awa Ndiaye", "Responsable des Laborantins",
            "a.ndiaye@visioncare.com", "+221 76 234 56 78",
            "10 Juin 2019", "Point E, Dakar - Sénégal", None
        )
    
    def _create_resp_chirurgiens(self):
        return self._create_resp_card(
            "Chirurgiens", "6 employés", "#F97316", "fa5s.cut",
            "Dr. Binta Fall", "Responsable des Chirurgiens",
            "b.fall@visioncare.com", "+221 78 345 67 89",
            "5 Janvier 2020", "Almadies, Dakar - Sénégal", None
        )
    
    def _create_resp_comptables(self):
        return self._create_resp_card(
            "Comptables", "4 employés", "#8B5CF6", "fa5s.calculator",
            "Mme. Fatou Diop", "Responsable de la Comptabilité",
            "f.diop@visioncare.com", "+221 70 456 78 90",
            "12 Septembre 2019", "Point E, Dakar - Sénégal", None
        )
    
    def _create_resp_directeur(self):
        return self._create_resp_card(
            "Directeur Général", "1 employé", "#EC4899", "fa5s.user-tie",
            "Dr. Moussa Diallo", "Directeur Général",
            "m.diallo@visioncare.com", "+221 77 123 45 67",
            "15 Mars 2018", "Almadies, Dakar - Sénégal", None
        )
    
    def _create_resp_card(self, fonction, nb_emp, couleur, icon_name, nom, titre, email, tel, date, lieu, photo_path):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        icon_label = QLabel()
        icon = qta.icon(icon_name, color=couleur)
        icon_label.setPixmap(icon.pixmap(22, 22))
        header.addWidget(icon_label)
        
        fonction_label = QLabel(fonction)
        fonction_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #1F2937;")
        header.addWidget(fonction_label)
        header.addStretch()
        
        nb_label = QLabel(nb_emp)
        nb_label.setStyleSheet(f"font-size: 11px; color: {couleur}; font-weight: 600;")
        header.addWidget(nb_label)
        layout.addLayout(header)
        
        # Ligne
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background: #E5E7EB;")
        layout.addWidget(line)
        
        # Contenu
        content = QHBoxLayout()
        content.setSpacing(12)
        
        # Photo
        photo = QLabel()
        photo.setFixedSize(70, 70)
        
        # Charger la photo si disponible
        photo_loaded = False
        if photo_path:
            import os
            from PySide6.QtGui import QPixmap, QPainter, QPainterPath
            
            script_dir = os.path.dirname(__file__)
            full_photo_path = os.path.normpath(
                os.path.join(script_dir, "..", "..", "connexion", "image", photo_path)
            )
            
            print(f"Tentative de chargement photo: {photo_path}")
            print(f"Chemin complet: {full_photo_path}")
            print(f"Existe: {os.path.exists(full_photo_path)}")
            
            if os.path.exists(full_photo_path):
                pixmap = QPixmap(full_photo_path)
                if not pixmap.isNull():
                    # Redimensionner
                    scaled_pixmap = pixmap.scaled(70, 70, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    
                    # Créer un pixmap circulaire
                    target = QPixmap(70, 70)
                    target.fill(Qt.transparent)
                    
                    painter = QPainter(target)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setRenderHint(QPainter.SmoothPixmapTransform)
                    
                    path = QPainterPath()
                    path.addEllipse(0, 0, 70, 70)
                    painter.setClipPath(path)
                    
                    x = (70 - scaled_pixmap.width()) // 2
                    y = (70 - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x, y, scaled_pixmap)
                    painter.end()
                    
                    photo.setPixmap(target)
                    photo.setStyleSheet("border-radius: 35px; border: 2px solid white;")
                    photo_loaded = True
                    print("Photo chargée avec succès!")
        
        # Si pas de photo, afficher le fond coloré
        if not photo_loaded:
            photo.setStyleSheet(f"""
                QLabel {{
                    background: {couleur};
                    border-radius: 35px;
                    border: 2px solid white;
                }}
            """)
            print(f"Pas de photo, affichage fond {couleur}")
        
        content.addWidget(photo)
        
        # Infos
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        nom_label = QLabel(nom)
        nom_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #1F2937;")
        info_layout.addWidget(nom_label)
        
        titre_label = QLabel(titre)
        titre_label.setStyleSheet("font-size: 10px; color: #6B7280;")
        info_layout.addWidget(titre_label)
        
        info_layout.addSpacing(3)
        
        self._add_info_line(info_layout, "fa5s.envelope", email)
        self._add_info_line(info_layout, "fa5s.phone", tel)
        self._add_info_line(info_layout, "fa5s.calendar", date)
        self._add_info_line(info_layout, "fa5s.map-marker-alt", lieu)
        
        info_layout.addStretch()
        content.addLayout(info_layout)
        
        layout.addLayout(content)
        
        return card
    
    def _add_info_line(self, parent_layout, icon_name, text):
        row = QHBoxLayout()
        row.setSpacing(6)
        
        icon_label = QLabel()
        icon = qta.icon(icon_name, color='#9CA3AF')
        icon_label.setPixmap(icon.pixmap(10, 10))
        row.addWidget(icon_label)
        
        text_label = QLabel(text)
        text_label.setStyleSheet("font-size: 9px; color: #6B7280;")
        row.addWidget(text_label)
        row.addStretch()
        
        parent_layout.addLayout(row)
    
    def _create_info_generales(self):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        icon_label = QLabel()
        icon = qta.icon('fa5s.info-circle', color='#3B82F6')
        icon_label.setPixmap(icon.pixmap(22, 22))
        header.addWidget(icon_label)
        
        titre = QLabel("Informations générales")
        titre.setStyleSheet("font-size: 13px; font-weight: bold; color: #1F2937;")
        header.addWidget(titre)
        header.addStretch()
        layout.addLayout(header)
        
        # Ligne
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background: #E5E7EB;")
        layout.addWidget(line)
        
        # Infos
        self._add_stat_row(layout, "fa5s.users", "Total du personnel", "31")
        self._add_stat_row(layout, "fa5s.birthday-cake", "Âge moyen", "36 ans")
        self._add_stat_row(layout, "fa5s.clock", "Ancienneté moyenne", "4.6 ans")
        self._add_stat_row(layout, "fa5s.sync", "Date de mise à jour", "23 Mai 2024 à 10:30")
        
        layout.addStretch()
        
        return card
    
    def _add_stat_row(self, parent_layout, icon_name, label, value):
        row = QHBoxLayout()
        row.setSpacing(8)
        
        icon_label = QLabel()
        icon = qta.icon(icon_name, color='#6B7280')
        icon_label.setPixmap(icon.pixmap(12, 12))
        row.addWidget(icon_label)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 10px; color: #6B7280;")
        row.addWidget(label_widget)
        row.addStretch()
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet("font-size: 11px; font-weight: bold; color: #1F2937;")
        row.addWidget(value_widget)
        
        parent_layout.addLayout(row)
    
    def charger_donnees(self):
        """Charge les données réelles depuis la base de données"""
        # Récupérer les statistiques par fonction
        stats_par_fonction = self.ctrl.compter_par_fonction()
        
        # Fonctions prédéfinies (ordre d'affichage)
        fonctions_predefinies = [
            ("Médecin", "#3B82F6", "fa5s.user-md"),
            ("Laborantin", "#10B981", "fa5s.flask"),
            ("Chirurgien", "#F97316", "fa5s.cut"),
            ("Comptable", "#8B5CF6", "fa5s.calculator"),
            ("Directeur Général", "#EC4899", "fa5s.user-tie"),
        ]
        
        # Calculer le total et les "Autres"
        total = sum(stats_par_fonction.values())
        fonctions_connues = [f[0] for f in fonctions_predefinies]
        autres = sum(nb for fonction, nb in stats_par_fonction.items() if fonction not in fonctions_connues)
        
        # Nettoyer les anciennes KPI cards
        while self.kpi_layout.count() > 0:
            item = self.kpi_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Créer les KPI cards pour les fonctions prédéfinies
        for fonction, couleur, icon in fonctions_predefinies:
            nombre = stats_par_fonction.get(fonction, 0)
            pourcentage = (nombre / total * 100) if total > 0 else 0
            pct_text = f"{pourcentage:.1f}% du personnel"
            card = self._create_kpi_card(fonction, str(nombre), pct_text, couleur, icon)
            self.kpi_layout.addWidget(card)
        
        # Card "Autres" si nécessaire
        if autres > 0:
            pourcentage_autres = (autres / total * 100) if total > 0 else 0
            pct_text = f"{pourcentage_autres:.1f}% du personnel"
            card_autres = self._create_kpi_card("Autres", str(autres), pct_text, "#6B7280", "fa5s.users")
            self.kpi_layout.addWidget(card_autres)
        
        # Card Total
        total_card = self._create_total_card_dynamic(total)
        self.kpi_layout.addWidget(total_card)
        
        # Nettoyer la grid des responsables
        while self.responsables_grid.count() > 0:
            item = self.responsables_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Créer les cards de responsables pour les fonctions prédéfinies
        row, col = 0, 0
        for fonction, couleur, icon in fonctions_predefinies:
            nombre = stats_par_fonction.get(fonction, 0)
            responsable = self.ctrl.get_responsable(fonction)
            
            if responsable:
                nom = f"{responsable.get('prenom', '')} {responsable.get('nom', '')}".strip()
                titre = f"Responsable des {fonction}s" if not fonction.endswith('Général') else fonction
                email = responsable.get('mail', '')
                tel = responsable.get('contact', '')
                date = str(responsable.get('date_naissance', ''))
                lieu = responsable.get('adresse', '')
                photo = responsable.get('photo_path')
            else:
                nom = "Non assigné"
                titre = f"Responsable des {fonction}s" if not fonction.endswith('Général') else fonction
                email = tel = date = lieu = ""
                photo = None
            
            nb_emp = f"{nombre} employé{'s' if nombre > 1 else ''}"
            card = self._create_resp_card(fonction, nb_emp, couleur, icon, nom, titre, email, tel, date, lieu, photo)
            self.responsables_grid.addWidget(card, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        # Card "Autres" dans les responsables si nécessaire
        if autres > 0:
            nb_emp = f"{autres} employé{'s' if autres > 1 else ''}"
            card_autres = self._create_resp_card(
                "Autres", nb_emp, "#6B7280", "fa5s.users",
                "Personnel divers", "Autres fonctions",
                "", "", "", "", None
            )
            self.responsables_grid.addWidget(card_autres, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        # Ajouter la card Informations générales
        age_moyen = self._calculer_age_moyen()
        anciennete_moyenne = self._calculer_anciennete_moyenne()
        info_card = self._create_info_generales_dynamic(total, age_moyen, anciennete_moyenne)
        self.responsables_grid.addWidget(info_card, row, col)
    
    def _create_total_card_dynamic(self, total):
        """Crée la card total avec le nombre réel"""
        card = QFrame()
        card.setMinimumWidth(160)
        card.setFixedHeight(85)
        card.setStyleSheet("""
            QFrame {
                background: #F0F9FF;
                border: 2px solid #3B82F6;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)
        
        titre = QLabel("Total du personnel")
        titre.setStyleSheet("font-size: 8px; color: #6B7280; font-weight: 500;")
        layout.addWidget(titre)
        
        nombre = QLabel(str(total))
        nombre.setStyleSheet("font-size: 26px; font-weight: bold; color: #3B82F6;")
        layout.addWidget(nombre)
        
        pct = QLabel("100%")
        pct.setStyleSheet("font-size: 10px; color: #3B82F6; font-weight: 600;")
        layout.addWidget(pct)
        
        effectifs = QLabel("Effectifs totaux")
        effectifs.setStyleSheet("font-size: 8px; color: #9CA3AF;")
        layout.addWidget(effectifs)
        
        icon_label = QLabel()
        icon = qta.icon('fa5s.users', color='#3B82F6')
        icon_label.setPixmap(icon.pixmap(14, 14))
        icon_label.setAlignment(Qt.AlignRight)
        layout.addWidget(icon_label)
        
        return card
    
    def _create_info_generales_dynamic(self, total, age_moyen, anciennete_moyenne):
        """Crée la card info générales avec les données réelles"""
        from datetime import datetime
        
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        icon_label = QLabel()
        icon = qta.icon('fa5s.info-circle', color='#3B82F6')
        icon_label.setPixmap(icon.pixmap(22, 22))
        header.addWidget(icon_label)
        
        titre = QLabel("Informations générales")
        titre.setStyleSheet("font-size: 13px; font-weight: bold; color: #1F2937;")
        header.addWidget(titre)
        header.addStretch()
        layout.addLayout(header)
        
        # Ligne
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background: #E5E7EB;")
        layout.addWidget(line)
        
        # Infos
        self._add_stat_row(layout, "fa5s.users", "Total du personnel", str(total))
        self._add_stat_row(layout, "fa5s.birthday-cake", "Âge moyen", f"{age_moyen:.0f} ans")
        self._add_stat_row(layout, "fa5s.clock", "Ancienneté moyenne", f"{anciennete_moyenne:.1f} ans")
        
        now = datetime.now().strftime("%d %B %Y à %H:%M")
        self._add_stat_row(layout, "fa5s.sync", "Date de mise à jour", now)
        
        layout.addStretch()
        
        return card
    
    def _calculer_age_moyen(self):
        """Calcule l'âge moyen des personnels"""
        from datetime import datetime
        personnels = self.ctrl.lister_tout()
        ages = []
        for p in personnels:
            date_naissance = p.get('date_naissance')
            if date_naissance:
                try:
                    if isinstance(date_naissance, str):
                        naissance = datetime.strptime(date_naissance, "%Y-%m-%d")
                    else:
                        naissance = date_naissance
                    age = (datetime.now() - naissance).days / 365.25
                    ages.append(age)
                except:
                    pass
        return sum(ages) / len(ages) if ages else 0
    
    def _calculer_anciennete_moyenne(self):
        """Calcule l'ancienneté moyenne (pour l'instant valeur fixe)"""
        # À améliorer si vous avez une date d'embauche dans la base
        return 4.6
