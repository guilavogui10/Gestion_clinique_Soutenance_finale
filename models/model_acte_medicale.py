from datetime import datetime


class ActeMedical:
    """
    Modèle représentant un acte médical prescrit lors d'une consultation.

    Responsabilité : porter uniquement les données de PRESCRIPTION.
    Le suivi temporel (file d'attente, durées) est géré par ActeVisite.

    Valeurs métier :
      choix_patient   : maintenant | plus_tard | ailleurs
      mode_realisation: interne | externe
      statut_acte     : en_attente | planifie | en_cours | termine | refuse
      type_acte       : examen | chirurgie | lunette | prescription
    """

    def __init__(
        self,
        id_acte          = None,
        code_consultation = None,
        type_acte        = None,
        decision_medicale = None,
        choix_patient    = None,
        mode_realisation = "interne",
        statut_acte      = "en_attente",
        raison_refus     = None,
        # Champs virtuels (non stockés en base, préservés pour compatibilité)
        date_creation    = None,
        id_acte_parent   = None,
        source_acte      = None,
        reference_source = None,
    ):
        self._id_acte           = id_acte
        self._code_consultation = code_consultation
        self._type_acte         = type_acte
        self._decision_medicale = decision_medicale
        self._choix_patient     = choix_patient
        self._mode_realisation  = mode_realisation
        self._statut_acte       = statut_acte
        self._raison_refus      = raison_refus
        # Virtuels
        self._date_creation     = date_creation
        self._id_acte_parent    = id_acte_parent
        self._source_acte       = source_acte
        self._reference_source  = reference_source

    # =========================================================================
    # PROPRIÉTÉS
    # =========================================================================

    @property
    def id_acte(self):
        return self._id_acte

    @id_acte.setter
    def id_acte(self, value):
        self._id_acte = value

    @property
    def code_consultation(self):
        return self._code_consultation

    @code_consultation.setter
    def code_consultation(self, value):
        self._code_consultation = value

    @property
    def type_acte(self):
        return self._type_acte

    @type_acte.setter
    def type_acte(self, value):
        self._type_acte = value

    @property
    def decision_medicale(self):
        return self._decision_medicale

    @decision_medicale.setter
    def decision_medicale(self, value):
        self._decision_medicale = value

    @property
    def choix_patient(self):
        return self._choix_patient

    @choix_patient.setter
    def choix_patient(self, value):
        self._choix_patient = value

    @property
    def mode_realisation(self):
        return self._mode_realisation

    @mode_realisation.setter
    def mode_realisation(self, value):
        self._mode_realisation = value

    @property
    def statut_acte(self):
        return self._statut_acte

    @statut_acte.setter
    def statut_acte(self, value):
        self._statut_acte = value

    @property
    def date_creation(self):
        return self._date_creation

    @date_creation.setter
    def date_creation(self, value):
        self._date_creation = value

    @property
    def id_acte_parent(self):
        return self._id_acte_parent

    @id_acte_parent.setter
    def id_acte_parent(self, value):
        self._id_acte_parent = value

    @property
    def source_acte(self):
        return self._source_acte

    @source_acte.setter
    def source_acte(self, value):
        self._source_acte = value

    @property
    def reference_source(self):
        return self._reference_source

    @reference_source.setter
    def reference_source(self, value):
        self._reference_source = value

    @property
    def raison_refus(self):
        return self._raison_refus

    @raison_refus.setter
    def raison_refus(self, value):
        self._raison_refus = value

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def __repr__(self):
        return (
            f"<ActeMedical id={self._id_acte} | type={self._type_acte} "
            f"| statut={self._statut_acte} | choix={self._choix_patient}>"
        )

    def to_dict(self) -> dict:
        return {
            'id_acte'          : self._id_acte,
            'code_acte'        : self._id_acte,  # Alias pour compatibilité
            'code_consultation': self._code_consultation,
            'type_acte'        : self._type_acte,
            'decision_medicale': self._decision_medicale,
            'choix_patient'    : self._choix_patient,
            'mode_realisation' : self._mode_realisation,
            'statut_acte'      : self._statut_acte,
            'raison_refus'     : self._raison_refus,
        }