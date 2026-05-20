from fpdf import FPDF
from datetime import datetime


class FacturePatientPDFService:
    """
    Génération PDF pour la facture patient.
    - Entête cabinet via controller.get_cabinet_info()
    - Détails consultation / examens / chirurgie / lunette / prescriptions
    - Résumé des coûts
    """

    @staticmethod
    def _fmt_money(value) -> str:
        try:
            return f"{float(value):,.0f} GNF".replace(",", " ")
        except Exception:
            return "0 GNF"

    @staticmethod
    def _fmt_date(value) -> str:
        if hasattr(value, "strftime"):
            return value.strftime("%d/%m/%Y")
        if value:
            return str(value)
        return "-"

    @staticmethod
    def _medecin(nom, prenom) -> str:
        nom = (nom or "").strip()
        prenom = (prenom or "").strip()
        if nom or prenom:
            return f"Dr {prenom} {nom}".strip()
        return "-"

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        text = str(text or "")
        return text if len(text) <= max_len else text[: max_len - 1] + "…"

    @staticmethod
    def _wrap_text(pdf: FPDF, text: str, max_width: float) -> list:
        """
        Coupe le texte en plusieurs lignes pour rentrer dans max_width.
        """
        text = str(text or "").strip()
        if not text:
            return [""]
        words = text.split()
        lines = []
        line = ""
        for w in words:
            test = f"{line} {w}".strip()
            if pdf.get_string_width(test) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                # Si un mot est plus long que la colonne, on le coupe
                if pdf.get_string_width(w) <= max_width:
                    line = w
                else:
                    chunk = ""
                    for ch in w:
                        test2 = f"{chunk}{ch}"
                        if pdf.get_string_width(test2) <= max_width:
                            chunk = test2
                        else:
                            if chunk:
                                lines.append(chunk)
                            chunk = ch
                    line = chunk
        if line:
            lines.append(line)
        return lines

    @staticmethod
    def _draw_header(pdf: FPDF, controller, title: str, font_name: str):
        info = controller.get_cabinet_info() if controller else {}
        nom = info.get("nom_cabinet", "Cabinet médical")
        adresse = info.get("adresse_cabinet", "")
        logo = info.get("logo_url")
        vert_fonce = (0, 63, 32)

        # Logo
        if logo:
            try:
                pdf.image(logo, x=10, y=8, w=18)
            except Exception:
                pass

        # Cabinet info
        pdf.set_font(font_name, "B", 13)
        pdf.set_xy(32, 8)
        pdf.cell(0, 6, nom, ln=1)
        pdf.set_font(font_name, "", 9)
        pdf.set_x(32)
        pdf.cell(0, 5, adresse, ln=1)

        # Title
        pdf.set_font(font_name, "B", 18)
        pdf.set_xy(150, 10)
        pdf.cell(50, 8, title.upper(), align="R")

        pdf.set_font(font_name, "", 9)
        pdf.set_xy(150, 18)
        pdf.cell(50, 5, datetime.now().strftime("%d/%m/%Y %H:%M"), align="R")

        pdf.ln(8)

    @staticmethod
    def _draw_info_boxes(pdf: FPDF, font_name: str, facture, patient):
        x_left = 10
        y = pdf.get_y()
        w = 90
        h = 18
        gap = 8
        vert_fonce = (0, 63, 32)

        # Left box: établissement
        pdf.set_draw_color(*vert_fonce)
        pdf.rect(x_left, y, w, h)
        pdf.set_font(font_name, "B", 9)
        pdf.set_xy(x_left + 2, y + 2)
        pdf.cell(w - 4, 4, "ETABLISSEMENT")
        pdf.set_font(font_name, "", 8)
        pdf.set_xy(x_left + 2, y + 7)
        pdf.cell(w - 4, 4, str(patient.get("cabinet", "Hôpital / Clinique")))

        # Right box: facture
        x_right = x_left + w + gap
        pdf.rect(x_right, y, w, h)
        pdf.set_font(font_name, "B", 8)
        pdf.set_xy(x_right + 2, y + 2)
        pdf.cell(w - 4, 4, f"FACTURE #: {facture.get('code_facture', '-')}")
        pdf.set_xy(x_right + 2, y + 7)
        pdf.cell(w - 4, 4, f"DOSSIER: {patient.get('code_patient', '-')}")
        pdf.set_xy(x_right + 2, y + 12)
        pdf.cell(w - 4, 4, f"DATE: {FacturePatientPDFService._fmt_date(facture.get('date_facture'))}")

        pdf.set_y(y + h + 6)

    @staticmethod
    def _draw_section_table(pdf: FPDF, x: float, y: float, w: float,
                            title: str, headers: list, rows: list,
                            col_widths: list, font_name: str) -> float:
        if not rows:
            return y
        # Ajuster les largeurs de colonnes pour ne jamais dépasser w
        total_w = sum(col_widths) if col_widths else 0
        if total_w <= 0:
            return y
        scale = w / total_w
        widths = [max(8, cw * scale) for cw in col_widths]
        # Recalage pour que la somme fasse exactement w
        if len(widths) > 1:
            widths[-1] = w - sum(widths[:-1])
        else:
            widths[0] = w
        header_h = 6
        line_h = 4.5
        title_h = 6
        total_rows = rows
        box_h = title_h + header_h + 2
        vert_fonce = (0, 63, 32)

        # Title bar
        pdf.set_fill_color(*vert_fonce)
        pdf.set_text_color(255, 255, 255)
        pdf.rect(x, y, w, title_h, style="F")
        pdf.set_font(font_name, "B", 8)
        pdf.set_xy(x + 2, y + 1)
        pdf.cell(w - 4, 4, title.upper())

        # Header row
        pdf.set_fill_color(235, 242, 236)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_name, "B", 7)
        pdf.set_xy(x, y + title_h)
        for i, h in enumerate(headers):
            pdf.cell(widths[i], header_h, h, 1, 0, "C", True)
        pdf.ln(header_h)

        # Rows
        pdf.set_font(font_name, "", 7)
        y_cursor = pdf.get_y()
        for row in total_rows:
            # Calculer hauteur nécessaire pour cette ligne
            cell_lines = []
            max_lines = 1
            for i, cell in enumerate(row):
                lines = FacturePatientPDFService._wrap_text(
                    pdf, cell, widths[i] - 2
                )
                cell_lines.append(lines)
                max_lines = max(max_lines, len(lines))
            row_h = (max_lines * line_h) + 2

            # Dessiner cellules + texte
            x_cursor = x
            for i, lines in enumerate(cell_lines):
                align = "L" if i == 0 else "C"
                pdf.rect(x_cursor, y_cursor, widths[i], row_h)
                pdf.set_xy(x_cursor + 1, y_cursor + 1)
                pdf.multi_cell(
                    widths[i] - 2,
                    line_h,
                    "\n".join(lines),
                    border=0,
                    align=align
                )
                x_cursor += widths[i]

            y_cursor += row_h
            pdf.set_xy(x, y_cursor)
            box_h += row_h

        # Border around section
        pdf.set_draw_color(*vert_fonce)
        pdf.rect(x, y, w, box_h)
        return y + box_h + 4

    @staticmethod
    def _draw_patient_box(pdf: FPDF, x: float, y: float, w: float,
                          patient: dict, font_name: str) -> float:
        title_h = 6
        pdf.set_fill_color(0, 63, 32)
        pdf.set_text_color(255, 255, 255)
        pdf.rect(x, y, w, title_h, style="F")
        pdf.set_font(font_name, "B", 8)
        pdf.set_xy(x + 2, y + 1)
        pdf.cell(w - 4, 4, "INFORMATIONS DU PATIENT")

        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_name, "", 7)
        line_h = 4.5
        ly = y + title_h + 2
        items = [
            ("Patient", f"{patient.get('prenom', '')} {patient.get('nom', '')}".strip()),
            ("Adresse", patient.get("adresse", "-")),
            ("Téléphone", patient.get("telephone", "-")),
            ("Naissance", FacturePatientPDFService._fmt_date(patient.get("naissance"))),
            ("Visite", patient.get("code_visite", "-")),
        ]
        max_lines_total = 0
        for label, val in items:
            lines = FacturePatientPDFService._wrap_text(pdf, val, w - 28)
            max_lines_total += max(1, len(lines))

        content_h = (max_lines_total * line_h) + 2
        h = title_h + content_h + 2

        ly = y + title_h + 2
        for label, val in items:
            pdf.set_xy(x + 2, ly)
            pdf.cell(22, line_h, f"{label}:")
            lines = FacturePatientPDFService._wrap_text(pdf, val, w - 28)
            pdf.set_xy(x + 26, ly)
            pdf.multi_cell(w - 28, line_h, "\n".join(lines), border=0, align="L")
            ly += (max(1, len(lines)) * line_h)

        pdf.set_draw_color(0, 63, 32)
        pdf.rect(x, y, w, h)
        return y + h + 4

    @staticmethod
    def _draw_resume_box(pdf: FPDF, x: float, y: float, w: float,
                         resume: dict, font_name: str) -> float:
        title_h = 6
        h = 32
        pdf.set_fill_color(0, 63, 32)
        pdf.set_text_color(255, 255, 255)
        pdf.rect(x, y, w, title_h, style="F")
        pdf.set_font(font_name, "B", 8)
        pdf.set_xy(x + 2, y + 1)
        pdf.cell(w - 4, 4, "RESUME FACTURE")

        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_name, "", 7)
        ly = y + title_h + 2
        items = []
        if resume.get("total_consultation", 0) > 0:
            items.append(("Consultation", resume.get("total_consultation", 0)))
        if resume.get("total_examens", 0) > 0:
            items.append(("Examens", resume.get("total_examens", 0)))
        if resume.get("total_chirurgie", 0) > 0:
            items.append(("Chirurgie", resume.get("total_chirurgie", 0)))
        if resume.get("total_lunettes", 0) > 0:
            items.append(("Lunettes", resume.get("total_lunettes", 0)))
        if resume.get("total_prescriptions", 0) > 0:
            items.append(("Prescriptions", resume.get("total_prescriptions", 0)))
        items.append(("TOTAL TTC", resume.get("total_facture", 0)))
        for label, val in items:
            pdf.set_xy(x + 2, ly)
            pdf.cell(w - 40, 4, label)
            pdf.set_xy(x + w - 38, ly)
            pdf.cell(36, 4, FacturePatientPDFService._fmt_money(val), align="R")
            ly += 5

        pdf.set_draw_color(0, 63, 32)
        pdf.rect(x, y, w, h)
        return y + h + 4

    @staticmethod
    def generer_facture_pdf(controller, chemin_fichier: str, details: dict):
        if not chemin_fichier:
            return False, "Chemin PDF non spécifié."
        if not details:
            return False, "Aucune donnée pour générer la facture."

        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=False)
            pdf.set_margins(10, 12, 10)

            # Police unicode si disponible
            font_name = "Helvetica"
            try:
                font_dir = "../Fonts/"
                pdf.add_font("YuGothic", "", font_dir + "YuGothM.ttc", uni=True)
                pdf.add_font("YuGothic", "B", font_dir + "YuGothB.ttc", uni=True)
                font_name = "YuGothic"
            except Exception:
                font_name = "Helvetica"

            pdf.add_page()

            facture = details.get("facture", {})
            patient = details.get("patient", {})
            consultations = details.get("consultations", [])
            examens = details.get("examens", [])
            chirurgies = details.get("chirurgies", [])
            lunettes = details.get("lunettes", [])
            prescriptions = details.get("prescriptions", [])

            # Header
            FacturePatientPDFService._draw_header(pdf, controller, "Facture", font_name)
            FacturePatientPDFService._draw_info_boxes(pdf, font_name, facture, patient)

            page_w = pdf.w
            margin = 10
            gap = 8
            col_w = (page_w - (2 * margin) - gap)
            col_w = col_w / 2
            x_left = margin
            x_right = margin + col_w + gap
            y_left = pdf.get_y()
            y_right = pdf.get_y()

            # Consultation
            consult_rows = []
            for c in consultations:
                consult_rows.append([
                    c.get("diagnostique", "-"),
                    c.get("resultat_consultation", "-"),
                    FacturePatientPDFService._fmt_money(c.get("frais_consultation", 0)),
                    FacturePatientPDFService._medecin(c.get("medecin_nom"), c.get("medecin_prenom")),
                ])
            y_left = FacturePatientPDFService._draw_section_table(
                pdf, x_left, y_left, col_w,
                "Consultation",
                ["Diagnostic", "Resultat", "Prix", "Medecin"],
                consult_rows,
                [36, 24, 14, 22],
                font_name
            )

            # Prescriptions
            presc_rows = []
            for p in prescriptions:
                montant = float(p.get("quantite_prescript", 0)) * float(p.get("prix_applique", 0))
                presc_rows.append([
                    p.get("designation", "-"),
                    str(p.get("quantite_prescript", "")),
                    FacturePatientPDFService._fmt_money(p.get("prix_applique", 0)),
                    FacturePatientPDFService._fmt_money(montant),
                ])
            y_left = FacturePatientPDFService._draw_section_table(
                pdf, x_left, y_left, col_w,
                "Prescription Produits",
                ["Produit", "Qté", "Prix", "Montant"],
                presc_rows,
                [44, 12, 16, 18],
                font_name
            )

            # Examens
            exam_rows = []
            for e in examens:
                exam_rows.append([
                    e.get("libelle_examen", "-"),
                    FacturePatientPDFService._fmt_money(e.get("frais_examen", 0)),
                    FacturePatientPDFService._medecin(e.get("medecin_nom"), e.get("medecin_prenom")),
                ])
            y_right = FacturePatientPDFService._draw_section_table(
                pdf, x_right, y_right, col_w,
                "Examens",
                ["Libelle", "Prix", "Medecin"],
                exam_rows,
                [44, 14, 22],
                font_name
            )

            # Chirurgie
            chir_rows = []
            for c in chirurgies:
                chir_rows.append([
                    c.get("libelle_chururgie", "-"),
                    FacturePatientPDFService._fmt_money(c.get("frais_chururgie", 0)),
                    FacturePatientPDFService._medecin(c.get("medecin_nom"), c.get("medecin_prenom")),
                ])
            y_right = FacturePatientPDFService._draw_section_table(
                pdf, x_right, y_right, col_w,
                "Chirurgie",
                ["Libelle", "Prix", "Medecin"],
                chir_rows,
                [46, 16, 26],
                font_name
            )

            # Lunette
            lun_rows = []
            for l in lunettes:
                lun_rows.append([
                    l.get("numero_verre", "-"),
                    FacturePatientPDFService._fmt_money(l.get("prix", 0)),
                    FacturePatientPDFService._medecin(l.get("medecin_nom"), l.get("medecin_prenom")),
                ])
            y_right = FacturePatientPDFService._draw_section_table(
                pdf, x_right, y_right, col_w,
                "Commande Lunette",
                ["Numero verre", "Prix", "Medecin"],
                lun_rows,
                [46, 16, 26],
                font_name
            )

            # Résumé + patient info
            y_bottom = max(y_left, y_right) + 2

            resume = details.get("resume", {})
            FacturePatientPDFService._draw_patient_box(pdf, x_left, y_bottom, col_w, patient, font_name)
            FacturePatientPDFService._draw_resume_box(pdf, x_right, y_bottom, col_w, resume, font_name)

            pdf.output(chemin_fichier)
            return True, "PDF généré avec succès."
        except Exception as e:
            return False, f"Erreur génération PDF : {e}"
