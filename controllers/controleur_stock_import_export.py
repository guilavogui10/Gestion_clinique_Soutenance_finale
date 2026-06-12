"""
controleur_stock_import_export.py
-----------------------------------
Contrôleur MVC pour l'import/export des données stock.
Délègue toute la logique à StockImportExportService.

Méthodes compatibles avec ApercuActeModal :
  - obtenir_produits_pour_export()     → liste de dicts pour l'aperçu
  - obtenir_lots_pour_export(session)  → liste de dicts pour l'aperçu
  - export_to_excel / export_to_csv    → export produits
  - import_produits(chemin, format)    → import produits (signature ApercuActeModal)
  - import_lots(chemin, format)        → import lots (nécessite code_session séparé)
"""

import logging
from service_metier.stock_import_export_service import StockImportExportService


class StockImportExportControleur:
    """
    Contrôleur pour l'import/export des produits et des lots de stock.
    Utilisé par GestionProduitsView (vue_gestion_panier_tabs.py).
    """

    def __init__(self):
        self.service = StockImportExportService()
        self.logger  = logging.getLogger(__name__)
        # code_session injecté par la vue avant tout import/export de lots
        self._code_session = None

    def set_code_session(self, code_session: str):
        """Injecte la session courante (appelé par la vue avant d'ouvrir le menu)."""
        self._code_session = code_session

    # =========================================================================
    # APERÇU — données pour ApercuActeModal
    # =========================================================================

    def obtenir_produits_pour_export(self) -> list:
        """Retourne tous les produits sous forme de liste de dicts (pour l'aperçu)."""
        produits = self.service.produit_dao.lister_tous()
        return [
            {
                'code_produit':        p.get_code_produit(),
                'libelle':             p.get_libelle(),
                'type':                p.get_type(),
                'prix_achat_unitaire': p.get_prix_achat_unitaire(),
                'prix_vente_unitaire': p.get_prix_vente_unitaire(),
            }
            for p in produits
        ]

    def obtenir_lots_pour_export(self) -> list:
        """Retourne tous les lots du stock (panier_facture_four) pour l'aperçu."""
        if not self._code_session:
            return []
        lots = self.service.panier_dao.lister_par_session(self._code_session)
        return [
            {
                'code_produit':      lot.code_produit,
                'designation':       lot.designation,
                'quantite_four':     lot.quantite_four,
                'prix_unitaire':     lot.prix_unitaire,
                'date_expiration':   str(lot.date_expiration)[:10] if lot.date_expiration else '',
                'code_facture_four': lot.code_facture_four,
            }
            for lot in lots
        ]

    # =========================================================================
    # PRODUITS — export
    # =========================================================================

    def export_to_excel(self, chemin: str):
        """Export produits Excel — compatible ApercuActeModal._appeler_export()."""
        return self.service.export_produits(chemin, "excel")

    def export_to_csv(self, chemin: str):
        """Export produits CSV — compatible ApercuActeModal._appeler_export()."""
        return self.service.export_produits(chemin, "csv")

    # =========================================================================
    # PRODUITS — import
    # =========================================================================

    def import_produits(self, chemin: str, format_fichier: str):
        """Import produits — compatible ApercuActeModal.ouvrir_import()."""
        return self.service.import_produits(chemin, format_fichier)

    # =========================================================================
    # LOTS DE STOCK — export
    # =========================================================================

    def export_lots_to_excel(self, chemin: str):
        """Export lots Excel (utilise self._code_session injecté par la vue)."""
        return self.service.export_lots_stock(chemin, "excel", self._code_session or "")

    def export_lots_to_csv(self, chemin: str):
        """Export lots CSV (utilise self._code_session injecté par la vue)."""
        return self.service.export_lots_stock(chemin, "csv", self._code_session or "")

    # =========================================================================
    # LOTS DE STOCK — import
    # =========================================================================

    def import_lots(self, chemin: str, format_fichier: str):
        """Import lots — signature compatible ApercuActeModal, utilise session injectée."""
        return self.service.import_lots_stock(chemin, format_fichier, self._code_session or "")

    # =========================================================================
    # FACTURES FOURNISSEUR — export uniquement
    # =========================================================================

    def export_factures_to_excel(self, chemin: str):
        return self.service.export_factures_fournisseur(chemin, "excel", self._code_session or "")

    def export_factures_to_csv(self, chemin: str):
        return self.service.export_factures_fournisseur(chemin, "csv", self._code_session or "")
