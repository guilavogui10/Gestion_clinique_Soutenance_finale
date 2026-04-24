class ModeleUser:
    def __init__(self, code: str, mdp: str, role: str, id_personnel:str):
        self._code = code
        self._mdp = mdp
        self._role = role
        self._id_personnel= id_personnel

    # --- Getters ---
    def get_code(self) -> str:
        return self._code

    def get_mdp(self) -> str:
        return self._mdp

    def get_role(self) -> str:
        return self._role
    
    def get_id_personnel(self) -> str:
        return self._id_personnel

    # --- Setters ---
    def set_code(self, code: str):
        self._code = code

    def set_mdp(self, mdp: str):
        self._mdp = mdp

    def set_role(self, role: str):
        self._role = role

    def set_id_personnel(self, id_personnel: str):
        self._id_personnel = id_personnel