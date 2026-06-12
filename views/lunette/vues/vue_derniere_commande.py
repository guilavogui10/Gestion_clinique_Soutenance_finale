import qtawesome as qta
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from views.shared.theme_manager import theme_manager


def _c():
    return theme_manager.colors()


def _sep(couleur=None):
    c = _c()
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


def _lbl_vide(texte):
    from PySide6.QtCore import Qt
    c = _c()
    lbl = QLabel(texte)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"color:{c['text_secondary']}; font-size:11px; background:{c['bg_card']};"
    )
    return lbl


def _row_ic_val(icone_name, valeur, couleur_ic=None, couleur_val=None, gras=False):
    c = _c()
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


class VueDerniereCommande(QWidget):
    """Affiche la dernière commande de chaque patient avec toutes les informations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{_c()['bg_card']};")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 12, 16, 16)
        self._layout.setSpacing(10)

    def charger(self, commandes: list):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not commandes:
            self._layout.addWidget(
                _lbl_vide("Aucune commande enregistrée sur cette session"))
            self._layout.addStretch()
            return

        # Dédoublonner : garder la plus récente par patient
        recents = {}
        for cmd in commandes:
            cle = cmd.get("code_visite") or cmd.get("patient_nom", "")
            if cle not in recents:
                recents[cle] = cmd

        c = _c()
        info = QLabel(
            f"{len(recents)} patient(s) · dernière commande par patient")
        info.setStyleSheet(
            f"color:{c['primary']}; font-size:11px; font-weight:700;"
            f"background:{c['success_bg']}; border-radius:8px; padding:6px 10px;"
            f"border:1px solid {c['primary']}33;"
        )
        self._layout.addWidget(info)

        for cmd in recents.values():
            self._layout.addWidget(self._carte_complete(cmd))

        self._layout.addStretch()

    def _carte_complete(self, cmd: dict) -> QFrame:
        """Carte avec toutes les informations de la commande en disposition horizontale."""
        c = _c()
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame{{background:{c['bg_card']}; border-radius:12px;"
            f"border:1px solid {c['border']};}}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)

        # Ligne 1 : En-tête avec patient + code commande
        l1 = QHBoxLayout()
        nom = cmd.get("patient_nom", "")
        prenom = cmd.get("patient_prenom", "")
        nom_lbl = QLabel(f"{nom} {prenom}".strip() or "—")
        nom_lbl.setStyleSheet(
            f"color:{c['text_primary']}; font-size:13px; font-weight:700;"
            f"background:{c['bg_card']}; border:none;"
        )
        code = cmd.get("commande_code") or cmd.get("code", "—")
        code_lbl = QLabel(f"#{code}")
        code_lbl.setStyleSheet(
            f"color:{c['primary']}; font-size:10px; font-weight:700;"
            f"background:{c['success_bg']}; border-radius:6px;"
            f"padding:3px 8px; border:none;"
        )
        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.user", color=c['primary']).pixmap(QSize(14, 14)))
        ic.setStyleSheet(f"background:{c['bg_card']}; border:none;")
        l1.addWidget(ic)
        l1.addSpacing(6)
        l1.addWidget(nom_lbl)
        l1.addStretch()
        l1.addWidget(code_lbl)
        lay.addLayout(l1)
        lay.addWidget(_sep())

        # Ligne 2 : Informations lunettes (Verre + Cadre) en horizontal
        l2 = QHBoxLayout()
        l2.setSpacing(20)
        l2.addWidget(_row_ic_val("fa5s.eye",
            f"Verre : {cmd.get('numero_verre', '—')}", gras=True))
        l2.addWidget(_row_ic_val("fa5s.glasses",
            f"Cadre : {cmd.get('numero_cadre', '—')}", gras=True))
        l2.addStretch()
        lay.addLayout(l2)

        # Ligne 3 : Dates (Commande + Livraison) en horizontal
        l3 = QHBoxLayout()
        l3.setSpacing(20)
        l3.addWidget(_row_ic_val("fa5s.calendar-plus",
            f"Commandé : {_fmt_date(cmd.get('date_commande'))}"))
        l3.addWidget(_row_ic_val("fa5s.calendar-check",
            f"Livraison : {_fmt_date(cmd.get('date_livraison'))}", c['warning'], c['warning']))
        l3.addStretch()
        lay.addLayout(l3)

        # Ligne 4 : Prix + Personnel + Statut en horizontal
        l4 = QHBoxLayout()
        l4.setSpacing(20)
        
        # Prix
        prix = cmd.get("prix", 0)
        if prix:
            l4.addWidget(_row_ic_val("fa5s.money-bill-wave",
                f"Prix : {float(prix):,.0f} GNF", c['primary'], c['primary'], gras=True))
        
        # Personnel
        nom_per = cmd.get("personnel_nom", "")
        pre_per = cmd.get("personnel_prenom", "")
        if nom_per or pre_per:
            l4.addWidget(_row_ic_val("fa5s.user-md",
                f"Personnel : {nom_per} {pre_per}".strip()))
        
        # Statut
        statut = cmd.get("statut", "")
        if statut:
            couleur_statut = c['warning'] if statut == "attente" else c['primary']
            l4.addWidget(_row_ic_val("fa5s.info-circle",
                f"Statut : {statut}", couleur_statut, couleur_statut))
        
        l4.addStretch()
        lay.addLayout(l4)

        return frame
