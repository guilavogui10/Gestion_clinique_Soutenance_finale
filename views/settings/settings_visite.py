import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QLabel, QGraphicsDropShadowEffect,
    QLineEdit, QGridLayout, QMessageBox, QSpinBox
)
from views.shared.theme_manager import theme_manager
from parametre.config_metier_controller import config_metier_controller


class SettingsVisite(QWidget):
    """Interface de gestion des paramètres de visite."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = config_metier_controller
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        """Initialise l'interface."""
        self.setStyleSheet("background-color: #FFFFFF;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # En-tête
        header = self._creer_header()
        main_layout.addWidget(header)

        # Contenu en 2 colonnes
        content = QWidget()
        content.setStyleSheet("background-color: #FFFFFF;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(20, 15, 20, 15)
        content_layout.setSpacing(20)

        # Colonne gauche: Types de visite
        left_col = QVBoxLayout()
        left_col.setSpacing(0)
        section_types = self._creer_section_types_visite()
        left_col.addWidget(section_types)
        left_col.addStretch()
        content_layout.addLayout(left_col, 1)

        # Colonne droite: Durées
        right_col = QVBoxLayout()
        right_col.setSpacing(15)
        section_durees = self._creer_section_durees_services()
        section_parcours = self._creer_section_parcours_patient()
        right_col.addWidget(section_durees)
        right_col.addWidget(section_parcours)
        right_col.addStretch()
        content_layout.addLayout(right_col, 1)

        main_layout.addWidget(content, 1)

        # Footer avec boutons
        footer = self._creer_footer()
        main_layout.addWidget(footer)

    def _creer_header(self) -> QWidget:
        """Crée l'en-tête."""
        c = theme_manager.colors()
        
        container = QWidget()
        container.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 12, 20, 0)
        layout.setSpacing(8)

        # Titre
        titre_layout = QHBoxLayout()
        titre_layout.setSpacing(10)
        
        icone = QLabel()
        icone.setPixmap(qta.icon("fa5s.hospital-alt", color=c['primary']).pixmap(QSize(20, 20)))
        icone.setStyleSheet("border: none;")
        
        titre = QLabel("Paramètres de visite")
        titre.setStyleSheet(f"color: {c['primary']}; font-size: 16px; font-weight: 700; border: none;")
        
        titre_layout.addWidget(icone)
        titre_layout.addWidget(titre)
        titre_layout.addStretch()
        
        layout.addLayout(titre_layout)

        # Sous-titre
        sous_titre = QLabel("Configurez les types de visite, tarifs et durées")
        sous_titre.setStyleSheet(f"color: {c['text_muted']}; font-size: 12px; border: none;")
        layout.addWidget(sous_titre)

        # Séparateur
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {c['border']}; border: none;")
        layout.addWidget(sep)

        return container

    def _creer_section_types_visite(self) -> QFrame:
        """Crée la section types de visite."""
        c = theme_manager.colors()
        
        frame = self._creer_card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Titre section
        titre_layout = QHBoxLayout()
        titre_layout.setSpacing(8)
        
        icone = QLabel()
        icone.setPixmap(qta.icon("fa5s.user-md", color=c['primary']).pixmap(QSize(16, 16)))
        icone.setStyleSheet("border: none;")
        
        titre = QLabel("Types de visite et tarifs")
        titre.setStyleSheet(f"color: {c['text_primary']}; font-size: 14px; font-weight: 700; border: none;")
        
        titre_layout.addWidget(icone)
        titre_layout.addWidget(titre)
        titre_layout.addStretch()
        layout.addLayout(titre_layout)

        # Grille
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(2, 1)

        # En-têtes
        headers = ["Type", "Tarif (GNF)", "Description"]
        for col, txt in enumerate(headers):
            lbl = QLabel(txt)
            lbl.setStyleSheet(f"color: {c['text_muted']}; font-size: 10px; font-weight: 600; border: none;")
            if col == 1:
                lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl, 0, col)

        self.inputs_types = {}
        row = 1

        types_visite = self.controller.obtenir_types_visite()
        for nom, info in types_visite.items():
            # Type
            lbl = QLabel(nom)
            lbl.setStyleSheet(f"color: {c['text_primary']}; font-size: 12px; font-weight: 600; border: none;")
            grid.addWidget(lbl, row, 0)

            # Tarif
            input_tarif = QLineEdit(str(info.get('tarif', 0)))
            input_tarif.setFixedHeight(30)
            input_tarif.setFixedWidth(120)
            input_tarif.setAlignment(Qt.AlignCenter)
            input_tarif.setStyleSheet(self._css_input())
            grid.addWidget(input_tarif, row, 1)

            # Description
            input_desc = QLineEdit(info.get('description', ''))
            input_desc.setFixedHeight(30)
            input_desc.setStyleSheet(self._css_input())
            grid.addWidget(input_desc, row, 2)

            self.inputs_types[nom] = {'tarif': input_tarif, 'description': input_desc}
            row += 1

        layout.addLayout(grid)
        return frame

    def _creer_section_durees_services(self) -> QFrame:
        """Crée la section durées services."""
        c = theme_manager.colors()
        
        frame = self._creer_card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Titre
        titre_layout = QHBoxLayout()
        titre_layout.setSpacing(8)
        
        icone = QLabel()
        icone.setPixmap(qta.icon("fa5s.clock", color=c['primary']).pixmap(QSize(16, 16)))
        icone.setStyleSheet("border: none;")
        
        titre = QLabel("Durées des services (minutes)")
        titre.setStyleSheet(f"color: {c['text_primary']}; font-size: 14px; font-weight: 700; border: none;")
        
        titre_layout.addWidget(icone)
        titre_layout.addWidget(titre)
        titre_layout.addStretch()
        layout.addLayout(titre_layout)

        # Grille
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        # En-têtes
        headers = ["Service", "Normale", "Maximale"]
        for col, txt in enumerate(headers):
            lbl = QLabel(txt)
            lbl.setStyleSheet(f"color: {c['text_muted']}; font-size: 10px; font-weight: 600; border: none;")
            if col > 0:
                lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl, 0, col)

        self.inputs_durees = {}
        row = 1

        durees_services = self.controller.obtenir_durees_services()
        for nom, info in durees_services.items():
            # Service
            lbl = QLabel(nom.capitalize())
            lbl.setStyleSheet(f"color: {c['text_primary']}; font-size: 12px; font-weight: 600; border: none;")
            grid.addWidget(lbl, row, 0)

            # Normale
            input_normale = QLineEdit(str(info.get('duree_normale_minutes', 30)))
            input_normale.setFixedHeight(30)
            input_normale.setFixedWidth(120)
            input_normale.setAlignment(Qt.AlignCenter)
            input_normale.setPlaceholderText("Minutes")
            input_normale.setStyleSheet(self._css_input())
            grid.addWidget(input_normale, row, 1)

            # Maximale
            input_max = QLineEdit(str(info.get('duree_maximale_minutes', 60)))
            input_max.setFixedHeight(30)
            input_max.setFixedWidth(120)
            input_max.setAlignment(Qt.AlignCenter)
            input_max.setPlaceholderText("Minutes")
            input_max.setStyleSheet(self._css_input())
            grid.addWidget(input_max, row, 2)

            self.inputs_durees[nom] = {'normale': input_normale, 'maximale': input_max}
            row += 1

        layout.addLayout(grid)
        return frame

    def _creer_section_parcours_patient(self) -> QFrame:
        """Crée la section parcours patient."""
        c = theme_manager.colors()
        
        frame = self._creer_card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Titre
        titre_layout = QHBoxLayout()
        titre_layout.setSpacing(8)
        
        icone = QLabel()
        icone.setPixmap(qta.icon("fa5s.route", color=c['primary']).pixmap(QSize(16, 16)))
        icone.setStyleSheet("border: none;")
        
        titre = QLabel("Durée totale du parcours patient")
        titre.setStyleSheet(f"color: {c['text_primary']}; font-size: 14px; font-weight: 700; border: none;")
        
        titre_layout.addWidget(icone)
        titre_layout.addWidget(titre)
        titre_layout.addStretch()
        layout.addLayout(titre_layout)

        # Description
        desc = QLabel("De la création de visite jusqu'à la libération")
        desc.setStyleSheet(f"color: {c['text_muted']}; font-size: 11px; border: none;")
        layout.addWidget(desc)

        # Inputs
        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(15)

        duree_normale, duree_max = self.controller.obtenir_duree_totale_parcours()

        for label_txt, attr, val in [
            ("Durée normale", "input_parcours_normale", duree_normale),
            ("Durée maximale", "input_parcours_max", duree_max)
        ]:
            col = QVBoxLayout()
            col.setSpacing(5)

            lbl = QLabel(label_txt)
            lbl.setStyleSheet(f"color: {c['text_primary']}; font-size: 11px; font-weight: 600; border: none;")

            input_field = QLineEdit(str(val))
            input_field.setFixedHeight(30)
            input_field.setFixedWidth(120)
            input_field.setAlignment(Qt.AlignCenter)
            input_field.setPlaceholderText("Minutes")
            input_field.setStyleSheet(self._css_input())

            setattr(self, attr, input_field)

            col.addWidget(lbl)
            col.addWidget(input_field)
            inputs_layout.addLayout(col)

        inputs_layout.addStretch()
        layout.addLayout(inputs_layout)
        return frame

    def _creer_footer(self) -> QWidget:
        """Crée le footer avec les boutons."""
        c = theme_manager.colors()
        
        footer = QWidget()
        footer.setStyleSheet(f"background-color: #FFFFFF; border-top: 1px solid {c['border']};")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)
        layout.addStretch()

        # Bouton Réinitialiser
        self.btn_annuler = QPushButton()
        self.btn_annuler.setCursor(Qt.PointingHandCursor)
        self.btn_annuler.setFixedSize(160, 40)
        
        btn_layout = QHBoxLayout(self.btn_annuler)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignCenter)
        
        icon_reset = QLabel()
        icon_reset.setPixmap(qta.icon("fa5s.undo-alt", color=c['text_primary']).pixmap(QSize(16, 16)))
        icon_reset.setStyleSheet("border: none; background: transparent;")
        
        lbl_reset = QLabel("Réinitialiser")
        lbl_reset.setStyleSheet(f"color: {c['text_primary']}; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        
        btn_layout.addWidget(icon_reset)
        btn_layout.addWidget(lbl_reset)
        
        self.btn_annuler.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                border: 1.5px solid {c['border']};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
                border-color: {c['primary']};
            }}
        """)
        self.btn_annuler.clicked.connect(self._annuler)

        # Bouton Sauvegarder
        self.btn_enregistrer = QPushButton()
        self.btn_enregistrer.setCursor(Qt.PointingHandCursor)
        self.btn_enregistrer.setFixedSize(160, 40)
        
        btn_layout2 = QHBoxLayout(self.btn_enregistrer)
        btn_layout2.setContentsMargins(0, 0, 0, 0)
        btn_layout2.setSpacing(10)
        btn_layout2.setAlignment(Qt.AlignCenter)
        
        icon_save = QLabel()
        icon_save.setPixmap(qta.icon("fa5s.check-circle", color=c['text_inverse']).pixmap(QSize(16, 16)))
        icon_save.setStyleSheet("border: none; background: transparent;")
        
        lbl_save = QLabel("Sauvegarder")
        lbl_save.setStyleSheet(f"color: {c['text_inverse']}; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        
        btn_layout2.addWidget(icon_save)
        btn_layout2.addWidget(lbl_save)
        
        self.btn_enregistrer.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['primary']};
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {c['primary']};
                opacity: 0.9;
            }}
        """)
        self.btn_enregistrer.clicked.connect(self._enregistrer)

        layout.addWidget(self.btn_annuler)
        layout.addWidget(self.btn_enregistrer)
        layout.addStretch()

        return footer

    def _creer_card(self) -> QFrame:
        """Crée une card."""
        c = theme_manager.colors()
        
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 12px;
                border: 1px solid {c['border']};
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 20))
        frame.setGraphicsEffect(shadow)
        
        return frame

    def _annuler(self):
        """Réinitialise."""
        types_visite = self.controller.obtenir_types_visite()
        for nom, info in types_visite.items():
            if nom in self.inputs_types:
                self.inputs_types[nom]['tarif'].setText(str(info.get('tarif', 0)))
                self.inputs_types[nom]['description'].setText(info.get('description', ''))

        durees_services = self.controller.obtenir_durees_services()
        for nom, info in durees_services.items():
            if nom in self.inputs_durees:
                self.inputs_durees[nom]['normale'].setText(str(info.get('duree_normale_minutes', 30)))
                self.inputs_durees[nom]['maximale'].setText(str(info.get('duree_maximale_minutes', 60)))

        duree_normale, duree_max = self.controller.obtenir_duree_totale_parcours()
        self.input_parcours_normale.setText(str(duree_normale))
        self.input_parcours_max.setText(str(duree_max))

        QMessageBox.information(self, "Réinitialisé", "Les valeurs ont été réinitialisées.")

    def _enregistrer(self):
        """Enregistre."""
        try:
            for nom, inputs in self.inputs_types.items():
                tarif = float(inputs['tarif'].text())
                description = inputs['description'].text()
                success, message = self.controller.modifier_type_visite(nom, tarif, description)
                if not success:
                    QMessageBox.warning(self, "Erreur", f"Erreur pour {nom}: {message}")
                    return

            for nom, inputs in self.inputs_durees.items():
                duree_normale = int(inputs['normale'].text())
                duree_max = int(inputs['maximale'].text())
                success, message = self.controller.modifier_duree_service(nom, duree_normale, duree_max)
                if not success:
                    QMessageBox.warning(self, "Erreur", f"Erreur pour {nom}: {message}")
                    return

            duree_normale = int(self.input_parcours_normale.text())
            duree_max = int(self.input_parcours_max.text())
            success, message = self.controller.modifier_duree_parcours_patient(duree_normale, duree_max)
            if not success:
                QMessageBox.warning(self, "Erreur", message)
                return

            QMessageBox.information(self, "Succès", "Les paramètres ont été enregistrés avec succès!")

        except ValueError:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer des valeurs numériques valides.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur: {e}")

    def _css_input(self) -> str:
        c = theme_manager.colors()
        return f"""
            QLineEdit {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {c['primary']};
            }}
        """

    def _css_spinbox(self) -> str:
        c = theme_manager.colors()
        return f"""
            QSpinBox {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QSpinBox:focus {{
                border: 1.5px solid {c['primary']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 16px;
                border: none;
            }}
        """

    def apply_theme(self):
        """Applique le thème."""
        pass
