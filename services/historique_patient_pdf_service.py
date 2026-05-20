from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import os


class HistoriquePatientPDFService:
    """
    Service pour générer des rapports PDF de l'historique patient.
    """

    @staticmethod
    def _obtenir_valeur(obj, cle, valeur_par_defaut=''):
        """Obtient une valeur d'un objet ou d'un dictionnaire."""
        if isinstance(obj, dict):
            return obj.get(cle, valeur_par_defaut)
        else:
            return getattr(obj, cle, valeur_par_defaut)

    @staticmethod
    def dessiner_entete_et_fond(c, width, height, info_cabinet):
        """
        Gère l'aspect visuel commun : Entête de la clinique.
        """
        nom_clinique = info_cabinet.get("nom_cabinet", "CLINIQUE")
        adresse_clinique = info_cabinet.get("adresse_cabinet", "")
        logo_path = info_cabinet.get("logo")
        bleu_medical = colors.Color(0.15, 0.38, 0.93)  # Bleu

        # --- ENTÊTE (Texte à gauche + Logo à droite) ---
        # Texte à gauche
        c.setFillColor(bleu_medical)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.6*cm, height - 1.1*cm, nom_clinique.upper())

        c.setFillColor(colors.black)
        c.setFont("Helvetica", 7)
        c.drawString(0.6*cm, height - 1.5*cm, adresse_clinique)
        
        # Logo à droite
        if logo_path and os.path.exists(logo_path):
            # Positionner le logo en haut à droite
            c.drawImage(logo_path, width - 2*cm, height - 2*cm, width=1.3*cm, height=1.3*cm, mask='auto')

        # Ligne de séparation sous l'entête
        c.setStrokeColor(bleu_medical)
        c.setLineWidth(1.5)
        c.line(0.6*cm, height - 2.3*cm, width - 0.6*cm, height - 2.3*cm)

    @staticmethod
    def generer_pdf_consultation(consultation, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour une consultation complète.
        
        Args:
            consultation: Dictionnaire contenant les détails de la consultation
            info_cabinet: Informations du cabinet (nom, logo, adresse)
            chemin_pdf: Chemin où sauvegarder le PDF (si None, crée un fichier temporaire)
        
        Returns:
            str: Chemin du fichier PDF généré
        """
        import tempfile
        
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="consultation_")
            os.close(fd)
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
            textColor=colors.Color(0.15, 0.38, 0.93)  # Bleu
        )

        # Titre du rapport
        titre = Paragraph("RAPPORT DE CONSULTATION", titre_style)
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
        elements.append(Spacer(1, 0.5*cm))

        # Informations de la consultation dans des sections
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leading=12
        )
        
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.Color(0.42, 0.45, 0.50),
            spaceAfter=2
        )

        code = HistoriquePatientPDFService._obtenir_valeur(consultation, 'code', 'N/A')
        date_consultation = HistoriquePatientPDFService._obtenir_valeur(consultation, 'date_consultation', 'N/A')
        diagnostique = HistoriquePatientPDFService._obtenir_valeur(consultation, 'diagnostique', 'N/A')
        frais = HistoriquePatientPDFService._obtenir_valeur(consultation, 'frais_consultation', 0)
        statut_facture = HistoriquePatientPDFService._obtenir_valeur(consultation, 'statut_facture', 'N/A')

        # Informations patient
        patient_nom = HistoriquePatientPDFService._obtenir_valeur(consultation, 'patient_nom', 'N/A')
        patient_prenom = HistoriquePatientPDFService._obtenir_valeur(consultation, 'patient_prenom', 'N/A')
        patient_telephone = HistoriquePatientPDFService._obtenir_valeur(consultation, 'patient_telephone', 'N/A')
        patient_adresse = HistoriquePatientPDFService._obtenir_valeur(consultation, 'patient_adresse', 'N/A')

        # Informations personnel
        personnel_nom = HistoriquePatientPDFService._obtenir_valeur(consultation, 'personnel_nom', 'N/A')
        personnel_prenom = HistoriquePatientPDFService._obtenir_valeur(consultation, 'personnel_prenom', 'N/A')
        personnel_fonction = HistoriquePatientPDFService._obtenir_valeur(consultation, 'personnel_fonction', 'N/A')

        # Style pour les titres de section
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=13,
            spaceAfter=8,
            textColor=colors.Color(0.15, 0.38, 0.93),
            fontName='Helvetica-Bold'
        )

        # === SECTION 1 : PATIENT ET PERSONNEL CÔTE À CÔTE ===
        elements.append(Spacer(1, 0.3*cm))
        
        # Créer deux frames séparés côte à côte
        # Frame Patient
        frame_patient = Table([
            [Paragraph("INFORMATIONS PATIENT", section_style)],
            [Table([
                [Paragraph("<b>Nom</b>", label_style), Paragraph(str(patient_nom), info_style)],
                [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(patient_prenom), info_style)],
                [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
                [Paragraph("<b>Adresse</b>", label_style), Paragraph(str(patient_adresse), info_style)]
            ], colWidths=[3*cm, 5.5*cm])]
        ], colWidths=[8.5*cm])
        
        frame_patient.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, 0), 0),
            ('RIGHTPADDING', (0, 0), (-1, 0), 0),
            ('TOPPADDING', (0, 0), (-1, 0), 0),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            # Bordure autour du contenu
            ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ('LEFTPADDING', (0, 1), (0, 1), 15),
            ('RIGHTPADDING', (0, 1), (0, 1), 15),
            ('TOPPADDING', (0, 1), (0, 1), 15),
            ('BOTTOMPADDING', (0, 1), (0, 1), 15),
        ]))
        
        # Frame Personnel
        frame_personnel = Table([
            [Paragraph("PERSONNEL SOIGNANT", section_style)],
            [Table([
                [Paragraph("<b>Nom</b>", label_style), Paragraph(str(personnel_nom), info_style)],
                [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(personnel_prenom), info_style)],
                [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(personnel_fonction), info_style)],
                ["", ""]  # Ligne vide pour alignement
            ], colWidths=[3*cm, 5.5*cm])]
        ], colWidths=[8.5*cm])
        
        frame_personnel.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, 0), 0),
            ('RIGHTPADDING', (0, 0), (-1, 0), 0),
            ('TOPPADDING', (0, 0), (-1, 0), 0),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            # Bordure autour du contenu
            ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ('LEFTPADDING', (0, 1), (0, 1), 15),
            ('RIGHTPADDING', (0, 1), (0, 1), 15),
            ('TOPPADDING', (0, 1), (0, 1), 15),
            ('BOTTOMPADDING', (0, 1), (0, 1), 15),
        ]))
        
        # Style pour les sous-tableaux internes des deux frames
        for frame in [frame_patient, frame_personnel]:
            inner_table = frame._cellvalues[1][0]
            if inner_table:
                inner_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
        
        # Mettre les deux frames côte à côte avec un espace de 0.5cm entre eux
        patient_personnel_table = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
        patient_personnel_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(patient_personnel_table)
        elements.append(Spacer(1, 0.8*cm))

        # === SECTION 2 : DÉTAILS CONSULTATION ===
        elements.append(Paragraph("DÉTAILS DE LA CONSULTATION", section_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Création du tableau pour afficher les informations en grille
        data = [
            [Paragraph("<b>Code Consultation</b>", label_style), Paragraph(str(code), info_style),
             Paragraph("<b>Date</b>", label_style), Paragraph(str(date_consultation), info_style)],
            [Paragraph("<b>Frais</b>", label_style), Paragraph(f"{frais:,.0f} GNF".replace(',', ' '), info_style),
             Paragraph("<b>Statut Facture</b>", label_style), Paragraph(str(statut_facture), info_style)],
            [Paragraph("<b>Diagnostique</b>", label_style), 
             Paragraph(str(diagnostique), info_style), "", ""]
        ]
        
        info_table = Table(data, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        
        elements.append(info_table)

        elements.append(Spacer(1, 1*cm))

        # Génération du PDF avec entête personnalisé
        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)

        return chemin_pdf

    @staticmethod
    def generer_pdf_consultations_multiples(consultations, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour plusieurs consultations.
        
        Args:
            consultations: Liste de dictionnaires contenant les consultations
            info_cabinet: Informations du cabinet
            chemin_pdf: Chemin où sauvegarder le PDF (si None, crée un fichier temporaire)
        
        Returns:
            str: Chemin du fichier PDF généré
        """
        import tempfile
        
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="consultations_")
            os.close(fd)
        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Titre
        titre_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,
            textColor=colors.Color(0.15, 0.38, 0.93)  # Bleu
        )

        titre = Paragraph("RAPPORT DES CONSULTATIONS", titre_style)
        elements.append(titre)
        elements.append(Spacer(1, 0.5*cm))

        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,
            textColor=colors.gray
        )
        date_texte = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(date_texte, date_style))
        elements.append(Spacer(1, 0.3*cm))

        # Nombre de consultations
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.green
        )
        stats_texte = f"Nombre total de consultations : {len(consultations)}"
        elements.append(Paragraph(stats_texte, stats_style))
        elements.append(Spacer(1, 0.5*cm))

        if consultations:
            # En-têtes du tableau
            headers = ['Code', 'Date', 'Diagnostique', 'Frais', 'Statut']

            # Données du tableau
            data = [headers]

            for consultation in consultations:
                code = HistoriquePatientPDFService._obtenir_valeur(consultation, 'code', 'N/A')
                date_val = HistoriquePatientPDFService._obtenir_valeur(consultation, 'date_consultation')
                date_str = ''
                if date_val:
                    if isinstance(date_val, str):
                        date_str = date_val
                    elif hasattr(date_val, 'strftime'):
                        date_str = date_val.strftime('%d/%m/%Y')
                
                diagnostique = HistoriquePatientPDFService._obtenir_valeur(consultation, 'diagnostique', 'N/A')
                if len(diagnostique) > 30:
                    diagnostique = diagnostique[:30] + "..."
                
                frais = HistoriquePatientPDFService._obtenir_valeur(consultation, 'frais_consultation', 0)
                statut = HistoriquePatientPDFService._obtenir_valeur(consultation, 'statut_facture', 'N/A')
                
                row = [code, date_str, diagnostique, f"{frais} GNF", statut]
                data.append(row)

            # Création du tableau
            table = Table(data, colWidths=[3*cm, 3*cm, 5*cm, 3*cm, 3*cm])

            # Style du tableau
            table_style = TableStyle([
                # En-tête
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.15, 0.38, 0.93)),  # Bleu
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

        # Génération du PDF
        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)

        return chemin_pdf

    @staticmethod
    def generer_pdf_acte(acte, type_acte, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour un acte médical.
        
        Args:
            acte: Dictionnaire contenant les détails de l'acte
            type_acte: Type d'acte (examen, chirurgie, lunette, prescription)
            info_cabinet: Informations du cabinet
            chemin_pdf: Chemin où sauvegarder le PDF (si None, crée un fichier temporaire)
        
        Returns:
            str: Chemin du fichier PDF généré
        """
        import tempfile
        
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix=f"{type_acte}_")
            os.close(fd)
        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Titre
        titre_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,
            textColor=colors.Color(0.15, 0.38, 0.93)  # Bleu
        )

        titre = Paragraph(f"RAPPORT D'ACTE MÉDICAL - {type_acte.upper()}", titre_style)
        elements.append(titre)
        elements.append(Spacer(1, 0.5*cm))

        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,
            textColor=colors.gray
        )
        date_texte = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(date_texte, date_style))
        elements.append(Spacer(1, 0.5*cm))

        # Informations de l'acte dans des sections
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leading=12
        )
        
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.Color(0.42, 0.45, 0.50),
            spaceAfter=2
        )

        if acte:
            # Informations patient
            patient_nom = HistoriquePatientPDFService._obtenir_valeur(acte, 'patient_nom', 'N/A')
            patient_prenom = HistoriquePatientPDFService._obtenir_valeur(acte, 'patient_prenom', 'N/A')
            patient_telephone = HistoriquePatientPDFService._obtenir_valeur(acte, 'patient_telephone', 'N/A')
            patient_adresse = HistoriquePatientPDFService._obtenir_valeur(acte, 'patient_adresse', 'N/A')

            # Informations personnel
            personnel_nom = HistoriquePatientPDFService._obtenir_valeur(acte, 'personnel_nom', 'N/A')
            personnel_prenom = HistoriquePatientPDFService._obtenir_valeur(acte, 'personnel_prenom', 'N/A')
            personnel_fonction = HistoriquePatientPDFService._obtenir_valeur(acte, 'personnel_fonction', 'N/A')

            # Style pour les titres de section
            section_style = ParagraphStyle(
                'SectionStyle',
                parent=styles['Heading2'],
                fontSize=13,
                spaceAfter=8,
                textColor=colors.Color(0.15, 0.38, 0.93),
                fontName='Helvetica-Bold'
            )

            # === SECTION 1 : PATIENT ET PERSONNEL CÔTE À CÔTE ===
            elements.append(Spacer(1, 0.3*cm))
            
            # Créer deux frames séparés côte à côte
            # Frame Patient
            frame_patient = Table([
                [Paragraph("INFORMATIONS PATIENT", section_style)],
                [Table([
                    [Paragraph("<b>Nom</b>", label_style), Paragraph(str(patient_nom), info_style)],
                    [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(patient_prenom), info_style)],
                    [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
                    [Paragraph("<b>Adresse</b>", label_style), Paragraph(str(patient_adresse), info_style)]
                ], colWidths=[3*cm, 5.5*cm])]
            ], colWidths=[8.5*cm])
            
            frame_patient.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, 0), 0),
                ('RIGHTPADDING', (0, 0), (-1, 0), 0),
                ('TOPPADDING', (0, 0), (-1, 0), 0),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                # Bordure autour du contenu
                ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),
                ('LEFTPADDING', (0, 1), (0, 1), 15),
                ('RIGHTPADDING', (0, 1), (0, 1), 15),
                ('TOPPADDING', (0, 1), (0, 1), 15),
                ('BOTTOMPADDING', (0, 1), (0, 1), 15),
            ]))
            
            # Frame Personnel
            frame_personnel = Table([
                [Paragraph("PERSONNEL SOIGNANT", section_style)],
                [Table([
                    [Paragraph("<b>Nom</b>", label_style), Paragraph(str(personnel_nom), info_style)],
                    [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(personnel_prenom), info_style)],
                    [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(personnel_fonction), info_style)],
                    ["", ""]  # Ligne vide pour alignement
                ], colWidths=[3*cm, 5.5*cm])]
            ], colWidths=[8.5*cm])
            
            frame_personnel.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, 0), 0),
                ('RIGHTPADDING', (0, 0), (-1, 0), 0),
                ('TOPPADDING', (0, 0), (-1, 0), 0),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                # Bordure autour du contenu
                ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),
                ('LEFTPADDING', (0, 1), (0, 1), 15),
                ('RIGHTPADDING', (0, 1), (0, 1), 15),
                ('TOPPADDING', (0, 1), (0, 1), 15),
                ('BOTTOMPADDING', (0, 1), (0, 1), 15),
            ]))
            
            # Style pour les sous-tableaux internes des deux frames
            for frame in [frame_patient, frame_personnel]:
                inner_table = frame._cellvalues[1][0]
                if inner_table:
                    inner_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ]))
            
            # Mettre les deux frames côte à côte avec un espace de 0.5cm entre eux
            patient_personnel_table = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
            patient_personnel_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            elements.append(patient_personnel_table)
            elements.append(Spacer(1, 0.8*cm))

            # Informations communes de l'acte
            elements.append(Paragraph("INFORMATIONS GÉNÉRALES", section_style))
            elements.append(Spacer(1, 0.3*cm))
            
            code_acte = HistoriquePatientPDFService._obtenir_valeur(acte, 'code_acte', 'N/A')
            decision = HistoriquePatientPDFService._obtenir_valeur(acte, 'decision_medicale', 'N/A')
            choix = HistoriquePatientPDFService._obtenir_valeur(acte, 'choix_patient', 'N/A')
            statut = HistoriquePatientPDFService._obtenir_valeur(acte, 'statut_acte', 'N/A')

            # Section informations générales
            data_general = [
                [Paragraph("<b>Code Acte</b>", label_style), Paragraph(str(code_acte), info_style),
                 Paragraph("<b>Type</b>", label_style), Paragraph(type_acte.capitalize(), info_style)],
                [Paragraph("<b>Décision médicale</b>", label_style), Paragraph(str(decision), info_style),
                 Paragraph("<b>Choix patient</b>", label_style), Paragraph(str(choix), info_style)],
                [Paragraph("<b>Statut</b>", label_style), Paragraph(str(statut), info_style),
                 "", ""]
            ]
            
            general_table = Table(data_general, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
            general_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ]))
            
            elements.append(general_table)
            elements.append(Spacer(1, 0.6*cm))

            # Informations spécifiques selon le type
            elements.append(Paragraph("INFORMATIONS SPÉCIFIQUES", section_style))
            elements.append(Spacer(1, 0.3*cm))
            if type_acte == 'examen':
                libelle = HistoriquePatientPDFService._obtenir_valeur(acte, 'libelle_examen', 'N/A')
                frais = HistoriquePatientPDFService._obtenir_valeur(acte, 'frais_examen', 0)
                conclusion = HistoriquePatientPDFService._obtenir_valeur(acte, 'conclusion_medicale', 'N/A')
                
                data_specifique = [
                    [Paragraph("<b>Libellé</b>", label_style), Paragraph(str(libelle), info_style),
                     Paragraph("<b>Frais</b>", label_style), Paragraph(f"{frais} GNF", info_style)],
                    [Paragraph("<b>Conclusion</b>", label_style), Paragraph(str(conclusion), info_style),
                     "", ""]
                ]

            elif type_acte == 'chirurgie':
                libelle = HistoriquePatientPDFService._obtenir_valeur(acte, 'libelle_chururgie', 'N/A')
                frais = HistoriquePatientPDFService._obtenir_valeur(acte, 'frais_chururgie', 0)
                compte_rendu = HistoriquePatientPDFService._obtenir_valeur(acte, 'compte_rendu_operatoire', 'N/A')
                
                data_specifique = [
                    [Paragraph("<b>Libellé</b>", label_style), Paragraph(str(libelle), info_style),
                     Paragraph("<b>Frais</b>", label_style), Paragraph(f"{frais} GNF", info_style)],
                    [Paragraph("<b>Compte rendu</b>", label_style), Paragraph(str(compte_rendu), info_style),
                     "", ""]
                ]

            elif type_acte == 'lunette':
                type_verre = HistoriquePatientPDFService._obtenir_valeur(acte, 'type_verre', 'N/A')
                prix = HistoriquePatientPDFService._obtenir_valeur(acte, 'prix_total', 0)
                statut_commande = HistoriquePatientPDFService._obtenir_valeur(acte, 'statut_commande', 'N/A')
                
                data_specifique = [
                    [Paragraph("<b>Type de verre</b>", label_style), Paragraph(str(type_verre), info_style),
                     Paragraph("<b>Prix total</b>", label_style), Paragraph(f"{prix} GNF", info_style)],
                    [Paragraph("<b>Statut commande</b>", label_style), Paragraph(str(statut_commande), info_style),
                     "", ""]
                ]

            elif type_acte == 'prescription':
                produits = HistoriquePatientPDFService._obtenir_valeur(acte, 'produits', [])
                
                data_specifique = [
                    [Paragraph("<b>Nombre de produits</b>", label_style), Paragraph(str(len(produits)), info_style),
                     "", ""]
                ]
            else:
                data_specifique = []
            
            if data_specifique:
                specifique_table = Table(data_specifique, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
                specifique_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
                    ('ROUNDEDCORNERS', [10, 10, 10, 10]),
                ]))
                
                elements.append(specifique_table)

        elements.append(Spacer(1, 1*cm))

        # Génération du PDF
        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)

        return chemin_pdf

    @staticmethod
    def generer_pdf_actes_multiples(actes, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour plusieurs actes médicaux.
        
        Args:
            actes: Liste de dictionnaires contenant les actes
            info_cabinet: Informations du cabinet
            chemin_pdf: Chemin où sauvegarder le PDF (si None, crée un fichier temporaire)
        
        Returns:
            str: Chemin du fichier PDF généré
        """
        import tempfile
        
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="actes_")
            os.close(fd)
        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Titre
        titre_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,
            textColor=colors.Color(0.15, 0.38, 0.93)  # Bleu
        )

        titre = Paragraph("RAPPORT DES ACTES MÉDICAUX", titre_style)
        elements.append(titre)
        elements.append(Spacer(1, 0.5*cm))

        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,
            textColor=colors.gray
        )
        date_texte = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(date_texte, date_style))
        elements.append(Spacer(1, 0.3*cm))

        # Nombre d'actes
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.green
        )
        stats_texte = f"Nombre total d'actes : {len(actes)}"
        elements.append(Paragraph(stats_texte, stats_style))
        elements.append(Spacer(1, 0.5*cm))

        if actes:
            # En-têtes du tableau
            headers = ['Code', 'Type', 'Décision', 'Choix', 'Statut']

            # Données du tableau
            data = [headers]

            for acte in actes:
                code = HistoriquePatientPDFService._obtenir_valeur(acte, 'code_acte', 'N/A')
                type_acte = HistoriquePatientPDFService._obtenir_valeur(acte, 'type_acte', 'N/A')
                decision = HistoriquePatientPDFService._obtenir_valeur(acte, 'decision_medicale', 'N/A')
                if len(decision) > 25:
                    decision = decision[:25] + "..."
                
                choix = HistoriquePatientPDFService._obtenir_valeur(acte, 'choix_patient', 'N/A')
                statut = HistoriquePatientPDFService._obtenir_valeur(acte, 'statut_acte', 'N/A')
                
                row = [code, type_acte.capitalize(), decision, choix, statut]
                data.append(row)

            # Création du tableau
            table = Table(data, colWidths=[3*cm, 2.5*cm, 5*cm, 2.5*cm, 3*cm])

            # Style du tableau
            table_style = TableStyle([
                # En-tête
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.15, 0.38, 0.93)),  # Bleu
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

        # Génération du PDF
        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)

        return chemin_pdf
