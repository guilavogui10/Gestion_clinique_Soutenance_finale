import ast
import sys

def check_file(filepath):
    """Vérifie la syntaxe et la structure d'un fichier Python."""
    print(f"\n{'='*60}")
    print(f"Vérification: {filepath.split('\\')[-1]}")
    print('='*60)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier la syntaxe
        ast.parse(content)
        print("✓ Syntaxe Python valide")
        
        # Vérifier les méthodes clés
        if 'vue_gestion_panier.py' in filepath:
            required = [
                'show_payment_panel',
                '_setup_payment_overlay',
                '_ouvrir_payment_overlay',
                '_fermer_payment_overlay',
                '_animer_payment_overlay'
            ]
            for method in required:
                if f'def {method}' in content:
                    print(f"✓ Méthode {method} présente")
                else:
                    print(f"✗ MANQUE: Méthode {method}")
        
        elif 'panier_widget.py' in filepath:
            if 'def _finaliser_facture' in content:
                print("✓ Méthode _finaliser_facture présente")
                if 'show_payment_panel' in content:
                    print("✓ Appel à show_payment_panel présent")
                else:
                    print("✗ MANQUE: Appel à show_payment_panel")
        
        elif 'payment_slide_panel.py' in filepath:
            if 'def load_data' in content:
                print("✓ Méthode load_data présente")
            if 'def show_panel' in content:
                print("✓ Méthode show_panel présente")
        
        return True
        
    except SyntaxError as e:
        print(f"✗ ERREUR DE SYNTAXE: {e}")
        return False
    except Exception as e:
        print(f"✗ ERREUR: {e}")
        return False

# Vérifier les fichiers
files = [
    r'c:\Users\Kaissa BILIVOGUI\Desktop\Soutenance\projetSoutenance\views\produit\vue_gestion_panier.py',
    r'c:\Users\Kaissa BILIVOGUI\Desktop\Soutenance\projetSoutenance\views\facturation\patient\panier\panier_widget.py',
    r'c:\Users\Kaissa BILIVOGUI\Desktop\Soutenance\projetSoutenance\views\facturation\patient\panier\components\payment_slide_panel.py'
]

all_ok = True
for f in files:
    if not check_file(f):
        all_ok = False

print(f"\n{'='*60}")
if all_ok:
    print("✓ TOUS LES FICHIERS SONT VALIDES")
else:
    print("✗ DES ERREURS ONT ÉTÉ DÉTECTÉES")
print('='*60)
