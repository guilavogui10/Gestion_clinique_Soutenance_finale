from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


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
                titre = "LISTE DES PATIENTS  : "
                canvas.drawCentredString(width/2, height - 3.1*cm, titre)

            doc.build(elements, onFirstPage=dessiner_decor_clinique, onLaterPages=dessiner_decor_clinique)
            return True, "Rapport PDF généré avec succès."

        except Exception as e:
            return False, f"Erreur Service PDF : {str(e)}"
