"""Bulk theme update script for all 9 form files."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def theme_common_form(content, domain_styles_import, obj_name):
    """Apply common theming patterns to a form file."""
    # Replace hardcoded icon colors "#1558B0" in qta.icon calls
    # (but not in setStyleSheet strings)
    content = content.replace('color="#1558B0"', 'color=theme_manager.colors()["primary"]')
    content = content.replace("color='#1558B0'", "color=theme_manager.colors()['primary']")
    
    # Replace hardcoded icon colors "#1492C6"
    content = content.replace('color="#1492C6"', 'color=theme_manager.colors()["primary"]')
    
    # Replace "#555" icon colors  
    content = content.replace('color="#555"', 'color=theme_manager.colors()["text_muted"]')
    
    # Replace "white" icon colors in qta.icon
    content = content.replace('color="white"', 'color=theme_manager.colors()["text_inverse"]')
    
    # Replace "#e74c3c" icon colors
    content = content.replace('color="#e74c3c"', 'color=theme_manager.colors()["danger"]')
    
    # Replace "#e67e22" icon colors
    content = content.replace('color="#e67e22"', 'color=theme_manager.colors()["warning"]')
    
    # Replace "#3498db" icon colors
    content = content.replace('color="#3498db"', 'color=theme_manager.colors()["info"]')
    
    # Replace "#9b59b6" icon colors  
    content = content.replace('color="#9b59b6"', 'color=theme_manager.colors()["accent"]')
    
    # Replace "#f1c40f" icon colors
    content = content.replace('color="#f1c40f"', 'color=theme_manager.colors()["warning"]')
    
    # Replace "#A8B7C6" icon colors
    content = content.replace('color="#A8B7C6"', 'color=theme_manager.colors()["text_muted"]')
    
    # Replace "#1384B6" icon colors
    content = content.replace('color="#1384B6"', 'color=theme_manager.colors()["primary"]')
    
    # Replace inline validation styles (common across patient/fournisseur/personnel/visite)
    # appliquer_validation method
    content = content.replace(
        'widget.setStyleSheet("border: 1px solid #e74c3c; background-color: #fdf2f2;")',
        'widget.setStyleSheet(f"border: 1px solid {theme_manager.colors()[\'danger\']}; background-color: {theme_manager.colors()[\'danger_bg\']};")'
    )
    content = content.replace(
        'widget.setStyleSheet("border: 1px solid #D6EEF8; background-color: #F9FCFF; color: #102536;")',
        'widget.setStyleSheet(f"border: 1px solid {theme_manager.colors()[\'border\']}; background-color: {theme_manager.colors()[\'bg_input\']}; color: {theme_manager.colors()[\'text_primary\']};")'
    )
    content = content.replace(
        'widget.setStyleSheet("border: 2px solid #66D0F2; background-color: white;")',
        'widget.setStyleSheet(f"border: 2px solid {theme_manager.colors()[\'border_focus\']}; background-color: {theme_manager.colors()[\'bg_card\']};")'
    )
    content = content.replace(
        'widget.setStyleSheet("border: 2px solid #66D0F2; background-color: white; color: #102536;")',
        'widget.setStyleSheet(f"border: 2px solid {theme_manager.colors()[\'border_focus\']}; background-color: {theme_manager.colors()[\'bg_card\']}; color: {theme_manager.colors()[\'text_primary\']};")'
    )
    
    # Replace inline label styles
    content = content.replace(
        'lbl.setStyleSheet("font-weight: bold; color: #46647D;")',
        'lbl.setStyleSheet(f"font-weight: bold; color: {theme_manager.colors()[\'text_secondary\']};")'
    )
    content = content.replace(
        'lbl.setStyleSheet("font-weight: bold; color: #555;")',
        'lbl.setStyleSheet(f"font-weight: bold; color: {theme_manager.colors()[\'text_secondary\']};")'
    )
    
    # Replace err_lbl styles
    content = content.replace(
        'err_lbl.setStyleSheet("color: #e74c3c; font-size: 10px; font-style: italic;")',
        'err_lbl.setStyleSheet(f"color: {theme_manager.colors()[\'danger\']}; font-size: 10px; font-style: italic;")'
    )
    content = content.replace(
        '.setStyleSheet("color: #e74c3c; font-size: 10px; font-style: italic;")',
        '.setStyleSheet(f"color: {theme_manager.colors()[\'danger\']}; font-size: 10px; font-style: italic;")'
    )
    content = content.replace(
        '.setStyleSheet("color: #e74c3c; font-size: 10px;")',
        '.setStyleSheet(f"color: {theme_manager.colors()[\'danger\']}; font-size: 10px;")'
    )
    
    # Replace address label style
    content = content.replace(
        '.setStyleSheet("color: #68819A; font-size: 11px;")',
        '.setStyleSheet(f"color: {theme_manager.colors()[\'text_muted\']}; font-size: 11px;")'
    )
    content = content.replace(
        '.setStyleSheet("color: #68819A; font-size: 12px; background: transparent;")',
        '.setStyleSheet(f"color: {theme_manager.colors()[\'text_muted\']}; font-size: 12px; background: transparent;")'
    )
    content = content.replace(
        '.setStyleSheet("color: #68819A; font-size: 12px;")',
        '.setStyleSheet(f"color: {theme_manager.colors()[\'text_muted\']}; font-size: 12px;")'
    )
    
    # Replace title form style
    content = content.replace(
        '"color: #1558B0; font-size: 21px; font-weight: 900; letter-spacing: 0.8px;"',
        'f"color: {theme_manager.colors()[\'primary\']}; font-size: 21px; font-weight: 900; letter-spacing: 0.8px;"'
    )
    
    # Replace appliquer_style_validation for visite
    content = content.replace(
        'widget.setStyleSheet("border: 2px solid #66D0F2; background-color: #fafffa;")',
        'widget.setStyleSheet(f"border: 2px solid {theme_manager.colors()[\'border_focus\']}; background-color: {theme_manager.colors()[\'success_bg\']};")'
    )
    content = content.replace(
        'widget.setStyleSheet("border: 1px solid #e74c3c; background-color: #fdf2f2;")',
        'widget.setStyleSheet(f"border: 1px solid {theme_manager.colors()[\'danger\']}; background-color: {theme_manager.colors()[\'danger_bg\']};")'
    )
    
    # Replace date validation styles
    content = content.replace(
        'self.date_naissance.setStyleSheet("border: 1px solid #e74c3c; background-color: #fdf2f2;")',
        'self.date_naissance.setStyleSheet(f"border: 1px solid {theme_manager.colors()[\'danger\']}; background-color: {theme_manager.colors()[\'danger_bg\']};")'
    )
    content = content.replace(
        'self.date_naissance.setStyleSheet("border: 2px solid #66D0F2; background-color: white; color: #102536;")',
        'self.date_naissance.setStyleSheet(f"border: 2px solid {theme_manager.colors()[\'border_focus\']}; background-color: {theme_manager.colors()[\'bg_card\']}; color: {theme_manager.colors()[\'text_primary\']};")'
    )
    
    return content


def update_file(filepath, domain_import, obj_name):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add imports if not present
    if 'theme_manager' not in content:
        content = f"from views.shared.theme_manager import theme_manager\n{content}"
    if domain_import and domain_import.split('import ')[1] not in content:
        content = f"{domain_import}\n{content}"
    
    content = theme_common_form(content, domain_import, obj_name)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Updated: {os.path.basename(filepath)}")


# Files that DON'T already have theme_manager imported (consultation & examen already done)
files = [
    ("views/chirurgie/chirurgie_form.py", "from views.chirurgie.styles import ChirurgieStyles", "chururgie_obj"),
    ("views/lunette/commande_lunette_form.py", "from views.lunette.styles import LunetteStyles", "commande_obj"),
    ("views/produit/produit_form.py", "from views.produit.styles import ProduitStyles", "produit_obj"),
    ("views/patient/patient_form.py", "from views.patient.styles import PatientStyles", "patient_obj"),
    ("views/personnel/personnel_form.py", "from views.personnel.styles import PersonnelStyles", "personnel_obj"),
    ("views/fournisseur/fournisseur_form.py", "from views.fournisseur.styles import FournisseurStyles", "fournisseur_obj"),
    ("views/visite/visite_form.py", "from views.visite.styles import VisiteStyles", "visite_obj"),
]

# Also update examen (already has theme_manager but needs icon fixes)
files_already_imported = [
    ("views/examen/examen_form.py", "", "examen_obj"),
]

for rel_path, domain_import, obj_name in files + files_already_imported:
    fp = os.path.join(BASE, rel_path)
    if os.path.exists(fp):
        update_file(fp, domain_import, obj_name)
    else:
        print(f"  NOT FOUND: {rel_path}")

print("\nDone - icon colors updated in all form files.")
