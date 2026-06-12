"""
=============================================================================
 DIAGNOSTIC THÈME - Détection des Widgets Non-Conformes
=============================================================================
 Script pour identifier les widgets qui ne répondent pas au changement
 de thème (couleurs hardcodées, styles fixes).
=============================================================================
"""

import os
import re
from pathlib import Path


# Couleurs hardcodées à détecter
HARDCODED_COLORS = [
    r'#000000', r'#000', r'black',
    r'#ffffff', r'#fff', r'white',
    r'background:\s*transparent',
    r'color:\s*#[0-9A-Fa-f]{3,6}',
    r'background-color:\s*#[0-9A-Fa-f]{3,6}',
    r'border:\s*.*#[0-9A-Fa-f]{3,6}',
]


def analyser_fichier(filepath):
    """Analyse un fichier Python pour détecter les couleurs hardcodées."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        problemes = []
        
        # Vérifier si le fichier utilise theme_manager
        utilise_theme = 'theme_manager' in content
        
        # Chercher les setStyleSheet avec couleurs fixes
        for num_ligne, ligne in enumerate(content.split('\n'), 1):
            if 'setStyleSheet' in ligne or 'QSS' in ligne or '"""' in ligne:
                # Détecter les couleurs hardcodées
                for pattern in HARDCODED_COLORS:
                    if re.search(pattern, ligne, re.IGNORECASE):
                        # Ignorer les commentaires
                        if ligne.strip().startswith('#'):
                            continue
                        # Ignorer transparent (c'est OK)
                        if 'transparent' in ligne and 'background' in ligne:
                            continue
                        
                        problemes.append({
                            'ligne': num_ligne,
                            'contenu': ligne.strip(),
                            'pattern': pattern
                        })
        
        return {
            'fichier': filepath,
            'utilise_theme': utilise_theme,
            'problemes': problemes
        }
    
    except Exception as e:
        return None


def scanner_dossier(base_path, dossier_cible):
    """Scanne tous les fichiers Python dans un dossier."""
    chemin = os.path.join(base_path, dossier_cible)
    resultats = []
    
    for root, dirs, files in os.walk(chemin):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                resultat = analyser_fichier(filepath)
                if resultat and resultat['problemes']:
                    resultats.append(resultat)
    
    return resultats


def generer_rapport(resultats, output_file):
    """Génère un rapport HTML des problèmes détectés."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Diagnostic Thème - Widgets Non-Conformes</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }
            h1 { color: #2563EB; }
            .fichier { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .fichier-nom { font-weight: bold; color: #1e40af; margin-bottom: 10px; }
            .probleme { background: #fef2f2; padding: 8px; margin: 5px 0; border-left: 3px solid #ef4444; font-family: monospace; font-size: 12px; }
            .ligne { color: #059669; font-weight: bold; }
            .sans-theme { color: #dc2626; font-weight: bold; }
            .stats { background: #dbeafe; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>🔍 Diagnostic Thème - Widgets avec Couleurs Hardcodées</h1>
    """
    
    total_fichiers = len(resultats)
    total_problemes = sum(len(r['problemes']) for r in resultats)
    sans_theme = sum(1 for r in resultats if not r['utilise_theme'])
    
    html += f"""
        <div class="stats">
            <h3>📊 Statistiques</h3>
            <p><strong>Fichiers analysés:</strong> {total_fichiers}</p>
            <p><strong>Total de problèmes:</strong> {total_problemes}</p>
            <p><strong>Fichiers sans theme_manager:</strong> <span class="sans-theme">{sans_theme}</span></p>
        </div>
    """
    
    for resultat in resultats:
        rel_path = resultat['fichier'].replace('\\', '/')
        if 'Gestion_clinique_Soutenance_finale' in rel_path:
            rel_path = rel_path.split('Gestion_clinique_Soutenance_finale/')[1]
        
        html += f"""
        <div class="fichier">
            <div class="fichier-nom">📄 {rel_path}</div>
        """
        
        if not resultat['utilise_theme']:
            html += '<p class="sans-theme">⚠️ Ce fichier n\'importe pas theme_manager !</p>'
        
        html += f'<p><strong>Problèmes détectés:</strong> {len(resultat["problemes"])}</p>'
        
        for prob in resultat['problemes']:
            html += f"""
            <div class="probleme">
                <span class="ligne">Ligne {prob['ligne']}:</span> {prob['contenu'][:150]}
            </div>
            """
        
        html += '</div>'
    
    html += """
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[OK] Rapport genere : {output_file}")


if __name__ == '__main__':
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("[DIAGNOSTIC] Analyse du module facturation...")
    resultats = scanner_dossier(BASE, 'views/facturation')
    
    if resultats:
        rapport_path = os.path.join(BASE, 'diagnostic_theme_facturation.html')
        generer_rapport(resultats, rapport_path)
        print(f"\n[RESULTATS] {len(resultats)} fichiers avec problemes detectes")
    else:
        print("[OK] Aucun probleme detecte !")
