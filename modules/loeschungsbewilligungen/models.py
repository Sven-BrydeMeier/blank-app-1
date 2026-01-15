"""
Datenmodelle für das Löschungsbewilligungen-Modul

Definiert alle Dataclasses und Enums für:
- Organisationen und Mitgliedschaften
- Löschungsbewilligungs-Fälle
- Dokumente und Templates
- Audit-Logging
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


# ==================== ENUMS ====================

class LBOrgRole(Enum):
    """Rolle innerhalb einer Organisation"""
    NOTAR = "notar"
    STAFF = "staff"
    AUFTRAGGEBER = "auftraggeber"


class LBCaseStatus(Enum):
    """Status eines Löschungsbewilligungs-Falls"""
    ENTWURF = "entwurf"
    ANGEFORDERT = "angefordert"
    BEWILLIGUNG_DA = "bewilligung_da"
    ABGESCHLOSSEN = "abgeschlossen"
    STORNIERT = "storniert"

    @property
    def label(self) -> str:
        """Benutzerfreundliche Bezeichnung"""
        labels = {
            "entwurf": "Entwurf",
            "angefordert": "Angefordert",
            "bewilligung_da": "Bewilligung erhalten",
            "abgeschlossen": "Abgeschlossen",
            "storniert": "Storniert"
        }
        return labels.get(self.value, self.value)

    @property
    def color(self) -> str:
        """Farbe für UI-Darstellung"""
        colors = {
            "entwurf": "#6c757d",        # Grau
            "angefordert": "#ffc107",     # Gelb
            "bewilligung_da": "#17a2b8",  # Blau
            "abgeschlossen": "#28a745",   # Grün
            "storniert": "#dc3545"        # Rot
        }
        return colors.get(self.value, "#6c757d")


class LBDocumentType(Enum):
    """Typ des generierten Dokuments"""
    ANSCHREIBEN_EIGENTUEMER = "anschreiben_eigentuemer"
    ANSCHREIBEN_VERSORGER = "anschreiben_versorger"
    ANSCHREIBEN_BANK = "anschreiben_bank"
    LOESCHUNGSBEWILLIGUNG = "loeschungsbewilligung"
    SONSTIGE = "sonstige"

    @property
    def label(self) -> str:
        """Benutzerfreundliche Bezeichnung"""
        labels = {
            "anschreiben_eigentuemer": "Anschreiben Eigentümer",
            "anschreiben_versorger": "Anschreiben Versorger",
            "anschreiben_bank": "Anschreiben Bank/Gläubiger",
            "loeschungsbewilligung": "Löschungsbewilligung",
            "sonstige": "Sonstiges"
        }
        return labels.get(self.value, self.value)


# ==================== DATACLASSES ====================

@dataclass
class LBOrganization:
    """Kanzlei/Mandant für Löschungsbewilligungen"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""

    # Kontaktdaten
    strasse: Optional[str] = None
    plz: Optional[str] = None
    ort: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    # Notarspezifisch
    notar_name: Optional[str] = None
    amtssitz: Optional[str] = None
    urkundenrolle_praefix: Optional[str] = None

    # Einstellungen
    settings: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für Supabase"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "strasse": self.strasse,
            "plz": self.plz,
            "ort": self.ort,
            "telefon": self.telefon,
            "email": self.email,
            "website": self.website,
            "notar_name": self.notar_name,
            "amtssitz": self.amtssitz,
            "urkundenrolle_praefix": self.urkundenrolle_praefix,
            "settings": self.settings,
        }


@dataclass
class LBMembership:
    """Benutzer-zu-Organisation Zuordnung"""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)

    role: LBOrgRole = LBOrgRole.STAFF

    # Granulare Berechtigungen
    permissions: Dict[str, bool] = field(default_factory=lambda: {
        "kann_faelle_erstellen": True,
        "kann_faelle_bearbeiten": True,
        "kann_faelle_loeschen": False,
        "kann_dokumente_generieren": True,
        "kann_vorlagen_verwalten": False,
        "kann_mitglieder_verwalten": False,
        "kann_einstellungen_aendern": False
    })

    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission: str) -> bool:
        """Prüft ob Berechtigung vorhanden"""
        if self.role == LBOrgRole.NOTAR:
            return True  # Notar hat alle Berechtigungen
        return self.permissions.get(permission, False)


@dataclass
class LBCase:
    """Einzelner Löschungsbewilligungs-Fall"""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    # Aktenzeichen
    aktenzeichen: Optional[str] = None
    externe_referenz: Optional[str] = None

    # Grundbuchdaten
    grundbuch: str = ""
    gb_blatt: str = ""
    gemarkung: Optional[str] = None
    flur: Optional[str] = None
    flurstueck: Optional[str] = None

    # Eigentümer/Empfänger
    vorname: Optional[str] = None
    nachname: Optional[str] = None
    firma: Optional[str] = None
    strasse: Optional[str] = None
    plz: Optional[str] = None
    ort: Optional[str] = None

    # Zu löschendes Recht
    abteilung: Optional[str] = None  # II oder III
    laufende_nummer: Optional[str] = None
    recht_art: Optional[str] = None
    recht_betrag: Optional[Decimal] = None
    recht_waehrung: str = "EUR"
    recht_beschreibung: Optional[str] = None

    # Gläubiger
    glaeubiger_name: Optional[str] = None
    glaeubiger_strasse: Optional[str] = None
    glaeubiger_plz: Optional[str] = None
    glaeubiger_ort: Optional[str] = None
    glaeubiger_iban: Optional[str] = None
    glaeubiger_bic: Optional[str] = None

    # Ablösung
    abloesebetrag: Optional[Decimal] = None
    abloese_datum: Optional[date] = None

    # Status
    status: LBCaseStatus = LBCaseStatus.ENTWURF
    prioritaet: int = 0  # 0=normal, 1=hoch, 2=dringend

    # Fristen
    frist_datum: Optional[date] = None
    erinnerung_datum: Optional[date] = None

    # Notizen
    notizen: Optional[str] = None

    # Verknüpfung
    projekt_id: Optional[UUID] = None
    created_by: Optional[UUID] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def empfaenger_name(self) -> str:
        """Formatierter Empfängername"""
        if self.firma:
            return self.firma
        parts = [self.vorname, self.nachname]
        return " ".join(p for p in parts if p)

    @property
    def empfaenger_adresse(self) -> str:
        """Formatierte Adresse"""
        lines = []
        if self.strasse:
            lines.append(self.strasse)
        if self.plz or self.ort:
            lines.append(f"{self.plz or ''} {self.ort or ''}".strip())
        return "\n".join(lines)

    @property
    def grundbuch_bezeichnung(self) -> str:
        """Formatierte Grundbuchbezeichnung"""
        return f"{self.grundbuch} Blatt {self.gb_blatt}"

    @property
    def recht_formatiert(self) -> str:
        """Formatierte Beschreibung des Rechts"""
        parts = []
        if self.abteilung:
            parts.append(f"Abt. {self.abteilung}")
        if self.laufende_nummer:
            parts.append(f"lfd. Nr. {self.laufende_nummer}")
        if self.recht_art:
            parts.append(self.recht_art)
        if self.recht_betrag:
            parts.append(f"{self.recht_betrag:,.2f} {self.recht_waehrung}")
        return ", ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für Supabase"""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "aktenzeichen": self.aktenzeichen,
            "externe_referenz": self.externe_referenz,
            "grundbuch": self.grundbuch,
            "gb_blatt": self.gb_blatt,
            "gemarkung": self.gemarkung,
            "flur": self.flur,
            "flurstueck": self.flurstueck,
            "vorname": self.vorname,
            "nachname": self.nachname,
            "firma": self.firma,
            "strasse": self.strasse,
            "plz": self.plz,
            "ort": self.ort,
            "abteilung": self.abteilung,
            "laufende_nummer": self.laufende_nummer,
            "recht_art": self.recht_art,
            "recht_betrag": float(self.recht_betrag) if self.recht_betrag else None,
            "recht_waehrung": self.recht_waehrung,
            "recht_beschreibung": self.recht_beschreibung,
            "glaeubiger_name": self.glaeubiger_name,
            "glaeubiger_strasse": self.glaeubiger_strasse,
            "glaeubiger_plz": self.glaeubiger_plz,
            "glaeubiger_ort": self.glaeubiger_ort,
            "glaeubiger_iban": self.glaeubiger_iban,
            "glaeubiger_bic": self.glaeubiger_bic,
            "abloesebetrag": float(self.abloesebetrag) if self.abloesebetrag else None,
            "abloese_datum": self.abloese_datum.isoformat() if self.abloese_datum else None,
            "status": self.status.value,
            "prioritaet": self.prioritaet,
            "frist_datum": self.frist_datum.isoformat() if self.frist_datum else None,
            "erinnerung_datum": self.erinnerung_datum.isoformat() if self.erinnerung_datum else None,
            "notizen": self.notizen,
            "projekt_id": str(self.projekt_id) if self.projekt_id else None,
            "created_by": str(self.created_by) if self.created_by else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LBCase":
        """Erstellt Instanz aus Dictionary"""
        # Status parsen
        status = data.get("status", "entwurf")
        if isinstance(status, str):
            status = LBCaseStatus(status)

        return cls(
            id=UUID(data["id"]) if data.get("id") else uuid4(),
            organization_id=UUID(data["organization_id"]) if data.get("organization_id") else uuid4(),
            aktenzeichen=data.get("aktenzeichen"),
            externe_referenz=data.get("externe_referenz"),
            grundbuch=data.get("grundbuch", ""),
            gb_blatt=data.get("gb_blatt", ""),
            gemarkung=data.get("gemarkung"),
            flur=data.get("flur"),
            flurstueck=data.get("flurstueck"),
            vorname=data.get("vorname"),
            nachname=data.get("nachname"),
            firma=data.get("firma"),
            strasse=data.get("strasse"),
            plz=data.get("plz"),
            ort=data.get("ort"),
            abteilung=data.get("abteilung"),
            laufende_nummer=data.get("laufende_nummer"),
            recht_art=data.get("recht_art"),
            recht_betrag=Decimal(str(data["recht_betrag"])) if data.get("recht_betrag") else None,
            recht_waehrung=data.get("recht_waehrung", "EUR"),
            recht_beschreibung=data.get("recht_beschreibung"),
            glaeubiger_name=data.get("glaeubiger_name"),
            glaeubiger_strasse=data.get("glaeubiger_strasse"),
            glaeubiger_plz=data.get("glaeubiger_plz"),
            glaeubiger_ort=data.get("glaeubiger_ort"),
            glaeubiger_iban=data.get("glaeubiger_iban"),
            glaeubiger_bic=data.get("glaeubiger_bic"),
            abloesebetrag=Decimal(str(data["abloesebetrag"])) if data.get("abloesebetrag") else None,
            abloese_datum=date.fromisoformat(data["abloese_datum"]) if data.get("abloese_datum") else None,
            status=status,
            prioritaet=data.get("prioritaet", 0),
            frist_datum=date.fromisoformat(data["frist_datum"]) if data.get("frist_datum") else None,
            erinnerung_datum=date.fromisoformat(data["erinnerung_datum"]) if data.get("erinnerung_datum") else None,
            notizen=data.get("notizen"),
            projekt_id=UUID(data["projekt_id"]) if data.get("projekt_id") else None,
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
        )


@dataclass
class LBDocument:
    """Generiertes Dokument"""
    id: UUID = field(default_factory=uuid4)
    case_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    document_type: LBDocumentType = LBDocumentType.SONSTIGE

    # Template
    template_id: Optional[UUID] = None
    template_name: Optional[str] = None

    # Datei
    file_name: str = ""
    file_path: str = ""
    file_size: Optional[int] = None
    mime_type: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # Versand
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    sent_via: Optional[str] = None
    sent_to: Optional[str] = None

    # Generierungsdaten
    generated_data: Dict[str, Any] = field(default_factory=dict)

    created_by: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class LBUpload:
    """Hochgeladenes Dokument"""
    id: UUID = field(default_factory=uuid4)
    case_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    # Datei
    file_name: str = ""
    original_name: str = ""
    file_path: str = ""
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

    # Beschreibung
    beschreibung: Optional[str] = None
    kategorie: Optional[str] = None

    eingangsdatum: date = field(default_factory=date.today)

    # OCR
    ocr_text: Optional[str] = None
    ocr_status: Optional[str] = None

    uploaded_by: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class LBTemplate:
    """Dokumentvorlage"""
    id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None  # None = globale Vorlage

    name: str = ""
    beschreibung: Optional[str] = None
    document_type: LBDocumentType = LBDocumentType.SONSTIGE

    # Datei
    file_name: str = ""
    file_path: str = ""

    # Platzhalter
    placeholders: List[str] = field(default_factory=list)

    is_active: bool = True
    is_default: bool = False

    created_by: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class LBAuditLog:
    """Audit-Eintrag (append-only)"""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    aktion: str = ""

    case_id: Optional[UUID] = None
    document_id: Optional[UUID] = None

    details: Dict[str, Any] = field(default_factory=dict)

    user_id: Optional[UUID] = None
    user_email: Optional[str] = None

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)


# ==================== STANDARD-PLATZHALTER ====================

STANDARD_PLATZHALTER = [
    # Grundbuch
    ("$Grundbuch", "Name des Grundbuchamts"),
    ("$GBBlatt", "Grundbuch-Blattnummer"),
    ("$Gemarkung", "Gemarkung"),
    ("$Flur", "Flur"),
    ("$Flurstueck", "Flurstück"),

    # Eigentümer/Empfänger
    ("$Vorname", "Vorname des Empfängers"),
    ("$Nachname", "Nachname des Empfängers"),
    ("$Firma", "Firmenname"),
    ("$Strasse", "Straße und Hausnummer"),
    ("$PLZ", "Postleitzahl"),
    ("$Ort", "Ort"),

    # Recht
    ("$Abteilung", "Grundbuch-Abteilung (II/III)"),
    ("$LfdNr", "Laufende Nummer"),
    ("$RechtArt", "Art des Rechts"),
    ("$RechtBetrag", "Betrag (formatiert)"),
    ("$RechtBeschreibung", "Beschreibung des Rechts"),

    # Gläubiger
    ("$GlaeubigerName", "Name des Gläubigers"),
    ("$GlaeubigerStrasse", "Straße des Gläubigers"),
    ("$GlaeubigerPLZ", "PLZ des Gläubigers"),
    ("$GlaeubigerOrt", "Ort des Gläubigers"),
    ("$GlaeubigerIBAN", "IBAN des Gläubigers"),
    ("$GlaeubigerBIC", "BIC des Gläubigers"),

    # Ablösung
    ("$Abloesebetrag", "Ablösebetrag (formatiert)"),
    ("$AbloeseDatum", "Ablösedatum"),

    # Meta
    ("$Aktenzeichen", "Aktenzeichen"),
    ("$Datum", "Aktuelles Datum"),
    ("$NotarName", "Name des Notars"),
    ("$NotarAmtssitz", "Amtssitz des Notars"),
]
