"""
session_manager.py
------------------
Gestionnaire de session de visualisation.
Permet au Directeur Général de consulter les données d'une session passée
sans modifier le statut en base de données.

Utilisation :
    from core import session_manager
    session_manager.set_session_override("SESS-2024")
    code = session_manager.get_session_courante(dao.get_code_session_active)
"""

_session_override: str | None = None


def get_session_courante(get_session_active_fn) -> str | None:
    """
    Retourne la session sélectionnée par le DG si elle est définie,
    sinon délègue à get_session_active_fn() (requête DB).
    """
    global _session_override
    if _session_override:
        return _session_override
    return get_session_active_fn()


def set_session_override(code_session: str) -> None:
    """Définit la session à utiliser pour tous les affichages."""
    global _session_override
    _session_override = code_session.strip() if code_session else None


def reinitialiser_session() -> None:
    """Revient à la session active en base (annule l'override)."""
    global _session_override
    _session_override = None


def get_override() -> str | None:
    """Retourne le code_session override actuel (None si aucun)."""
    return _session_override
