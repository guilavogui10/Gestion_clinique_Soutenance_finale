from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import os


class ChirurgiePDFService:
    """
    Service pour générer des rapports PDF des chirurgies filtrées.
    Utilisé par la vue analyses (tableau_chirurgie).
    """

    @staticmethod
    def _obtenir_valeur(obj, cle, valeur_par_defaut=''):
        if isinstance(obj, dict):
            return obj.get(cle, valeur_par_defaut)
        return getattr(obj, cle, valeur_par_defaut)

    @staticmethod
    def dessiner_entete_et_fond(c, width, height, info_cabinet):
        nom_clinique = info_cabinet.get("nom_cabinet", "CLINIQUE")
        adresse_clinique = info_cabinet.get("adresse_cabinet", "")
        logo_path = info_cabinet.get("logo") or info_cabinet.get("logo_url")
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
    def generer_pdf_chirurgies_filtrees(chirurgies_filtrees, filtres_appliques, chemin_pdf, info_cabinet):
        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        titre_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1,
            textColor=colors.Color(0, 0.4, 0.2)
        )
        elements.append(Paragraph("RAPPORT DES CHIRURGIES", titre_style))
        elements.append(Spacer(1, 0.5*cm))

        date_style = ParagraphStyle('DateStyle', parent=styles['Normal'],
                                    fontSize=10, alignment=2, textColor=colors.gray)
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.3*cm))

        if filtres_appliques:
            filtres_style = ParagraphStyle('FiltresStyle', parent=styles['Normal'],
                                           fontSize=10, textColor=colors.blue)
            filtres_liste = []
            if filtres_appliques.get('date_debut') and filtres_appliques.get('date_fin'):
                filtres_liste.append(f"Période: {filtres_appliques['date_debut']} - {filtres_appliques['date_fin']}")
            if filtres_appliques.get('recherche'):
                filtres_liste.append(f"Recherche: {filtres_appliques['recherche']}")
            if filtres_liste:
                elements.append(Paragraph("Filtres appliqués : " + " | ".join(filtres_liste), filtres_style))
                elements.append(Spacer(1, 0.3*cm))

        stats_style = ParagraphStyle('StatsStyle', parent=styles['Normal'],
                                     fontSize=11, textColor=colors.green)
        elements.append(Paragraph(f"Nombre total de chirurgies : {len(chirurgies_filtrees)}", stats_style))
        elements.append(Spacer(1, 0.5*cm))

        if chirurgies_filtrees:
            headers = ['Date', 'Patient', 'Libellé', 'Frais (GNF)']
            data = [headers]

            for chir in chirurgies_filtrees:
                _get = ChirurgiePDFService._obtenir_valeur

                date_val = _get(chir, 'date_chururgie')
                if date_val:
                    date_str = date_val.strftime('%d/%m/%Y') if hasattr(date_val, 'strftime') else str(date_val)
                else:
                    date_str = ''

                nom    = _get(chir, 'nom_patient',    '') or _get(chir, 'patient_nom',    '')
                prenom = _get(chir, 'prenom_patient', '') or _get(chir, 'patient_prenom', '')
                patient = f"{nom} {prenom}".strip() or '-'

                libelle = str(_get(chir, 'libelle_chururgie', '-'))
                frais   = str(_get(chir, 'frais_chururgie',   '-'))

                data.append([date_str, patient, libelle, frais])

            table = Table(data, colWidths=[2.5*cm, 4.5*cm, 7*cm, 3.5*cm])
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
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
            ]))
            elements.append(table)
        else:
            no_data_style = ParagraphStyle('NoDataStyle', parent=styles['Normal'],
                                           fontSize=12, textColor=colors.red, alignment=1)
            elements.append(Paragraph("Aucune chirurgie trouvée avec les filtres appliqués.", no_data_style))

        def ajouter_entete(canvas, doc):
            ChirurgiePDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return True
