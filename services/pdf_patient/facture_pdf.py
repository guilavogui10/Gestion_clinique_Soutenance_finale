from fpdf import FPDF
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os


class FacturePatientPDFService:
    """
    Génération PDF pour la facture patient (format FPDF compact).
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

        if logo:
            try:
                pdf.image(logo, x=10, y=8, w=18)
            except Exception:
                pass

        pdf.set_font(font_name, "B", 13)
        pdf.set_xy(32, 8)
        pdf.cell(0, 6, nom, ln=1)
        pdf.set_font(font_name, "", 9)
        pdf.set_x(32)
        pdf.cell(0, 5, adresse, ln=1)

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

        pdf.set_draw_color(*vert_fonce)
        pdf.rect(x_left, y, w, h)
        pdf.set_font(font_name, "B", 9)
        pdf.set_xy(x_left + 2, y + 2)
        pdf.cell(w - 4, 4, "ETABLISSEMENT")
        pdf.set_font(font_name, "", 8)
        pdf.set_xy(x_left + 2, y + 7)
        pdf.cell(w - 4, 4, str(patient.get("cabinet", "Hôpital / Clinique")))

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
        total_w = sum(col_widths) if col_widths else 0
        if total_w <= 0:
            return y
        scale = w / total_w
        widths = [max(8, cw * scale) for cw in col_widths]
        if len(widths) > 1:
            widths[-1] = w - sum(widths[:-1])
        else:
            widths[0] = w
        header_h = 6
        line_h = 4.5
        title_h = 6
        box_h = title_h + header_h + 2
        vert_fonce = (0, 63, 32)

        pdf.set_fill_color(*vert_fonce)
        pdf.set_text_color(255, 255, 255)
        pdf.rect(x, y, w, title_h, style="F")
        pdf.set_font(font_name, "B", 8)
        pdf.set_xy(x + 2, y + 1)
        pdf.cell(w - 4, 4, title.upper())

        pdf.set_fill_color(235, 242, 236)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_name, "B", 7)
        pdf.set_xy(x, y + title_h)
        for i, h in enumerate(headers):
            pdf.cell(widths[i], header_h, h, 1, 0, "C", True)
        pdf.ln(header_h)

        pdf.set_font(font_name, "", 7)
        y_cursor = pdf.get_y()
        for row in rows:
            cell_lines = []
            max_lines = 1
            for i, cell in enumerate(row):
                lines = FacturePatientPDFService._wrap_text(pdf, cell, widths[i] - 2)
                cell_lines.append(lines)
                max_lines = max(max_lines, len(lines))
            row_h = (max_lines * line_h) + 2

            x_cursor = x
            for i, lines in enumerate(cell_lines):
                align = "L" if i == 0 else "C"
                pdf.rect(x_cursor, y_cursor, widths[i], row_h)
                pdf.set_xy(x_cursor + 1, y_cursor + 1)
                pdf.multi_cell(widths[i] - 2, line_h, "\n".join(lines), border=0, align=align)
                x_cursor += widths[i]

            y_cursor += row_h
            pdf.set_xy(x, y_cursor)
            box_h += row_h

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

            FacturePatientPDFService._draw_header(pdf, controller, "Facture", font_name)
            FacturePatientPDFService._draw_info_boxes(pdf, font_name, facture, patient)

            page_w = pdf.w
            margin = 10
            gap = 8
            col_w = (page_w - (2 * margin) - gap) / 2
            x_left = margin
            x_right = margin + col_w + gap
            y_left = pdf.get_y()
            y_right = pdf.get_y()

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
                consult_rows, [36, 24, 14, 22], font_name
            )

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
                presc_rows, [44, 12, 16, 18], font_name
            )

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
                exam_rows, [44, 14, 22], font_name
            )

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
                chir_rows, [46, 16, 26], font_name
            )

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
                lun_rows, [46, 16, 26], font_name
            )

            y_bottom = max(y_left, y_right) + 2
            resume = details.get("resume", {})
            FacturePatientPDFService._draw_patient_box(pdf, x_left, y_bottom, col_w, patient, font_name)
            FacturePatientPDFService._draw_resume_box(pdf, x_right, y_bottom, col_w, resume, font_name)

            pdf.output(chemin_fichier)
            return True, "PDF généré avec succès."
        except Exception as e:
            return False, f"Erreur génération PDF : {e}"


class PDFFactureHistoriquePatient:
    """
    Service pour générer la facture depuis l'historique patient.
    Affiche tous les actes du panier dans un format élégant avec cadres (ReportLab).
    """

    @staticmethod
    def _obtenir_valeur(obj, cle, valeur_par_defaut=''):
        if isinstance(obj, dict):
            return obj.get(cle, valeur_par_defaut)
        else:
            return getattr(obj, cle, valeur_par_defaut)

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
        return "N/A"

    @staticmethod
    def _medecin(nom, prenom) -> str:
        nom = (nom or "").strip()
        prenom = (prenom or "").strip()
        if nom or prenom:
            return f"Dr {prenom} {nom}".strip()
        return "N/A"

    @staticmethod
    def dessiner_entete_et_fond(c, width, height, info_cabinet):
        nom_clinique = info_cabinet.get("nom_cabinet", "CLINIQUE")
        adresse_clinique = info_cabinet.get("adresse_cabinet", "")
        logo_path = info_cabinet.get("logo")
        if not logo_path and "logo_url" in info_cabinet:
            logo_path = info_cabinet["logo_url"]

        bleu_medical = colors.Color(0.15, 0.38, 0.93)

        c.setFillColor(bleu_medical)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.6*cm, height - 1.1*cm, nom_clinique.upper())

        c.setFillColor(colors.black)
        c.setFont("Helvetica", 7)
        c.drawString(0.6*cm, height - 1.5*cm, adresse_clinique)

        if logo_path and os.path.exists(logo_path):
            c.drawImage(logo_path, width - 2*cm, height - 2*cm, width=1.3*cm, height=1.3*cm, mask='auto')

        c.setStrokeColor(bleu_medical)
        c.setLineWidth(1.5)
        c.line(0.6*cm, height - 2.3*cm, width - 0.6*cm, height - 2.3*cm)

    @staticmethod
    def generer_facture_pdf(details: dict, info_cabinet: dict, chemin_pdf=None) -> str:
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="facture_historique_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4,
                                rightMargin=1*cm, leftMargin=1*cm,
                                topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        elements = []

        titre_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1,
            textColor=colors.Color(0.15, 0.38, 0.93)
        )
        elements.append(Paragraph("FACTURE DÉTAILLÉE DU PATIENT", titre_style))
        elements.append(Spacer(1, 0.2*cm))

        date_style = ParagraphStyle('DateStyle', parent=styles['Normal'],
                                    fontSize=10, alignment=2, textColor=colors.gray)
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'],
                                    fontSize=9, spaceAfter=4, leading=12)
        label_style = ParagraphStyle('LabelStyle', parent=styles['Normal'],
                                     fontSize=8, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2)
        section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'],
                                       fontSize=11, spaceAfter=8,
                                       textColor=colors.Color(0.15, 0.38, 0.93),
                                       fontName='Helvetica-Bold')

        facture = details.get("facture", {})
        patient = details.get("patient", {})

        patient_nom = patient.get("nom", "N/A")
        patient_prenom = patient.get("prenom", "N/A")
        patient_telephone = patient.get("telephone", "N/A")
        patient_adresse = patient.get("adresse", "N/A")
        patient_naissance = PDFFactureHistoriquePatient._fmt_date(patient.get("naissance"))

        code_facture = facture.get('code_facture', 'N/A')
        date_facture = PDFFactureHistoriquePatient._fmt_date(facture.get('date_facture'))
        statut_facture = facture.get('statut_facture', 'N/A')

        frame_patient = Table([
            [Paragraph("INFORMATIONS PATIENT", section_style)],
            [Table([
                [Paragraph("<b>Nom</b>", label_style), Paragraph(str(patient_nom), info_style)],
                [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(patient_prenom), info_style)],
                [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
                [Paragraph("<b>Adresse</b>", label_style), Paragraph(str(patient_adresse), info_style)],
                [Paragraph("<b>Naissance</b>", label_style), Paragraph(str(patient_naissance), info_style)]
            ], colWidths=[2.5*cm, 6*cm])]
        ], colWidths=[9*cm])

        frame_facture = Table([
            [Paragraph("DÉTAILS FACTURE", section_style)],
            [Table([
                [Paragraph("<b>Code Facture</b>", label_style), Paragraph(str(code_facture), info_style)],
                [Paragraph("<b>Date Facture</b>", label_style), Paragraph(str(date_facture), info_style)],
                [Paragraph("<b>Statut</b>", label_style), Paragraph(str(statut_facture), info_style)],
                ["", ""]
            ], colWidths=[3*cm, 5.5*cm])]
        ], colWidths=[9*cm])

        for frame in [frame_patient, frame_facture]:
            frame.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, 0), 0),
                ('RIGHTPADDING', (0, 0), (-1, 0), 0),
                ('TOPPADDING', (0, 0), (-1, 0), 0),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
                ('ROUNDEDCORNERS', [8, 8, 8, 8]),
                ('LEFTPADDING', (0, 1), (0, 1), 10),
                ('RIGHTPADDING', (0, 1), (0, 1), 10),
                ('TOPPADDING', (0, 1), (0, 1), 10),
                ('BOTTOMPADDING', (0, 1), (0, 1), 10),
            ]))
            inner_table = frame._cellvalues[1][0]
            if inner_table:
                inner_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))

        patient_personnel_table = Table(
            [[frame_patient, "", frame_facture]], colWidths=[9*cm, 0.5*cm, 9*cm]
        )
        patient_personnel_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(patient_personnel_table)
        elements.append(Spacer(1, 0.8*cm))

        def ajouter_tableau(titre, en_tetes, data_lignes, col_widths_t):
            if not data_lignes:
                return
            elements.append(Paragraph(titre, section_style))
            elements.append(Spacer(1, 0.2*cm))
            table_data = [en_tetes] + data_lignes
            t = Table(table_data, colWidths=col_widths_t)
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.98, 0.98, 0.99)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
                ('ROUNDEDCORNERS', [8, 8, 8, 8]),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.Color(0.90, 0.91, 0.93)),
                ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.Color(0.95, 0.95, 0.96)),
            ])
            t.setStyle(style)
            elements.append(t)
            elements.append(Spacer(1, 0.6*cm))

        consult_rows = []
        for c in details.get("consultations", []):
            consult_rows.append([
                Paragraph(str(c.get("diagnostique", "-")), info_style),
                Paragraph(str(c.get("resultat_consultation", "-")), info_style),
                Paragraph(PDFFactureHistoriquePatient._fmt_money(c.get("frais_consultation", 0)), info_style),
                Paragraph(PDFFactureHistoriquePatient._medecin(c.get("medecin_nom"), c.get("medecin_prenom")), info_style),
            ])
        ajouter_tableau("CONSULTATIONS", ["Diagnostic", "Résultat", "Prix", "Médecin"],
                        consult_rows, [5*cm, 4*cm, 4*cm, 5.5*cm])

        exam_rows = []
        for e in details.get("examens", []):
            exam_rows.append([
                Paragraph(str(e.get("libelle_examen", "-")), info_style),
                Paragraph(PDFFactureHistoriquePatient._fmt_money(e.get("frais_examen", 0)), info_style),
                Paragraph(PDFFactureHistoriquePatient._medecin(e.get("medecin_nom"), e.get("medecin_prenom")), info_style),
            ])
        ajouter_tableau("EXAMENS", ["Libellé", "Prix", "Médecin"],
                        exam_rows, [8*cm, 4*cm, 6.5*cm])

        chir_rows = []
        for c in details.get("chirurgies", []):
            chir_rows.append([
                Paragraph(str(c.get("libelle_chururgie", "-")), info_style),
                Paragraph(PDFFactureHistoriquePatient._fmt_money(c.get("frais_chururgie", 0)), info_style),
                Paragraph(PDFFactureHistoriquePatient._medecin(c.get("medecin_nom"), c.get("medecin_prenom")), info_style),
            ])
        ajouter_tableau("CHIRURGIES", ["Libellé", "Prix", "Médecin"],
                        chir_rows, [8*cm, 4*cm, 6.5*cm])

        lun_rows = []
        for l in details.get("lunettes", []):
            lun_rows.append([
                Paragraph(str(l.get("numero_verre", "-")), info_style),
                Paragraph(PDFFactureHistoriquePatient._fmt_money(l.get("prix", 0)), info_style),
                Paragraph(PDFFactureHistoriquePatient._medecin(l.get("medecin_nom"), l.get("medecin_prenom")), info_style),
            ])
        ajouter_tableau("COMMANDES LUNETTES", ["Numéro Verre", "Prix", "Médecin"],
                        lun_rows, [8*cm, 4*cm, 6.5*cm])

        presc_rows = []
        for p in details.get("prescriptions", []):
            montant = float(p.get("quantite_prescript", 0)) * float(p.get("prix_applique", 0))
            presc_rows.append([
                Paragraph(str(p.get("designation", "-")), info_style),
                Paragraph(str(p.get("quantite_prescript", "")), info_style),
                Paragraph(PDFFactureHistoriquePatient._fmt_money(p.get("prix_applique", 0)), info_style),
                Paragraph(PDFFactureHistoriquePatient._fmt_money(montant), info_style),
            ])
        ajouter_tableau("PRESCRIPTIONS (PHARMACIE)", ["Produit", "Qté", "Prix U.", "Montant Total"],
                        presc_rows, [8.5*cm, 2*cm, 3.5*cm, 4.5*cm])

        elements.append(Spacer(1, 0.5*cm))

        resume = details.get("resume", {})
        total_data = [
            [Paragraph("<b>Consultations</b>", info_style),
             Paragraph(PDFFactureHistoriquePatient._fmt_money(resume.get("total_consultation", 0)), info_style)],
            [Paragraph("<b>Examens</b>", info_style),
             Paragraph(PDFFactureHistoriquePatient._fmt_money(resume.get("total_examens", 0)), info_style)],
            [Paragraph("<b>Chirurgies</b>", info_style),
             Paragraph(PDFFactureHistoriquePatient._fmt_money(resume.get("total_chirurgie", 0)), info_style)],
            [Paragraph("<b>Lunettes</b>", info_style),
             Paragraph(PDFFactureHistoriquePatient._fmt_money(resume.get("total_lunettes", 0)), info_style)],
            [Paragraph("<b>Prescriptions</b>", info_style),
             Paragraph(PDFFactureHistoriquePatient._fmt_money(resume.get("total_prescriptions", 0)), info_style)],
            [Paragraph("<b>TOTAL GÉNÉRAL TTC</b>",
                       ParagraphStyle('T', parent=styles['Normal'],
                                      fontName='Helvetica-Bold', fontSize=12,
                                      textColor=colors.Color(0.15, 0.38, 0.93))),
             Paragraph(f"<b>{PDFFactureHistoriquePatient._fmt_money(resume.get('total_facture', 0))}</b>",
                       ParagraphStyle('T2', parent=styles['Normal'],
                                      fontName='Helvetica-Bold', fontSize=12))]
        ]

        total_data_filtered = []
        for i in range(len(total_data) - 1):
            montant = list(resume.values())[i]
            if montant > 0:
                total_data_filtered.append(total_data[i])
        total_data_filtered.append(total_data[-1])

        t_total = Table(total_data_filtered, colWidths=[6*cm, 4*cm])
        t_total.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
            ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.Color(0.15, 0.38, 0.93)),
            ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.92, 0.95, 1.0)),
        ]))

        elements.append(Table([[t_total]], colWidths=[18.5*cm],
                               style=TableStyle([('ALIGN', (0, 0), (-1, -1), 'RIGHT')])))

        def ajouter_entete(canvas, doc):
            PDFFactureHistoriquePatient.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf
