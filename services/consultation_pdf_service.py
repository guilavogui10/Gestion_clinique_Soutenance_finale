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
    """

    @staticmethod
    def _obtenir_valeur(consultation, cle, valeur_par_defaut=''):
        """Obtient une valeur d'un objet Consultation ou d'un dictionnaire."""
        if isinstance(consultation, dict):
            return consultation.get(cle, valeur_par_defaut)
        else:
            return getattr(consultation, cle, valeur_par_defaut)

    @staticmethod
    def dessiner_entete_et_fond(c, width, height, info_cabinet):
        """
        Gère l'aspect visuel commun : Logo en fond et Entête de la clinique.
        """
        nom_clinique = info_cabinet.get("nom_cabinet", "CLINIQUE")
        adresse_clinique = info_cabinet.get("adresse_cabinet", "")
        logo_path = info_cabinet.get("logo")
        vert_medical = colors.Color(0, 0.4, 0.2)

        # --- 1. LOGO EN ARRIÈRE-PLAN (FILIGRANE) ---
        if logo_path and os.path.exists(logo_path):
            c.saveState()
            c.setFillAlpha(0.08)  # Transparence pour le fond
            taille_fond = 7.5*cm
            c.drawImage(logo_path, (width-taille_fond)/2, (height-taille_fond)/2,
                        width=taille_fond, height=taille_fond, mask='auto')
            c.restoreState()

        # --- 2. ENTÊTE (Logo + Texte) ---
        if logo_path and os.path.exists(logo_path):
            # Le logo en haut à gauche (Petit et opaque)
            c.drawImage(logo_path, 0.6*cm, height - 2*cm, width=1.3*cm, height=1.3*cm, mask='auto')

        c.setFillColor(vert_medical)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2.1*cm, height - 1.1*cm, nom_clinique.upper())

        c.setFillColor(colors.black)
        c.setFont("Helvetica", 7)
        c.drawString(2.1*cm, height - 1.5*cm, adresse_clinique)

        # Ligne de séparation sous l'entête
        c.setStrokeColor(vert_medical)
        c.setLineWidth(1.5)
        c.line(0.6*cm, height - 2.3*cm, width - 0.6*cm, height - 2.3*cm)

    @staticmethod
    def generer_pdf_consultations_filtrees(consultations_filtrees, filtres_appliques, chemin_pdf, info_cabinet):
        """
        Génère un PDF avec les consultations filtrées.

        Args:
            consultations_filtrees: Liste des consultations à inclure
            filtres_appliques: Dictionnaire des filtres appliqués
            chemin_pdf: Chemin où sauvegarder le PDF
            info_cabinet: Informations du cabinet (nom, logo, adresse)
        """
        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Style personnalisé pour le titre
        titre_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,  # Centré
            textColor=colors.Color(0, 0.4, 0.2)
        )

        # Titre du rapport
        titre = Paragraph("RAPPORT DES CONSULTATIONS", titre_style)
        elements.append(titre)
        elements.append(Spacer(1, 0.5*cm))

        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,  # Droite
            textColor=colors.gray
        )
        date_texte = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(date_texte, date_style))
        elements.append(Spacer(1, 0.3*cm))

        # Filtres appliqués
        if filtres_appliques:
            filtres_style = ParagraphStyle(
                'FiltresStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.blue
            )

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

        # Statistiques
        nb_consultations = len(consultations_filtrees)
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.green
        )
        stats_texte = f"Nombre total de consultations : {nb_consultations}"
        elements.append(Paragraph(stats_texte, stats_style))
        elements.append(Spacer(1, 0.5*cm))

        if consultations_filtrees:
            # En-têtes du tableau
            headers = ['Date', 'Patient', 'Service', 'Motif', 'Diagnostic']

            # Données du tableau
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
                
                row = [
                    date_str,
                    f"{nom} {prenom}".strip(),
                    service,
                    motif,
                    diagnostic
                ]
                data.append(row)

            # Création du tableau
            table = Table(data, colWidths=[2.5*cm, 4*cm, 3*cm, 4*cm, 4*cm])

            # Style du tableau
            table_style = TableStyle([
                # En-tête
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0, 0.4, 0.2)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

                # Corps du tableau
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),

                # Bordures
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ])

            table.setStyle(table_style)
            elements.append(table)
        else:
            # Message si aucune consultation
            no_data_style = ParagraphStyle(
                'NoDataStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.red,
                alignment=1
            )
            elements.append(Paragraph("Aucune consultation trouvée avec les filtres appliqués.", no_data_style))

        # Génération du PDF avec entête personnalisé
        def ajouter_entete(canvas, doc):
            ConsultationPDFService.dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)

        return True