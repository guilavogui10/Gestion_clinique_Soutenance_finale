-- ============================================================================
-- MIGRATION : Ajout des colonnes de vérification d'intégrité
-- ============================================================================
-- Date : 2026-05-19
-- Description : Ajoute les colonnes empreinte_sha256 et hmac_integrite
--               pour la vérification d'intégrité des fichiers résultats médicaux
-- ============================================================================

USE clinique_db;

-- Vérifier si les colonnes existent déjà
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'resultat_medical' 
  AND TABLE_SCHEMA = 'clinique_db'
ORDER BY ORDINAL_POSITION;

-- Ajouter la colonne empreinte_sha256 (hash SHA-256 du fichier)
ALTER TABLE resultat_medical 
ADD COLUMN empreinte_sha256 VARCHAR(64) NULL 
COMMENT 'Empreinte SHA-256 du fichier pour vérification d''intégrité';

-- Ajouter la colonne hmac_integrite (signature HMAC Vault)
ALTER TABLE resultat_medical 
ADD COLUMN hmac_integrite VARCHAR(255) NULL 
COMMENT 'Signature HMAC Vault de l''empreinte pour authentification';

-- Vérifier que les colonnes ont été ajoutées
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'resultat_medical' 
  AND TABLE_SCHEMA = 'clinique_db'
  AND COLUMN_NAME IN ('empreinte_sha256', 'hmac_integrite');

-- Afficher un résumé
SELECT 
    COUNT(*) as total_resultats,
    SUM(CASE WHEN empreinte_sha256 IS NOT NULL THEN 1 ELSE 0 END) as avec_empreinte,
    SUM(CASE WHEN empreinte_sha256 IS NULL THEN 1 ELSE 0 END) as sans_empreinte
FROM resultat_medical;

-- ============================================================================
-- NOTES :
-- - Les fichiers existants auront empreinte_sha256 = NULL
-- - Seuls les NOUVEAUX fichiers uploadés auront une empreinte
-- - Les anciens fichiers restent accessibles (rétrocompatibilité)
-- - Pour protéger un ancien fichier : le supprimer et le re-uploader
-- ============================================================================
