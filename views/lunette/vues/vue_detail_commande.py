import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
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


class VueDetailCommande(QWidget):
    """Vue détail d'une commande affichée dans le panneau (onglet Détail)."""

    def __init__(self, ctrl, on_retour, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.on_retour = on_retour
        self.setStyleSheet(f"background:{_c()['bg_card']};")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 12, 16, 16)
        self._layout.setSpacing(12)

        # Bouton retour
        c = _c()
        btn_retour = QPushButton(
            qta.icon("fa5s.arrow-left", color=c['primary']), "  Retour aux livraisons")
        btn_retour.setFixedHeight(34)
        btn_retour.setCursor(Qt.PointingHandCursor)
        btn_retour.setStyleSheet(
            f"background:{c['success_bg']}; color:{c['primary']};"
            f"border-radius:8px; border:none; font-size:11px; font-weight:600;"
            f"padding:0 12px;"
        )
        btn_retour.clicked.connect(self.on_retour)
        self._layout.addWidget(btn_retour)

        # Placeholder
        self._corps = QWidget()
        self._corps.setStyleSheet(f"background:{_c()['bg_card']};")
        self._corps_lay = QVBoxLayout(self._corps)
        self._corps_lay.setContentsMargins(0, 0, 0, 0)
        self._corps_lay.setSpacing(12)
        self._layout.addWidget(self._corps)
        self._layout.addStretch()

    def charger(self, code_commande: str, row_apercu: dict = None):
        """Charge les données complètes et construit les blocs."""
        while self._corps_lay.count():
            item = self._corps_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        data = row_apercu or {}
        try:
            result = self.ctrl.obtenir_commande_en_attente_complete(code_commande)
            if result:
                data = result if isinstance(result, dict) else vars(result)
        except Exception:
            pass

        c = _c()

        # Bloc patient
        nom = data.get("patient_nom", "")
        prenom = data.get("patient_prenom", "")
        self._corps_lay.addWidget(self._bloc(
            "fa5s.user-injured", c['info'], "Patient", [
                ("fa5s.id-card",
                    f"{nom} {prenom}".strip() or "—", c['text_primary'], True),
                ("fa5s.phone",
                    data.get("patient_telephone", "—")),
                ("fa5s.birthday-cake",
                    data.get("patient_date_naissance", "—")),
            ]))

        # Bloc commande
        self._corps_lay.addWidget(self._bloc(
            "fa5s.glasses", c['primary'], "Détails de la Commande", [
                ("fa5s.glasses",
                    f"Cadre : {data.get('numero_cadre', '—')}"),
                ("fa5s.eye",
                    f"Verre : {data.get('numero_verre', '—')}"),
                ("fa5s.calendar-plus",
                    f"Commandé le : {_fmt_date(data.get('date_commande'))}"),
                ("fa5s.calendar-check",
                    f"Livraison prévue : {_fmt_date(data.get('date_livraison'))}",
                    c['warning'], True),
                ("fa5s.money-bill-wave",
                    f"Prix : {float(data.get('prix', 0) or 0):,.0f} GNF",
                    c['primary'], True),
            ]))

        # Bloc statuts
        statut = data.get("statut", "attente")
        facture = data.get("statut_facture", "—")
        c_stat = c['warning'] if statut == "attente" else c['success']
        self._corps_lay.addWidget(self._bloc(
            "fa5s.info-circle", c['warning'], "Statuts", [
                ("fa5s.truck", f"Livraison : {statut}", c_stat, True),
                ("fa5s.file-invoice", f"Facture : {facture}"),
            ]))

        # Bloc personnel
        nom_per = data.get("personnel_nom", "")
        prenom_per = data.get("personnel_prenom", "")
        self._corps_lay.addWidget(self._bloc(
            "fa5s.user-md", c['success'], "Personnel Responsable", [
                ("fa5s.user-md",
                    f"{nom_per} {prenom_per}".strip() or "—", c['text_primary'], True),
                ("fa5s.briefcase",
                    data.get("personnel_fonction", "—")),
            ]))

        self._corps_lay.addStretch()

    def _bloc(self, icone_name, couleur, titre, champs) -> QFrame:
        c = _c()
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame{{background:{c['bg_card']}; border-radius:12px;"
            f"border:1px solid {c['border']};}}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        hdr = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(qta.icon(icone_name, color=couleur).pixmap(QSize(13, 13)))
        ic.setStyleSheet(f"background:{c['bg_card']}; border:none;")
        tl = QLabel(titre)
        tl.setStyleSheet(
            f"color:{couleur}; font-size:11px; font-weight:700; border:none;")
        hdr.addWidget(ic)
        hdr.addSpacing(6)
        hdr.addWidget(tl)
        hdr.addStretch()
        lay.addLayout(hdr)
        lay.addWidget(_sep(c['success_bg']))

        for champ in champs:
            ic_c = champ[0]
            valeur = champ[1]
            coul = champ[2] if len(champ) > 2 else None
            gras = champ[3] if len(champ) > 3 else False
            lay.addWidget(_row_ic_val(ic_c, valeur, coul, coul, gras))

        return frame
