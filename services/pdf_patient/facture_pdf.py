from fpdf import FPDF
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os




class FacturePatientPDFService:
    """
    Service pour générer la facture détaillée du patient avec ReportLab.
    Affiche tous les actes du panier dans un format élégant avec cadres.
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
                                topMargin=3*cm, bottomMargin=1.5*cm)
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
        patient_naissance = FacturePatientPDFService._fmt_date(patient.get("naissance"))

        code_facture = facture.get('code_facture', 'N/A')
        date_facture = FacturePatientPDFService._fmt_date(facture.get('date_facture'))
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
            
            titre_para = Paragraph(titre, section_style)
            spacer_avant = Spacer(1, 0.2*cm)
            table_data = [en_tetes] + data_lignes
            t = Table(table_data, colWidths=col_widths_t, repeatRows=1)
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
            spacer_apres = Spacer(1, 0.6*cm)
            
            # Si le tableau a peu de lignes (<=3), garder ensemble
            # Sinon, juste le titre avec le tableau (sans forcer toutes les lignes ensemble)
            if len(data_lignes) <= 3:
                elements.append(KeepTogether([titre_para, spacer_avant, t, spacer_apres]))
            else:
                elements.append(KeepTogether([titre_para, spacer_avant]))
                elements.append(t)
                elements.append(spacer_apres)

        consult_rows = []
        for c in details.get("consultations", []):
            consult_rows.append([
                Paragraph(str(c.get("diagnostique", "-")), info_style),
                Paragraph(str(c.get("resultat_consultation", "-")), info_style),
                Paragraph(FacturePatientPDFService._fmt_money(c.get("frais_consultation", 0)), info_style),
                Paragraph(FacturePatientPDFService._medecin(c.get("medecin_nom"), c.get("medecin_prenom")), info_style),
            ])
        ajouter_tableau("CONSULTATIONS", ["Diagnostic", "Résultat", "Prix", "Médecin"],
                        consult_rows, [5*cm, 4*cm, 4*cm, 5.5*cm])

        exam_rows = []
        for e in details.get("examens", []):
            exam_rows.append([
                Paragraph(str(e.get("libelle_examen", "-")), info_style),
                Paragraph(FacturePatientPDFService._fmt_money(e.get("frais_examen", 0)), info_style),
                Paragraph(FacturePatientPDFService._medecin(e.get("medecin_nom"), e.get("medecin_prenom")), info_style),
            ])
        ajouter_tableau("EXAMENS", ["Libellé", "Prix", "Médecin"],
                        exam_rows, [8*cm, 4*cm, 6.5*cm])

        chir_rows = []
        for c in details.get("chirurgies", []):
            chir_rows.append([
                Paragraph(str(c.get("libelle_chururgie", "-")), info_style),
                Paragraph(FacturePatientPDFService._fmt_money(c.get("frais_chururgie", 0)), info_style),
                Paragraph(FacturePatientPDFService._medecin(c.get("medecin_nom"), c.get("medecin_prenom")), info_style),
            ])
        ajouter_tableau("CHIRURGIES", ["Libellé", "Prix", "Médecin"],
                        chir_rows, [8*cm, 4*cm, 6.5*cm])

        lun_rows = []
        for l in details.get("lunettes", []):
            lun_rows.append([
                Paragraph(str(l.get("numero_verre", "-")), info_style),
                Paragraph(FacturePatientPDFService._fmt_money(l.get("prix", 0)), info_style),
                Paragraph(FacturePatientPDFService._medecin(l.get("medecin_nom"), l.get("medecin_prenom")), info_style),
            ])
        ajouter_tableau("COMMANDES LUNETTES", ["Numéro Verre", "Prix", "Médecin"],
                        lun_rows, [8*cm, 4*cm, 6.5*cm])

        presc_rows = []
        for p in details.get("prescriptions", []):
            montant = float(p.get("quantite_prescript", 0)) * float(p.get("prix_applique", 0))
            presc_rows.append([
                Paragraph(str(p.get("designation", "-")), info_style),
                Paragraph(str(p.get("quantite_prescript", "")), info_style),
                Paragraph(FacturePatientPDFService._fmt_money(p.get("prix_applique", 0)), info_style),
                Paragraph(FacturePatientPDFService._fmt_money(montant), info_style),
            ])
        ajouter_tableau("PRESCRIPTIONS (PHARMACIE)", ["Produit", "Qté", "Prix U.", "Montant Total"],
                        presc_rows, [8.5*cm, 2*cm, 3.5*cm, 4.5*cm])

        elements.append(Spacer(1, 0.5*cm))

        resume = details.get("resume", {})
        total_data = [
            [Paragraph("<b>Consultations</b>", info_style),
             Paragraph(FacturePatientPDFService._fmt_money(resume.get("total_consultation", 0)), info_style)],
            [Paragraph("<b>Examens</b>", info_style),
             Paragraph(FacturePatientPDFService._fmt_money(resume.get("total_examens", 0)), info_style)],
            [Paragraph("<b>Chirurgies</b>", info_style),
             Paragraph(FacturePatientPDFService._fmt_money(resume.get("total_chirurgie", 0)), info_style)],
            [Paragraph("<b>Lunettes</b>", info_style),
             Paragraph(FacturePatientPDFService._fmt_money(resume.get("total_lunettes", 0)), info_style)],
            [Paragraph("<b>Prescriptions</b>", info_style),
             Paragraph(FacturePatientPDFService._fmt_money(resume.get("total_prescriptions", 0)), info_style)],
            [Paragraph("<b>TOTAL GÉNÉRAL TTC</b>",
                       ParagraphStyle('T', parent=styles['Normal'],
                                      fontName='Helvetica-Bold', fontSize=12,
                                      textColor=colors.Color(0.15, 0.38, 0.93))),
             Paragraph(f"<b>{FacturePatientPDFService._fmt_money(resume.get('total_facture', 0))}</b>",
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
            FacturePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf
