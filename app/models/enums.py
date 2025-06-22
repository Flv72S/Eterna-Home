"""
Enum per il sistema Eterna Home
"""
from enum import Enum


class UserRole(str, Enum):
    """
    Enum per i ruoli utente nel sistema Eterna Home.
    I ruoli non sono gerarchici per ora, la gestione dei permessi specifici avverrà in seguito.
    """
    # Ruoli amministrativi
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    
    # Ruoli utenti privati
    OWNER = "owner"
    FAMILY_MEMBER = "family_member"
    GUEST = "guest"
    RESIDENT = "resident"
    
    # Ruoli professionali immobiliari
    MANAGER = "manager"  # Amministratore di condominio
    TECHNICIAN = "technician"  # Tecnico abilitato
    MAINTENANCE = "maintenance"  # Manutentore
    SECURITY = "security"  # Sicurezza
    CLEANER = "cleaner"  # Impresa di pulizie
    
    # Ruoli commerciali
    TENANT = "tenant"  # Affittuario
    CONTRACTOR = "contractor"  # Appaltatore
    SUPPLIER = "supplier"  # Fornitore
    VISITOR = "visitor"  # Visitatore
    SYSTEM = "system"  # Sistema
    
    @classmethod
    def get_display_name(cls, role: str) -> str:
        """
        Restituisce il nome visualizzato per un ruolo.
        """
        display_names = {
            cls.SUPER_ADMIN.value: "Super Amministratore",
            cls.ADMIN.value: "Amministratore",
            cls.OWNER.value: "Proprietario",
            cls.FAMILY_MEMBER.value: "Membro della famiglia",
            cls.GUEST.value: "Ospite",
            cls.RESIDENT.value: "Residente",
            cls.MANAGER.value: "Manager",
            cls.TECHNICIAN.value: "Tecnico",
            cls.MAINTENANCE.value: "Manutentore",
            cls.SECURITY.value: "Sicurezza",
            cls.CLEANER.value: "Addetto pulizie",
            cls.TENANT.value: "Affittuario",
            cls.CONTRACTOR.value: "Appaltatore",
            cls.SUPPLIER.value: "Fornitore",
            cls.VISITOR.value: "Visitatore",
            cls.SYSTEM.value: "Sistema"
        }
        return display_names.get(role, role)
    
    @classmethod
    def get_default_role(cls) -> str:
        """
        Restituisce il ruolo di default per nuovi utenti.
        """
        return cls.GUEST.value
    
    @classmethod
    def get_admin_roles(cls) -> list[str]:
        """
        Restituisce la lista dei ruoli amministrativi.
        """
        return [cls.SUPER_ADMIN.value, cls.ADMIN.value]
    
    @classmethod
    def get_professional_roles(cls) -> list[str]:
        """
        Restituisce la lista dei ruoli professionali.
        """
        return [
            cls.MANAGER.value, cls.TECHNICIAN.value, cls.MAINTENANCE.value,
            cls.SECURITY.value, cls.CLEANER.value, cls.CONTRACTOR.value,
            cls.SUPPLIER.value
        ]
    
    @classmethod
    def get_private_roles(cls) -> list[str]:
        """
        Restituisce la lista dei ruoli per utenti privati.
        """
        return [cls.OWNER.value, cls.FAMILY_MEMBER.value, cls.GUEST.value, cls.RESIDENT.value, cls.TENANT.value, cls.VISITOR.value]
