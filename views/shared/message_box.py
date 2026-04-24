from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, QGridLayout
from PySide6.QtCore import Qt
import qtawesome as qta
from views.shared.theme_manager import theme_manager
from views.shared.styles import Styles


class CustomMessageBox(QDialog):
    def __init__(self, title, message, is_success=True, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        s = Styles.message_box(is_success)
        
        layout = QVBoxLayout(self)
        
        self.frame = QFrame()
        self.frame.setStyleSheet(s["frame"])
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(15)

        icon_code = "fa5s.check-circle" if is_success else "fa5s.exclamation-triangle"
        self.lbl_icon = QLabel()
        self.lbl_icon.setPixmap(qta.icon(icon_code, color=s["accent"]).pixmap(50, 50))
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(s["title"])
        self.lbl_title.setAlignment(Qt.AlignCenter)

        self.lbl_message = QLabel(message)
        self.lbl_message.setStyleSheet(s["message"])
        self.lbl_message.setAlignment(Qt.AlignCenter)
        self.lbl_message.setWordWrap(True)

        self.btn_ok = QPushButton("D'accord")
        self.btn_ok.setFixedSize(120, 35)
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.setStyleSheet(s["button"])
        self.btn_ok.clicked.connect(self.accept)

        frame_layout.addWidget(self.lbl_icon)
        frame_layout.addWidget(self.lbl_title)
        frame_layout.addWidget(self.lbl_message)
        frame_layout.addWidget(self.btn_ok, 0, Qt.AlignCenter)
        
        layout.addWidget(self.frame)



class PatientDetailDialog(QDialog):
    def __init__(self, patient, parent=None):
        super().__init__(parent)
        self.patient = patient
        self.setWindowTitle(f"Détails - {patient.get_nom()}")
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        
        self.init_ui()
        self.apply_theme()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(Styles.dialog_full())

    def init_ui(self):
        c = theme_manager.colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- HEADER (Avatar + Nom) ---
        header = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon("fa5s.user-circle", color=c['primary']).pixmap(80, 80))
        
        info_header = QVBoxLayout()
        lbl_nom = QLabel(f"{self.patient.get_nom()} {self.patient.get_prenom()}")
        lbl_nom.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {c['primary']};")
        lbl_code = QLabel(f"Code Patient: {self.patient.get_code_patient()}")
        lbl_code.setStyleSheet(f"font-size: 14px; color: {c['text_muted']}; font-style: italic;")
        
        info_header.addWidget(lbl_nom)
        info_header.addWidget(lbl_code)
        header.addWidget(icon_label)
        header.addLayout(info_header)
        header.addStretch()
        layout.addLayout(header)

        # --- SEPARATEUR ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {c['border_light']};")
        layout.addWidget(line)

        # --- CORPS (Informations détaillées) ---
        grid = QGridLayout()
        grid.setSpacing(15)

        def add_info_row(row, label, value, icon):
            ic = QLabel()
            ic.setPixmap(qta.icon(icon, color=c['primary']).pixmap(20, 20))
            lbl = QLabel(f"<b>{label}:</b>")
            val = QLabel(str(value))
            val.setStyleSheet(f"color: {c['text_primary']};")
            grid.addWidget(ic, row, 0)
            grid.addWidget(lbl, row, 1)
            grid.addWidget(val, row, 2)

        add_info_row(0, "Téléphone", self.patient.get_telephone(), "fa5s.phone")
        add_info_row(1, "Genre", self.patient.get_genre(), "fa5s.venus-mars")
        add_info_row(2, "Naissance", self.patient.get_naissance(), "fa5s.calendar-alt")
        add_info_row(3, "Profession", self.patient.get_profession(), "fa5s.briefcase")
        add_info_row(4, "Adresse", self.patient.get_adresse(), "fa5s.map-marker-alt")

        layout.addLayout(grid)
        layout.addStretch()

        # --- BOUTON IMPRIMER ---
        self.btn_print = QPushButton(qta.icon("fa5s.print", color=c['text_inverse']), " Imprimer le carnet")
        self.btn_print.setCursor(Qt.PointingHandCursor)
        self.btn_print.setFixedHeight(45)
        self.btn_print.setStyleSheet(Styles.button_primary())
        # Ici on connectera ta méthode d'impression
        self.btn_print.clicked.connect(self.imprimer_carnet)
        layout.addWidget(self.btn_print)

    def imprimer_carnet(self):
        from PySide6.QtWidgets import QFileDialog
        
        # 1. Sélection du dossier
        dossier = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier d'enregistrement")
        
        if dossier:
            # 2. Appel du contrôleur via le parent (PatientView)
            # On utilise self.parent() pour atteindre le contrôleur de PatientView
            reussite, message = self.parent().controleur.generer_carnet_par_code(
                self.patient.get_code_patient(), 
                dossier
            )
            
            # 3. Appel DIRECT de CustomMessageBox (puisque c'est dans le même fichier)
            titre = "Succès" if reussite else "Erreur"
            msg_dialog = CustomMessageBox(
                title=titre, 
                message=message, 
                is_success=reussite, 
                parent=self
            )
            msg_dialog.exec()
            
            if reussite:
                self.accept() # On ferme la fiche détail si l'impression est lancée
