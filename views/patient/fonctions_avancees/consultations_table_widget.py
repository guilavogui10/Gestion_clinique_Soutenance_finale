"""
Widget tableau des consultations d'une visite
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                                QTableWidgetItem, QPushButton, QLabel, QHeaderView,
                                QFrame, QLineEdit)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class ConsultationsTableWidget(QWidget):
    """Tableau affichant les consultations d'une visite"""
    
    # Signaux
    consultation_clicked = Signal(dict)  # Émet la consultation sélectionnée
    retour_clicked = Signal()  # Retour aux visites
    
    def __init__(self, controleur_consultation, parent=None):
        super().__init__(parent)
        self.controleur = controleur_consultation
        self.consultations = []
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
            "Code", "Date", "Diagnostique", "Frais", "Statut Facture", "Action"
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
        header.setSectionResizeMode(0, QHeaderView.Fixed)         # Code
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.Stretch)       # Diagnostique
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Frais
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Statut
        header.setSectionResizeMode(5, QHeaderView.Fixed)         # Action
        self.table.setColumnWidth(0, 120)  # Code
        self.table.setColumnWidth(5, 130)  # Action
        
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
        btn_retour = QPushButton("  Retour aux visites")
        btn_retour.setIcon(qta.icon("fa5s.arrow-left", color=theme_manager.colors()['primary']))
        btn_retour.setObjectName("BtnRetour")
        btn_retour.setFixedHeight(36)
        btn_retour.setCursor(Qt.PointingHandCursor)
        btn_retour.clicked.connect(self.retour_clicked.emit)
        layout.addWidget(btn_retour)
        
        # Label
        label = QLabel("Consultations de la visite")
        label.setObjectName("TopLabel")
        layout.addWidget(label)
        
        layout.addStretch()
        
        # Bouton Imprimer Tout
        btn_imprimer_tout = QPushButton("  Imprimer Tout")
        btn_imprimer_tout.setIcon(qta.icon("fa5s.print", color="white"))
        btn_imprimer_tout.setObjectName("BtnImprimerTout")
        btn_imprimer_tout.setFixedHeight(36)
        btn_imprimer_tout.setCursor(Qt.PointingHandCursor)
        btn_imprimer_tout.clicked.connect(self._imprimer_toutes_consultations)
        layout.addWidget(btn_imprimer_tout)
        
        # Champ de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher une consultation...")
        self.search_input.setFixedWidth(250)
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self._filter_table)
        layout.addWidget(self.search_input)
        
        return frame
    
    def charger_consultations(self, code_visite):
        """Charge les consultations d'une visite"""
        try:
            # Récupérer les consultations depuis le contrôleur
            self.consultations = self.controleur.lister_consultations_visite(code_visite)
            self._populate_table()
            
            # Afficher un message si aucune consultation
            if not self.consultations or len(self.consultations) == 0:
                from views.shared.message_box import CustomMessageBox
                CustomMessageBox(
                    "Information",
                    f"Aucune consultation trouvée pour cette visite.\n\n"
                    f"La visite n'a pas encore de consultation associée.",
                    is_success=False,
                    parent=self
                ).exec()
        except Exception as e:
            from views.shared.message_box import CustomMessageBox
            print(f"Erreur chargement consultations: {e}")
            self.consultations = []
            self.table.setRowCount(0)
            CustomMessageBox(
                "Erreur",
                f"Erreur lors du chargement des consultations:\n{str(e)}",
                is_success=False,
                parent=self
            ).exec()
    
    def _populate_table(self):
        """Remplit le tableau avec les consultations"""
        self.table.setRowCount(0)
        
        for consultation in self.consultations:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 66)  # Même hauteur que le tableau patients
            
            # Code consultation
            self.table.setItem(row, 0, QTableWidgetItem(consultation.get('code', 'N/A')))
            
            # Date
            date_consultation = consultation.get('date_consultation', 'N/A')
            if hasattr(date_consultation, 'strftime'):
                date_consultation = date_consultation.strftime('%d/%m/%Y %H:%M')
            self.table.setItem(row, 1, QTableWidgetItem(str(date_consultation)))
            
            # Diagnostique
            diagnostique = consultation.get('diagnostique', 'N/A')
            if len(diagnostique) > 50:
                diagnostique = diagnostique[:50] + "..."
            self.table.setItem(row, 2, QTableWidgetItem(diagnostique))
            
            # Frais
            frais = consultation.get('frais_consultation', 0)
            frais_str = f"{frais:,.0f} GNF".replace(",", " ")
            self.table.setItem(row, 3, QTableWidgetItem(frais_str))
            
            # Statut facture
            statut = consultation.get('statut_facture', 'N/A')
            item_statut = QTableWidgetItem(statut)
            if statut == 'payee':
                item_statut.setForeground(Qt.darkGreen)
            elif statut == 'impayee':
                item_statut.setForeground(Qt.red)
            self.table.setItem(row, 4, item_statut)
            
            # Bouton Voir Actes - Utiliser setCellWidget comme dans le tableau patients
            self.table.setCellWidget(row, 5, self._create_action_button(consultation))
    
    def _create_action_button(self, consultation):
        """Crée le bouton d'action avec menu déroulant (même style que le tableau patients)"""
        c = theme_manager.colors()
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)
        
        btn_voir = QPushButton("  Actions")
        btn_voir.setIcon(qta.icon("fa5s.ellipsis-v", color="white"))
        btn_voir.setObjectName("BtnVoir")
        btn_voir.setCursor(Qt.PointingHandCursor)
        btn_voir.setFixedSize(110, 32)
        btn_voir.clicked.connect(lambda checked, c=consultation: self._show_consultation_menu(c, btn_voir))
        
        layout.addWidget(btn_voir)
        
        return widget
    
    def _show_consultation_menu(self, consultation, button):
        """Affiche le menu déroulant pour une consultation"""
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
        
        # Action Voir Actes
        action_voir_actes = menu.addAction(qta.icon("fa5s.procedures", color=c['accent']), "  Voir les Actes")
        action_voir_actes.triggered.connect(lambda: self.consultation_clicked.emit(consultation))
        
        menu.addSeparator()
        
        # Action Imprimer Info Consultation
        action_imprimer_info = menu.addAction(qta.icon("fa5s.file-alt", color=c['info']), "  Imprimer Info Consultation")
        action_imprimer_info.triggered.connect(lambda: self._imprimer_info_consultation(consultation))
        
        # Action Imprimer Consultation
        action_imprimer = menu.addAction(qta.icon("fa5s.print", color=c['danger']), "  Imprimer Consultation")
        action_imprimer.triggered.connect(lambda: self._imprimer_consultation(consultation))
        
        # Action Imprimer Tous les Actes
        action_imprimer_actes = menu.addAction(qta.icon("fa5s.file-medical", color=c['success']), "  Imprimer Tous les Actes")
        action_imprimer_actes.triggered.connect(lambda: self._imprimer_tous_actes_consultation(consultation))
        
        # Afficher le menu sous le bouton
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
    
    def _imprimer_toutes_consultations(self):
        """Imprime toutes les consultations affichées dans le tableau"""
        from views.shared.message_box import CustomMessageBox
        from services.pdf_actes.consultation_pdf import ConsultationPDF
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog

        if not self.consultations or len(self.consultations) == 0:
            CustomMessageBox(
                "Information",
                "Aucune consultation à imprimer.",
                is_success=False,
                parent=self
            ).exec()
            return
        
        try:
            consultations_completes = []
            for consultation in self.consultations:
                code = consultation.get('code')
                if code:
                    details = self.controleur.get_consultation_complete(code)
                    if details:
                        consultations_completes.append(details)
            
            if consultations_completes:
                # Récupérer les informations du cabinet
                try:
                    info_cabinet = self.controleur.get_cabinet_info() if hasattr(self.controleur, 'get_cabinet_info') else {}
                except:
                    info_cabinet = {}
                
                pdf_path = ConsultationPDF.generer_pdf_consultations_multiples(
                    consultations_completes, info_cabinet, None
                )
                dialog = ApercuPDFDialog(pdf_path, "Aperçu - Consultations", self)
                dialog.exec()
            else:
                CustomMessageBox(
                    "Erreur",
                    "Impossible de récupérer les détails des consultations.",
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
    
    def _imprimer_info_consultation(self, consultation):
        """Imprime les informations d'une consultation"""
        from views.shared.message_box import CustomMessageBox
        from services.pdf_actes.consultation_pdf import ConsultationPDF
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        
        code = consultation.get('code', 'N/A')
        
        try:
            details = self.controleur.get_consultation_complete(code)
            if details:
                # Récupérer les informations du cabinet
                try:
                    info_cabinet = self.controleur.get_cabinet_info() if hasattr(self.controleur, 'get_cabinet_info') else {}
                except:
                    info_cabinet = {}
                
                pdf_path = ConsultationPDF.generer_pdf_consultation(
                    details, info_cabinet, None
                )
                dialog = ApercuPDFDialog(pdf_path, f"Aperçu - Consultation {code}", self)
                dialog.exec()
            else:
                CustomMessageBox(
                    "Erreur",
                    f"Impossible de récupérer les détails de la consultation {code}.",
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
    
    def _imprimer_consultation(self, consultation):
        """Imprime une consultation complète"""
        from views.shared.message_box import CustomMessageBox
        from services.pdf_actes.consultation_pdf import ConsultationPDF
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        
        code = consultation.get('code', 'N/A')
        
        try:
            details = self.controleur.get_consultation_complete(code)
            if details:
                # Récupérer les informations du cabinet
                try:
                    info_cabinet = self.controleur.get_cabinet_info() if hasattr(self.controleur, 'get_cabinet_info') else {}
                except:
                    info_cabinet = {}
                
                pdf_path = ConsultationPDF.generer_pdf_consultation(
                    details, info_cabinet, None
                )
                dialog = ApercuPDFDialog(pdf_path, f"Aperçu - Consultation {code}", self)
                dialog.exec()
            else:
                CustomMessageBox(
                    "Erreur",
                    f"Impossible de récupérer la consultation {code}.",
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
    
    def _imprimer_tous_actes_consultation(self, consultation):
        """Imprime tous les actes liés à une consultation"""
        from views.shared.message_box import CustomMessageBox
        from services.pdf_patient.historique_pdf import HistoriquePatientPDFService
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        
        code = consultation.get('code', 'N/A')
        
        try:
            actes = self.controleur.lister_actes_consultation(code)
            
            if actes and len(actes) > 0:
                # Récupérer les informations du cabinet
                try:
                    info_cabinet = self.controleur.get_cabinet_info() if hasattr(self.controleur, 'get_cabinet_info') else {}
                except:
                    info_cabinet = {}
                
                pdf_path = HistoriquePatientPDFService.generer_pdf_actes_multiples(
                    actes, info_cabinet, None
                )
                dialog = ApercuPDFDialog(pdf_path, f"Aperçu - Actes de la consultation {code}", self)
                dialog.exec()
            else:
                CustomMessageBox(
                    "Information",
                    f"Aucun acte trouvé pour la consultation {code}.",
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
    
    def _filter_table(self, text):
        """Filtre le tableau selon le texte de recherche"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
    
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
            
            QPushButton#BtnVoir {{
                background: {c['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            
            QPushButton#BtnVoir:hover {{
                background: {c['accent']}dd;
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
