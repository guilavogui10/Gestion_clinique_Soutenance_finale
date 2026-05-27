"""
Widget tableau des actes médicaux d'une consultation
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                                QTableWidgetItem, QPushButton, QLabel, QHeaderView,
                                QFrame, QLineEdit)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class ActesTableWidget(QWidget):
    """Tableau affichant les actes médicaux d'une consultation"""
    
    # Signaux
    voir_resultat_clicked = Signal(str, str)  # (type_acte, code_acte)
    retour_clicked = Signal()  # Retour aux consultations
    
    def __init__(self, controleur_acte, parent=None):
        super().__init__(parent)
        self.controleur = controleur_acte
        self.actes = []
        self._init_ui()
    
    def _init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Barre avec bouton retour et recherche
        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)
        
        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Code Acte", "Type", "Décision Médicale", "Choix Patient", "Statut", "Actions"
        ])
        
        # Configuration du tableau (identique au tableau patients)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.setMouseTracking(True)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        
        # Ajuster les colonnes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)         # Code Acte
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.Stretch)       # Décision Médicale
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Choix Patient
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Statut
        header.setSectionResizeMode(5, QHeaderView.Fixed)         # Actions
        self.table.setColumnWidth(0, 120)  # Code Acte
        self.table.setColumnWidth(5, 180)  # Actions
        
        layout.addWidget(self.table)
        
        self.apply_theme()
    
    def _create_top_bar(self):
        """Crée la barre supérieure avec bouton retour"""
        frame = QFrame()
        frame.setObjectName("TopBar")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Bouton Retour
        btn_retour = QPushButton("  Retour aux consultations")
        btn_retour.setIcon(qta.icon("fa5s.arrow-left", color=theme_manager.colors()['primary']))
        btn_retour.setObjectName("BtnRetour")
        btn_retour.setFixedHeight(36)
        btn_retour.setCursor(Qt.PointingHandCursor)
        btn_retour.clicked.connect(self.retour_clicked.emit)
        layout.addWidget(btn_retour)
        
        # Label
        label = QLabel("Actes médicaux de la consultation")
        label.setObjectName("TopLabel")
        layout.addWidget(label)
        
        layout.addStretch()
        
        # Bouton Imprimer Tout
        btn_imprimer_tout = QPushButton("  Imprimer Tout")
        btn_imprimer_tout.setIcon(qta.icon("fa5s.print", color="white"))
        btn_imprimer_tout.setObjectName("BtnImprimerTout")
        btn_imprimer_tout.setFixedHeight(36)
        btn_imprimer_tout.setCursor(Qt.PointingHandCursor)
        btn_imprimer_tout.clicked.connect(self._imprimer_tous_actes)
        layout.addWidget(btn_imprimer_tout)
        
        # Champ de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un acte...")
        self.search_input.setFixedWidth(250)
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self._filter_table)
        layout.addWidget(self.search_input)
        
        return frame
    
    def charger_actes(self, code_consultation):
        """Charge les actes d'une consultation"""
        try:
            # Récupérer les actes depuis le contrôleur
            self.actes = self.controleur.lister_actes_consultation(code_consultation)
            self._populate_table()
            
            # Afficher un message si aucun acte
            if not self.actes or len(self.actes) == 0:
                from views.shared.message_box import CustomMessageBox
                CustomMessageBox(
                    "Information",
                    f"Aucun acte médical trouvé pour cette consultation.\n\n"
                    f"La consultation n'a pas encore d'acte médical associé "
                    f"(examen, chirurgie, lunette, prescription).",
                    is_success=False,
                    parent=self
                ).exec()
        except Exception as e:
            from views.shared.message_box import CustomMessageBox
            print(f"Erreur chargement actes: {e}")
            self.actes = []
            self.table.setRowCount(0)
            CustomMessageBox(
                "Erreur",
                f"Erreur lors du chargement des actes médicaux:\n{str(e)}",
                is_success=False,
                parent=self
            ).exec()
    
    def _populate_table(self):
        """Remplit le tableau avec les actes"""
        self.table.setRowCount(0)
        
        for acte in self.actes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 66)  # Même hauteur que le tableau patients
            
            # Code acte
            code_acte = acte.get('code_acte', 'N/A')
            self.table.setItem(row, 0, QTableWidgetItem(code_acte))
            
            # Type acte
            type_acte = acte.get('type_acte', 'N/A')
            item_type = QTableWidgetItem(type_acte.capitalize())
            if type_acte.lower() == 'examen':
                item_type.setForeground(Qt.blue)
            elif type_acte.lower() == 'chirurgie':
                item_type.setForeground(Qt.red)
            elif type_acte.lower() == 'lunette':
                item_type.setForeground(Qt.darkGreen)
            elif type_acte.lower() == 'prescription':
                item_type.setForeground(Qt.darkMagenta)
            self.table.setItem(row, 1, item_type)
            
            # Décision médicale
            decision = acte.get('decision_medicale', 'N/A')
            if len(decision) > 50:
                decision = decision[:50] + "..."
            self.table.setItem(row, 2, QTableWidgetItem(decision))
            
            # Choix patient
            choix = acte.get('choix_patient', 'N/A')
            item_choix = QTableWidgetItem(choix.capitalize() if choix else 'N/A')
            if choix and choix.lower() == 'maintenant':
                item_choix.setForeground(Qt.darkGreen)
            elif choix and choix.lower() == 'plus_tard':
                item_choix.setForeground(Qt.blue)
            elif choix and choix.lower() == 'ailleurs':
                item_choix.setForeground(Qt.red)
            self.table.setItem(row, 3, item_choix)
            
            # Statut
            statut = acte.get('statut_acte', 'N/A')
            item_statut = QTableWidgetItem(statut.replace('_', ' ').capitalize() if statut else 'N/A')
            if statut and statut.lower() == 'termine':
                item_statut.setForeground(Qt.darkGreen)
            elif statut and statut.lower() == 'en_cours':
                item_statut.setForeground(Qt.blue)
            elif statut and statut.lower() in ['annule', 'refuse']:
                item_statut.setForeground(Qt.red)
            self.table.setItem(row, 4, item_statut)
            
            # Boutons Actions (Info + Résultats)
            self.table.setCellWidget(row, 5, self._create_actions_buttons(acte))
    
    def _create_actions_buttons(self, acte):
        """Crée les boutons d'actions avec menu déroulant"""
        c = theme_manager.colors()
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        
        # Bouton Menu Actions
        btn_menu = QPushButton("  Actions")
        btn_menu.setIcon(qta.icon("fa5s.ellipsis-v", color="white"))
        btn_menu.setObjectName("BtnMenu")
        btn_menu.setCursor(Qt.PointingHandCursor)
        btn_menu.setFixedSize(90, 32)
        btn_menu.clicked.connect(lambda checked, a=acte: self._show_acte_menu(a, btn_menu))
        layout.addWidget(btn_menu)
        
        # Bouton Résultats
        type_acte = acte.get('type_acte', '')
        code_acte = acte.get('code_acte', '')
        btn_resultat = QPushButton("  Résultats")
        btn_resultat.setIcon(qta.icon("fa5s.file-medical", color="white"))
        btn_resultat.setObjectName("BtnResultat")
        btn_resultat.setCursor(Qt.PointingHandCursor)
        btn_resultat.setFixedSize(90, 32)
        btn_resultat.clicked.connect(
            lambda checked, t=type_acte, c=code_acte: self.voir_resultat_clicked.emit(t, c)
        )
        layout.addWidget(btn_resultat)
        
        return widget
    
    def _show_acte_menu(self, acte, button):
        """Affiche le menu déroulant pour un acte"""
        from PySide6.QtWidgets import QMenu
        
        c = theme_manager.colors()
        menu = QMenu(self)
        
        # Style du menu
        menu.setStyleSheet(f"""
            QMenu {{
                background: white;
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 8px 0;
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QMenu::item:selected {{
                background: {c['primary_light']};
                color: {c['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['border_light']};
                margin: 4px 0;
            }}
        """)
        
        # Action Voir Info
        action_info = menu.addAction(qta.icon("fa5s.info-circle", color=c['info']), "  Voir Info Détaillée")
        action_info.triggered.connect(lambda: self._show_acte_detail(acte))
        
        menu.addSeparator()
        
        # Action Imprimer Info Acte
        action_imprimer_info = menu.addAction(qta.icon("fa5s.file-alt", color=c['warning']), "  Imprimer Info Acte")
        action_imprimer_info.triggered.connect(lambda: self._imprimer_info_acte(acte))
        
        # Action Imprimer Acte
        action_imprimer = menu.addAction(qta.icon("fa5s.print", color=c['danger']), "  Imprimer Acte")
        action_imprimer.triggered.connect(lambda: self._imprimer_acte(acte))
        
        # Afficher le menu sous le bouton
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
    
    def _show_acte_detail(self, acte):
        """Affiche les détails d'un acte"""
        from views.shared.message_box import CustomMessageBox
        
        type_acte = acte.get('type_acte', 'N/A')
        code_acte = acte.get('code_acte', 'N/A')
        decision = acte.get('decision_medicale', 'N/A')
        choix = acte.get('choix_patient', 'N/A')
        mode = acte.get('mode_realisation', 'N/A')
        statut = acte.get('statut_acte', 'N/A')
        raison_refus = acte.get('raison_refus', '')
        
        message = f"""
<b>Type :</b> {type_acte.capitalize()}<br>
<b>Code :</b> {code_acte}<br>
<b>Décision médicale :</b> {decision}<br>
<b>Choix patient :</b> {choix.capitalize() if choix else 'N/A'}<br>
<b>Mode de réalisation :</b> {mode.capitalize() if mode else 'N/A'}<br>
<b>Statut :</b> {statut.replace('_', ' ').capitalize() if statut else 'N/A'}
        """
        
        if raison_refus:
            message += f"<br><b>Raison refus :</b> {raison_refus}"
        
        CustomMessageBox(
            f"Détails de l'acte {code_acte}",
            message,
            is_success=True,
            parent=self
        ).exec_()
    
    def _filter_table(self, text):
        """Filtre le tableau selon le texte de recherche"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):  # Exclure la colonne Actions
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
    
    def _imprimer_tous_actes(self):
        """Imprime tous les actes affichés dans le tableau"""
        from views.shared.message_box import CustomMessageBox
        from services.pdf_patient.historique_pdf import HistoriquePatientPDFService
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        
        if not self.actes or len(self.actes) == 0:
            CustomMessageBox(
                "Information",
                "Aucun acte à imprimer.",
                is_success=False,
                parent=self
            ).exec()
            return
        
        try:
            actes_complets = []
            for acte in self.actes:
                code_acte = acte.get('code_acte')
                type_acte = acte.get('type_acte', '').lower()
                
                if code_acte and type_acte:
                    details = self._get_acte_complet(code_acte, type_acte)
                    if details:
                        actes_complets.append({
                            'type': type_acte,
                            'details': details
                        })
            
            if actes_complets:
                # Récupérer les informations du cabinet
                try:
                    info_cabinet = self.controleur.get_cabinet_info() if hasattr(self.controleur, 'get_cabinet_info') else {}
                except:
                    info_cabinet = {}
                
                pdf_path = HistoriquePatientPDFService.generer_pdf_actes_multiples(
                    self.actes, info_cabinet, None
                )
                dialog = ApercuPDFDialog(pdf_path, "Aperçu - Actes médicaux", self)
                dialog.exec()
            else:
                CustomMessageBox(
                    "Erreur",
                    "Impossible de récupérer les détails des actes.",
                    is_success=False,
                    parent=self
                ).exec()
        except Exception as e:
            CustomMessageBox(
                "Erreur",
                f"Erreur lors de la génération du PDF:\n{str(e)}",
                is_success=False,
                parent=self
            ).exec()
    
    def _imprimer_info_acte(self, acte):
        """Imprime les informations d'un acte"""
        from views.shared.message_box import CustomMessageBox
        from services.pdf_patient.historique_pdf import HistoriquePatientPDFService
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        
        code = acte.get('code_acte', 'N/A')
        type_acte = acte.get('type_acte', '').lower()
        
        try:
            details = self._get_acte_complet(code, type_acte)
            if details:
                # Récupérer les informations du cabinet
                try:
                    info_cabinet = self.controleur.get_cabinet_info() if hasattr(self.controleur, 'get_cabinet_info') else {}
                except:
                    info_cabinet = {}
                
                pdf_path = HistoriquePatientPDFService.generer_pdf_acte(
                    details, type_acte, info_cabinet, None
                )
                dialog = ApercuPDFDialog(pdf_path, f"Aperçu - Acte {code}", self)
                dialog.exec()
            else:
                CustomMessageBox(
                    "Erreur",
                    f"Impossible de récupérer les détails de l'acte {code}.",
                    is_success=False,
                    parent=self
                ).exec()
        except Exception as e:
            CustomMessageBox(
                "Erreur",
                f"Erreur lors de la génération du PDF:\n{str(e)}",
                is_success=False,
                parent=self
            ).exec()
    
    def _imprimer_acte(self, acte):
        """Imprime un acte complet"""
        from views.shared.message_box import CustomMessageBox
        from services.pdf_patient.historique_pdf import HistoriquePatientPDFService
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        
        code = acte.get('code_acte', 'N/A')
        type_acte = acte.get('type_acte', '').lower()
        
        try:
            details = self._get_acte_complet(code, type_acte)
            if details:
                # Récupérer les informations du cabinet
                try:
                    info_cabinet = self.controleur.get_cabinet_info() if hasattr(self.controleur, 'get_cabinet_info') else {}
                except:
                    info_cabinet = {}
                
                pdf_path = HistoriquePatientPDFService.generer_pdf_acte(
                    details, type_acte, info_cabinet, None
                )
                dialog = ApercuPDFDialog(pdf_path, f"Aperçu - Acte {code}", self)
                dialog.exec()
            else:
                CustomMessageBox(
                    "Erreur",
                    f"Impossible de récupérer l'acte {code}.",
                    is_success=False,
                    parent=self
                ).exec()
        except Exception as e:
            CustomMessageBox(
                "Erreur",
                f"Erreur lors de la génération du PDF:\n{str(e)}",
                is_success=False,
                parent=self
            ).exec()
    
    def _get_acte_complet(self, code_acte: str, type_acte: str):
        """Récupère les détails complets d'un acte selon son type"""
        try:
            # D'abord récupérer les informations de base de l'acte médical
            acte_base = None
            for acte in self.actes:
                if acte.get('code_acte') == code_acte:
                    acte_base = acte
                    break
            
            # Ensuite récupérer les détails spécifiques selon le type
            details = None
            if type_acte == 'examen':
                details = self.controleur.get_examen_complet(code_acte)
            elif type_acte == 'chirurgie':
                details = self.controleur.get_chirurgie_complete(code_acte)
            elif type_acte == 'lunette':
                details = self.controleur.get_lunette_complete(code_acte)
            elif type_acte == 'prescription':
                details = self.controleur.get_prescription_complete(code_acte)
            
            # Fusionner les informations de base avec les détails spécifiques
            if details and acte_base:
                # Ajouter les informations de base de l'acte médical
                details['code_acte'] = acte_base.get('code_acte', code_acte)
                details['type_acte'] = acte_base.get('type_acte', type_acte)
                details['decision_medicale'] = acte_base.get('decision_medicale', 'N/A')
                details['choix_patient'] = acte_base.get('choix_patient', 'N/A')
                details['statut_acte'] = acte_base.get('statut_acte', 'N/A')
                details['mode_realisation'] = acte_base.get('mode_realisation', 'N/A')
                details['raison_refus'] = acte_base.get('raison_refus', '')
            
            return details
        except Exception as e:
            print(f"Erreur _get_acte_complet: {e}")
            return None
    
    def apply_theme(self):
        """Applique le thème (identique au tableau patients)"""
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QFrame#TopBar {{
                background: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 10px;
            }}
            
            QLabel#TopLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
            
            QPushButton#BtnRetour {{
                background: white;
                color: {c['primary']};
                border: 1.5px solid {c['primary']};
                border-radius: 8px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            
            QPushButton#BtnRetour:hover {{
                background: {c['primary']}10;
            }}
            
            QLineEdit {{
                background: {c['bg_input']};
                border: 1.5px solid {c['border']};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 12px;
                color: {c['text_primary']};
            }}
            
            QLineEdit:focus {{
                border-color: {c['primary']};
                background: {c['bg_card']};
            }}
            
            QTableWidget {{
                background: white;
                border: 1.5px solid {c['border_light']};
                border-radius: 10px;
                gridline-color: transparent;
                color: {c['text_primary']};
                selection-background-color: transparent;
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border: none;
                border-bottom: 1px solid {c['border_light']};
            }}
            
            QTableWidget::item:selected {{
                background: {c['primary']}20;
                color: {c['text_primary']};
            }}
            
            QHeaderView::section {{
                background: {c['table_header_bg']};
                color: {c['text_secondary']};
                padding: 10px;
                border: none;
                border-bottom: 1px solid {c['border_light']};
                font-weight: 700;
                font-size: 11px;
            }}
            
            QPushButton#BtnInfo {{
                background: {c['info']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            
            QPushButton#BtnInfo:hover {{
                background: {c['info']}dd;
            }}
            
            QPushButton#BtnMenu {{
                background: {c['secondary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            
            QPushButton#BtnMenu:hover {{
                background: {c['secondary']}dd;
            }}
            
            QPushButton#BtnResultat {{
                background: {c['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            
            QPushButton#BtnResultat:hover {{
                background: {c['success']}dd;
            }}
            
            QPushButton#BtnImprimerTout {{
                background: {c['danger']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            
            QPushButton#BtnImprimerTout:hover {{
                background: {c['danger']}dd;
            }}
        """)
