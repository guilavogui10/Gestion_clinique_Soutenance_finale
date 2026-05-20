"""
Script de test pour vérifier la limitation des tentatives OTP
"""
from service_metier.user_service import UserService

def test_limitation():
    service = UserService()
    
    # Simuler 3 tentatives échouées
    print("=== TEST DE LIMITATION DES TENTATIVES OTP ===\n")
    
    code_utilisateur = "TEST_USER"
    
    for i in range(1, 5):
        print(f"Tentative {i}:")
        resultat = service.verifier_otp_connexion(code_utilisateur, "000000")
        print(f"  Status: {resultat['status']}")
        print(f"  Message: {resultat['message']}")
        print()
        
        if "bloqué" in resultat['message'].lower():
            print("✅ BLOCAGE DÉTECTÉ APRÈS 3 TENTATIVES !")
            break
    else:
        print("❌ PROBLÈME: Pas de blocage après 3 tentatives")

if __name__ == "__main__":
    test_limitation()
