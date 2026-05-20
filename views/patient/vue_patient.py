from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QHeaderView, QTableWidgetItem, QFrame,QLayout) # QFrame ajouté ici
from PySide6.QtCore import Qt
import qtawesome as qta
from views.shared.stat_card import StatCard
from views.shared.graph_factory import PatientGraphs
from controllers.controleur_patient import ControleurPatient
from PySide6.QtWidgets import QMenu # Ajoute QMenu aux imports en haut
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFileDialog, QMessageBox)
from views.shared.message_box import CustomMessageBox, PatientDetailDialog 
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import QPropertyAnimation, QPoint, QEasingCurve
from .patient_form import PatientFormDialog

from controllers.controleur_visite import VisiteControleur # Import du contrôleur visite
from views.shared.theme_manager import theme_manager
from views.patient.styles import PatientStyles

class PatientView(QWidget):
    def __init__(self):
        super().__init__()
        self.controleur = ControleurPatient()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # --- HAUT : TOOLBAR ---
        self.setup_header()

        # --- MILIEU : 3 CARDS ---
        self.setup_stats_cards()

        # --- BAS : CONTENT (Tableau à gauche + Graphes à droite) ---
        content_layout = QHBoxLayout()

        # Tableau (Container arrondi)
        self.setup_table()
        content_layout.addWidget(self.table_container, 7) 
        
        # Graphes (Container arrondi)
        self.graph_container = QFrame()
        self.graph_container.setMinimumWidth(280)
        graph_layout = QVBoxLayout(self.graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(0)
        self.graph_factory = PatientGraphs()
        graph_layout.addWidget(self.graph_factory)
        # On donne un stretch de 3 pour que les graphes soient compacts mais lisibles
        content_layout.addWidget(self.graph_container, 3)
        # content_layout.addWidget(self.graph_container)

        self.main_layout.addLayout(content_layout)
        
        

        # ... (après avoir créé self.table_container et self.graph_container)
        
        # On anime le container du tableau
        self.animer_cadre(self.table_container)
        
        # On anime le container du graphique
        self.animer_cadre(self.graph_container)
        
        # Appliquer le thème initial et écouter les changements
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

        self.load_all_data()

    def apply_theme(self):
        """Applique le thème actif à tous les composants de la vue patient."""
        c = theme_manager.colors()
        # Fond principal
        self.setStyleSheet(f"background-color: {c['bg_main']};")
        # Barre de recherche
        self.search_entry.setStyleSheet(PatientStyles.search_bar())
        # Bouton Ajouter
        self.btn_add.setStyleSheet(PatientStyles.button_primary())
        self.btn_add.setIcon(qta.icon("fa5s.plus", color=c['text_inverse']))
        # Barre d'actions
        self.action_frame.setStyleSheet(PatientStyles.action_bar())
        self.btn_data.setIcon(qta.icon("fa5s.database", color=c['text_inverse']))
        self.btn_print.setIcon(qta.icon("fa5s.print", color=c['text_inverse']))
        # Menus
        menu_style = PatientStyles.menu()
        for menu in self.findChildren(type(self.btn_data.menu())):
            if menu:
                menu.setStyleSheet(menu_style)
        # Tableau
        self.table.setStyleSheet(PatientStyles.table())
        # Conteneurs
        self.table_container.setStyleSheet(PatientStyles.card())
        self.graph_container.setStyleSheet(PatientStyles.card())
        # Stat cards se mettent à jour elles-mêmes
        # Boutons d'actions dans le tableau
        btn_style = PatientStyles.button_table_action()
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 5)
            if w:
                for b in w.findChildren(type(self.btn_add)):
                    b.setStyleSheet(btn_style)

    

    def setup_header(self):
        header = QHBoxLayout()
        
        # --- 1. RECHERCHE ET AJOUT (Inchangés) ---
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText(" Rechercher un patient (Nom, Code)...")
        self.search_entry.setFixedHeight(40)
        self.search_entry.setFixedWidth(350)
        self.search_entry.textChanged.connect(self.filtrer_patients)
        
        self.btn_add = QPushButton(qta.icon("fa5s.plus", color="white"), " Ajouter")
        self.btn_add.setFixedSize(110, 40)
        self.btn_add.clicked.connect(self.ouvrir_formulaire)

        header.addWidget(self.search_entry)
        header.addWidget(self.btn_add)
        header.addStretch()

        # --- 2. STYLE DES MENUS ---
        style_menu = PatientStyles.menu()

        # --- 3. BARRE D'ACTIONS ---
        self.action_frame = QFrame()
        self.action_frame.setFixedHeight(45)
        
        frame_layout = QHBoxLayout(self.action_frame)
        frame_layout.setContentsMargins(5, 2, 5, 2)
        frame_layout.setSpacing(0)

        # --- A. MENU DONNÉES (IMPORT & EXPORT) ---
        c = theme_manager.colors()
        self.btn_data = QPushButton(qta.icon("fa5s.database", color="white"), " Données")
        data_menu = QMenu(self)
        data_menu.setStyleSheet(style_menu)

        import_submenu = data_menu.addMenu(qta.icon("fa5s.file-import", color=c['primary']), " Importation")
        import_submenu.addAction(qta.icon("fa5s.file-excel", color=c['success']), "Depuis Excel").triggered.connect(self.import_from_excel)
        import_submenu.addAction(qta.icon("fa5s.file-csv", color=c['primary']), "Depuis CSV").triggered.connect(self.import_from_csv)

        export_submenu = data_menu.addMenu(qta.icon("fa5s.file-export", color=c['primary']), " Exportation")
        export_submenu.addAction(qta.icon("fa5s.file-excel", color=c['success']), "Vers Excel").triggered.connect(self.export_to_excel)
        export_submenu.addAction(qta.icon("fa5s.file-csv", color=c['primary']), "Vers CSV").triggered.connect(self.export_to_csv)

        self.btn_data.setMenu(data_menu)

        # --- B. MENU IMPRIMER (TOUT & GENRE) ---
        self.btn_print = QPushButton(qta.icon("fa5s.print", color="white"), " Imprimer")
        print_menu = QMenu(self)
        print_menu.setStyleSheet(style_menu)

        print_menu.addAction(qta.icon("fa5s.file-pdf", color=c['danger']), "Imprimer Tout").triggered.connect(self.imprimer_tout)
        
        genre_menu = print_menu.addMenu(qta.icon("fa5s.venus-mars", color=c['primary']), " Par Genre")
        genre_menu.addAction(qta.icon("fa5s.mars", color=c['info']), "Hommes").triggered.connect(lambda: self.imprimer_par_genre("Homme"))
        genre_menu.addAction(qta.icon("fa5s.venus", color=c['danger']), "Femmes").triggered.connect(lambda: self.imprimer_par_genre("Femme"))

        self.btn_print.setMenu(print_menu)

        # --- C. ASSEMBLAGE DANS LA FRAME ---
        frame_layout.addWidget(self.btn_data)
        
        # Petit séparateur vertical
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); border: none; margin: 8px 0px;")
        frame_layout.addWidget(sep)
        
        frame_layout.addWidget(self.btn_print)

        # Ajout de la frame au header principal
        header.addWidget(self.action_frame)
        
        self.main_layout.addLayout(header)

    def setup_stats_cards(self):
        c = theme_manager.colors()
        layout = QHBoxLayout()
        self.card_total = StatCard("Total Patients", "0", "fa5s.users", c['primary'])
        self.card_fille = StatCard("Filles", "0", "fa5s.venus", c['success'])
        self.card_garcon = StatCard("Garçons", "0", "fa5s.mars", c['info'])

        # On anime les 3 cartes
        self.animer_cadre(self.card_total)
        self.animer_cadre(self.card_fille)
        self.animer_cadre(self.card_garcon)
        
        layout.addWidget(self.card_total)
        layout.addWidget(self.card_fille)
        layout.addWidget(self.card_garcon)
        self.main_layout.addLayout(layout)

    def setup_table(self):
        self.table_container = QFrame()
        self.table_container.setObjectName("tableFrame")
        
        layout_table = QVBoxLayout(self.table_container)
        layout_table.setContentsMargins(10, 10, 10, 10)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Code", "Nom & Prénom", "Téléphone", "Genre", "Profession", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setAlternatingRowColors(True)
        
        layout_table.addWidget(self.table)

    def load_all_data(self):
        stats = self.controleur.statistique()
        self.card_total.lbl_value.setText(str(stats.get('total', 0)))
        self.card_fille.lbl_value.setText(str(stats.get('filles', 0)))
        self.card_garcon.lbl_value.setText(str(stats.get('garçons', 0)))
        self.graph_factory.update_charts(stats)

        patients = self.controleur.reed_Allpatient()
        self.display_patients(patients)

    def display_patients(self, liste_patients):
        self.table.setRowCount(0)
        for p in liste_patients:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(p.get_code_patient())))
            self.table.setItem(row, 1, QTableWidgetItem(f"{p.get_nom()} {p.get_prenom()}"))
            self.table.setItem(row, 2, QTableWidgetItem(p.get_telephone()))
            self.table.setItem(row, 3, QTableWidgetItem(p.get_genre()))
            self.table.setItem(row, 4, QTableWidgetItem(p.get_profession()))
            self.add_action_buttons(row, p)

    def add_action_buttons(self, row, patient_obj):
        btn_container = QWidget()
        l = QHBoxLayout(btn_container)
        l.setContentsMargins(5, 2, 5, 2)
        l.setSpacing(8)
        
        # 1. Création des boutons
        view_btn = QPushButton(qta.icon("fa5s.eye", color="#3498db"), "")
        edit_btn = QPushButton(qta.icon("fa5s.edit", color="#f39c12"), "")
        visit_btn = QPushButton(qta.icon("fa5s.walking", color="#034429"), "")
        del_btn = QPushButton(qta.icon("fa5s.trash", color="#e74c3c"), "")
        
        # 2. Style et ajout au layout
        btn_style = PatientStyles.button_table_action()
        for b in [view_btn, edit_btn, visit_btn, del_btn]: 
            b.setFixedSize(28, 28)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(btn_style)
            l.addWidget(b)
        
        # 3. Attachement des données (L'objet complet pour tout le monde !)
        for b in [view_btn, edit_btn, visit_btn, del_btn]:
            b.setProperty("patient_data", patient_obj)

        # 4. Connexion des signaux
        view_btn.clicked.connect(self.show_patient_details)
        edit_btn.clicked.connect(self.ouvrir_formulaire_modification) # On va la créer
        visit_btn.clicked.connect(self.ouvrir_formulaire_visite)
        # del_btn.clicked.connect(self.confirmer_suppression)           # On va la créer
            
        self.table.setCellWidget(row, 5, btn_container)

    def filtrer_patients(self, texte):
        """ Utilise les méthodes de recherche du contrôleur selon l'entrée """
        texte = texte.strip() # On enlève les espaces inutiles
        
        if not texte:
            # Si le champ est vide, on recharge la liste complète
            self.load_all_data()
            return
        else:
            # Sinon, on utilise la recherche par critère (nom, tel, etc.)
            patients = self.controleur.reed_by_critere_patient(texte)

        # On met à jour le tableau avec les résultats trouvés
        self.display_patients(patients)

    # --- MÉTHODES D'EXPORTATION ---
    def export_to_excel(self):
        # 1. Ouvrir la boîte pour choisir où enregistrer
        chemin, _ = QFileDialog.getSaveFileName(self, "Exporter en Excel", "", "Excel Files (*.xlsx)")
        if chemin:
            reussite, message = self.controleur.export_to_excel(chemin)
            self.show_message(reussite, message)

    def export_to_csv(self):
        chemin, _ = QFileDialog.getSaveFileName(self, "Exporter en CSV", "", "CSV Files (*.csv)")
        if chemin:
            reussite, message = self.controleur.export_to_csv(chemin)
            self.show_message(reussite, message)

    # --- MÉTHODES D'IMPORTATION ---
    def import_from_excel(self):
        # 1. Ouvrir la boîte pour choisir le fichier à lire
        chemin, _ = QFileDialog.getOpenFileName(self, "Importer Excel", "", "Excel Files (*.xlsx)")
        if chemin:
            reussite, message = self.controleur.import_from_excel(chemin)
            self.show_message(reussite, message)
            if reussite: self.load_all_data() # Rafraîchir le tableau

    def import_from_csv(self):
        chemin, _ = QFileDialog.getOpenFileName(self, "Importer CSV", "", "CSV Files (*.csv)")
        if chemin:
            reussite, message = self.controleur.import_from_csv(chemin)
            self.show_message(reussite, message)
            if reussite: self.load_all_data()
            
    def imprimer_tout(self):
        # 1. On demande où enregistrer le fichier
        dossier = QFileDialog.getExistingDirectory(self, "Choisir le dossier d'enregistrement")
        
        if dossier:
            # 2. On appelle le contrôleur
            success, message = self.controleur.generer_liste_total_patient(dossier)
            # 3. On affiche le résultat avec ta CustomMessageBox
            self.show_message(success, message)
            
    def imprimer_par_genre(self, genre):
        # 1. On demande où enregistrer le fichier
        dossier = QFileDialog.getExistingDirectory(self, f"Enregistrer la liste ({genre})")
        
        if dossier:
            # 2. On appelle le contrôleur avec le genre sélectionné (Homme ou Femme)
            success, message = self.controleur.generer_liste_patients_par_genre(genre, dossier)
            # 3. On affiche le résultat
            self.show_message(success, message)

    # --- LA BOITE DE MESSAGE COMMUNE ---
    def show_message(self, reussite, message):
        titre = "Succès" if reussite else "Information / Erreur"
        dialog = CustomMessageBox(titre, message, is_success=reussite, parent=self)
        dialog.exec()

    def show_patient_details(self):
        button = self.sender()
        if button:
            patient = button.property("patient_data")
            # On affiche la boîte de dialogue qu'on a créée plus haut
            dialog = PatientDetailDialog(patient, self)
            dialog.exec()
            
    

    def animer_cadre(self, widget):
        """ Applique une ombre et une animation de survol au widget """
        # 1. Création de l'ombre portée initiale
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 40)) # Noir transparent
        widget.setGraphicsEffect(shadow)
        widget._shadow = shadow

        # 2. Préparation de l'animation de mouvement (Propriété 'pos')
        widget._ani = QPropertyAnimation(widget, b"pos")
        widget._ani.setDuration(150)
        widget._ani.setEasingCurve(QEasingCurve.OutCubic)

        # 3. Définition du comportement au survol
        def enterEvent(event):
            # Monte de 5 pixels et accentue l'ombre
            widget._ani.setStartValue(widget.pos())
            widget._ani.setEndValue(QPoint(widget.pos().x(), widget.pos().y() - 5))
            widget._shadow.setBlurRadius(25)
            widget._ani.start()

        def leaveEvent(event):
            # Redescend et restaure l'ombre
            widget._ani.setStartValue(widget.pos())
            widget._ani.setEndValue(QPoint(widget.pos().x(), widget.pos().y() + 5))
            widget._shadow.setBlurRadius(15)
            widget._ani.start()
        # On remplace les événements du widget par les nôtres
        widget.enterEvent = enterEvent
        widget.leaveEvent = leaveEvent
            
    def ouvrir_formulaire(self):
        dialog = PatientFormDialog(self.controleur, parent=self)
        if dialog.exec(): # Si l'utilisateur a cliqué sur Enregistrer
            self.load_all_data() # On rafraîchit le tableau

    def ouvrir_formulaire_modification(self):
        """Ouvre le formulaire pré-rempli avec les données du patient"""
        button = self.sender()
        if button:
            patient = button.property("patient_data")
            # On passe l'objet patient au formulaire pour qu'il se remplisse
            dialog = PatientFormDialog(self.controleur, patient_obj=patient, parent=self)
            if dialog.exec():
                self.show_message(True, "Les informations du patient ont été mises à jour.")
                self.load_all_data()
                
    def ouvrir_formulaire_visite(self):
        """Ouvre l'onglet Nouveau de la vue visite pour créer une visite"""
        button = self.sender()
        if button:
            patient = button.property("patient_data")
            # TODO: Implémenter l'ouverture de l'onglet Nouveau de la vue visite
            # avec le code_patient pré-rempli
            self.show_message(False, "Fonctionnalité en cours d'implémentation.\nUtilisez la vue Visite pour créer une nouvelle visite.")

    # def confirmer_suppression(self):
    #     """Demande confirmation avant de supprimer définitivement"""
    #     button = self.sender()
    #     if button:
    #         patient = button.property("patient_data")
            
    #         # On utilise ta boîte de message personnalisée ou une standard pour la question
    #         rep = QMessageBox.question(
    #             self, "Confirmation", 
    #             f"Voulez-vous vraiment supprimer le patient {patient.get_nom()} ?",
    #             QMessageBox.Yes | QMessageBox.No
    #         )

    #         if rep == QMessageBox.Yes:
    #             ok, msg = self.controleur.delete_patient(patient.get_code_patient())
    #             if ok:
    #                 self.show_message(True, "Patient supprimé avec succès.")
    #                 self.load_all_data()
    #             else:
    #                 self.show_message(False, f"Erreur de suppression : {msg}")