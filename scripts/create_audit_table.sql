-- ============================================================================
-- Table d'audit pour tracer toutes les demandes d'autorisation
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Informations sur le demandeur
    code_demandeur VARCHAR(20) NOT NULL,
    role_demandeur VARCHAR(100) NOT NULL,
    est_responsable BOOLEAN DEFAULT FALSE,
    
    -- Informations sur l'action
    action VARCHAR(50) NOT NULL,  -- modification, suppression, consultation
    contexte TEXT,  -- Description de l'action (ex: "Chirurgie #CH001")
    
    -- Informations sur l'autorisation
    code_autorisateur VARCHAR(20),  -- Code du responsable/DG qui autorise
    statut VARCHAR(20) NOT NULL,  -- en_attente, autorise, refuse, expire
    
    -- Informations techniques
    code_otp_envoye VARCHAR(10),  -- Code OTP généré (pour debug)
    email_destinataire VARCHAR(255),  -- Email où l'OTP a été envoyé
    
    -- Horodatage
    date_demande DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_reponse DATETIME NULL,
    
    -- Métadonnées
    ip_demandeur VARCHAR(45),  -- Adresse IP du demandeur
    user_agent TEXT,  -- Navigateur/Application
    
    INDEX idx_demandeur (code_demandeur),
    INDEX idx_autorisateur (code_autorisateur),
    INDEX idx_statut (statut),
    INDEX idx_date_demande (date_demande)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table pour limiter les tentatives OTP
-- ============================================================================

CREATE TABLE IF NOT EXISTS otp_tentatives (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Identification
    code_utilisateur VARCHAR(20) NOT NULL,
    identifiant_otp VARCHAR(255) NOT NULL,  -- {code}_{action}_{contexte}
    
    -- Compteurs
    nb_tentatives INT DEFAULT 0,
    nb_echecs INT DEFAULT 0,
    
    -- Statut
    est_bloque BOOLEAN DEFAULT FALSE,
    date_blocage DATETIME NULL,
    
    -- Horodatage
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_derniere_tentative DATETIME NULL,
    
    UNIQUE KEY unique_otp (identifiant_otp),
    INDEX idx_utilisateur (code_utilisateur),
    INDEX idx_bloque (est_bloque)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
