import os
import re
import shutil
from datetime import datetime

from fpdf import FPDF
import pandas as pd

from data.dao_personnel import PersonnelDAO
from models.modele_personnel import ModelePersonnel
from parametre.dao_param import CabinetDAO


class PersonnelService:
    def __init__(self, dao=None, cabinet_dao=None):
        self.dao = dao or PersonnelDAO()
        self.cabinet_dao = cabinet_dao or CabinetDAO()
        script_dir = os.path.dirname(__file__)
        self.image_folder = os.path.normpath(
            os.path.join(script_dir, "..", "connexion", "image")
        )
        os.makedirs(self.image_folder, exist_ok=True)

    def _modele_vers_dict(self, personnel):
        if personnel is None:
            return None
        if isinstance(personnel, dict):
            return personnel
        if hasattr(personnel, "to_dict"):
            return personnel.to_dict()
        return {
            "code": personnel.get_code(),
            "nom": personnel.get_nom(),
            "prenom": personnel.get_prenom(),
            "adresse": personnel.get_adresse(),
            "date_naissance": personnel.get_date_naissance(),
            "contact": personnel.get_contact(),
            "mail": personnel.get_mail(),
            "fonction": personnel.get_fonction(),
            "photo_path": personnel.get_photo_path(),
        }

    def _modeles_vers_dicts(self, personnels):
        return [self._modele_vers_dict(personnel) for personnel in personnels]

    def _creer_modele(self, code, data, photo_nom):
        return ModelePersonnel(
            code,
            data.get("nom").strip(),
            data.get("prenom").strip(),
            data.get("adresse").strip(),
            str(data.get("date_naissance")).strip(),
            str(data.get("contact")).strip(),
            data.get("mail").strip(),
            data.get("fonction").strip(),
            photo_nom,
        )

    def _valider_nom_prenom_fonction(self, valeur):
        if not valeur or len(valeur.strip()) < 3:
            return False, "Doit contenir au moins 3 caractères."
        if not re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s'-]+$", valeur):
            return False, "Ne doit contenir que des lettres (pas de chiffres ni caractères spéciaux)."
        return True, None

    def _valider_email(self, mail):
        if not mail or "@" not in mail or (not (mail.endswith(".com") or mail.endswith(".fr") or "." in mail.split("@")[-1])):
            return False, "Email invalide (doit contenir '@' et domaine valide)."
        pattern = r"^[^@]+@[^@]+\.[^@]+$"
        if not re.match(pattern, mail):
            return False, "Email invalide."
        return True, None

    def _valider_adresse(self, adresse):
        if not adresse or len(adresse.strip()) == 0:
            return False, "Adresse requise."
        if not re.match(r"^[A-Za-z0-9À-ÖØ-öø-ÿ\s,.\-/']+$", adresse):
            return False, "Adresse contient des caractères non autorisés."
        return True, None

    def _valider_contact(self, contact):
        if not contact:
            return False, "Contact requis."
        contact_clean = re.sub(r"[^\d]", "", str(contact))
        if len(contact_clean) != 9:
            return False, "Le contact doit contenir exactement 9 chiffres."
        return True, None

    def _valider_date(self, date_str):
        if isinstance(date_str, datetime):
            return True, None
        if pd.notna(date_str) and isinstance(date_str, float):
            date_str = str(pd.to_datetime(date_str).date())
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                datetime.strptime(str(date_str), fmt)
                return True, None
            except Exception:
                continue
        return False, "Date invalide. Format attendu: YYYY-MM-DD ou DD/MM/YYYY."

    def valider_champs(self, data):
        ok, msg = self._valider_nom_prenom_fonction(data.get("nom"))
        if not ok:
            return False, f"Nom: {msg}"

        ok, msg = self._valider_nom_prenom_fonction(data.get("prenom"))
        if not ok:
            return False, f"Prénom: {msg}"

        ok, msg = self._valider_nom_prenom_fonction(data.get("fonction"))
        if not ok:
            return False, f"Fonction: {msg}"

        ok, msg = self._valider_email(data.get("mail"))
        if not ok:
            return False, f"Email: {msg}"

        ok, msg = self._valider_adresse(data.get("adresse"))
        if not ok:
            return False, f"Adresse: {msg}"

        ok, msg = self._valider_contact(data.get("contact"))
        if not ok:
            return False, f"Contact: {msg}"

        ok, msg = self._valider_date(data.get("date_naissance"))
        if not ok:
            return False, f"Date de naissance: {msg}"

        return True, None

    def _copier_photo_et_retourner_nom(self, source_path):
        if not source_path:
            return None, "Aucun chemin photo fourni."
        if not os.path.exists(source_path):
            return None, f"Fichier photo introuvable: {source_path}"
        try:
            filename = os.path.basename(source_path)
            dest = os.path.join(self.image_folder, filename)
            if os.path.exists(dest):
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{name}_{timestamp}{ext}"
                dest = os.path.join(self.image_folder, filename)
            shutil.copy2(source_path, dest)
            return filename, None
        except Exception as e:
            return None, f"Erreur copie photo: {e}"

    def ajouter_personnel(self, data):
        valid, msg = self.valider_champs(data)
        if not valid:
            return False, msg

        photo_nom = None
        if data.get("photo_path"):
            photo_nom, err = self._copier_photo_et_retourner_nom(data["photo_path"])
            if err:
                return False, err

        code = self.dao.generer_nouveau_code()
        personnel = self._creer_modele(code, data, photo_nom)
        ok = self.dao.enregistrer_personnel(personnel)
        if ok:
            return True, f"Personnel enregistré avec code {code}."
        return False, "Erreur lors de l'enregistrement en base."

    def modifier_personnel(self, code, data):
        existing = self.dao.obtenir_par_code(code)
        if not existing:
            return False, "Personnel introuvable."

        valid, msg = self.valider_champs(data)
        if not valid:
            return False, msg

        photo_nom = existing.get_photo_path()
        if data.get("photo_path"):
            photo_nom_new, err = self._copier_photo_et_retourner_nom(data["photo_path"])
            if err:
                return False, err
            photo_nom = photo_nom_new

        personnel = self._creer_modele(code, data, photo_nom)
        ok = self.dao.modifier_personnel(personnel)
        if ok:
            return True, "Personnel mis à jour."
        return False, "Erreur mise à jour en base."

    def supprimer_par_mail(self, mail):
        ok = self.dao.supprimer_par_mail(mail)
        if ok:
            return True, "Personnel supprimé."
        return False, "Aucun personnel supprimé (mail introuvable)."

    def rechercher(self, critere):
        return self.dao.rechercher(critere)

    def lister_tout(self):
        return self.dao.lister_tout()

    def nombre_total(self):
        return self.dao.nombre_total()

    def obtenir_par_code(self, code):
        return self.dao.obtenir_par_code(code)

    def obtenir_par_mail(self, mail):
        personnels = self.dao.rechercher(mail)
        mail_normalise = (mail or "").strip().lower()
        for personnel in personnels:
            if (personnel.get_mail() or "").strip().lower() == mail_normalise:
                return personnel
        return None

    def get_personnel_stats(self):
        personnels = self.dao.lister_tout()
        total = len(personnels)
        avec_photo = sum(1 for p in personnels if p.get_photo_path())
        sans_photo = total - avec_photo
        return {
            "total": total,
            "avec_photo": avec_photo,
            "sans_photo": sans_photo,
        }

    def get_cabinet_info(self):
        info = self.cabinet_dao.get_info_cabinet() or {}

        nom_cabinet = info.get("nom_cabinet", "Cabinet Ophtalmologique")
        adresse = info.get("adresse", "")
        logo = info.get("logo")

        final_logo = None
        if logo:
            script = os.path.dirname(__file__)
            path = os.path.normpath(os.path.join(script, "..", "connexion", "image", logo))
            if os.path.exists(path):
                final_logo = path

        return {
            "nom_cabinet": nom_cabinet,
            "adresse_cabinet": adresse,
            "logo_url": final_logo,
        }

    def _get_personnel_for_printing_data(self):
        info = self.cabinet_dao.get_info_cabinet() or {}
        nom_cabinet = info.get("nom_cabinet", "Cabinet Ophtalmologique")
        adresse = info.get("adresse", "")
        logo = info.get("logo")

        final_logo = None
        if logo:
            script = os.path.dirname(__file__)
            path = os.path.normpath(os.path.join(script, "..", "connexion", "image", logo))
            if os.path.exists(path):
                final_logo = path

        entete = {
            "nom_cabinet": nom_cabinet,
            "adresse_cabinet": adresse,
            "logo_url": final_logo,
            "titre": "Liste Complète du Personnel",
            "date_heure": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        personnels = self._modeles_vers_dicts(self.dao.lister_tout())
        return entete, personnels

    def generer_liste_pdf(self, chemin_fichier):
        if not chemin_fichier:
            return False, "Chemin PDF non spécifié."
        try:
            entete, personnels = self._get_personnel_for_printing_data()
            if not personnels:
                return False, "Aucun personnel à imprimer."

            pdf = FPDF()
            pdf.add_page()
            if entete["logo_url"]:
                try:
                    pdf.image(entete["logo_url"], x=10, y=8, w=30)
                except Exception:
                    pass

            pdf.set_font("Arial", "B", 16)
            pdf.set_xy(50, 10)
            pdf.cell(0, 5, entete["nom_cabinet"], ln=True, align="C")

            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 10, entete["adresse_cabinet"], ln=True, align="C")
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, entete["titre"], ln=True, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, entete["date_heure"], ln=True, align="C")
            pdf.ln(5)

            col_widths = [30, 35, 35, 50, 40]
            pdf.set_font("Arial", "B", 10)
            pdf.cell(col_widths[0], 10, "Code", 1, 0, "C")
            pdf.cell(col_widths[1], 10, "Nom", 1, 0, "C")
            pdf.cell(col_widths[2], 10, "Prénom", 1, 0, "C")
            pdf.cell(col_widths[3], 10, "Email", 1, 0, "C")
            pdf.cell(col_widths[4], 10, "Contact", 1, 1, "C")

            pdf.set_font("Arial", "", 9)
            for personnel in personnels:
                pdf.cell(col_widths[0], 8, str(personnel.get("code", ""))[:12], 1, 0)
                pdf.cell(col_widths[1], 8, str(personnel.get("nom", ""))[:30], 1, 0)
                pdf.cell(col_widths[2], 8, str(personnel.get("prenom", ""))[:30], 1, 0)
                pdf.cell(col_widths[3], 8, str(personnel.get("mail", ""))[:40], 1, 0)
                pdf.cell(col_widths[4], 8, str(personnel.get("contact", ""))[:15], 1, 1)

            pdf.output(chemin_fichier)
            return True, f"PDF généré : {chemin_fichier}"
        except Exception as e:
            return False, f"Erreur génération PDF liste: {e}"

    def generer_carte_membre_pdf(self, code_personnel, chemin_fichier, couleur_hex="#2E86C1"):
        if not chemin_fichier:
            return False, "Chemin PDF non spécifié."
        try:
            personnel = self.obtenir_par_code(code_personnel)
            if not personnel:
                return False, "Personnel introuvable."

            p = self._modele_vers_dict(personnel)
            info = self.get_cabinet_info()
            nom_cabinet = info.get("nom_cabinet", "Cabinet Ophtalmologique")
            adresse_cabinet = info.get("adresse_cabinet", "")
            final_logo = info.get("logo_url")

            pdf = FPDF(orientation="L", unit="mm", format="A4")
            pdf.add_page()
            pdf.set_auto_page_break(False)

            def hex_to_rgb(h):
                h = (h or "").lstrip("#")
                if len(h) != 6:
                    return 46, 134, 193
                return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

            def mix(c1, c2, ratio):
                return tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))

            def draw_gradient_rect(x, y, w, h, start_rgb, end_rgb, steps=32):
                step_h = h / steps
                for i in range(steps):
                    color = mix(start_rgb, end_rgb, i / max(steps - 1, 1))
                    pdf.set_fill_color(*color)
                    pdf.rect(x, y + i * step_h, w, step_h + 0.3, style="F")

            def draw_rays(x, y, w, h):
                origin_x = x + 4
                origin_y = y + 6
                pdf.set_draw_color(214, 242, 255)
                for offset in range(-10, 28, 2):
                    pdf.line(origin_x, origin_y, x + w, y + max(0, offset))
                for offset in range(8, 48, 2):
                    pdf.line(origin_x, origin_y, x + offset, y + h)

            def draw_card_shell(x, y, w, h):
                pdf.set_fill_color(200, 208, 218)
                pdf.rect(x + 2.2, y + 2.6, w, h, style="F")
                draw_gradient_rect(x, y, w, h, (207, 244, 255), (255, 255, 255))
                draw_rays(x, y, w, h)
                pdf.set_fill_color(101, 208, 242)
                pdf.rect(x, y + h - 6, w, 6, style="F")
                pdf.set_draw_color(128, 221, 247)
                pdf.set_line_width(0.6)
                pdf.rect(x, y, w, h)
                pdf.set_draw_color(255, 255, 255)
                pdf.set_line_width(0.25)
                pdf.line(x + 2, y + h - 6.2, x + w - 2, y + h - 6.2)

            def add_logo_or_title(x, y, w, h):
                if final_logo and os.path.exists(final_logo):
                    try:
                        pdf.image(final_logo, x=x, y=y, w=w, h=h)
                        return
                    except Exception:
                        pass
                pdf.set_xy(x, y + 1)
                pdf.set_text_color(0, 143, 213)
                pdf.set_font("Arial", "B", 16)
                pdf.cell(w, 6, "OP", align="C")

            def draw_flag(x, y, w=10, h=6):
                stripe_w = w / 3
                pdf.set_fill_color(206, 17, 38)
                pdf.rect(x, y, stripe_w, h, style="F")
                pdf.set_fill_color(252, 209, 22)
                pdf.rect(x + stripe_w, y, stripe_w, h, style="F")
                pdf.set_fill_color(0, 150, 57)
                pdf.rect(x + (2 * stripe_w), y, stripe_w, h, style="F")
                pdf.set_draw_color(255, 255, 255)
                pdf.set_line_width(0.2)
                pdf.rect(x, y, w, h)

            def draw_photo_box(x, y, w, h):
                pdf.set_fill_color(255, 255, 255)
                pdf.rect(x, y, w, h, style="F")
                pdf.set_draw_color(108, 226, 242)
                pdf.set_line_width(0.8)
                pdf.rect(x, y, w, h)

                photo_nom = p.get("photo_path")
                if photo_nom:
                    photo_path = os.path.join(self.image_folder, photo_nom)
                    if os.path.exists(photo_path):
                        try:
                            pdf.image(photo_path, x=x + 1.5, y=y + 1.5, w=w - 3, h=h - 3)
                            return
                        except Exception:
                            pass

                pdf.set_fill_color(232, 236, 240)
                pdf.rect(x + 1.5, y + 1.5, w - 3, h - 3, style="F")
                pdf.set_fill_color(198, 204, 210)
                pdf.ellipse(x + 7, y + 5, 10, 10, style="F")
                pdf.ellipse(x + 5.5, y + 15, 13, 10, style="F")

            def write_pair(label, value, x, y, label_w=17, value_w=34):
                pdf.set_xy(x, y)
                pdf.set_font("Arial", "B", 6.8)
                pdf.set_text_color(60, 84, 104)
                pdf.cell(label_w, 3.7, f"{label}:")
                pdf.set_font("Arial", "", 6.6)
                pdf.set_text_color(22, 33, 44)
                text = str(value or "")[:46]
                pdf.multi_cell(value_w, 3.7, text)

            front_x, front_y = 28, 54
            back_x, back_y = 120, 34
            card_w, card_h = 86, 54

            pdf.set_fill_color(245, 245, 245)
            pdf.rect(0, 0, 297, 210, style="F")

            draw_card_shell(front_x, front_y, card_w, card_h)
            add_logo_or_title(front_x + 27, front_y + 5, 28, 12)
            pdf.set_xy(front_x + 9, front_y + 16)
            pdf.set_text_color(199, 42, 62)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(card_w - 18, 4, nom_cabinet[:28].upper(), align="C")
            pdf.set_xy(front_x + 10, front_y + 21)
            pdf.set_text_color(95, 119, 137)
            pdf.set_font("Arial", "", 5.5)
            pdf.cell(card_w - 20, 3, "ASSOCIATION / ETABLISSEMENT", align="C")
            pdf.set_xy(front_x + 8, front_y + 29)
            pdf.set_text_color(22, 88, 176)
            pdf.set_font("Arial", "B", 13)
            pdf.cell(card_w - 16, 6, "CARTE DE MEMBRE", align="C")
            pdf.set_xy(front_x + 10, front_y + 37)
            pdf.set_font("Arial", "B", 8)
            pdf.set_text_color(19, 119, 166)
            pdf.cell(card_w - 20, 4, p.get("code", ""), align="C")
            pdf.set_xy(front_x + 6, front_y + card_h - 4.8)
            pdf.set_font("Arial", "B", 5.8)
            pdf.set_text_color(208, 46, 64)
            pdf.cell(24, 3, "ID CARD")
            pdf.set_xy(front_x + card_w - 28, front_y + card_h - 4.8)
            pdf.cell(22, 3, datetime.now().strftime("%d/%m/%Y"), align="R")

            draw_card_shell(back_x, back_y, card_w, card_h)
            draw_flag(back_x + 4, back_y + 5.5)
            pdf.set_xy(back_x + 16, back_y + 5.2)
            pdf.set_text_color(55, 93, 126)
            pdf.set_font("Arial", "B", 5.5)
            pdf.cell(46, 3, "REPUBLIQUE DEMOCRATIQUE DE GUINEE")
            pdf.set_xy(back_x + 16, back_y + 9.2)
            pdf.set_text_color(25, 91, 176)
            pdf.set_font("Arial", "B", 10.8)
            pdf.cell(38, 5, "CARTE DE MEMBRE")
            add_logo_or_title(back_x + 67, back_y + 3.5, 13, 8)

            pdf.set_draw_color(102, 216, 241)
            pdf.set_line_width(0.45)
            pdf.line(back_x + 4, back_y + 14.5, back_x + 82, back_y + 14.5)

            draw_photo_box(back_x + 60.5, back_y + 16.5, 19, 25.5)

            full_name = f"{p.get('nom', '').upper()} {p.get('prenom', '').upper()}".strip()
            write_pair("Nom", full_name, back_x + 4.5, back_y + 17.3)
            write_pair("Fonction", p.get("fonction", ""), back_x + 4.5, back_y + 22.2)
            write_pair("Contact", p.get("contact", ""), back_x + 4.5, back_y + 27.1)
            write_pair("Email", p.get("mail", ""), back_x + 4.5, back_y + 32.0)
            write_pair("Naissance", p.get("date_naissance", ""), back_x + 4.5, back_y + 36.9)
            write_pair("Adresse", p.get("adresse", ""), back_x + 4.5, back_y + 41.8, label_w=17, value_w=36)

            pdf.set_xy(back_x + 61.5, back_y + 43.4)
            pdf.set_text_color(120, 140, 160)
            pdf.set_font("Arial", "I", 5.6)
            pdf.cell(17, 3, "Signature", align="C")

            pdf.set_xy(back_x + 4, back_y + card_h - 4.8)
            pdf.set_text_color(12, 110, 167)
            pdf.set_font("Arial", "B", 6.2)
            pdf.cell(38, 3, f"ID: {p.get('code', '')}")
            pdf.set_text_color(208, 46, 64)
            pdf.cell(40, 3, "CARTE OFFICIELLE", align="R")

            pdf.output(chemin_fichier)
            return True, f"Carte générée : {chemin_fichier}"
        except Exception as e:
            return False, f"Erreur génération carte: {e}"

    def export_to_csv(self, chemin_fichier):
        try:
            data = self._modeles_vers_dicts(self.dao.lister_tout())
            if not data:
                return False, "Aucun personnel à exporter."
            pd.DataFrame(data).to_csv(chemin_fichier, index=False)
            return True, f"Export CSV réalisé: {chemin_fichier}"
        except Exception as e:
            return False, f"Erreur export CSV: {e}"

    def import_from_csv(self, chemin_fichier, action_si_existant="skip"):
        try:
            df = pd.read_csv(chemin_fichier)
            if df.empty:
                return False, "Fichier CSV vide."
            count = 0
            for _, row in df.iterrows():
                data = {
                    "nom": str(row.get("nom", "")).strip(),
                    "prenom": str(row.get("prenom", "")).strip(),
                    "adresse": str(row.get("adresse", "")).strip(),
                    "date_naissance": str(row.get("date_naissance", "")).strip(),
                    "contact": str(row.get("contact", "")).strip(),
                    "mail": str(row.get("mail", "")).strip(),
                    "fonction": str(row.get("fonction", "")).strip(),
                    "photo_path": row.get("photo_path"),
                }
                valid, _ = self.valider_champs(data)
                if not valid:
                    continue
                if data.get("photo_path") and pd.notna(data.get("photo_path")):
                    photo_nom, _ = self._copier_photo_et_retourner_nom(data["photo_path"])
                    data["photo_path"] = photo_nom if photo_nom else None

                code = row.get("code")
                code = str(code).strip() if pd.notna(code) else None
                if code and self.dao.obtenir_par_code(code):
                    if action_si_existant == "update":
                        ok, _ = self.modifier_personnel(code, data)
                        if ok:
                            count += 1
                    continue

                ok, _ = self.ajouter_personnel(data)
                if ok:
                    count += 1
            return True, f"Import CSV terminé. {count} enregistrements importés."
        except Exception as e:
            return False, f"Erreur import CSV: {e}"

    def export_to_excel(self, chemin_fichier):
        try:
            data = self._modeles_vers_dicts(self.dao.lister_tout())
            if not data:
                return False, "Aucun personnel à exporter."
            pd.DataFrame(data).to_excel(chemin_fichier, index=False)
            return True, f"Export Excel réalisé: {chemin_fichier}"
        except Exception as e:
            return False, f"Erreur export Excel: {e}"

    def import_from_excel(self, chemin_fichier, action_si_existant="skip"):
        try:
            df = pd.read_excel(chemin_fichier)
            if df.empty:
                return False, "Fichier Excel vide."
            count = 0
            for _, row in df.iterrows():
                data = {
                    "nom": str(row.get("nom", "")).strip(),
                    "prenom": str(row.get("prenom", "")).strip(),
                    "adresse": str(row.get("adresse", "")).strip(),
                    "date_naissance": str(row.get("date_naissance", "")).strip(),
                    "contact": str(row.get("contact", "")).strip(),
                    "mail": str(row.get("mail", "")).strip(),
                    "fonction": str(row.get("fonction", "")).strip(),
                    "photo_path": row.get("photo_path"),
                }
                valid, _ = self.valider_champs(data)
                if not valid:
                    continue
                if data.get("photo_path") and pd.notna(data.get("photo_path")):
                    photo_nom, _ = self._copier_photo_et_retourner_nom(data["photo_path"])
                    data["photo_path"] = photo_nom if photo_nom else None

                code = row.get("code")
                code = str(code).strip() if pd.notna(code) else None
                if code and self.dao.obtenir_par_code(code):
                    if action_si_existant == "update":
                        ok, _ = self.modifier_personnel(code, data)
                        if ok:
                            count += 1
                    continue

                ok, _ = self.ajouter_personnel(data)
                if ok:
                    count += 1
            return True, f"Import Excel terminé. {count} enregistrements importés."
        except Exception as e:
            return False, f"Erreur import Excel: {e}"
