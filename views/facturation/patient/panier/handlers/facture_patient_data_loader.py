"""
Chargement des donnees pour facture patient.
Responsabilite : remplir combo patients et lignes panier.
"""

import qtawesome as qta


class FacturePatientDataLoader:
    """Charge patients en attente et lignes de facture."""

    def __init__(self, bleu_principal: str):
        self.bleu_principal = bleu_principal

    def charger_patients_en_attente(self, facture_ctrl, combo_visite, code_session: str) -> None:
        if not facture_ctrl:
            return
        try:
            # 1) Patients sans facture (generation)
            patients = facture_ctrl.obtenir_patients_en_attente(code_session) or []

            # 2) Factures en attente (deja generees)
            factures = []
            try:
                factures = facture_ctrl.lister_en_attente(code_session) or []
            except Exception:
                factures = []

            combo_visite.clear()
            combo_visite.addItem(
                qta.icon("fa5s.user-injured", color=self.bleu_principal),
                "  Selectionner un patient en attente...",
                None
            )

            # Index par code_visite pour eviter doublons
            seen = set()

            for p in patients:
                code_visite = p.get("code_visite", "")
                if not code_visite or code_visite in seen:
                    continue
                seen.add(code_visite)
                nom = p.get("nom", "")
                prenom = p.get("prenom", "")
                label = f"  {prenom} {nom} - {code_visite}"
                combo_visite.addItem(
                    qta.icon("fa5s.user", color=self.bleu_principal),
                    label.strip(),
                    p
                )

            # Ajouter les factures en attente (si pas deja presentes)
            for f in factures:
                code_visite = getattr(f, "get_code_visite", lambda: "")()
                if not code_visite or code_visite in seen:
                    continue
                seen.add(code_visite)
                nom = getattr(f, "nom_patient", "") or ""
                prenom = getattr(f, "prenom_patient", "") or ""
                code_facture = getattr(f, "get_code_facture", lambda: "")()
                data = {
                    "code_visite": code_visite,
                    "nom": nom,
                    "prenom": prenom,
                    "telephone": getattr(f, "get_telephone", lambda: "")(),
                    "code_facture": code_facture,
                    "date_facture": getattr(f, "get_date_facture", lambda: None)(),
                }
                label = f"  {prenom} {nom} - {code_visite} ({code_facture})"
                combo_visite.addItem(
                    qta.icon("fa5s.file-invoice-dollar", color=self.bleu_principal),
                    label.strip(),
                    data
                )
        except Exception as e:
            print(f"[FacturePatientDataLoader] Erreur chargement patients: {e}")

    def charger_lignes_facture(self, panier_ctrl, code_facture: str, add_callback) -> None:
        if not panier_ctrl or not code_facture:
            return
        try:
            lignes = panier_ctrl.lister_par_facture(code_facture) or []
            for l in lignes:
                add_callback({
                    "designation": getattr(l, "get_designation", lambda: "")(),
                    "description": getattr(l, "get_numero_reference", lambda: "")(),
                    "quantite": getattr(l, "get_quantite_facture", lambda: 1)(),
                    "prix": getattr(l, "get_prix_applique", lambda: 0.0)(),
                    "code_paniere": getattr(l, "get_code_paniere", lambda: "")(),
                })
        except Exception as e:
            print(f"[FacturePatientDataLoader] Erreur chargement lignes: {e}")
