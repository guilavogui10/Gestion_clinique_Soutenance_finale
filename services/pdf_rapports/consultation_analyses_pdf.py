from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import os


class ConsultationPDFService:
    """
    Service pour générer des rapports PDF des consultations filtrées.
    Utilisé par la vue analyses (tableau_consultation).
    """

    @staticmethod
    def _obtenir_valeur(consultation, cle, valeur_par_defaut=''):
        if isinstance(consultation, dict):
            return consultation.get(cle, valeur_par_defaut)
        else:
            return getattr(consultation, cle, valeur_par_defaut)

    @staticmethod
    def dessiner_entete_et_fond(c, width, height, info_cabinet):
        nom_clinique = info_cabinet.get("nom_cabinet", "CLINIQUE")
        adresse_clinique = info_cabinet.get("adresse_cabinet", "")
        logo_path = info_cabinet.get("logo")
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
    def generer_pdf_consultations_filtrees(consultations_filtrees, filtres_appliques, chemin_pdf, info_cabinet):
        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        titre_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1,
            textColor=colors.Color(0, 0.4, 0.2)
        )
        elements.append(Paragraph("RAPPORT DES CONSULTATIONS", titre_style))
        elements.append(Spacer(1, 0.5*cm))

        date_style = ParagraphStyle('DateStyle', parent=styles['Normal'],
                                    fontSize=10, alignment=2, textColor=colors.gray)
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.3*cm))

        if filtres_appliques:
            filtres_style = ParagraphStyle('FiltresStyle', parent=styles['Normal'],
                                           fontSize=10, textColor=colors.blue)
            filtres_texte = "Filtres appliqués : "
            filtres_liste = []

            if filtres_appliques.get('date_debut') and filtres_appliques.get('date_fin'):
                filtres_liste.append(f"Période: {filtres_appliques['date_debut']} - {filtres_appliques['date_fin']}")

            if filtres_appliques.get('recherche'):
                filtres_liste.append(f"Recherche: {filtres_appliques['recherche']}")

            services_actifs = []
            if filtres_appliques.get('examen'):
                services_actifs.append('Examen')
            if filtres_appliques.get('chirurgie'):
                services_actifs.append('Chirurgie')
            if filtres_appliques.get('lunette'):
                services_actifs.append('Lunette')
            if filtres_appliques.get('prescription'):
                services_actifs.append('Prescription')

            if services_actifs:
                filtres_liste.append(f"Services: {', '.join(services_actifs)}")

            if filtres_liste:
                filtres_texte += " | ".join(filtres_liste)
                elements.append(Paragraph(filtres_texte, filtres_style))
                elements.append(Spacer(1, 0.3*cm))

        nb_consultations = len(consultations_filtrees)
        stats_style = ParagraphStyle('StatsStyle', parent=styles['Normal'],
                                     fontSize=11, textColor=colors.green)
        elements.append(Paragraph(f"Nombre total de consultations : {nb_consultations}", stats_style))
        elements.append(Spacer(1, 0.5*cm))

        if consultations_filtrees:
            headers = ['Date', 'Patient', 'Service', 'Motif', 'Diagnostic']
            data = [headers]

            for consultation in consultations_filtrees:
                date_val = ConsultationPDFService._obtenir_valeur(consultation, 'date_consultation')
                date_str = ''
                if date_val:
                    if isinstance(date_val, str):
                        date_str = date_val
                    else:
                        date_str = date_val.strftime('%d/%m/%Y')

                nom = ConsultationPDFService._obtenir_valeur(consultation, 'nom_patient', '')
                prenom = ConsultationPDFService._obtenir_valeur(consultation, 'prenom_patient', '')
                service = ConsultationPDFService._obtenir_valeur(consultation, 'service', '')
                motif = ConsultationPDFService._obtenir_valeur(consultation, 'motif_consultation', '')
                diagnostic = ConsultationPDFService._obtenir_valeur(consultation, 'diagnostic', '')

                data.append([date_str, f"{nom} {prenom}".strip(), service, motif, diagnostic])

            table = Table(data, colWidths=[2.5*cm, 4*cm, 3*cm, 4*cm, 4*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0, 0.4, 0.2)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
        else:
            no_data_style = ParagraphStyle('NoDataStyle', parent=styles['Normal'],
                                           fontSize=12, textColor=colors.red, alignment=1)
            elements.append(Paragraph("Aucune consultation trouvée avec les filtres appliqués.", no_data_style))

        def ajouter_entete(canvas, doc):
            ConsultationPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return True
