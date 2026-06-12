from reportlab.lib.pagesizes import A6, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import os
import tempfile


class PatientPDFService:

    @staticmethod
    def dessiner_entete_et_fond(c, width, height, info_cabinet):
        nom_clinique = info_cabinet.get("nom_cabinet", "CLINIQUE")
        adresse_clinique = info_cabinet.get("adresse_cabinet", "")
        logo_path = info_cabinet.get("logo_url")
        vert_medical = colors.Color(0, 0.4, 0.2)

        if logo_path and os.path.exists(logo_path):
            c.saveState()
            c.setFillAlpha(0.08)
            taille_fond = 7.5*cm
            c.drawImage(logo_path, (width-taille_fond)/2, (height-taille_fond)/2,
                        width=taille_fond, height=taille_fond, mask='auto')
            c.restoreState()

        if logo_path and os.path.exists(logo_path):
            c.drawImage(logo_path, 0.6*cm, height - 2*cm, width=1.3*cm, height=1.3*cm, mask='auto')

        c.setFillColor(vert_medical)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2.1*cm, height - 1.1*cm, nom_clinique.upper())

        c.setFillColor(colors.black)
        c.setFont("Helvetica", 7)
        c.drawString(2.1*cm, height - 1.5*cm, adresse_clinique)

        c.setStrokeColor(vert_medical)
        c.setLineWidth(1.5)
        c.line(0.6*cm, height - 2.3*cm, width - 0.6*cm, height - 2.3*cm)

    @staticmethod
    def generer_carnet_patient(controller, chemin_save, patient):
        try:
            info_cabinet = controller.get_cabinet_info()

            c = canvas.Canvas(chemin_save, pagesize=A6)
            width, height = A6
            vert_medical = colors.Color(0, 0.4, 0.2)

            PatientPDFService.dessiner_entete_et_fond(c, width, height, info_cabinet)

            y_pos = height - 3.5*cm
            espacement = 1.2*cm

            def draw_item(label, valeur, y):
                c.setFillColor(vert_medical)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(0.8*cm, y, f"{label.upper()}:")
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 11)
                c.drawString(0.8*cm, y - 0.5*cm, str(valeur))
                c.setDash(1, 2)
                c.setStrokeColor(colors.grey)
                c.setLineWidth(0.2)
                c.line(0.8*cm, y - 0.7*cm, width - 0.8*cm, y - 0.7*cm)
                c.setDash()

            draw_item("Identifiant", patient.get_code_patient(), y_pos)
            draw_item("Nom Complet", f"{patient.get_nom()} {patient.get_prenom()}", y_pos - espacement)
            draw_item("Date de Naissance", patient.get_naissance(), y_pos - (espacement * 2))
            draw_item("Téléphone", patient.get_telephone(), y_pos - (espacement * 3))
            draw_item("Sexe / Genre", patient.get_genre(), y_pos - (espacement * 4))
            draw_item("Adresse", patient.get_adresse(), y_pos - (espacement * 5))

            c.setFillColor(vert_medical)
            c.setFont("Helvetica-BoldOblique", 7)
            date_jour = datetime.now().strftime("%d/%m/%Y")
            c.drawString(0.6*cm, 0.6*cm, f"Fiche établie le : {date_jour}")
            c.drawRightString(width - 0.6*cm, 0.6*cm, f"© {info_cabinet.get('nom_cabinet')}")

            c.save()
            return True, "Fiche patient générée avec succès."

        except Exception as e:
            return False, f"Erreur de génération PDF : {str(e)}"

    @staticmethod
    def generer_liste_patients_par_genre(controller, chemin_save, liste_patients, genre_selectionne):
        try:
            doc = SimpleDocTemplate(
                chemin_save,
                pagesize=A4,
                rightMargin=1*cm, leftMargin=1*cm,
                topMargin=3.8*cm,
                bottomMargin=1.5*cm
            )

            elements = []
            info_cabinet = controller.get_cabinet_info()
            styles = getSampleStyleSheet()

            style_cellule = styles["BodyText"]
            style_cellule.fontSize = 8.5
            style_cellule.leading = 10

            headers = ["ID", "NOM", "PRÉNOM", "TEL", "NAISSANCE", "GENRE", "PROFESSION", "ADRESSE"]
            table_data = [headers]

            for p in liste_patients:
                table_data.append([
                    p.get_code_patient(),
                    Paragraph(p.get_nom(), style_cellule),
                    Paragraph(p.get_prenom(), style_cellule),
                    p.get_telephone(),
                    p.get_naissance(),
                    p.get_genre(),
                    Paragraph(p.get_profession(), style_cellule),
                    Paragraph(p.get_adresse(), style_cellule)
                ])

            col_widths = [1.8*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 1.4*cm, 3.2*cm, 3.8*cm]

            tableau = Table(table_data, colWidths=col_widths, repeatRows=1)
            tableau.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0, 0.4, 0.2)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke])
            ]))

            elements.append(tableau)

            def dessiner_decor_clinique(canvas, doc):
                width, height = A4
                PatientPDFService.dessiner_entete_et_fond(canvas, width, height, info_cabinet)
                canvas.setFont("Helvetica-Bold", 14)
                canvas.setFillColor(colors.Color(0, 0.4, 0.2))
                titre = f"LISTE DES PATIENTS - GENRE : {genre_selectionne.upper()}"
                canvas.drawCentredString(width/2, height - 3.1*cm, titre)

            doc.build(elements, onFirstPage=dessiner_decor_clinique, onLaterPages=dessiner_decor_clinique)
            return True, "Rapport PDF généré avec succès."

        except Exception as e:
            return False, f"Erreur Service PDF : {str(e)}"

    @staticmethod
    def generer_liste_total_patients(controller, chemin_save, liste_patients):
        """Ancienne méthode conservée pour compatibilité (sauvegarde directe)."""
        try:
            return PatientPDFService.generer_rapport_liste_patients(
                controller, liste_patients, chemin_save
            ), "Rapport PDF généré."
        except Exception as e:
            return False, f"Erreur Service PDF : {str(e)}"

    @staticmethod
    def generer_rapport_liste_patients(controller, liste_patients, chemin_pdf=None):
        """
        Génère le rapport PDF liste patients vers un fichier temporaire (ou chemin_pdf si fourni).
        Retourne le chemin du fichier PDF généré.
        Style identique au PDF consultation : bleu, titre centré, sections avec bordures.
        """
        from services.pdf_actes._base import dessiner_entete_et_fond

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="patients_rapport_")
            os.close(fd)

        info_cabinet = controller.get_cabinet_info()
        bleu = colors.Color(0.15, 0.38, 0.93)
        gris_label = colors.Color(0.42, 0.45, 0.50)

        doc = SimpleDocTemplate(
            chemin_pdf,
            pagesize=A4,
            rightMargin=1.5*cm, leftMargin=1.5*cm,
            topMargin=3.8*cm, bottomMargin=1.5*cm
        )

        styles = getSampleStyleSheet()

        titre_style = ParagraphStyle(
            'RapportTitre', parent=styles['Heading1'],
            fontSize=16, spaceAfter=6, alignment=1,
            textColor=bleu, fontName='Helvetica-Bold'
        )
        date_style = ParagraphStyle(
            'RapportDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray, spaceAfter=16
        )
        section_style = ParagraphStyle(
            'RapportSection', parent=styles['Normal'],
            fontSize=11, textColor=bleu, fontName='Helvetica-Bold',
            spaceAfter=8
        )
        cellule_style = ParagraphStyle(
            'RapportCellule', parent=styles['BodyText'],
            fontSize=8.5, leading=11
        )
        label_style = ParagraphStyle(
            'RapportLabel', parent=styles['Normal'],
            fontSize=8, textColor=gris_label, fontName='Helvetica-Bold'
        )

        elements = []

        # Titre + date (identique consultation)
        elements.append(Paragraph("RAPPORT — LISTE DES PATIENTS", titre_style))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_style
        ))
        elements.append(Spacer(1, 0.3*cm))

        # Résumé: nombre de patients
        elements.append(Paragraph(f"RÉCAPITULATIF", section_style))
        resume_data = [
            [Paragraph("<b>Total patients</b>", label_style), Paragraph(str(len(liste_patients)), cellule_style)],
            [Paragraph("<b>Date du rapport</b>", label_style), Paragraph(datetime.now().strftime('%d/%m/%Y'), cellule_style)],
        ]
        resume_table = Table(resume_data, colWidths=[4*cm, 6*cm])
        resume_table.setStyle(TableStyle([
            ('VALIGN',  (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING',   (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1.2, colors.Color(0.85, 0.85, 0.85)),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.97, 0.97, 0.99)),
        ]))
        elements.append(resume_table)
        elements.append(Spacer(1, 0.5*cm))

        # Tableau patients
        elements.append(Paragraph("LISTE DÉTAILLÉE", section_style))

        headers = ["ID", "NOM", "PRÉNOM", "TÉLÉPHONE", "NAISSANCE", "GENRE", "PROFESSION", "ADRESSE"]
        table_data = [headers]
        for p in liste_patients:
            table_data.append([
                str(p.get_code_patient() or ""),
                Paragraph(str(p.get_nom()        or ""), cellule_style),
                Paragraph(str(p.get_prenom()     or ""), cellule_style),
                str(p.get_telephone()  or ""),
                str(p.get_naissance()  or ""),
                str(p.get_genre()      or ""),
                Paragraph(str(p.get_profession() or ""), cellule_style),
                Paragraph(str(p.get_adresse()    or ""), cellule_style),
            ])

        col_widths = [1.6*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.0*cm, 1.3*cm, 2.8*cm, 3.2*cm]
        tableau = Table(table_data, colWidths=col_widths, repeatRows=1)
        tableau.setStyle(TableStyle([
            # En-tête bleu
            ('BACKGROUND',    (0, 0), (-1, 0), bleu),
            ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0), 8),
            ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
            ('TOPPADDING',    (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
            # Données
            ('ALIGN',  (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING',    (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('LEFTPADDING',   (0, 0), (-1, -1), 5),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
            # Grille
            ('GRID',          (0, 0), (-1, -1), 0.4, colors.Color(0.85, 0.85, 0.85)),
            # Alternance de lignes
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 1.0)]),
        ]))
        elements.append(tableau)

        def _entete_page(c, doc):
            w, h = A4
            dessiner_entete_et_fond(c, w, h, info_cabinet)
            c.setFont("Helvetica-Bold", 13)
            c.setFillColor(bleu)
            c.drawCentredString(w / 2, h - 3.1*cm, "LISTE DES PATIENTS")

        doc.build(elements, onFirstPage=_entete_page, onLaterPages=_entete_page)
        return chemin_pdf
