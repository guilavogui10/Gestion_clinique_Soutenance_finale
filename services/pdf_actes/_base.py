"""
Imports communs et fonction de dessin d'entête partagée par tous les modules PDF.
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import os


def obtenir_valeur(obj, cle, valeur_par_defaut=''):
    """Obtient une valeur d'un objet ou d'un dictionnaire."""
    if isinstance(obj, dict):
        return obj.get(cle, valeur_par_defaut)
    return getattr(obj, cle, valeur_par_defaut)


def dessiner_entete_et_fond(c, width, height, info_cabinet):
    """
    Dessine l'entête de la clinique (nom, adresse, logo, ligne de séparation).
    Partagée par tous les modules PDF.
    """
    nom_clinique = info_cabinet.get("nom_cabinet", "CLINIQUE")
    adresse_clinique = info_cabinet.get("adresse_cabinet", "")
    logo_path = info_cabinet.get("logo")
    bleu_medical = colors.Color(0.15, 0.38, 0.93)

    c.setFillColor(bleu_medical)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(0.6*cm, height - 1.1*cm, nom_clinique.upper())

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 7)
    c.drawString(0.6*cm, height - 1.5*cm, adresse_clinique)

    if logo_path and os.path.exists(logo_path):
        c.drawImage(logo_path, width - 2*cm, height - 2*cm,
                    width=1.3*cm, height=1.3*cm, mask='auto')

    c.setStrokeColor(bleu_medical)
    c.setLineWidth(1.5)
    c.line(0.6*cm, height - 2.3*cm, width - 0.6*cm, height - 2.3*cm)
