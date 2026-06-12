import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from views.shared.theme_manager import theme_manager


def _sep(couleur=None):
    c = theme_manager.colors()
    if couleur is None:
        couleur = c['border']
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{couleur}; border:none;")
    return f


def _fmt_date(val):
    if val and hasattr(val, "strftime"):
        return val.strftime("%d/%m/%Y")
    return str(val) if val else "—"


def _row_ic_val(icone_name, valeur, couleur_ic=None, couleur_val=None, gras=False):
    from PySide6.QtWidgets import QWidget
    c = theme_manager.colors()
    if couleur_ic is None:
        couleur_ic = c['text_secondary']
    if couleur_val is None:
        couleur_val = c['text_secondary']
    w = QWidget()
    w.setStyleSheet(f"background:{c['bg_card']};")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(5)
    ic = QLabel()
    ic.setPixmap(qta.icon(icone_name, color=couleur_ic).pixmap(QSize(11, 11)))
    ic.setStyleSheet(f"background:{c['bg_card']}; border:none;")
    lbl = QLabel(str(valeur) if valeur else "—")
    poids = "700" if gras else "400"
    lbl.setStyleSheet(
        f"color:{couleur_val}; font-size:11px; font-weight:{poids};"
        f"background:{c['bg_card']}; border:none;"
    )
    lbl.setWordWrap(True)
    lay.addWidget(ic)
    lay.addWidget(lbl)
    lay.addStretch()
    return w


class CarteCommandeAttente(QFrame):
    """Carte commande en attente avec bouton 'Voir détail' qui switche l'onglet."""

    def __init__(self, row: dict, ctrl, on_voir_detail, on_livre_callback, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.row = row
        self.on_voir_detail = on_voir_detail
        self.on_livre_callback = on_livre_callback
        self.code_commande = row.get("commande_code") or row.get("code", "")

        c = theme_manager.colors()

        self.setStyleSheet(
            f"QFrame{{background:{c['bg_card']}; border-radius:12px;"
            f"border:1px solid {c['border']};}}"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        # Ligne 1 : code + badge + boutons
        ligne1 = QHBoxLayout()

        code_lbl = QLabel(f"#{self.code_commande}")
        code_lbl.setStyleSheet(
            f"color:{c['primary']}; font-size:12px; font-weight:700;"
            f"background:{c['bg_card']}; border:none;"
        )
        badge = QLabel("En attente")
        badge.setStyleSheet(
            f"background:{c['warning_bg']}; color:{c['warning']};"
            f"border-radius:8px; font-size:10px; font-weight:700;"
            f"padding:2px 8px; border:1px solid {c['warning']};"
        )
        ligne1.addWidget(code_lbl)
        ligne1.addSpacing(6)
        ligne1.addWidget(badge)
        ligne1.addStretch()

        btn_detail = QPushButton(qta.icon("fa5s.eye", color=c['info']), "  Détail")
        btn_detail.setFixedHeight(28)
        btn_detail.setCursor(Qt.PointingHandCursor)
        btn_detail.setStyleSheet(
            f"background:{c['primary_light']}; color:{c['info']};"
            f"border-radius:8px; border:none; font-size:11px;"
            f"font-weight:600; padding:0 10px;"
        )
        btn_detail.clicked.connect(
            lambda: self.on_voir_detail(self.code_commande, self.row))

        btn_livrer = QPushButton(qta.icon("fa5s.check", color=c['text_inverse']), "  Livré")
        btn_livrer.setFixedHeight(28)
        btn_livrer.setCursor(Qt.PointingHandCursor)
        btn_livrer.setStyleSheet(
            f"background:{c['primary']}; color:{c['text_inverse']};"
            f"border-radius:8px; border:none; font-size:11px;"
            f"font-weight:700; padding:0 10px;"
        )
        btn_livrer.clicked.connect(self._marquer_livre)

        ligne1.addWidget(btn_detail)
        ligne1.addSpacing(6)
        ligne1.addWidget(btn_livrer)
        lay.addLayout(ligne1)
        lay.addWidget(_sep())

        # Patient
        nom = row.get("patient_nom", "")
        prenom = row.get("patient_prenom", "")
        lay.addWidget(_row_ic_val(
            "fa5s.user-injured",
            f"{nom} {prenom}".strip() or "Patient inconnu",
            c['text_secondary'], c['text_primary'], gras=True))

        # Verre + Cadre
        l3 = QHBoxLayout()
        l3.setSpacing(14)
        l3.addWidget(_row_ic_val("fa5s.eye",
            f"Verre : {row.get('numero_verre', '—')}"))
        l3.addWidget(_row_ic_val("fa5s.glasses",
            f"Cadre : {row.get('numero_cadre', '—')}"))
        lay.addLayout(l3)

        # Date livraison + Personnel
        l4 = QHBoxLayout()
        l4.setSpacing(14)
        nom_per = row.get("personnel_nom", "")
        pre_per = row.get("personnel_prenom", "")
        l4.addWidget(_row_ic_val("fa5s.calendar-check",
            _fmt_date(row.get("date_livraison")), c['warning'], c['warning']))
        l4.addWidget(_row_ic_val("fa5s.user-md",
            f"{nom_per} {pre_per}".strip() or "—"))
        lay.addLayout(l4)

    def _marquer_livre(self):
        try:
            ok, _ = self.ctrl.marquer_comme_livree(self.code_commande)
            if ok and self.on_livre_callback:
                self.on_livre_callback()
        except Exception as e:
            print(f"Erreur marquer livré : {e}")
