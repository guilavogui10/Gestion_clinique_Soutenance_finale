from datetime import datetime


class ActeVisite:
    """
    Modèle représentant le lien entre un acte médical et une visite.

    Cette table pivot est le cœur du suivi temporel et de la file d'attente.
    Elle permet de distinguer :
      - la visite d'origine  (prescription de l'acte)
      - la visite d'exécution (réalisation de l'acte, même jour ou retour)
      - la visite de contrôle (suivi post-acte)

    Valeurs métier :
      role_visite    : origine | execution | controle
      statut_passage : en_attente | en_cours | termine

    Durées calculées dynamiquement (non stockées) :
      durée attente    = date_debut_execution - date_entree
      durée exécution  = date_sortie - date_debut_execution
      durée totale     = date_sortie - date_entree
    """

    def __init__(
        self,
        id_acte_visite       = None,
        code_acte            = None,
        code_visite          = None,
        role_visite          = "origine",
        date_liaison         = None,
        date_entree          = None,
        date_debut_execution = None,
        date_sortie          = None,
        statut_passage       = "en_attente",
    ):
        self._id_acte_visite       = id_acte_visite
        self._code_acte            = code_acte
        self._code_visite          = code_visite
        self._role_visite          = role_visite
        self._date_liaison         = self._convert_to_datetime(date_liaison) or datetime.now()
        self._date_entree          = self._convert_to_datetime(date_entree)
        self._date_debut_execution = self._convert_to_datetime(date_debut_execution)
        self._date_sortie          = self._convert_to_datetime(date_sortie)
        self._statut_passage       = statut_passage

    def _convert_to_datetime(self, value):
        """Convertit une valeur en datetime si nécessaire."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return None
        return None

    # =========================================================================
    # PROPRIÉTÉS
    # =========================================================================

    @property
    def id_acte_visite(self):
        return self._id_acte_visite

    @id_acte_visite.setter
    def id_acte_visite(self, value):
        self._id_acte_visite = value

    @property
    def code_acte(self):
        return self._code_acte

    @code_acte.setter
    def code_acte(self, value):
        self._code_acte = value

    @property
    def code_visite(self):
        return self._code_visite

    @code_visite.setter
    def code_visite(self, value):
        self._code_visite = value

    @property
    def role_visite(self):
        return self._role_visite

    @role_visite.setter
    def role_visite(self, value):
        self._role_visite = value

    @property
    def date_liaison(self):
        return self._date_liaison

    @date_liaison.setter
    def date_liaison(self, value):
        self._date_liaison = value

    @property
    def date_entree(self):
        return self._date_entree

    @date_entree.setter
    def date_entree(self, value):
        self._date_entree = self._convert_to_datetime(value)

    @property
    def date_debut_execution(self):
        return self._date_debut_execution

    @date_debut_execution.setter
    def date_debut_execution(self, value):
        self._date_debut_execution = self._convert_to_datetime(value)

    @property
    def date_sortie(self):
        return self._date_sortie

    @date_sortie.setter
    def date_sortie(self, value):
        self._date_sortie = self._convert_to_datetime(value)

    @property
    def statut_passage(self):
        return self._statut_passage

    @statut_passage.setter
    def statut_passage(self, value):
        self._statut_passage = value

    # =========================================================================
    # DURÉES CALCULÉES (logique pure, sans BDD)
    # =========================================================================

    def duree_attente_minutes(self) -> int | None:
        """Temps d'attente en file : date_debut_execution - date_entree (minutes)."""
        if self._date_entree and self._date_debut_execution:
            delta = self._date_debut_execution - self._date_entree
            return max(0, int(delta.total_seconds() // 60))
        if self._date_entree:
            delta = datetime.now() - self._date_entree
            return max(0, int(delta.total_seconds() // 60))
        return None

    def duree_execution_minutes(self) -> int | None:
        """Durée d'exécution : date_sortie - date_debut_execution (minutes)."""
        if self._date_debut_execution and self._date_sortie:
            delta = self._date_sortie - self._date_debut_execution
            return max(0, int(delta.total_seconds() // 60))
        if self._date_debut_execution:
            delta = datetime.now() - self._date_debut_execution
            return max(0, int(delta.total_seconds() // 60))
        return None

    def duree_totale_minutes(self) -> int | None:
        """Durée totale de passage : date_sortie - date_entree (minutes)."""
        if self._date_entree and self._date_sortie:
            delta = self._date_sortie - self._date_entree
            return max(0, int(delta.total_seconds() // 60))
        if self._date_entree:
            delta = datetime.now() - self._date_entree
            return max(0, int(delta.total_seconds() // 60))
        return None

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def __repr__(self):
        return (
            f"<ActeVisite acte={self._code_acte} | visite={self._code_visite} "
            f"| role={self._role_visite} | statut={self._statut_passage}>"
        )

    def to_dict(self) -> dict:
        return {
            'id_acte_visite'      : self._id_acte_visite,
            'code_acte'           : self._code_acte,
            'code_visite'         : self._code_visite,
            'role_visite'         : self._role_visite,
            'date_liaison'        : self._date_liaison,
            'date_entree'         : self._date_entree,
            'date_debut_execution': self._date_debut_execution,
            'date_sortie'         : self._date_sortie,
            'statut_passage'      : self._statut_passage,
            # Calculés
            'duree_attente_min'   : self.duree_attente_minutes(),
            'duree_execution_min' : self.duree_execution_minutes(),
            'duree_totale_min'    : self.duree_totale_minutes(),
        }
