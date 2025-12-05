"""
Immobilien-Transaktionsplattform
Rollen: Makler, Käufer, Verkäufer, Finanzierer, Notar
Erweiterte Version mit Timeline, OCR, Benachrichtigungen, etc.
"""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import io
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import re
import base64

# ============================================================================
# ENUMS UND KONSTANTEN
# ============================================================================

class UserRole(Enum):
    MAKLER = "Makler"
    KAEUFER = "Käufer"
    VERKAEUFER = "Verkäufer"
    FINANZIERER = "Finanzierer"
    NOTAR = "Notar"

class DocumentType(Enum):
    MAKLERAUFTRAG = "Maklerauftrag"
    DATENSCHUTZ = "Datenschutzerklärung"
    WIDERRUFSBELEHRUNG = "Widerrufsbelehrung"
    WIDERRUFSVERZICHT = "Verzicht auf Widerruf"
    BWA = "BWA"
    STEUERBESCHEID = "Steuerbescheid"
    GEHALTSABRECHNUNG = "Gehaltsabrechnung"
    VERMOEGENSNACHWEIS = "Vermögensnachweis"
    SONSTIGE = "Sonstige Bonitätsunterlage"
    EXPOSE = "Exposé"

class FinanzierungsStatus(Enum):
    ENTWURF = "Entwurf"
    GESENDET = "An Käufer gesendet"
    ANGENOMMEN = "Vom Käufer angenommen"
    ZURUECKGEZOGEN = "Zurückgezogen / gegenstandslos"

class ProjektStatus(Enum):
    VORBEREITUNG = "Vorbereitung"
    EXPOSE_ERSTELLT = "Exposé erstellt"
    TEILNEHMER_EINGELADEN = "Teilnehmer eingeladen"
    ONBOARDING_LAUFEND = "Onboarding läuft"
    DOKUMENTE_VOLLSTAENDIG = "Dokumente vollständig"
    WIRTSCHAFTSDATEN_HOCHGELADEN = "Wirtschaftsdaten hochgeladen"
    FINANZIERUNG_ANGEFRAGT = "Finanzierung angefragt"
    FINANZIERUNG_GESICHERT = "Finanzierung gesichert"
    NOTARTERMIN_VEREINBART = "Notartermin vereinbart"
    KAUFVERTRAG_UNTERZEICHNET = "Kaufvertrag unterzeichnet"
    ABGESCHLOSSEN = "Abgeschlossen"

class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class PropertyType(Enum):
    """Objektarten"""
    WOHNUNG = "Wohnung"
    HAUS = "Haus"
    MFH = "Mehrfamilienhaus"
    LAND = "Grundstück/Land"

class DocumentCategory(Enum):
    """Dokumenten-Kategorien"""
    PERSON = "Personenbezogene Unterlagen"
    OBJEKT_BASIS = "Objektunterlagen Grundsätzlich"
    WEG_SPEZIAL = "Wohnung/Teileigentum Spezial"
    LAND_SPEZIAL = "Land/Acker/Wald Spezial"
    FINANZIERUNG = "Finanzierungsunterlagen"
    NOTAR = "Notarielle Dokumente"

class ChecklistType(Enum):
    """Notarielle Checklisten-Typen"""
    KAUFVERTRAG = "Checkliste Kaufvertrag Grundstück/Wohnung"
    UEBERLASSUNG = "Checkliste Überlassungsvertrag"
    MANDANT = "Mandantenfragebogen Notariat"
    DATENSCHUTZ = "Datenschutz-Info Notariat"
    VERBRAUCHER = "Verbraucher-Informationsblatt"

class DocumentRequestStatus(Enum):
    """Status einer Dokumentenanforderung"""
    ANGEFORDERT = "Angefordert"
    BEREITGESTELLT = "Bereitgestellt"
    FEHLT = "Fehlt noch"
    NICHT_RELEVANT = "Nicht relevant"

class NotarMitarbeiterRolle(Enum):
    """Rollen für Notar-Mitarbeiter"""
    VOLLZUGRIFF = "Vollzugriff"
    SACHBEARBEITER = "Sachbearbeiter"
    NUR_LESEN = "Nur Lesen"
    CHECKLISTEN_VERWALTER = "Checklisten-Verwalter"

class VerkäuferDokumentTyp(Enum):
    """Dokumenttypen für Verkäufer"""
    GRUNDBUCHAUSZUG = "Grundbuchauszug"
    TEILUNGSERKLARUNG = "Teilungserklärung"
    WEG_PROTOKOLLE = "WEG-Protokolle"
    ENERGIEAUSWEIS = "Energieausweis"
    LAGEPLAN = "Lageplan"
    GRUNDRISS = "Grundriss"
    BAUGENEHMIGUNG = "Baugenehmigung"
    FLURKARTE = "Flurkarte"
    WIRTSCHAFTSPLAN = "Wirtschaftsplan (WEG)"
    HAUSVERWALTUNG_BESCHEINIGUNG = "Bescheinigung Hausverwaltung"
    MIETVERTRÄGE = "Mietverträge (bei vermieteten Objekten)"
    NEBENKOSTENABRECHNUNG = "Nebenkostenabrechnung"
    MODERNISIERUNGSNACHWEISE = "Modernisierungsnachweise"
    WOHNFLACHENBERECHNUNG = "Wohnflächenberechnung"
    SONSTIGES = "Sonstige Dokumente"

# ============================================================================
# DATENMODELLE
# ============================================================================

@dataclass
class LegalDocument:
    """Rechtliche Dokumente vom Makler"""
    doc_type: str
    version: str
    content_text: str
    pdf_data: Optional[bytes] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class DocumentAcceptance:
    """Akzeptanz-Protokoll für rechtliche Dokumente"""
    user_id: str
    document_type: str
    document_version: str
    accepted_at: datetime
    ip_address: Optional[str] = None
    role: str = ""

@dataclass
class FinancingOffer:
    """Finanzierungsangebot"""
    offer_id: str
    finanzierer_id: str
    projekt_id: str
    darlehensbetrag: float
    zinssatz: float
    sollzinsbindung: int
    tilgungssatz: float
    gesamtlaufzeit: int
    monatliche_rate: float
    besondere_bedingungen: str
    status: str
    pdf_data: Optional[bytes] = None
    created_at: datetime = field(default_factory=datetime.now)
    accepted_at: Optional[datetime] = None
    fuer_notar_markiert: bool = False

@dataclass
class WirtschaftsdatenDokument:
    """Wirtschaftsdaten des Käufers"""
    doc_id: str
    kaeufer_id: str
    doc_type: str
    filename: str
    upload_date: datetime
    pdf_data: bytes
    kategorie: str = "Noch zuzuordnen"
    ocr_text: str = ""
    sichtbar_fuer_makler: bool = False
    sichtbar_fuer_notar: bool = False
    freigegeben_fuer_notar: bool = False

@dataclass
class Notification:
    """Benachrichtigung"""
    notif_id: str
    user_id: str
    titel: str
    nachricht: str
    typ: str
    created_at: datetime
    gelesen: bool = False
    link: Optional[str] = None

@dataclass
class Comment:
    """Kommentar/Nachricht"""
    comment_id: str
    projekt_id: str
    user_id: str
    nachricht: str
    created_at: datetime
    sichtbar_fuer: List[str] = field(default_factory=list)

@dataclass
class Invitation:
    """Einladung"""
    invitation_id: str
    projekt_id: str
    email: str
    rolle: str
    eingeladen_von: str
    token: str
    created_at: datetime
    verwendet: bool = False

@dataclass
class User:
    """Benutzer"""
    user_id: str
    name: str
    email: str
    role: str
    password_hash: str
    projekt_ids: List[str] = field(default_factory=list)
    onboarding_complete: bool = False
    document_acceptances: List[DocumentAcceptance] = field(default_factory=list)
    notifications: List[str] = field(default_factory=list)
    # Personalausweis-Daten
    personal_daten: Optional['PersonalDaten'] = None
    ausweis_foto: Optional[bytes] = None  # Foto des Ausweises

@dataclass
class PersonalDaten:
    """Persönliche Daten aus Personalausweis/Reisepass"""
    # Aus dem Ausweis extrahierte Daten
    vorname: str = ""
    nachname: str = ""
    geburtsname: str = ""
    geburtsdatum: Optional[date] = None
    geburtsort: str = ""
    nationalitaet: str = "DEUTSCH"

    # Adresse
    strasse: str = ""
    hausnummer: str = ""
    plz: str = ""
    ort: str = ""

    # Ausweis-Infos
    ausweisnummer: str = ""
    ausweisart: str = "Personalausweis"  # oder "Reisepass"
    ausstellungsbehoerde: str = ""
    ausstellungsdatum: Optional[date] = None
    gueltig_bis: Optional[date] = None

    # Zusätzliche Infos
    augenfarbe: str = ""
    groesse_cm: int = 0
    geschlecht: str = ""  # "M", "W", "D"

    # OCR-Metadaten
    ocr_vertrauenswuerdigkeit: float = 0.0  # 0-1
    ocr_durchgefuehrt_am: Optional[datetime] = None
    manuell_bestaetigt: bool = False
    bestaetigt_am: Optional[datetime] = None

@dataclass
class TimelineEvent:
    """Timeline-Event"""
    event_id: str
    projekt_id: str
    titel: str
    beschreibung: str
    status: str
    completed: bool
    completed_at: Optional[datetime] = None
    position: int = 0
    wartet_auf: Optional[str] = None

@dataclass
class Projekt:
    """Immobilien-Projekt/Transaktion"""
    projekt_id: str
    name: str
    beschreibung: str
    adresse: str = ""
    kaufpreis: float = 0.0
    expose_pdf: Optional[bytes] = None
    makler_id: str = ""
    kaeufer_ids: List[str] = field(default_factory=list)
    verkaeufer_ids: List[str] = field(default_factory=list)
    finanzierer_ids: List[str] = field(default_factory=list)
    notar_id: str = ""
    status: str = ProjektStatus.VORBEREITUNG.value
    expose_nach_akzeptanz: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    timeline_events: List[str] = field(default_factory=list)
    notartermin: Optional[datetime] = None
    property_type: str = PropertyType.WOHNUNG.value  # Objektart
    expose_data_id: Optional[str] = None  # Verweis auf ExposeData
    termine: List[str] = field(default_factory=list)  # Liste von Termin-IDs

class TerminTyp(Enum):
    """Termin-Typen"""
    BESICHTIGUNG = "Besichtigung"
    UEBERGABE = "Übergabe"
    BEURKUNDUNG = "Beurkundung"
    SONSTIGES = "Sonstiges"

class TerminStatus(Enum):
    """Termin-Status"""
    VORGESCHLAGEN = "Vorgeschlagen"  # Notar hat Termine vorgeschlagen
    ANGEFRAGT = "Angefragt"  # Makler/Käufer/Verkäufer hat Termin angefragt
    AUSSTEHEND = "Ausstehend"  # Wartet auf Bestätigung aller Parteien
    TEILWEISE_BESTAETIGT = "Teilweise bestätigt"  # Einige haben bestätigt
    BESTAETIGT = "Bestätigt"  # Alle Parteien haben bestätigt
    ABGESAGT = "Abgesagt"
    ABGESCHLOSSEN = "Abgeschlossen"

@dataclass
class Termin:
    """Termin für Besichtigung, Übergabe oder Beurkundung"""
    termin_id: str
    projekt_id: str
    termin_typ: str  # TerminTyp value
    datum: date
    uhrzeit_start: str  # Format: "HH:MM"
    uhrzeit_ende: str  # Format: "HH:MM"
    tageszeit: str = ""  # "Vormittag" oder "Nachmittag"
    ort: str = ""  # Adresse/Ort des Termins
    beschreibung: str = ""
    status: str = TerminStatus.ANGEFRAGT.value

    # Ersteller und Beteiligte
    erstellt_von: str = ""  # User ID
    erstellt_am: datetime = field(default_factory=datetime.now)

    # Bestätigungen (User ID -> Bestätigungszeitpunkt)
    bestaetigt_von_makler: Optional[datetime] = None
    bestaetigt_von_kaeufer: List[str] = field(default_factory=list)  # Liste der Käufer-IDs die bestätigt haben
    bestaetigt_von_verkaeufer: List[str] = field(default_factory=list)  # Liste der Verkäufer-IDs
    bestaetigt_von_notar: Optional[datetime] = None

    # Für Outlook-Integration
    outlook_event_id: Optional[str] = None
    outlook_status: str = ""  # "provisorisch", "bestätigt"

    # Kontaktdaten für Termin-Notizen
    kontakte: List[Dict[str, str]] = field(default_factory=list)  # Liste von {name, telefon, rolle}

    # Erinnerungen
    erinnerung_gesendet: bool = False
    erinnerung_gesendet_am: Optional[datetime] = None

@dataclass
class TerminVorschlag:
    """Terminvorschlag vom Notar"""
    vorschlag_id: str
    projekt_id: str
    termin_typ: str
    vorschlaege: List[Dict[str, Any]] = field(default_factory=list)  # Liste von {datum, uhrzeit_start, uhrzeit_ende, tageszeit}
    erstellt_am: datetime = field(default_factory=datetime.now)
    erstellt_von: str = ""  # Notar User ID
    status: str = "offen"  # "offen", "angenommen", "abgelehnt"
    ausgewaehlt_index: int = -1  # Welcher Vorschlag wurde gewählt

@dataclass
class MaklerAgent:
    """Makler-Team-Mitglied"""
    agent_id: str
    name: str
    position: str  # z.B. "Geschäftsführer", "Immobilienberater"
    telefon: str
    email: str
    foto: Optional[bytes] = None

@dataclass
class MaklerProfile:
    """Makler-Profil"""
    profile_id: str
    makler_id: str
    firmenname: str
    adresse: str
    telefon: str
    email: str
    website: str = ""
    logo: Optional[bytes] = None
    team_mitglieder: List[MaklerAgent] = field(default_factory=list)
    backoffice_kontakt: str = ""
    backoffice_email: str = ""
    backoffice_telefon: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    # Erweiterte Felder für Makler-Onboarding
    kurzvita: str = ""  # Kurze Beschreibung für Verkäufer
    spezialisierung: List[str] = field(default_factory=list)  # z.B. ["Ferienimmobilien", "Luxusimmobilien"]
    regionen: List[str] = field(default_factory=list)  # z.B. ["Mallorca", "Ibiza"]
    provision_kaeufer_prozent: float = 0.0
    provision_verkaeufer_prozent: float = 0.0
    agb_text: str = ""
    widerrufsbelehrung_text: str = ""
    datenschutz_text: str = ""
    maklervertrag_vorlage: str = ""
    # Notar-Empfehlung
    empfohlen_von_notar: bool = False
    empfohlen_am: Optional[datetime] = None
    empfohlen_von_notar_id: str = ""
    empfehlung_aktiv: bool = False
    # Onboarding-Status
    onboarding_token: str = ""
    onboarding_abgeschlossen: bool = False
    onboarding_email_gesendet: bool = False

class MaklerEmpfehlungStatus(Enum):
    """Status einer Makler-Empfehlung"""
    EINGELADEN = "Eingeladen"
    DATEN_EINGEGEBEN = "Daten eingegeben"
    FREIGEGEBEN = "Vom Notar freigegeben"
    ABGELEHNT = "Abgelehnt"
    DEAKTIVIERT = "Deaktiviert"

@dataclass
class MaklerEmpfehlung:
    """Makler-Empfehlung durch Notar für Verkäufer"""
    empfehlung_id: str
    notar_id: str
    makler_email: str
    makler_name: str = ""
    firmenname: str = ""
    status: str = MaklerEmpfehlungStatus.EINGELADEN.value
    eingeladen_am: datetime = field(default_factory=datetime.now)
    onboarding_token: str = ""
    makler_user_id: str = ""  # Nach Registrierung
    # Vom Makler eingegebene Daten
    kurzvita: str = ""
    telefon: str = ""
    website: str = ""
    adresse: str = ""
    spezialisierung: List[str] = field(default_factory=list)
    regionen: List[str] = field(default_factory=list)
    provision_kaeufer_prozent: float = 0.0
    provision_verkaeufer_prozent: float = 0.0
    agb_text: str = ""
    widerrufsbelehrung_text: str = ""
    datenschutz_text: str = ""
    logo: Optional[bytes] = None
    freigegeben_am: Optional[datetime] = None
    notiz_notar: str = ""  # Interne Notiz des Notars

@dataclass
class ExposeData:
    """Exposé-Daten für PDF und Web-Generierung"""
    expose_id: str
    projekt_id: str

    # Basis-Informationen
    objekttitel: str = ""
    objektbeschreibung: str = ""
    lage_beschreibung: str = ""

    # Adresse
    strasse: str = ""
    hausnummer: str = ""
    plz: str = ""
    ort: str = ""
    land: str = "Deutschland"
    adresse_validiert: bool = False
    adresse_vorschlag: str = ""  # Vorschlag aus Internet-Validierung

    # Objektdaten
    objektart: str = PropertyType.WOHNUNG.value
    wohnflaeche: float = 0.0
    grundstuecksflaeche: float = 0.0
    anzahl_zimmer: float = 0.0
    anzahl_schlafzimmer: int = 0
    anzahl_badezimmer: int = 0
    anzahl_etagen: int = 0
    etage: str = ""
    baujahr: int = 0
    zustand: str = ""  # z.B. "Erstbezug", "Renoviert", "Sanierungsbedürftig"
    ausstattung: str = ""  # Freitext

    # Nutzungsart
    nutzungsart: str = "Keine Angabe"  # "Ferienvermietung", "Dauerwohnen", "Zweitwohnung", "Keine Angabe"
    ferienvermietung_erlaubt: str = "Keine Angabe"  # "Ja", "Nein", "Keine Angabe"
    dauerwohnen_erlaubt: str = "Keine Angabe"
    zweitwohnung_erlaubt: str = "Keine Angabe"

    # Ausstattungsmerkmale (Boolean-Flags)
    hat_balkon: bool = False
    hat_terrasse: bool = False
    hat_garten: bool = False
    hat_garage: bool = False
    hat_tiefgarage: bool = False
    hat_stellplatz: bool = False
    hat_sauna: bool = False
    hat_gemeinschaftssauna: bool = False
    hat_schwimmbad: bool = False
    hat_gemeinschaftspool: bool = False
    hat_fahrstuhl: bool = False
    hat_meerblick: bool = False
    hat_bergblick: bool = False
    hat_seeblick: bool = False
    nichtraucher: bool = False
    haustiere_erlaubt: str = "Keine Angabe"  # "Ja", "Nein", "Auf Anfrage", "Keine Angabe"

    # Entfernungen
    entfernung_stadt_m: int = 0  # Meter zur nächsten Stadt
    entfernung_strand_m: int = 0  # Meter zum Strand
    entfernung_zentrum_m: int = 0  # Meter zum Ortszentrum
    entfernung_supermarkt_m: int = 0
    entfernung_arzt_m: int = 0
    entfernung_flughafen_km: int = 0

    # Preise
    kaufpreis: float = 0.0
    kaufpreis_vorschlag: float = 0.0  # Basierend auf Vergleichsdaten
    provision: str = ""
    hausgeld: float = 0.0
    grundsteuer: float = 0.0
    preis_pro_qm: float = 0.0  # Wird berechnet

    # Energie
    energieausweis_typ: str = ""  # "Verbrauch" oder "Bedarf"
    energieeffizienzklasse: str = ""
    endenergieverbrauch: float = 0.0
    wesentliche_energietraeger: str = ""
    baujahr_energieausweis: int = 0
    gueltig_bis: Optional[date] = None

    # Besonderheiten
    besonderheiten: str = ""
    verfuegbar_ab: Optional[date] = None

    # WEG-spezifisch (für Wohnungen)
    weg_verwaltung: str = ""
    ruecklage: float = 0.0

    # Marktanalyse / Vergleichsobjekte
    vergleichsobjekte: List[Dict[str, Any]] = field(default_factory=list)
    # Format: [{"titel": "...", "url": "...", "preis": 0, "qm": 0, "quelle": "immoscout/immowelt/..."}]

    # Bilder und Dokumente
    titelbild: Optional[bytes] = None
    weitere_bilder: List[bytes] = field(default_factory=list)
    grundrisse: List[bytes] = field(default_factory=list)
    lageplan: Optional[bytes] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class DocumentRequest:
    """Dokumenten-Anforderung"""
    request_id: str
    projekt_id: str
    dokument_typ: str
    angefordert_von: str  # user_id
    angefordert_bei: str  # user_id
    status: str = DocumentRequestStatus.ANGEFORDERT.value
    nachricht: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    bereitgestellt_am: Optional[datetime] = None
    dokument_id: Optional[str] = None

@dataclass
class NotarChecklist:
    """Notarielle Checklisten"""
    checklist_id: str
    projekt_id: str
    checklist_typ: str  # ChecklistType
    partei: str  # "Käufer" oder "Verkäufer"

    # Daten-Dictionary (flexibel für verschiedene Checklisten)
    daten: Dict[str, Any] = field(default_factory=dict)

    # Status
    vollstaendig: bool = False
    freigegeben: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class BankFolder:
    """Bankenmappe"""
    folder_id: str
    projekt_id: str
    erstellt_von: str  # user_id

    # Enthaltene Dokumente (IDs)
    expose_id: Optional[str] = None
    grundrisse_ids: List[str] = field(default_factory=list)
    dokument_ids: List[str] = field(default_factory=list)

    # Generiertes PDF
    pdf_data: Optional[bytes] = None

    created_at: datetime = field(default_factory=datetime.now)
    status: str = "Entwurf"

@dataclass
class NotarMitarbeiter:
    """Notar-Mitarbeiter mit Zugriffsrechten"""
    mitarbeiter_id: str
    notar_id: str  # Zugehöriger Notar
    name: str
    email: str
    password_hash: str
    rolle: str  # NotarMitarbeiterRolle

    # Berechtigungen
    kann_checklisten_bearbeiten: bool = False
    kann_dokumente_freigeben: bool = False
    kann_termine_verwalten: bool = False
    kann_finanzierung_sehen: bool = False

    # Zugewiesene Projekte
    projekt_ids: List[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)
    aktiv: bool = True

@dataclass
class VerkäuferDokument:
    """Dokumente vom Verkäufer"""
    dokument_id: str
    verkaeufer_id: str
    projekt_id: str
    dokument_typ: str  # VerkäuferDokumentTyp
    dateiname: str
    dateigröße: int
    pdf_data: bytes

    # Metadaten
    beschreibung: str = ""
    gueltig_bis: Optional[date] = None

    # Freigaben
    freigegeben_fuer_makler: bool = False
    freigegeben_fuer_notar: bool = False
    freigegeben_fuer_finanzierer: bool = False
    freigegeben_fuer_kaeufer: bool = False

    upload_datum: datetime = field(default_factory=datetime.now)
    status: str = "Hochgeladen"  # Hochgeladen, Geprüft, Freigegeben, Abgelehnt

# ============================================================================
# SESSION STATE INITIALISIERUNG
# ============================================================================

def init_session_state():
    """Initialisiert den Session State mit Demo-Daten"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_user = None
        st.session_state.users = {}
        st.session_state.projekte = {}
        st.session_state.legal_documents = {}
        st.session_state.financing_offers = {}
        st.session_state.wirtschaftsdaten = {}
        st.session_state.notifications = {}
        st.session_state.comments = {}
        st.session_state.invitations = {}
        st.session_state.timeline_events = {}

        # Neue Datenstrukturen
        st.session_state.makler_profiles = {}
        st.session_state.expose_data = {}
        st.session_state.document_requests = {}
        st.session_state.notar_checklists = {}
        st.session_state.bank_folders = {}
        st.session_state.notar_mitarbeiter = {}
        st.session_state.verkaeufer_dokumente = {}

        # Termin-Koordination
        st.session_state.termine = {}  # Termin-ID -> Termin
        st.session_state.terminvorschlaege = {}  # Vorschlag-ID -> TerminVorschlag
        st.session_state.notar_kalender = {}  # Simulierter Outlook-Kalender

        # Makler-Empfehlungssystem
        st.session_state.makler_empfehlungen = {}  # ID -> MaklerEmpfehlung

        # Demo-Daten
        create_demo_users()
        create_demo_projekt()
        create_demo_timeline()
        create_demo_makler_empfehlungen()

def create_demo_users():
    """Erstellt Demo-Benutzer für alle Rollen"""
    demo_users = [
        User("makler1", "Max Makler", "makler@demo.de", UserRole.MAKLER.value, hash_password("makler123")),
        User("kaeufer1", "Karl Käufer", "kaeufer@demo.de", UserRole.KAEUFER.value, hash_password("kaeufer123"), projekt_ids=["projekt1"]),
        User("verkaeufer1", "Vera Verkäufer", "verkaeufer@demo.de", UserRole.VERKAEUFER.value, hash_password("verkaeufer123"), projekt_ids=["projekt1"]),
        User("finanzierer1", "Frank Finanzierer", "finanz@demo.de", UserRole.FINANZIERER.value, hash_password("finanz123"), projekt_ids=["projekt1"]),
        User("notar1", "Nina Notar", "notar@demo.de", UserRole.NOTAR.value, hash_password("notar123"), projekt_ids=["projekt1"]),
    ]
    for user in demo_users:
        st.session_state.users[user.user_id] = user

def create_demo_projekt():
    """Erstellt ein Demo-Projekt"""
    projekt = Projekt(
        projekt_id="projekt1",
        name="Musterwohnung München",
        beschreibung="Schöne 3-Zimmer-Wohnung in München-Schwabing, 85m², Baujahr 2015",
        adresse="Leopoldstraße 123, 80802 München",
        kaufpreis=485000.00,
        makler_id="makler1",
        kaeufer_ids=["kaeufer1"],
        verkaeufer_ids=["verkaeufer1"],
        finanzierer_ids=["finanzierer1"],
        notar_id="notar1",
        status=ProjektStatus.TEILNEHMER_EINGELADEN.value
    )
    st.session_state.projekte[projekt.projekt_id] = projekt

def create_demo_timeline():
    """Erstellt Demo-Timeline-Events"""
    events = [
        TimelineEvent("evt1", "projekt1", "Projekt erstellt", "Projekt wurde vom Makler angelegt", ProjektStatus.VORBEREITUNG.value, True, datetime.now() - timedelta(days=10), 1, None),
        TimelineEvent("evt2", "projekt1", "Exposé hochgeladen", "Exposé wurde bereitgestellt", ProjektStatus.EXPOSE_ERSTELLT.value, True, datetime.now() - timedelta(days=9), 2, None),
        TimelineEvent("evt3", "projekt1", "Teilnehmer eingeladen", "Käufer und Verkäufer wurden eingeladen", ProjektStatus.TEILNEHMER_EINGELADEN.value, True, datetime.now() - timedelta(days=8), 3, None),
        TimelineEvent("evt4", "projekt1", "Onboarding-Dokumente akzeptieren", "Käufer und Verkäufer müssen rechtliche Dokumente akzeptieren", ProjektStatus.ONBOARDING_LAUFEND.value, False, None, 4, "Käufer und Verkäufer müssen Maklerauftrag, Datenschutz, Widerrufsbelehrung akzeptieren"),
        TimelineEvent("evt5", "projekt1", "Wirtschaftsdaten hochladen", "Käufer lädt Bonitätsunterlagen hoch", ProjektStatus.WIRTSCHAFTSDATEN_HOCHGELADEN.value, False, None, 5, "Käufer muss BWA, Einkommensnachweise und Vermögensnachweise hochladen"),
        TimelineEvent("evt6", "projekt1", "Finanzierungsanfrage", "Finanzierer prüft Unterlagen und erstellt Angebot", ProjektStatus.FINANZIERUNG_ANGEFRAGT.value, False, None, 6, "Finanzierer muss Wirtschaftsdaten prüfen und Finanzierungsangebot erstellen"),
        TimelineEvent("evt7", "projekt1", "Finanzierung gesichert", "Käufer nimmt Finanzierungsangebot an", ProjektStatus.FINANZIERUNG_GESICHERT.value, False, None, 7, "Käufer muss Finanzierungsangebot annehmen"),
        TimelineEvent("evt8", "projekt1", "Notartermin vereinbaren", "Notartermin wird festgelegt", ProjektStatus.NOTARTERMIN_VEREINBART.value, False, None, 8, "Makler oder Notar muss Termin vereinbaren"),
        TimelineEvent("evt9", "projekt1", "Kaufvertrag unterzeichnen", "Alle Parteien unterzeichnen beim Notar", ProjektStatus.KAUFVERTRAG_UNTERZEICHNET.value, False, None, 9, "Käufer und Verkäufer beim Notartermin"),
        TimelineEvent("evt10", "projekt1", "Transaktion abgeschlossen", "Übergabe und Eintragung ins Grundbuch", ProjektStatus.ABGESCHLOSSEN.value, False, None, 10, "Notar bestätigt Abschluss"),
    ]
    for event in events:
        st.session_state.timeline_events[event.event_id] = event
        if event.event_id not in st.session_state.projekte["projekt1"].timeline_events:
            st.session_state.projekte["projekt1"].timeline_events.append(event.event_id)

def create_demo_makler_empfehlungen():
    """Erstellt Demo-Makler-Empfehlungen vom Notar"""
    import uuid

    # Demo-Makler, die vom Notar empfohlen wurden
    demo_empfehlungen = [
        MaklerEmpfehlung(
            empfehlung_id="emp1",
            notar_id="notar1",
            makler_email="premium.makler@mallorca.de",
            makler_name="Carlos Immobilien",
            firmenname="Carlos Premium Immobilien S.L.",
            status=MaklerEmpfehlungStatus.FREIGEGEBEN.value,
            kurzvita="Seit 25 Jahren spezialisiert auf Luxusimmobilien in Mallorca. Über 500 erfolgreiche Transaktionen. Deutschsprachige Betreuung.",
            telefon="+34 971 123 456",
            website="www.carlos-immobilien.es",
            adresse="Paseo Marítimo 45, 07015 Palma de Mallorca",
            spezialisierung=["Luxusimmobilien", "Ferienimmobilien", "Neubauprojekte"],
            regionen=["Mallorca", "Ibiza"],
            provision_kaeufer_prozent=3.0,
            provision_verkaeufer_prozent=3.0,
            freigegeben_am=datetime.now() - timedelta(days=30),
            onboarding_token=str(uuid.uuid4())
        ),
        MaklerEmpfehlung(
            empfehlung_id="emp2",
            notar_id="notar1",
            makler_email="info@costa-homes.de",
            makler_name="Costa Homes GmbH",
            firmenname="Costa Homes Immobilien GmbH",
            status=MaklerEmpfehlungStatus.FREIGEGEBEN.value,
            kurzvita="Deutsches Maklerbüro mit Niederlassung auf den Balearen. Rechtssichere Abwicklung durch deutsche Anwälte.",
            telefon="+49 89 123 4567",
            website="www.costa-homes.de",
            adresse="Maximilianstraße 10, 80539 München",
            spezialisierung=["Ferienimmobilien", "Anlageimmobilien"],
            regionen=["Mallorca", "Costa Brava", "Algarve"],
            provision_kaeufer_prozent=3.57,
            provision_verkaeufer_prozent=3.57,
            freigegeben_am=datetime.now() - timedelta(days=60),
            onboarding_token=str(uuid.uuid4())
        ),
        MaklerEmpfehlung(
            empfehlung_id="emp3",
            notar_id="notar1",
            makler_email="kontakt@insel-immobilien.de",
            makler_name="Insel Immobilien",
            firmenname="Insel Immobilien Verwaltungs GmbH",
            status=MaklerEmpfehlungStatus.EINGELADEN.value,
            kurzvita="",  # Noch nicht ausgefüllt
            telefon="",
            onboarding_token=str(uuid.uuid4())
        ),
    ]

    for emp in demo_empfehlungen:
        st.session_state.makler_empfehlungen[emp.empfehlung_id] = emp

def hash_password(password: str) -> str:
    """Einfaches Password-Hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

# ============================================================================
# HELPER-FUNKTIONEN
# ============================================================================

def create_notification(user_id: str, titel: str, nachricht: str, typ: str = NotificationType.INFO.value, link: str = None):
    """Erstellt eine neue Benachrichtigung"""
    notif_id = f"notif_{len(st.session_state.notifications)}"
    notification = Notification(
        notif_id=notif_id,
        user_id=user_id,
        titel=titel,
        nachricht=nachricht,
        typ=typ,
        created_at=datetime.now(),
        link=link
    )
    st.session_state.notifications[notif_id] = notification
    if user_id in st.session_state.users:
        st.session_state.users[user_id].notifications.append(notif_id)
    return notif_id

def get_unread_notifications(user_id: str) -> List[Notification]:
    """Holt ungelesene Benachrichtigungen"""
    user = st.session_state.users.get(user_id)
    if not user:
        return []

    notifications = []
    for notif_id in user.notifications:
        notif = st.session_state.notifications.get(notif_id)
        if notif and not notif.gelesen:
            notifications.append(notif)

    return sorted(notifications, key=lambda x: x.created_at, reverse=True)

def simulate_ocr(pdf_data: bytes, filename: str) -> Tuple[str, str]:
    """Simuliert OCR und KI-Klassifizierung"""
    # In Produktion: echte OCR mit pytesseract oder Cloud-Service
    # Hier: Simulation basierend auf Dateiname

    ocr_text = f"[OCR-Text aus {filename}]\n\nDies ist ein simulierter OCR-Text.\n"

    filename_lower = filename.lower()

    if "bwa" in filename_lower:
        kategorie = "BWA"
        ocr_text += "Betriebswirtschaftliche Auswertung erkannt.\nUmsatz: 85.000 EUR\nGewinn: 42.000 EUR"
    elif "gehalt" in filename_lower or "lohn" in filename_lower:
        kategorie = "Einkommensnachweise"
        ocr_text += "Gehaltsabrechnung erkannt.\nBrutto: 4.500 EUR\nNetto: 2.850 EUR"
    elif "steuer" in filename_lower or "steuerbescheid" in filename_lower:
        kategorie = "Steuerunterlagen"
        ocr_text += "Steuerbescheid erkannt.\nEinkommen: 68.000 EUR\nSteuerlast: 18.500 EUR"
    elif "vermögen" in filename_lower or "konto" in filename_lower:
        kategorie = "Sicherheiten / Vermögensnachweise"
        ocr_text += "Vermögensnachweis erkannt.\nKontostand: 85.000 EUR"
    else:
        kategorie = "Noch zuzuordnen"
        ocr_text += "Dokumenttyp konnte nicht automatisch erkannt werden."

    return ocr_text, kategorie


def ocr_personalausweis(image_data: bytes, filename: str) -> Tuple['PersonalDaten', str, float]:
    """
    OCR-Erkennung für Personalausweis/Reisepass

    Versucht pytesseract zu verwenden, falls verfügbar.
    Ansonsten Simulation mit Demo-Daten.

    Returns:
        Tuple von (PersonalDaten, OCR-Rohtext, Vertrauenswürdigkeit 0-1)
    """
    ocr_text = ""
    vertrauenswuerdigkeit = 0.0
    personal_daten = PersonalDaten()

    # Versuche echte OCR mit pytesseract
    try:
        import pytesseract
        from PIL import Image
        import io as pio

        # Bild laden
        image = Image.open(pio.BytesIO(image_data))

        # OCR durchführen (Deutsch)
        ocr_text = pytesseract.image_to_string(image, lang='deu')

        # Zusätzlich MRZ (Machine Readable Zone) erkennen
        try:
            mrz_text = pytesseract.image_to_string(
                image,
                config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<'
            )
            ocr_text += "\n\n[MRZ]:\n" + mrz_text
        except:
            pass

        vertrauenswuerdigkeit = 0.75
        # Echte OCR: Parsing erforderlich
        personal_daten = parse_ausweis_ocr_text(ocr_text)

    except ImportError:
        # pytesseract nicht verfügbar - Simulation mit zuverlässigen Demo-Daten
        personal_daten, ocr_text = simulate_personalausweis_ocr(filename)
        vertrauenswuerdigkeit = 0.85  # Simulation ist zuverlässig

    except Exception as e:
        # Anderer Fehler bei OCR - Fallback zu Simulation
        personal_daten, ocr_text = simulate_personalausweis_ocr(filename)
        ocr_text = f"⚠️ OCR-Fehler: {str(e)}\n\n{ocr_text}"
        vertrauenswuerdigkeit = 0.85

    # Metadaten setzen
    personal_daten.ocr_vertrauenswuerdigkeit = vertrauenswuerdigkeit
    personal_daten.ocr_durchgefuehrt_am = datetime.now()

    return personal_daten, ocr_text, vertrauenswuerdigkeit


def simulate_personalausweis_ocr(filename: str) -> Tuple['PersonalDaten', str]:
    """Simuliert OCR-Erkennung und gibt direkt strukturierte Daten zurück"""
    import random

    # Generiere realistische Demo-Daten
    vornamen = ["Max", "Anna", "Thomas", "Maria", "Michael", "Julia", "Stefan", "Laura"]
    nachnamen = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker"]
    orte = ["Berlin", "München", "Hamburg", "Köln", "Frankfurt", "Stuttgart", "Düsseldorf", "Leipzig"]
    strassen = ["Hauptstraße", "Bahnhofstraße", "Berliner Straße", "Gartenweg", "Schulstraße", "Kirchplatz"]

    vorname = random.choice(vornamen)
    nachname = random.choice(nachnamen)
    geb_tag = random.randint(1, 28)
    geb_monat = random.randint(1, 12)
    geb_jahr = random.randint(1960, 2000)
    geburtsort = random.choice(orte)
    wohnort = random.choice(orte)
    strasse = random.choice(strassen)
    hausnr = str(random.randint(1, 150))
    plz = f"{random.randint(10000, 99999)}"
    ausweisnummer = f"L{random.randint(10000000, 99999999)}"
    gueltig_tag = random.randint(1, 28)
    gueltig_monat = random.randint(1, 12)
    gueltig_jahr = random.randint(2026, 2035)
    groesse = random.randint(160, 195)
    augenfarbe = random.choice(["BRAUN", "BLAU", "GRÜN", "GRAU"])
    geschlecht = random.choice(["M", "W"])

    # Erstelle direkt PersonalDaten-Objekt (zuverlässiger als Regex-Parsing)
    personal_daten = PersonalDaten(
        vorname=vorname,
        nachname=nachname,
        geburtsdatum=date(geb_jahr, geb_monat, geb_tag),
        geburtsort=geburtsort,
        nationalitaet="DEUTSCH",
        strasse=strasse,
        hausnummer=hausnr,
        plz=plz,
        ort=wohnort,
        ausweisnummer=ausweisnummer,
        ausweisart="Personalausweis",
        gueltig_bis=date(gueltig_jahr, gueltig_monat, gueltig_tag),
        groesse_cm=groesse,
        augenfarbe=augenfarbe,
        geschlecht=geschlecht
    )

    # OCR-Text für Anzeige generieren
    ocr_text = f"""
=== SIMULIERTE OCR-ERKENNUNG ===
(Demo-Modus - echte OCR erfordert pytesseract)

BUNDESREPUBLIK DEUTSCHLAND
PERSONALAUSWEIS / IDENTITY CARD

Erkannte Daten:
---------------
Nachname: {nachname}
Vorname: {vorname}
Geburtsdatum: {geb_tag:02d}.{geb_monat:02d}.{geb_jahr}
Geburtsort: {geburtsort}
Staatsangehörigkeit: DEUTSCH

Anschrift:
{strasse} {hausnr}
{plz} {wohnort}

Ausweisnummer: {ausweisnummer}
Gültig bis: {gueltig_tag:02d}.{gueltig_monat:02d}.{gueltig_jahr}
Größe: {groesse} cm
Augenfarbe: {augenfarbe}
Geschlecht: {geschlecht}
"""

    return personal_daten, ocr_text


def parse_ausweis_ocr_text(ocr_text: str) -> 'PersonalDaten':
    """Extrahiert strukturierte Daten aus echtem OCR-Text eines Ausweises"""
    import re

    personal_daten = PersonalDaten()

    # Text normalisieren
    text_upper = ocr_text.upper()
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]

    # Verbesserte Nachname-Extraktion
    for i, line in enumerate(lines):
        line_upper = line.upper()
        if 'NACHNAME' in line_upper or 'SURNAME' in line_upper:
            # Nachname ist oft in der nächsten Zeile
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not any(x in next_line.upper() for x in ['VORNAME', 'GIVEN', 'GEBOREN']):
                    personal_daten.nachname = next_line.title()
                    break

    # Verbesserte Vorname-Extraktion
    for i, line in enumerate(lines):
        line_upper = line.upper()
        if 'VORNAME' in line_upper or 'GIVEN NAME' in line_upper:
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not any(x in next_line.upper() for x in ['NACHNAME', 'SURNAME', 'GEBOREN', 'GEBURT']):
                    personal_daten.vorname = next_line.title()
                    break

    # Geburtsdatum extrahieren (Format: DD.MM.YYYY oder ähnlich)
    date_pattern = r'(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})'
    for i, line in enumerate(lines):
        if 'GEBURTSDATUM' in line.upper() or 'DATE OF BIRTH' in line.upper() or 'GEBOREN' in line.upper():
            # Suche in dieser und nächster Zeile
            search_text = line + " " + (lines[i + 1] if i + 1 < len(lines) else "")
            match = re.search(date_pattern, search_text)
            if match:
                try:
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    personal_daten.geburtsdatum = date(year, month, day)
                except:
                    pass
                break

    # Geburtsort extrahieren
    for i, line in enumerate(lines):
        line_upper = line.upper()
        if 'GEBURTSORT' in line_upper or 'PLACE OF BIRTH' in line_upper:
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not any(x in next_line.upper() for x in ['STAATSANG', 'NATIONAL', 'WOHNORT']):
                    personal_daten.geburtsort = next_line.title()
                    break

    # Staatsangehörigkeit
    if "DEUTSCH" in text_upper:
        personal_daten.nationalitaet = "DEUTSCH"

    # Adresse extrahieren - suche nach PLZ-Muster
    plz_pattern = r'(\d{5})\s+([A-ZÄÖÜa-zäöüß\-\s]+)'
    for i, line in enumerate(lines):
        if 'ANSCHRIFT' in line.upper() or 'ADDRESS' in line.upper() or 'WOHNORT' in line.upper():
            # Suche in den nächsten Zeilen
            for j in range(i + 1, min(i + 4, len(lines))):
                plz_match = re.search(plz_pattern, lines[j])
                if plz_match:
                    personal_daten.plz = plz_match.group(1)
                    personal_daten.ort = plz_match.group(2).strip().title()
                    # Straße ist vermutlich in vorheriger Zeile
                    if j > i + 1:
                        strasse_zeile = lines[j - 1]
                        # Trenne Straße und Hausnummer
                        strasse_match = re.match(r'(.+?)\s+(\d+\s*[a-zA-Z]?)$', strasse_zeile)
                        if strasse_match:
                            personal_daten.strasse = strasse_match.group(1).strip()
                            personal_daten.hausnummer = strasse_match.group(2).strip()
                        else:
                            personal_daten.strasse = strasse_zeile
                    break
            break

    # Ausweisnummer extrahieren (Format: Lxxxxxxxx oder ähnlich)
    ausweis_pattern = r'[A-Z]\d{8,9}'
    for line in lines:
        if 'AUSWEISNUMMER' in line.upper() or 'DOCUMENT NUMBER' in line.upper():
            match = re.search(ausweis_pattern, line.upper())
            if match:
                personal_daten.ausweisnummer = match.group(0)
                break
    # Fallback: Suche überall
    if not personal_daten.ausweisnummer:
        for line in lines:
            match = re.search(ausweis_pattern, line.upper())
            if match:
                personal_daten.ausweisnummer = match.group(0)
                break

    # Gültig bis extrahieren
    for i, line in enumerate(lines):
        if 'GÜLTIG' in line.upper() or 'EXPIRY' in line.upper() or 'VALID' in line.upper():
            search_text = line + " " + (lines[i + 1] if i + 1 < len(lines) else "")
            match = re.search(date_pattern, search_text)
            if match:
                try:
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    personal_daten.gueltig_bis = date(year, month, day)
                except:
                    pass
                break

    # Größe extrahieren
    groesse_match = re.search(r'(\d{3})\s*CM', text_upper)
    if groesse_match:
        personal_daten.groesse_cm = int(groesse_match.group(1))

    # Augenfarbe extrahieren
    for farbe in ["BRAUN", "BLAU", "GRÜN", "GRAU", "SCHWARZ"]:
        if farbe in text_upper:
            # Prüfe ob es im Kontext von Augenfarbe steht
            if re.search(rf'AUGENFARBE.*{farbe}|{farbe}.*AUGENFARBE|EYE.*{farbe}', text_upper):
                personal_daten.augenfarbe = farbe
                break

    # Geschlecht extrahieren
    if re.search(r'\bSEX[:\s]+M\b|\bGESCHLECHT[:\s]+M\b', text_upper):
        personal_daten.geschlecht = "M"
    elif re.search(r'\bSEX[:\s]+[FW]\b|\bGESCHLECHT[:\s]+[FW]\b', text_upper):
        personal_daten.geschlecht = "W"

    # Ausweisart erkennen
    if "REISEPASS" in text_upper or "PASSPORT" in text_upper:
        personal_daten.ausweisart = "Reisepass"
    else:
        personal_daten.ausweisart = "Personalausweis"

    return personal_daten


def render_ausweis_upload(user_id: str, rolle: str):
    """
    Rendert das Ausweis-Upload-Widget mit OCR-Erkennung

    Args:
        user_id: ID des Benutzers
        rolle: Rolle des Benutzers (Käufer, Verkäufer)
    """
    user = st.session_state.users.get(user_id)
    if not user:
        st.error("Benutzer nicht gefunden.")
        return

    st.markdown("### 🪪 Personalausweis / Reisepass")
    st.info("📱 **Mobilgerät?** Nehmen Sie direkt ein Foto auf! Alternativ können Sie ein vorhandenes Foto hochladen. Die Daten werden automatisch per OCR erkannt und können dann übernommen werden.")

    # Bestehende Daten anzeigen
    if user.personal_daten and user.personal_daten.manuell_bestaetigt:
        st.success("✅ Ausweisdaten wurden erfasst und bestätigt.")
        with st.expander("📋 Gespeicherte Daten anzeigen", expanded=False):
            pd = user.personal_daten
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {pd.vorname} {pd.nachname}")
                st.write(f"**Geburtsdatum:** {pd.geburtsdatum.strftime('%d.%m.%Y') if pd.geburtsdatum else 'N/A'}")
                st.write(f"**Geburtsort:** {pd.geburtsort}")
                st.write(f"**Nationalität:** {pd.nationalitaet}")
            with col2:
                st.write(f"**Adresse:** {pd.strasse} {pd.hausnummer}")
                st.write(f"**PLZ/Ort:** {pd.plz} {pd.ort}")
                st.write(f"**Ausweisnummer:** {pd.ausweisnummer}")
                st.write(f"**Gültig bis:** {pd.gueltig_bis.strftime('%d.%m.%Y') if pd.gueltig_bis else 'N/A'}")

        if st.button("🔄 Neuen Ausweis hochladen", key=f"new_ausweis_{user_id}"):
            st.session_state[f"upload_new_ausweis_{user_id}"] = True
            st.rerun()

        if not st.session_state.get(f"upload_new_ausweis_{user_id}", False):
            return

    # Auswahl: Datei hochladen oder Foto aufnehmen
    st.markdown("#### Ausweis erfassen")

    upload_methode = st.radio(
        "Wie möchten Sie den Ausweis erfassen?",
        ["📁 Datei hochladen", "📷 Foto aufnehmen (Kamera)"],
        key=f"upload_methode_{user_id}",
        horizontal=True,
        help="Auf Mobilgeräten (iPhone, iPad, Android) können Sie direkt ein Foto aufnehmen."
    )

    file_data = None
    file_name = "camera_capture.jpg"

    if upload_methode == "📁 Datei hochladen":
        # Klassischer Datei-Upload
        uploaded_file = st.file_uploader(
            "Ausweisfoto hochladen (Vorderseite)",
            type=['jpg', 'jpeg', 'png', 'pdf'],
            key=f"ausweis_upload_{user_id}",
            help="Bitte laden Sie ein gut lesbares Foto der Vorderseite Ihres Ausweises hoch."
        )
        if uploaded_file:
            file_data = uploaded_file.read()
            file_name = uploaded_file.name
    else:
        # Kamera-Aufnahme (ideal für Mobilgeräte)
        st.info("📱 **Tipp für Mobilgeräte:** Halten Sie den Ausweis flach und gut beleuchtet. Vermeiden Sie Reflexionen und Schatten.")

        camera_photo = st.camera_input(
            "Ausweis fotografieren",
            key=f"ausweis_camera_{user_id}",
            help="Richten Sie die Kamera auf die Vorderseite Ihres Ausweises."
        )
        if camera_photo:
            file_data = camera_photo.read()
            file_name = "kamera_aufnahme.jpg"

    if file_data:
        # Bild anzeigen
        col1, col2 = st.columns([1, 2])
        with col1:
            try:
                st.image(file_data, caption="Erfasstes Bild", width=300)
            except:
                st.info(f"Datei: {file_name}")

        with col2:
            st.markdown("**Bildqualität prüfen:**")
            st.markdown("""
            - ✅ Ausweis vollständig sichtbar
            - ✅ Text gut lesbar
            - ✅ Keine Reflexionen/Schatten
            - ✅ Bild scharf und nicht verwackelt
            """)

            if st.button("🔍 OCR-Erkennung starten", key=f"start_ocr_{user_id}", type="primary"):
                with st.spinner("Analysiere Ausweis..."):
                    # OCR durchführen
                    personal_daten, ocr_text, vertrauen = ocr_personalausweis(file_data, file_name)

                    # In Session State speichern für Bearbeitung
                    st.session_state[f"ocr_result_{user_id}"] = {
                        'personal_daten': personal_daten,
                        'ocr_text': ocr_text,
                        'vertrauen': vertrauen,
                        'image_data': file_data
                    }

                st.success(f"✅ OCR abgeschlossen! Vertrauenswürdigkeit: {vertrauen*100:.0f}%")
                st.rerun()

    # OCR-Ergebnisse bearbeiten und bestätigen
    ocr_result = st.session_state.get(f"ocr_result_{user_id}")
    if ocr_result:
        st.markdown("---")
        st.markdown("### ✏️ Erkannte Daten prüfen und bearbeiten")

        vertrauen = ocr_result['vertrauen']
        if vertrauen < 0.5:
            st.warning("⚠️ Niedrige OCR-Vertrauenswürdigkeit. Bitte prüfen Sie alle Daten sorgfältig.")
        elif vertrauen < 0.75:
            st.info("ℹ️ Mittlere OCR-Vertrauenswürdigkeit. Bitte prüfen Sie die Daten.")

        pd = ocr_result['personal_daten']

        # Bearbeitungsformular
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Persönliche Daten**")
            vorname = st.text_input("Vorname*", value=pd.vorname, key=f"edit_vorname_{user_id}")
            nachname = st.text_input("Nachname*", value=pd.nachname, key=f"edit_nachname_{user_id}")
            geburtsname = st.text_input("Geburtsname (falls abweichend)", value=pd.geburtsname, key=f"edit_geburtsname_{user_id}")

            # Geburtsdatum
            geb_datum = pd.geburtsdatum if pd.geburtsdatum else date(1980, 1, 1)
            geburtsdatum = st.date_input("Geburtsdatum*", value=geb_datum, key=f"edit_gebdat_{user_id}")

            geburtsort = st.text_input("Geburtsort", value=pd.geburtsort, key=f"edit_geburtsort_{user_id}")
            nationalitaet = st.text_input("Nationalität", value=pd.nationalitaet, key=f"edit_nat_{user_id}")

        with col2:
            st.markdown("**Adresse**")
            strasse = st.text_input("Straße*", value=pd.strasse, key=f"edit_strasse_{user_id}")
            hausnummer = st.text_input("Hausnummer*", value=pd.hausnummer, key=f"edit_hausnr_{user_id}")
            plz = st.text_input("PLZ*", value=pd.plz, key=f"edit_plz_{user_id}")
            ort = st.text_input("Ort*", value=pd.ort, key=f"edit_ort_{user_id}")

            st.markdown("**Ausweis-Infos**")
            ausweisart = st.selectbox("Ausweisart", ["Personalausweis", "Reisepass"],
                                      index=0 if pd.ausweisart == "Personalausweis" else 1,
                                      key=f"edit_ausweisart_{user_id}")
            ausweisnummer = st.text_input("Ausweisnummer*", value=pd.ausweisnummer, key=f"edit_ausweisnr_{user_id}")

            # Gültig bis
            gueltig_datum = pd.gueltig_bis if pd.gueltig_bis else date.today()
            gueltig_bis = st.date_input("Gültig bis*", value=gueltig_datum, key=f"edit_gueltig_{user_id}")

        # OCR-Rohtext anzeigen (für Debugging)
        with st.expander("🔍 OCR-Rohtext anzeigen"):
            st.text_area("Erkannter Text", ocr_result['ocr_text'], height=200, disabled=True)

        # Speichern-Button
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 Daten übernehmen & bestätigen", key=f"save_ausweis_{user_id}", type="primary"):
                # Validierung
                if not all([vorname, nachname, strasse, hausnummer, plz, ort, ausweisnummer]):
                    st.error("Bitte füllen Sie alle Pflichtfelder (*) aus.")
                elif gueltig_bis < date.today():
                    st.error("⚠️ Der Ausweis ist abgelaufen! Bitte verwenden Sie einen gültigen Ausweis.")
                else:
                    # PersonalDaten aktualisieren
                    new_pd = PersonalDaten(
                        vorname=vorname,
                        nachname=nachname,
                        geburtsname=geburtsname,
                        geburtsdatum=geburtsdatum,
                        geburtsort=geburtsort,
                        nationalitaet=nationalitaet,
                        strasse=strasse,
                        hausnummer=hausnummer,
                        plz=plz,
                        ort=ort,
                        ausweisart=ausweisart,
                        ausweisnummer=ausweisnummer,
                        gueltig_bis=gueltig_bis,
                        groesse_cm=pd.groesse_cm,
                        augenfarbe=pd.augenfarbe,
                        geschlecht=pd.geschlecht,
                        ocr_vertrauenswuerdigkeit=vertrauen,
                        ocr_durchgefuehrt_am=pd.ocr_durchgefuehrt_am,
                        manuell_bestaetigt=True,
                        bestaetigt_am=datetime.now()
                    )

                    # User aktualisieren
                    user.personal_daten = new_pd
                    user.ausweis_foto = ocr_result['image_data']
                    user.name = f"{vorname} {nachname}"  # Name aktualisieren
                    st.session_state.users[user_id] = user

                    # Session State aufräumen
                    del st.session_state[f"ocr_result_{user_id}"]
                    if f"upload_new_ausweis_{user_id}" in st.session_state:
                        del st.session_state[f"upload_new_ausweis_{user_id}"]

                    st.success("✅ Ausweisdaten erfolgreich gespeichert!")
                    st.balloons()
                    st.rerun()

        with col2:
            if st.button("🔄 Erneut scannen", key=f"rescan_{user_id}"):
                del st.session_state[f"ocr_result_{user_id}"]
                st.rerun()

        with col3:
            if st.button("❌ Abbrechen", key=f"cancel_ausweis_{user_id}"):
                del st.session_state[f"ocr_result_{user_id}"]
                if f"upload_new_ausweis_{user_id}" in st.session_state:
                    del st.session_state[f"upload_new_ausweis_{user_id}"]
                st.rerun()


def update_projekt_status(projekt_id: str):
    """Aktualisiert den Projektstatus basierend auf Timeline-Events"""
    projekt = st.session_state.projekte.get(projekt_id)
    if not projekt:
        return

    # Finde höchsten abgeschlossenen Status
    completed_events = []
    for event_id in projekt.timeline_events:
        event = st.session_state.timeline_events.get(event_id)
        if event and event.completed:
            completed_events.append(event)

    if completed_events:
        latest_event = max(completed_events, key=lambda e: e.position)
        projekt.status = latest_event.status

# ============================================================================
# NOTAR-CHECKLISTEN-FUNKTIONEN
# ============================================================================

def get_checklist_fields(checklist_typ: str) -> Dict[str, Dict[str, Any]]:
    """Gibt die Felder-Definition für einen Checklisten-Typ zurück"""

    if checklist_typ == ChecklistType.KAUFVERTRAG.value:
        return {
            "vorname": {"label": "Vorname", "type": "text", "required": True},
            "nachname": {"label": "Nachname", "type": "text", "required": True},
            "geburtsdatum": {"label": "Geburtsdatum", "type": "date", "required": True},
            "geburtsort": {"label": "Geburtsort", "type": "text", "required": True},
            "staatsangehoerigkeit": {"label": "Staatsangehörigkeit", "type": "text", "required": True},
            "familienstand": {"label": "Familienstand", "type": "select", "options": ["ledig", "verheiratet", "geschieden", "verwitwet"], "required": True},
            "gueterstand": {"label": "Güterstand (bei Verheirateten)", "type": "select", "options": ["Zugewinngemeinschaft", "Gütertrennung", "Gütergemeinschaft", "N/A"], "required": False},
            "strasse": {"label": "Straße", "type": "text", "required": True},
            "hausnummer": {"label": "Hausnummer", "type": "text", "required": True},
            "plz": {"label": "PLZ", "type": "text", "required": True},
            "ort": {"label": "Ort", "type": "text", "required": True},
            "telefon": {"label": "Telefon", "type": "text", "required": True},
            "email": {"label": "E-Mail", "type": "text", "required": True},
            "steuer_id": {"label": "Steuer-ID", "type": "text", "required": True},
            "personalausweis": {"label": "Personalausweis-Nr.", "type": "text", "required": True},
            "ausgestellt_am": {"label": "Ausgestellt am", "type": "date", "required": True},
            "gueltig_bis": {"label": "Gültig bis", "type": "date", "required": True},
        }

    elif checklist_typ == ChecklistType.UEBERLASSUNG.value:
        return {
            "vorname": {"label": "Vorname", "type": "text", "required": True},
            "nachname": {"label": "Nachname", "type": "text", "required": True},
            "geburtsdatum": {"label": "Geburtsdatum", "type": "date", "required": True},
            "geburtsort": {"label": "Geburtsort", "type": "text", "required": True},
            "staatsangehoerigkeit": {"label": "Staatsangehörigkeit", "type": "text", "required": True},
            "strasse": {"label": "Straße", "type": "text", "required": True},
            "hausnummer": {"label": "Hausnummer", "type": "text", "required": True},
            "plz": {"label": "PLZ", "type": "text", "required": True},
            "ort": {"label": "Ort", "type": "text", "required": True},
            "telefon": {"label": "Telefon", "type": "text", "required": True},
            "email": {"label": "E-Mail", "type": "text", "required": True},
            "ueberlassungsdatum": {"label": "Überlassungsdatum", "type": "date", "required": True},
            "eigentumsverhaeltnis": {"label": "Eigentumsverhältnis", "type": "text", "required": True},
            "nutzungsvereinbarung": {"label": "Nutzungsvereinbarung", "type": "textarea", "required": False},
            "besondere_bedingungen": {"label": "Besondere Bedingungen", "type": "textarea", "required": False},
            "zustimmung_eigentuemer": {"label": "Zustimmung Eigentümer vorhanden", "type": "checkbox", "required": True},
            "vollmacht": {"label": "Vollmacht vorhanden", "type": "checkbox", "required": False},
        }

    elif checklist_typ == ChecklistType.MANDANT.value:
        return {
            "vorname": {"label": "Vorname", "type": "text", "required": True},
            "nachname": {"label": "Nachname", "type": "text", "required": True},
            "geburtsdatum": {"label": "Geburtsdatum", "type": "date", "required": True},
            "geburtsort": {"label": "Geburtsort", "type": "text", "required": True},
            "staatsangehoerigkeit": {"label": "Staatsangehörigkeit", "type": "text", "required": True},
            "strasse": {"label": "Straße", "type": "text", "required": True},
            "hausnummer": {"label": "Hausnummer", "type": "text", "required": True},
            "plz": {"label": "PLZ", "type": "text", "required": True},
            "ort": {"label": "Ort", "type": "text", "required": True},
            "telefon": {"label": "Telefon", "type": "text", "required": True},
            "email": {"label": "E-Mail", "type": "text", "required": True},
            "beruf": {"label": "Beruf", "type": "text", "required": True},
            "arbeitgeber": {"label": "Arbeitgeber", "type": "text", "required": False},
            "pep_status": {"label": "Politisch exponierte Person (PEP)", "type": "select", "options": ["Nein", "Ja"], "required": True},
            "herkunft_mittel": {"label": "Herkunft der Mittel", "type": "textarea", "required": True},
            "geldwaesche_erklaerung": {"label": "Geldwäsche-Erklärung abgegeben", "type": "checkbox", "required": True},
        }

    elif checklist_typ == ChecklistType.DATENSCHUTZ.value:
        return {
            "datenschutz_text": {
                "label": "Datenschutzinformation Notariat",
                "type": "info",
                "content": """
# Datenschutzinformation gemäß Art. 13, 14 DSGVO

## 1. Verantwortlicher
[Notariat] ist verantwortlich für die Verarbeitung Ihrer personenbezogenen Daten.

## 2. Zweck der Datenverarbeitung
Ihre Daten werden ausschließlich zur Erfüllung unserer notariellen Pflichten und zur Vertragsabwicklung verarbeitet.

## 3. Rechtsgrundlage
Die Verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. b) und c) DSGVO zur Erfüllung vertraglicher und gesetzlicher Pflichten.

## 4. Speicherdauer
Ihre Daten werden gemäß den gesetzlichen Aufbewahrungsfristen (§ 45 BNotO) für mindestens 10 Jahre gespeichert.

## 5. Ihre Rechte
Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch.
                """,
                "required": True
            },
            "datenschutz_bestaetigung": {"label": "Ich habe die Datenschutzinformation zur Kenntnis genommen", "type": "checkbox", "required": True},
            "datenschutz_datum": {"label": "Datum der Kenntnisnahme", "type": "date", "required": True},
        }

    elif checklist_typ == ChecklistType.VERBRAUCHER.value:
        return {
            "verbraucher_text": {
                "label": "Verbraucher-Informationsblatt",
                "type": "info",
                "content": """
# Verbraucher-Informationsblatt gemäß § 17a Abs. 1 BNotO

## Hinweise zum Grundstückskaufvertrag

### 1. Allgemeine Informationen
Der Notar ist unparteiischer Betreuer aller Beteiligten und berät Sie umfassend und neutral.

### 2. Kosten
Die Notarkosten richten sich nach dem Gerichts- und Notarkostengesetz (GNotKG) und sind gesetzlich festgelegt.

### 3. Wichtige Hinweise
- Der Kaufpreis wird erst nach Eigentumsumschreibung fällig
- Die Vormerkung sichert Ihre Rechte am Grundstück
- Die Grunderwerbsteuer ist vom Käufer zu zahlen
- Prüfen Sie die Finanzierung vor Vertragsunterzeichnung

### 4. Widerrufsrecht
Bei Verbraucherverträgen kann unter bestimmten Umständen ein Widerrufsrecht bestehen.

### 5. Rechtsberatung
Sie haben das Recht, sich vor Vertragsunterzeichnung rechtlich beraten zu lassen.
                """,
                "required": True
            },
            "verbraucher_bestaetigung": {"label": "Ich habe das Verbraucher-Informationsblatt erhalten und zur Kenntnis genommen", "type": "checkbox", "required": True},
            "verbraucher_datum": {"label": "Datum der Aushändigung", "type": "date", "required": True},
            "beratungswunsch": {"label": "Ich wünsche weitere rechtliche Beratung", "type": "checkbox", "required": False},
        }

    else:
        return {}

def render_checklist_form(checklist: NotarChecklist) -> bool:
    """Rendert ein Checklisten-Formular und gibt True zurück wenn Änderungen gespeichert wurden"""
    fields = get_checklist_fields(checklist.checklist_typ)

    if not fields:
        st.error("Unbekannter Checklisten-Typ")
        return False

    st.markdown(f"### {checklist.checklist_typ}")
    st.markdown(f"**Partei:** {checklist.partei}")

    changed = False
    new_data = checklist.daten.copy()

    for field_key, field_def in fields.items():
        field_type = field_def["type"]
        label = field_def["label"]
        required = field_def.get("required", False)

        if field_type == "info":
            st.info(field_def["content"])
        elif field_type == "text":
            current_val = new_data.get(field_key, "")
            new_val = st.text_input(f"{label}{'*' if required else ''}", value=current_val, key=f"{checklist.checklist_id}_{field_key}")
            if new_val != current_val:
                new_data[field_key] = new_val
                changed = True
        elif field_type == "textarea":
            current_val = new_data.get(field_key, "")
            new_val = st.text_area(f"{label}{'*' if required else ''}", value=current_val, key=f"{checklist.checklist_id}_{field_key}")
            if new_val != current_val:
                new_data[field_key] = new_val
                changed = True
        elif field_type == "date":
            current_val = new_data.get(field_key)
            if isinstance(current_val, str) and current_val:
                try:
                    current_val = datetime.fromisoformat(current_val).date()
                except:
                    current_val = None
            new_val = st.date_input(f"{label}{'*' if required else ''}", value=current_val, key=f"{checklist.checklist_id}_{field_key}")
            if new_val != current_val:
                new_data[field_key] = new_val.isoformat() if new_val else None
                changed = True
        elif field_type == "select":
            current_val = new_data.get(field_key, field_def["options"][0])
            new_val = st.selectbox(f"{label}{'*' if required else ''}", options=field_def["options"], index=field_def["options"].index(current_val) if current_val in field_def["options"] else 0, key=f"{checklist.checklist_id}_{field_key}")
            if new_val != current_val:
                new_data[field_key] = new_val
                changed = True
        elif field_type == "checkbox":
            current_val = new_data.get(field_key, False)
            new_val = st.checkbox(f"{label}{'*' if required else ''}", value=current_val, key=f"{checklist.checklist_id}_{field_key}")
            if new_val != current_val:
                new_data[field_key] = new_val
                changed = True

    # Prüfe Vollständigkeit
    is_complete = True
    for field_key, field_def in fields.items():
        if field_def.get("required", False) and field_def["type"] != "info":
            if field_key not in new_data or not new_data[field_key]:
                is_complete = False
                break

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Speichern", key=f"save_{checklist.checklist_id}"):
            checklist.daten = new_data
            checklist.vollstaendig = is_complete
            checklist.updated_at = datetime.now()
            st.session_state.notar_checklists[checklist.checklist_id] = checklist
            st.success("Checkliste gespeichert!")
            changed = True

    with col2:
        if is_complete and not checklist.freigegeben:
            if st.button("Freigeben", key=f"release_{checklist.checklist_id}"):
                checklist.freigegeben = True
                st.session_state.notar_checklists[checklist.checklist_id] = checklist
                st.success("Checkliste freigegeben!")
                changed = True

    with col3:
        status = "✅ Vollständig" if is_complete else "⚠️ Unvollständig"
        if checklist.freigegeben:
            status += " (Freigegeben)"
        st.markdown(f"**Status:** {status}")

    return changed

# ============================================================================
# BANKENMAPPE-GENERATOR
# ============================================================================

def create_bank_folder(projekt_id: str, erstellt_von: str) -> str:
    """Erstellt eine neue Bankenmappe für ein Projekt"""
    folder_id = f"bankfolder_{len(st.session_state.bank_folders)}"

    projekt = st.session_state.projekte.get(projekt_id)
    if not projekt:
        return None

    # Exposé-ID hinzufügen falls vorhanden
    expose_id = projekt.expose_data_id if projekt.expose_data_id else None

    bank_folder = BankFolder(
        folder_id=folder_id,
        projekt_id=projekt_id,
        erstellt_von=erstellt_von,
        expose_id=expose_id
    )

    st.session_state.bank_folders[folder_id] = bank_folder
    return folder_id

def render_bank_folder_view():
    """Rendert die Bankenmappe-Verwaltung"""
    st.markdown("### 💼 Bankenmappe-Generator")
    st.info("Erstellen Sie automatisch eine Bankenmappe mit allen relevanten Unterlagen für die Finanzierung.")

    makler_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.makler_id == makler_id]

    if not projekte:
        st.warning("Keine Projekte vorhanden.")
        return

    # Projekt auswählen
    projekt_options = {f"{p.name} (ID: {p.projekt_id})": p.projekt_id for p in projekte}
    selected_projekt_label = st.selectbox("Projekt auswählen:", list(projekt_options.keys()), key="bankfolder_projekt")
    selected_projekt_id = projekt_options[selected_projekt_label]
    selected_projekt = st.session_state.projekte[selected_projekt_id]

    st.markdown("---")

    # Prüfe ob bereits eine Bankenmappe für dieses Projekt existiert
    existing_folder = None
    for folder in st.session_state.bank_folders.values():
        if folder.projekt_id == selected_projekt_id:
            existing_folder = folder
            break

    if existing_folder:
        st.success(f"✅ Bankenmappe vorhanden (erstellt am {existing_folder.created_at.strftime('%d.%m.%Y')})")

        # Inhalt der Bankenmappe anzeigen
        st.markdown("#### 📋 Inhalt der Bankenmappe")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Exposé:**")
            if existing_folder.expose_id:
                expose = st.session_state.expose_data.get(existing_folder.expose_id)
                if expose:
                    st.write(f"✅ {expose.objekttitel}")
                else:
                    st.write("❌ Nicht gefunden")
            else:
                st.write("❌ Nicht hinzugefügt")

            st.markdown("**Grundrisse:**")
            if existing_folder.grundrisse_ids:
                st.write(f"✅ {len(existing_folder.grundrisse_ids)} Grundrisse")
            else:
                st.write("❌ Keine Grundrisse")

        with col2:
            st.markdown("**Weitere Dokumente:**")
            if existing_folder.dokument_ids:
                st.write(f"✅ {len(existing_folder.dokument_ids)} Dokumente")
            else:
                st.write("❌ Keine weiteren Dokumente")

            st.markdown("**Status:**")
            st.write(f"📊 {existing_folder.status}")

        st.markdown("---")

        # Dokumente zur Bankenmappe hinzufügen
        with st.expander("➕ Dokumente hinzufügen/verwalten"):
            st.markdown("##### Verfügbare Dokumente aus dem Projekt")

            # Exposé automatisch hinzufügen
            if selected_projekt.expose_data_id and not existing_folder.expose_id:
                if st.button("Exposé zur Bankenmappe hinzufügen", key="add_expose_to_folder"):
                    existing_folder.expose_id = selected_projekt.expose_data_id
                    st.session_state.bank_folders[existing_folder.folder_id] = existing_folder
                    st.success("Exposé hinzugefügt!")
                    st.rerun()

            st.markdown("**Hochgeladene Dokumente können hier hinzugefügt werden**")
            st.info("In einer vollständigen Implementierung würden hier alle Projektdokumente aufgelistet.")

        # Bankenmappe generieren
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📥 PDF generieren", type="primary"):
                st.info("PDF-Generierung mit allen Dokumenten würde hier mit reportlab/PyPDF2 erfolgen")
                existing_folder.status = "Generiert"
                existing_folder.pdf_data = b"PDF_PLACEHOLDER"  # Hier würde das echte PDF sein
                st.session_state.bank_folders[existing_folder.folder_id] = existing_folder

        with col2:
            if existing_folder.pdf_data:
                st.download_button(
                    "📤 Bankenmappe herunterladen",
                    existing_folder.pdf_data,
                    file_name=f"Bankenmappe_{selected_projekt.name}.pdf",
                    mime="application/pdf"
                )

        with col3:
            if st.button("📧 Per E-Mail versenden"):
                st.info("E-Mail-Versand würde hier implementiert werden")

        # Checkliste anzeigen
        st.markdown("---")
        st.markdown("#### ✅ Checkliste Bankenmappe")

        checklist_items = [
            ("Exposé", existing_folder.expose_id is not None),
            ("Grundrisse", len(existing_folder.grundrisse_ids) > 0),
            ("Kaufvertragsentwurf", False),  # Placeholder
            ("Grundbuchauszug", False),  # Placeholder
            ("Teilungserklärung (bei WEG)", selected_projekt.property_type == PropertyType.WOHNUNG.value),
            ("Energieausweis", False),  # Placeholder
            ("Finanzierungsbestätigung", False),  # Placeholder
        ]

        for item, completed in checklist_items:
            if completed:
                st.markdown(f"✅ {item}")
            else:
                st.markdown(f"⬜ {item}")

    else:
        st.info("Noch keine Bankenmappe für dieses Projekt erstellt.")

        if st.button("➕ Bankenmappe erstellen", type="primary"):
            folder_id = create_bank_folder(selected_projekt_id, makler_id)
            if folder_id:
                st.success("Bankenmappe erfolgreich erstellt!")
                st.rerun()
            else:
                st.error("Fehler beim Erstellen der Bankenmappe")

    st.markdown("---")
    st.markdown("#### ℹ️ Was ist eine Bankenmappe?")
    st.markdown("""
    Die Bankenmappe enthält alle relevanten Unterlagen für die Finanzierungsprüfung durch Banken:
    - **Exposé** mit allen Objektdaten
    - **Grundrisse** und Lagepläne
    - **Kaufvertragsentwurf** (vom Notar)
    - **Grundbuchauszug** (aktuell, nicht älter als 3 Monate)
    - **Teilungserklärung** (bei Eigentumswohnungen)
    - **WEG-Protokolle** der letzten 2 Jahre (bei WEG)
    - **Energieausweis**
    - **Wirtschaftsplan** (bei WEG)
    - **Wohnflächenberechnung**
    - **Finanzierungsbestätigung** des Käufers
    """)

# ============================================================================
# DOKUMENTEN-ANFORDERUNGS-SYSTEM
# ============================================================================

def create_document_request(projekt_id: str, dokument_typ: str, angefordert_von: str, angefordert_bei: str, nachricht: str = ""):
    """Erstellt eine neue Dokumentenanforderung"""
    request_id = f"req_{len(st.session_state.document_requests)}"
    request = DocumentRequest(
        request_id=request_id,
        projekt_id=projekt_id,
        dokument_typ=dokument_typ,
        angefordert_von=angefordert_von,
        angefordert_bei=angefordert_bei,
        nachricht=nachricht
    )
    st.session_state.document_requests[request_id] = request

    # Benachrichtigung an Empfänger
    empfaenger = st.session_state.users.get(angefordert_bei)
    anforderer = st.session_state.users.get(angefordert_von)
    if empfaenger and anforderer:
        create_notification(
            angefordert_bei,
            "Neue Dokumentenanforderung",
            f"{anforderer.name} hat das Dokument '{dokument_typ}' angefordert.",
            NotificationType.INFO.value
        )

    return request_id

def render_document_requests_view(user_id: str, user_role: str):
    """Rendert die Dokumentenanforderungs-Ansicht für einen Benutzer"""

    st.markdown("### 📋 Dokumentenanforderungen")

    tabs = st.tabs(["Meine Anfragen", "An mich gerichtet", "Neue Anfrage erstellen"])

    # Meine Anfragen (die ich gestellt habe)
    with tabs[0]:
        st.subheader("📤 Von mir gestellte Anfragen")
        my_requests = [r for r in st.session_state.document_requests.values() if r.angefordert_von == user_id]

        if not my_requests:
            st.info("Sie haben noch keine Dokumentenanforderungen gestellt.")
        else:
            for request in my_requests:
                empfaenger = st.session_state.users.get(request.angefordert_bei)
                empfaenger_name = empfaenger.name if empfaenger else "Unbekannt"

                status_icon = {
                    DocumentRequestStatus.ANGEFORDERT.value: "⏳",
                    DocumentRequestStatus.BEREITGESTELLT.value: "✅",
                    DocumentRequestStatus.FEHLT.value: "❌",
                    DocumentRequestStatus.NICHT_RELEVANT.value: "⊘"
                }.get(request.status, "❓")

                with st.expander(f"{status_icon} {request.dokument_typ} - von {empfaenger_name}"):
                    st.write(f"**Status:** {request.status}")
                    st.write(f"**Erstellt:** {request.created_at.strftime('%d.%m.%Y %H:%M')}")
                    if request.nachricht:
                        st.write(f"**Nachricht:** {request.nachricht}")

                    if request.status == DocumentRequestStatus.BEREITGESTELLT.value and request.bereitgestellt_am:
                        st.success(f"Bereitgestellt am: {request.bereitgestellt_am.strftime('%d.%m.%Y %H:%M')}")

    # An mich gerichtete Anfragen
    with tabs[1]:
        st.subheader("📥 An mich gerichtete Anfragen")
        requests_to_me = [r for r in st.session_state.document_requests.values() if r.angefordert_bei == user_id]

        if not requests_to_me:
            st.info("Es liegen keine Dokumentenanforderungen an Sie vor.")
        else:
            for request in requests_to_me:
                anforderer = st.session_state.users.get(request.angefordert_von)
                anforderer_name = anforderer.name if anforderer else "Unbekannt"

                status_icon = {
                    DocumentRequestStatus.ANGEFORDERT.value: "⏳",
                    DocumentRequestStatus.BEREITGESTELLT.value: "✅",
                    DocumentRequestStatus.FEHLT.value: "❌",
                    DocumentRequestStatus.NICHT_RELEVANT.value: "⊘"
                }.get(request.status, "❓")

                with st.expander(f"{status_icon} {request.dokument_typ} - von {anforderer_name}", expanded=(request.status == DocumentRequestStatus.ANGEFORDERT.value)):
                    st.write(f"**Dokument:** {request.dokument_typ}")
                    st.write(f"**Angefordert von:** {anforderer_name}")
                    st.write(f"**Erstellt:** {request.created_at.strftime('%d.%m.%Y %H:%M')}")
                    if request.nachricht:
                        st.info(f"**Nachricht:** {request.nachricht}")

                    st.markdown("---")

                    # Status ändern
                    new_status = st.selectbox(
                        "Status ändern:",
                        options=[s.value for s in DocumentRequestStatus],
                        index=[s.value for s in DocumentRequestStatus].index(request.status),
                        key=f"status_{request.request_id}"
                    )

                    if new_status != request.status:
                        if st.button("Status aktualisieren", key=f"update_status_{request.request_id}"):
                            request.status = new_status
                            if new_status == DocumentRequestStatus.BEREITGESTELLT.value:
                                request.bereitgestellt_am = datetime.now()

                                # Benachrichtigung an Anforderer
                                create_notification(
                                    request.angefordert_von,
                                    "Dokument bereitgestellt",
                                    f"{st.session_state.users[user_id].name} hat '{request.dokument_typ}' bereitgestellt.",
                                    NotificationType.SUCCESS.value
                                )

                            st.session_state.document_requests[request.request_id] = request
                            st.success("Status aktualisiert!")
                            st.rerun()

                    # Dokument hochladen (optional)
                    if request.status == DocumentRequestStatus.ANGEFORDERT.value:
                        uploaded_doc = st.file_uploader("Dokument hochladen", type=["pdf", "jpg", "jpeg", "png"], key=f"upload_doc_{request.request_id}")
                        if uploaded_doc:
                            if st.button("Dokument hochladen und als bereitgestellt markieren", key=f"upload_submit_{request.request_id}"):
                                # Hier würde man das Dokument in wirtschaftsdaten oder einen anderen Speicher legen
                                st.info("Dokument-Upload würde hier implementiert werden (in wirtschaftsdaten speichern)")
                                request.status = DocumentRequestStatus.BEREITGESTELLT.value
                                request.bereitgestellt_am = datetime.now()
                                st.session_state.document_requests[request.request_id] = request

                                # Benachrichtigung
                                create_notification(
                                    request.angefordert_von,
                                    "Dokument bereitgestellt",
                                    f"{st.session_state.users[user_id].name} hat '{request.dokument_typ}' hochgeladen.",
                                    NotificationType.SUCCESS.value
                                )
                                st.success("Dokument hochgeladen und Status aktualisiert!")
                                st.rerun()

    # Neue Anfrage erstellen
    with tabs[2]:
        st.subheader("➕ Neue Dokumentenanforderung erstellen")

        # Projekt auswählen
        if user_role == UserRole.MAKLER.value:
            projekte = [p for p in st.session_state.projekte.values() if p.makler_id == user_id]
        elif user_role == UserRole.NOTAR.value:
            projekte = [p for p in st.session_state.projekte.values() if p.notar_id == user_id]
        else:
            projekte = [p for p in st.session_state.projekte.values() if user_id in p.kaeufer_ids + p.verkaeufer_ids]

        if not projekte:
            st.warning("Sie sind keinem Projekt zugeordnet.")
            return

        projekt_options = {f"{p.name} (ID: {p.projekt_id})": p.projekt_id for p in projekte}
        selected_projekt_label = st.selectbox("Projekt auswählen:", list(projekt_options.keys()), key="new_req_projekt")
        selected_projekt_id = projekt_options[selected_projekt_label]
        selected_projekt = st.session_state.projekte[selected_projekt_id]

        # Empfänger auswählen
        empfaenger_options = {}
        for kid in selected_projekt.kaeufer_ids:
            k = st.session_state.users.get(kid)
            if k:
                empfaenger_options[f"Käufer: {k.name}"] = kid
        for vid in selected_projekt.verkaeufer_ids:
            v = st.session_state.users.get(vid)
            if v:
                empfaenger_options[f"Verkäufer: {v.name}"] = vid

        if not empfaenger_options:
            st.warning("Keine Empfänger in diesem Projekt verfügbar.")
            return

        empfaenger_label = st.selectbox("An wen soll die Anfrage gerichtet werden:", list(empfaenger_options.keys()), key="new_req_empf")
        empfaenger_id = empfaenger_options[empfaenger_label]

        dokument_typ = st.text_input("Dokument-Typ:", placeholder="z.B. Personalausweis, Grundbuchauszug, etc.", key="new_req_typ")
        nachricht = st.text_area("Nachricht (optional):", placeholder="Zusätzliche Informationen zur Anforderung", key="new_req_msg")

        if st.button("Anforderung erstellen", type="primary"):
            if dokument_typ:
                create_document_request(
                    projekt_id=selected_projekt_id,
                    dokument_typ=dokument_typ,
                    angefordert_von=user_id,
                    angefordert_bei=empfaenger_id,
                    nachricht=nachricht
                )
                st.success(f"Anforderung für '{dokument_typ}' wurde erstellt!")
                st.rerun()
            else:
                st.error("Bitte geben Sie einen Dokument-Typ an.")

# ============================================================================
# EXPOSÉ-GENERATOR-FUNKTIONEN
# ============================================================================

def validate_address_online(strasse: str, hausnummer: str, plz: str, ort: str, land: str) -> Dict[str, Any]:
    """
    Validiert eine Adresse über eine Online-API (Nominatim/OpenStreetMap).
    Gibt ein Dict mit validierter Adresse oder Vorschlag zurück.
    """
    import urllib.request
    import urllib.parse

    try:
        # Adresse zusammenbauen
        query = f"{strasse} {hausnummer}, {plz} {ort}, {land}"
        encoded_query = urllib.parse.quote(query)

        url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&addressdetails=1&limit=1"

        req = urllib.request.Request(url, headers={'User-Agent': 'ImmobilienApp/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

            if data and len(data) > 0:
                result = data[0]
                address = result.get('address', {})

                validated = {
                    'gefunden': True,
                    'strasse': address.get('road', strasse),
                    'hausnummer': address.get('house_number', hausnummer),
                    'plz': address.get('postcode', plz),
                    'ort': address.get('city') or address.get('town') or address.get('village', ort),
                    'land': address.get('country', land),
                    'lat': result.get('lat'),
                    'lon': result.get('lon'),
                    'display_name': result.get('display_name', '')
                }

                # Prüfe ob Abweichungen existieren
                eingabe = f"{strasse} {hausnummer}, {plz} {ort}".lower().strip()
                gefunden = f"{validated['strasse']} {validated['hausnummer']}, {validated['plz']} {validated['ort']}".lower().strip()

                validated['abweichung'] = eingabe != gefunden
                return validated
            else:
                return {'gefunden': False, 'nachricht': 'Adresse nicht gefunden'}
    except Exception as e:
        return {'gefunden': False, 'nachricht': f'Fehler bei Validierung: {str(e)}'}


def calculate_price_suggestion(expose: 'ExposeData') -> float:
    """
    Berechnet einen Kaufpreis-Vorschlag basierend auf den Objektdaten.
    Einfaches Modell basierend auf Durchschnittspreisen.
    """
    # Basis-Preise pro m² (vereinfacht, je nach Region unterschiedlich)
    basis_preise = {
        "Wohnung": 3500,
        "Haus": 3000,
        "Mehrfamilienhaus": 2500,
        "Grundstück/Land": 150,
    }

    basis = basis_preise.get(expose.objektart, 3000)

    # Fläche bestimmen
    if expose.objektart == "Grundstück/Land":
        flaeche = expose.grundstuecksflaeche if expose.grundstuecksflaeche > 0 else 500
    else:
        flaeche = expose.wohnflaeche if expose.wohnflaeche > 0 else 80

    # Zuschläge/Abschläge
    faktor = 1.0

    # Zustand
    zustand_faktoren = {
        "Erstbezug": 1.3,
        "Neuwertig": 1.2,
        "Renoviert": 1.1,
        "Gepflegt": 1.0,
        "Sanierungsbedürftig": 0.7,
    }
    faktor *= zustand_faktoren.get(expose.zustand, 1.0)

    # Baujahr
    if expose.baujahr > 0:
        alter = 2024 - expose.baujahr
        if alter < 5:
            faktor *= 1.15
        elif alter < 20:
            faktor *= 1.05
        elif alter > 50:
            faktor *= 0.85

    # Ausstattung
    if expose.hat_meerblick:
        faktor *= 1.25
    if expose.hat_fahrstuhl:
        faktor *= 1.05
    if expose.hat_balkon or expose.hat_terrasse:
        faktor *= 1.05
    if expose.hat_garage or expose.hat_tiefgarage:
        faktor *= 1.03
    if expose.hat_schwimmbad or expose.hat_gemeinschaftspool:
        faktor *= 1.08

    # Energieeffizienz
    if expose.energieeffizienzklasse in ["A+", "A", "B"]:
        faktor *= 1.05
    elif expose.energieeffizienzklasse in ["G", "H"]:
        faktor *= 0.95

    vorschlag = basis * flaeche * faktor
    return round(vorschlag, -3)  # Auf 1000er runden


# ============================================================================
# TERMIN-KOORDINATION FUNKTIONEN
# ============================================================================

def generate_ics_file(termin: 'Termin', projekt: 'Projekt') -> str:
    """Generiert eine ICS-Kalenderdatei für einen Termin"""
    from datetime import datetime, timedelta

    # Datum und Zeit kombinieren
    start_hour, start_min = map(int, termin.uhrzeit_start.split(':'))
    end_hour, end_min = map(int, termin.uhrzeit_ende.split(':'))

    start_dt = datetime.combine(termin.datum, datetime.min.time().replace(hour=start_hour, minute=start_min))
    end_dt = datetime.combine(termin.datum, datetime.min.time().replace(hour=end_hour, minute=end_min))

    # Teilnehmer sammeln
    teilnehmer_info = []
    for kontakt in termin.kontakte:
        teilnehmer_info.append(f"{kontakt.get('name', '')} ({kontakt.get('rolle', '')}): {kontakt.get('telefon', '')}")

    beschreibung = f"""Termin: {termin.termin_typ}
Projekt: {projekt.name}

Teilnehmer:
{chr(10).join(teilnehmer_info)}

Hinweis: Bitte bringen Sie einen gültigen Personalausweis oder Reisepass mit.
"""

    # ICS Format
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Immobilien-Transaktionsplattform//DE
BEGIN:VEVENT
UID:{termin.termin_id}@immobilien-plattform.de
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}
DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}
SUMMARY:{termin.termin_typ}: {projekt.name}
DESCRIPTION:{beschreibung.replace(chr(10), '\\n')}
LOCATION:{termin.ort}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

    return ics_content


def send_appointment_email(empfaenger: List[Dict[str, str]], termin: 'Termin', projekt: 'Projekt', email_typ: str = "bestaetigung"):
    """Simuliert das Senden von Termin-E-Mails

    Args:
        empfaenger: Liste von {email, name}
        termin: Der Termin
        projekt: Das Projekt
        email_typ: "bestaetigung", "erinnerung", "vorschlag"
    """
    # In einer echten Anwendung würde hier SMTP verwendet
    # Hier simulieren wir das Senden durch Logging

    email_templates = {
        "bestaetigung": f"""
Sehr geehrte(r) {{name}},

Ihr Termin wurde bestätigt:

Termin: {termin.termin_typ}
Datum: {termin.datum.strftime('%d.%m.%Y')}
Uhrzeit: {termin.uhrzeit_start} - {termin.uhrzeit_ende} Uhr
Ort: {termin.ort}
Projekt: {projekt.name}

Bitte bringen Sie einen gültigen Personalausweis oder Reisepass mit.

Im Anhang finden Sie eine Kalenderdatei zur Übernahme in Ihren Kalender.

Mit freundlichen Grüßen,
Ihre Immobilien-Transaktionsplattform
        """,
        "erinnerung": f"""
Sehr geehrte(r) {{name}},

Dies ist eine Erinnerung an Ihren morgigen Termin:

Termin: {termin.termin_typ}
Datum: {termin.datum.strftime('%d.%m.%Y')}
Uhrzeit: {termin.uhrzeit_start} - {termin.uhrzeit_ende} Uhr
Ort: {termin.ort}
Projekt: {projekt.name}

Bitte bringen Sie einen gültigen Personalausweis oder Reisepass mit.

Mit freundlichen Grüßen,
Ihre Immobilien-Transaktionsplattform
        """,
        "vorschlag": f"""
Sehr geehrte(r) {{name}},

Der Notar hat Terminvorschläge für die Beurkundung erstellt.
Bitte prüfen Sie die Vorschläge in Ihrem Dashboard und wählen Sie einen passenden Termin aus.

Projekt: {projekt.name}

Mit freundlichen Grüßen,
Ihre Immobilien-Transaktionsplattform
        """
    }

    # Simuliertes Senden - in der realen Anwendung würde hier SMTP verwendet
    sent_emails = []
    for emp in empfaenger:
        email_text = email_templates.get(email_typ, "").format(name=emp.get('name', 'Teilnehmer'))
        sent_emails.append({
            'to': emp.get('email'),
            'subject': f"[{email_typ.capitalize()}] {termin.termin_typ} - {projekt.name}",
            'body': email_text,
            'sent_at': datetime.now()
        })

    return sent_emails


def check_kaufvertrag_entwurf_status(projekt_id: str) -> bool:
    """Prüft, ob der Kaufvertragsentwurf bereits versendet wurde (Timeline-Check)"""
    projekt = st.session_state.projekte.get(projekt_id)
    if not projekt:
        return False

    # Prüfe Timeline-Events für versendeten Entwurf
    for event_id in projekt.timeline_events:
        event = st.session_state.timeline_events.get(event_id)
        if event and "Kaufvertrag" in event.titel and event.completed:
            return True

    # Alternative: Prüfe den Projekt-Status
    return projekt.status in [
        ProjektStatus.FINANZIERUNG_GESICHERT.value,
        ProjektStatus.NOTARTERMIN_VEREINBART.value,
        ProjektStatus.KAUFVERTRAG_UNTERZEICHNET.value,
        ProjektStatus.ABGESCHLOSSEN.value
    ]


def get_notar_calendar_availability(notar_id: str, datum_von: date, datum_bis: date) -> List[Dict[str, Any]]:
    """Simuliert die Outlook-Kalenderprüfung des Notars

    Returns:
        Liste von verfügbaren Zeitslots
    """
    import random

    verfuegbare_slots = []

    # Simuliere Kalenderverfügbarkeit
    current_date = datum_von
    while current_date <= datum_bis:
        # Wochenenden überspringen
        if current_date.weekday() < 5:  # Mo-Fr
            # Vormittag (9:00 - 12:00)
            if random.random() > 0.3:  # 70% Chance verfügbar
                verfuegbare_slots.append({
                    'datum': current_date,
                    'tageszeit': 'Vormittag',
                    'uhrzeit_start': f"{random.choice([9, 10, 11])}:00",
                    'uhrzeit_ende': f"{random.choice([10, 11, 12])}:00"
                })

            # Nachmittag (14:00 - 17:00)
            if random.random() > 0.3:  # 70% Chance verfügbar
                verfuegbare_slots.append({
                    'datum': current_date,
                    'tageszeit': 'Nachmittag',
                    'uhrzeit_start': f"{random.choice([14, 15, 16])}:00",
                    'uhrzeit_ende': f"{random.choice([15, 16, 17])}:00"
                })

        current_date += timedelta(days=1)

    return verfuegbare_slots


def create_termin_vorschlaege(projekt_id: str, notar_id: str, termin_typ: str = TerminTyp.BEURKUNDUNG.value) -> Optional['TerminVorschlag']:
    """Erstellt 3 Terminvorschläge basierend auf Notar-Kalenderverfügbarkeit"""

    projekt = st.session_state.projekte.get(projekt_id)
    if not projekt:
        return None

    # Prüfe ob Kaufvertragsentwurf versendet wurde (nur für Beurkundung)
    if termin_typ == TerminTyp.BEURKUNDUNG.value:
        if not check_kaufvertrag_entwurf_status(projekt_id):
            return None  # Kann keine Beurkundungstermine vorschlagen ohne Entwurf

    # Hole verfügbare Slots aus dem Kalender
    heute = date.today()
    verfuegbar = get_notar_calendar_availability(
        notar_id,
        heute + timedelta(days=7),  # Ab nächster Woche
        heute + timedelta(days=30)  # Bis in 4 Wochen
    )

    if len(verfuegbar) < 3:
        return None

    # Wähle 3 verschiedene Slots aus
    import random
    random.shuffle(verfuegbar)
    ausgewaehlte_slots = verfuegbar[:3]

    # Erstelle Terminvorschlag
    vorschlag_id = f"vorschlag_{len(st.session_state.terminvorschlaege)}"
    vorschlag = TerminVorschlag(
        vorschlag_id=vorschlag_id,
        projekt_id=projekt_id,
        termin_typ=termin_typ,
        vorschlaege=[
            {
                'datum': slot['datum'],
                'uhrzeit_start': slot['uhrzeit_start'],
                'uhrzeit_ende': slot['uhrzeit_ende'],
                'tageszeit': slot['tageszeit']
            }
            for slot in ausgewaehlte_slots
        ],
        erstellt_von=notar_id
    )

    st.session_state.terminvorschlaege[vorschlag_id] = vorschlag
    return vorschlag


def create_termin_from_vorschlag(vorschlag: 'TerminVorschlag', ausgewaehlter_index: int, projekt: 'Projekt') -> Optional['Termin']:
    """Erstellt einen Termin aus einem angenommenen Vorschlag"""

    if ausgewaehlter_index < 0 or ausgewaehlter_index >= len(vorschlag.vorschlaege):
        return None

    slot = vorschlag.vorschlaege[ausgewaehlter_index]

    # Kontakte sammeln
    kontakte = []

    # Makler
    if projekt.makler_id:
        makler = st.session_state.users.get(projekt.makler_id)
        if makler:
            kontakte.append({
                'name': makler.name,
                'telefon': makler.telefon if hasattr(makler, 'telefon') else '',
                'rolle': 'Makler'
            })

    # Käufer
    for kaeufer_id in projekt.kaeufer_ids:
        kaeufer = st.session_state.users.get(kaeufer_id)
        if kaeufer:
            kontakte.append({
                'name': kaeufer.name,
                'telefon': kaeufer.telefon if hasattr(kaeufer, 'telefon') else '',
                'rolle': 'Käufer'
            })

    # Verkäufer
    for verkaeufer_id in projekt.verkaeufer_ids:
        verkaeufer = st.session_state.users.get(verkaeufer_id)
        if verkaeufer:
            kontakte.append({
                'name': verkaeufer.name,
                'telefon': verkaeufer.telefon if hasattr(verkaeufer, 'telefon') else '',
                'rolle': 'Verkäufer'
            })

    # Notar
    if projekt.notar_id:
        notar = st.session_state.users.get(projekt.notar_id)
        if notar:
            kontakte.append({
                'name': notar.name,
                'telefon': notar.telefon if hasattr(notar, 'telefon') else '',
                'rolle': 'Notar'
            })

    # Termin-Titel erstellen: "Verkäufer ./. Käufer, Projektname (Makler)"
    verkaeufer_namen = [st.session_state.users.get(vid).name for vid in projekt.verkaeufer_ids
                        if st.session_state.users.get(vid)]
    kaeufer_namen = [st.session_state.users.get(kid).name for kid in projekt.kaeufer_ids
                     if st.session_state.users.get(kid)]
    makler_name = ""
    if projekt.makler_id:
        makler = st.session_state.users.get(projekt.makler_id)
        if makler:
            makler_name = f" ({makler.name})"

    termin_titel = f"{', '.join(verkaeufer_namen)} ./. {', '.join(kaeufer_namen)}, {projekt.name}{makler_name}"

    # Notar-Adresse als Ort
    notar = st.session_state.users.get(projekt.notar_id)
    ort = "Notariat"  # Default
    if notar and hasattr(notar, 'adresse'):
        ort = notar.adresse

    termin_id = f"termin_{len(st.session_state.termine)}"
    termin = Termin(
        termin_id=termin_id,
        projekt_id=projekt.projekt_id,
        termin_typ=vorschlag.termin_typ,
        datum=slot['datum'],
        uhrzeit_start=slot['uhrzeit_start'],
        uhrzeit_ende=slot['uhrzeit_ende'],
        tageszeit=slot['tageszeit'],
        ort=ort,
        beschreibung=termin_titel,
        status=TerminStatus.AUSSTEHEND.value,
        erstellt_von=vorschlag.erstellt_von,
        kontakte=kontakte,
        outlook_status="provisorisch"
    )

    st.session_state.termine[termin_id] = termin

    # Vorschlag als angenommen markieren
    vorschlag.status = "angenommen"
    vorschlag.ausgewaehlt_index = ausgewaehlter_index
    st.session_state.terminvorschlaege[vorschlag.vorschlag_id] = vorschlag

    # Termin zum Projekt hinzufügen
    if termin_id not in projekt.termine:
        projekt.termine.append(termin_id)
        st.session_state.projekte[projekt.projekt_id] = projekt

    return termin


def check_termin_bestaetigung(termin: 'Termin', projekt: 'Projekt') -> Dict[str, Any]:
    """Prüft den Bestätigungsstatus eines Termins"""

    result = {
        'alle_bestaetigt': False,
        'makler_bestaetigt': termin.bestaetigt_von_makler is not None,
        'notar_bestaetigt': termin.bestaetigt_von_notar is not None,
        'kaeufer_bestaetigt': [],
        'kaeufer_ausstehend': [],
        'verkaeufer_bestaetigt': [],
        'verkaeufer_ausstehend': []
    }

    # Käufer prüfen
    for kaeufer_id in projekt.kaeufer_ids:
        if kaeufer_id in termin.bestaetigt_von_kaeufer:
            result['kaeufer_bestaetigt'].append(kaeufer_id)
        else:
            result['kaeufer_ausstehend'].append(kaeufer_id)

    # Verkäufer prüfen
    for verkaeufer_id in projekt.verkaeufer_ids:
        if verkaeufer_id in termin.bestaetigt_von_verkaeufer:
            result['verkaeufer_bestaetigt'].append(verkaeufer_id)
        else:
            result['verkaeufer_ausstehend'].append(verkaeufer_id)

    # Prüfen ob alle bestätigt haben
    makler_ok = not projekt.makler_id or result['makler_bestaetigt']
    kaeufer_ok = len(result['kaeufer_ausstehend']) == 0
    verkaeufer_ok = len(result['verkaeufer_ausstehend']) == 0

    result['alle_bestaetigt'] = makler_ok and kaeufer_ok and verkaeufer_ok

    return result


def bestatige_termin(termin_id: str, user_id: str, rolle: str):
    """Bestätigt einen Termin für einen Benutzer"""

    termin = st.session_state.termine.get(termin_id)
    if not termin:
        return False

    projekt = st.session_state.projekte.get(termin.projekt_id)
    if not projekt:
        return False

    now = datetime.now()

    if rolle == UserRole.MAKLER.value:
        termin.bestaetigt_von_makler = now
    elif rolle == UserRole.KAEUFER.value:
        if user_id not in termin.bestaetigt_von_kaeufer:
            termin.bestaetigt_von_kaeufer.append(user_id)
    elif rolle == UserRole.VERKAEUFER.value:
        if user_id not in termin.bestaetigt_von_verkaeufer:
            termin.bestaetigt_von_verkaeufer.append(user_id)
    elif rolle == UserRole.NOTAR.value:
        termin.bestaetigt_von_notar = now

    # Prüfen ob alle bestätigt haben
    status = check_termin_bestaetigung(termin, projekt)

    if status['alle_bestaetigt']:
        termin.status = TerminStatus.BESTAETIGT.value
        termin.outlook_status = "bestätigt"

        # E-Mail-Benachrichtigungen senden
        empfaenger = []
        for kontakt in termin.kontakte:
            user = None
            if kontakt.get('rolle') == 'Makler' and projekt.makler_id:
                user = st.session_state.users.get(projekt.makler_id)
            elif kontakt.get('rolle') == 'Käufer':
                for kid in projekt.kaeufer_ids:
                    u = st.session_state.users.get(kid)
                    if u and u.name == kontakt.get('name'):
                        user = u
                        break
            elif kontakt.get('rolle') == 'Verkäufer':
                for vid in projekt.verkaeufer_ids:
                    u = st.session_state.users.get(vid)
                    if u and u.name == kontakt.get('name'):
                        user = u
                        break
            elif kontakt.get('rolle') == 'Notar' and projekt.notar_id:
                user = st.session_state.users.get(projekt.notar_id)

            if user:
                empfaenger.append({'email': user.email, 'name': user.name})

        send_appointment_email(empfaenger, termin, projekt, "bestaetigung")
    elif len(termin.bestaetigt_von_kaeufer) > 0 or len(termin.bestaetigt_von_verkaeufer) > 0 or termin.bestaetigt_von_makler:
        termin.status = TerminStatus.TEILWEISE_BESTAETIGT.value

    st.session_state.termine[termin_id] = termin
    return True


def render_termin_verwaltung(projekt: 'Projekt', user_rolle: str):
    """Rendert die Termin-Verwaltung UI"""

    st.markdown("#### 📅 Terminverwaltung")

    # Tabs für verschiedene Termintypen
    termin_tabs = st.tabs(["🔍 Besichtigung", "🔑 Übergabe", "📜 Beurkundung", "📋 Alle Termine"])

    with termin_tabs[0]:
        render_termin_section(projekt, TerminTyp.BESICHTIGUNG.value, user_rolle)

    with termin_tabs[1]:
        render_termin_section(projekt, TerminTyp.UEBERGABE.value, user_rolle)

    with termin_tabs[2]:
        render_termin_section(projekt, TerminTyp.BEURKUNDUNG.value, user_rolle)

    with termin_tabs[3]:
        render_alle_termine(projekt, user_rolle)


def render_termin_section(projekt: 'Projekt', termin_typ: str, user_rolle: str):
    """Rendert eine Termin-Sektion für einen bestimmten Termintyp"""

    # Bestehende Termine für diesen Typ anzeigen
    projekt_termine = [st.session_state.termine.get(tid) for tid in projekt.termine
                      if st.session_state.termine.get(tid) and
                      st.session_state.termine.get(tid).termin_typ == termin_typ]

    if projekt_termine:
        for termin in projekt_termine:
            render_termin_card(termin, projekt, user_rolle)
    else:
        st.info(f"Noch keine {termin_typ}-Termine vorhanden.")

    # Offene Terminvorschläge anzeigen
    offene_vorschlaege = [v for v in st.session_state.terminvorschlaege.values()
                         if v.projekt_id == projekt.projekt_id and
                         v.termin_typ == termin_typ and
                         v.status == "offen"]

    if offene_vorschlaege:
        st.markdown("##### 📨 Offene Terminvorschläge")
        for vorschlag in offene_vorschlaege:
            render_terminvorschlag_card(vorschlag, projekt, user_rolle)

    # Neuen Termin anlegen (nur für bestimmte Rollen)
    if user_rolle in [UserRole.MAKLER.value, UserRole.NOTAR.value]:
        with st.expander(f"➕ Neuen {termin_typ}-Termin anlegen"):
            render_neuer_termin_form(projekt, termin_typ, user_rolle)


def render_termin_card(termin: 'Termin', projekt: 'Projekt', user_rolle: str):
    """Rendert eine Termin-Karte"""

    status_colors = {
        TerminStatus.BESTAETIGT.value: "🟢",
        TerminStatus.TEILWEISE_BESTAETIGT.value: "🟡",
        TerminStatus.AUSSTEHEND.value: "🟠",
        TerminStatus.VORGESCHLAGEN.value: "🔵",
        TerminStatus.ABGESAGT.value: "🔴",
        TerminStatus.ABGESCHLOSSEN.value: "✅"
    }

    status_icon = status_colors.get(termin.status, "⚪")

    with st.container():
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            st.markdown(f"**{status_icon} {termin.termin_typ}**")
            st.write(f"📅 {termin.datum.strftime('%d.%m.%Y')} | ⏰ {termin.uhrzeit_start} - {termin.uhrzeit_ende}")
            st.write(f"📍 {termin.ort}")

        with col2:
            st.write(f"**Status:** {termin.status}")
            if termin.status == TerminStatus.BESTAETIGT.value:
                st.success("Alle Parteien haben bestätigt")

        with col3:
            # Bestätigungsbutton (wenn noch nicht bestätigt)
            user_id = st.session_state.current_user.user_id
            bereits_bestaetigt = False

            if user_rolle == UserRole.MAKLER.value:
                bereits_bestaetigt = termin.bestaetigt_von_makler is not None
            elif user_rolle == UserRole.KAEUFER.value:
                bereits_bestaetigt = user_id in termin.bestaetigt_von_kaeufer
            elif user_rolle == UserRole.VERKAEUFER.value:
                bereits_bestaetigt = user_id in termin.bestaetigt_von_verkaeufer
            elif user_rolle == UserRole.NOTAR.value:
                bereits_bestaetigt = termin.bestaetigt_von_notar is not None

            if termin.status not in [TerminStatus.BESTAETIGT.value, TerminStatus.ABGESAGT.value, TerminStatus.ABGESCHLOSSEN.value]:
                if bereits_bestaetigt:
                    st.success("✓ Sie haben bestätigt")
                else:
                    if st.button("✅ Termin bestätigen", key=f"confirm_{termin.termin_id}_{user_rolle}"):
                        bestatige_termin(termin.termin_id, user_id, user_rolle)
                        st.success("Termin bestätigt!")
                        st.rerun()

            # Download ICS
            if termin.status == TerminStatus.BESTAETIGT.value:
                ics_content = generate_ics_file(termin, projekt)
                st.download_button(
                    "📥 Kalenderdatei (.ics)",
                    data=ics_content,
                    file_name=f"termin_{termin.termin_id}.ics",
                    mime="text/calendar",
                    key=f"ics_{termin.termin_id}"
                )

        st.markdown("---")


def render_terminvorschlag_card(vorschlag: 'TerminVorschlag', projekt: 'Projekt', user_rolle: str):
    """Rendert eine Terminvorschlag-Karte"""

    st.markdown(f"**Terminvorschläge vom {vorschlag.erstellt_am.strftime('%d.%m.%Y %H:%M')}**")

    for i, slot in enumerate(vorschlag.vorschlaege):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Option {i+1}:** {slot['datum'].strftime('%d.%m.%Y')} ({slot['tageszeit']})")
            st.write(f"⏰ {slot['uhrzeit_start']} - {slot['uhrzeit_ende']} Uhr")
        with col2:
            if user_rolle in [UserRole.MAKLER.value, UserRole.KAEUFER.value, UserRole.VERKAEUFER.value]:
                if st.button(f"Auswählen", key=f"select_{vorschlag.vorschlag_id}_{i}"):
                    termin = create_termin_from_vorschlag(vorschlag, i, projekt)
                    if termin:
                        st.success(f"Termin wurde erstellt! Bitte bestätigen Sie den Termin.")
                        st.rerun()


def render_neuer_termin_form(projekt: 'Projekt', termin_typ: str, user_rolle: str):
    """Formular zum Anlegen eines neuen Termins"""

    col1, col2 = st.columns(2)

    with col1:
        datum = st.date_input("Datum", min_value=date.today(), key=f"new_termin_datum_{projekt.projekt_id}_{termin_typ}")
        tageszeit = st.selectbox("Tageszeit", ["Vormittag", "Nachmittag"], key=f"new_termin_tageszeit_{projekt.projekt_id}_{termin_typ}")

    with col2:
        uhrzeit_start = st.time_input("Beginn", value=datetime.strptime("10:00", "%H:%M").time(), key=f"new_termin_start_{projekt.projekt_id}_{termin_typ}")
        uhrzeit_ende = st.time_input("Ende", value=datetime.strptime("11:00", "%H:%M").time(), key=f"new_termin_ende_{projekt.projekt_id}_{termin_typ}")

    ort = st.text_input("Ort/Adresse", value=projekt.adresse, key=f"new_termin_ort_{projekt.projekt_id}_{termin_typ}")
    beschreibung = st.text_area("Beschreibung/Hinweise", key=f"new_termin_beschr_{projekt.projekt_id}_{termin_typ}")

    if st.button(f"Termin erstellen", key=f"create_termin_{projekt.projekt_id}_{termin_typ}"):
        # Kontakte sammeln
        kontakte = []
        if projekt.makler_id:
            makler = st.session_state.users.get(projekt.makler_id)
            if makler:
                kontakte.append({'name': makler.name, 'telefon': '', 'rolle': 'Makler'})

        for kid in projekt.kaeufer_ids:
            kaeufer = st.session_state.users.get(kid)
            if kaeufer:
                kontakte.append({'name': kaeufer.name, 'telefon': '', 'rolle': 'Käufer'})

        for vid in projekt.verkaeufer_ids:
            verkaeufer = st.session_state.users.get(vid)
            if verkaeufer:
                kontakte.append({'name': verkaeufer.name, 'telefon': '', 'rolle': 'Verkäufer'})

        if projekt.notar_id:
            notar = st.session_state.users.get(projekt.notar_id)
            if notar:
                kontakte.append({'name': notar.name, 'telefon': '', 'rolle': 'Notar'})

        termin_id = f"termin_{len(st.session_state.termine)}"
        termin = Termin(
            termin_id=termin_id,
            projekt_id=projekt.projekt_id,
            termin_typ=termin_typ,
            datum=datum,
            uhrzeit_start=uhrzeit_start.strftime("%H:%M"),
            uhrzeit_ende=uhrzeit_ende.strftime("%H:%M"),
            tageszeit=tageszeit,
            ort=ort,
            beschreibung=beschreibung,
            status=TerminStatus.AUSSTEHEND.value,
            erstellt_von=st.session_state.current_user.user_id,
            kontakte=kontakte
        )

        st.session_state.termine[termin_id] = termin

        if termin_id not in projekt.termine:
            projekt.termine.append(termin_id)
            st.session_state.projekte[projekt.projekt_id] = projekt

        st.success("✅ Termin wurde erstellt!")
        st.rerun()


def render_alle_termine(projekt: 'Projekt', user_rolle: str):
    """Zeigt alle Termine eines Projekts"""

    if not projekt.termine:
        st.info("Noch keine Termine vorhanden.")
        return

    for termin_id in projekt.termine:
        termin = st.session_state.termine.get(termin_id)
        if termin:
            render_termin_card(termin, projekt, user_rolle)


def render_expose_editor(projekt: Projekt):
    """Rendert den Exposé-Editor für ein Projekt"""

    # Expose-Daten suchen oder erstellen
    expose = None
    if projekt.expose_data_id:
        expose = st.session_state.expose_data.get(projekt.expose_data_id)

    if not expose:
        expose_id = f"expose_{len(st.session_state.expose_data)}"
        expose = ExposeData(
            expose_id=expose_id,
            projekt_id=projekt.projekt_id,
            objekttitel=projekt.name,
            objektbeschreibung=projekt.beschreibung,
            kaufpreis=projekt.kaufpreis
        )
        st.session_state.expose_data[expose_id] = expose
        projekt.expose_data_id = expose_id
        st.session_state.projekte[projekt.projekt_id] = projekt

    st.markdown("### 📄 Exposé-Daten bearbeiten")

    # Objektart auswählen
    property_type = st.selectbox(
        "Objektart*",
        options=[t.value for t in PropertyType],
        index=[t.value for t in PropertyType].index(expose.objektart) if expose.objektart else 0,
        key=f"expose_property_type_{expose.expose_id}"
    )

    # ===== ADRESSE MIT VALIDIERUNG =====
    st.markdown("#### Adresse")
    col1, col2, col3 = st.columns([3, 1, 2])
    with col1:
        strasse = st.text_input("Straße*", value=expose.strasse, key=f"expose_strasse_{expose.expose_id}")
    with col2:
        hausnummer = st.text_input("Nr.*", value=expose.hausnummer, key=f"expose_hausnr_{expose.expose_id}")
    with col3:
        plz = st.text_input("PLZ*", value=expose.plz, key=f"expose_plz_{expose.expose_id}")

    col1, col2 = st.columns(2)
    with col1:
        ort = st.text_input("Ort*", value=expose.ort, key=f"expose_ort_{expose.expose_id}")
    with col2:
        land = st.text_input("Land", value=expose.land if expose.land else "Deutschland", key=f"expose_land_{expose.expose_id}")

    # Adress-Validierung Button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Adresse prüfen", key=f"validate_addr_{expose.expose_id}"):
            if strasse and plz and ort:
                with st.spinner("Validiere Adresse..."):
                    result = validate_address_online(strasse, hausnummer, plz, ort, land)
                    st.session_state[f"addr_validation_{expose.expose_id}"] = result
            else:
                st.warning("Bitte Straße, PLZ und Ort eingeben.")

    with col2:
        # Validierungsergebnis anzeigen
        validation_result = st.session_state.get(f"addr_validation_{expose.expose_id}")
        if validation_result:
            if validation_result.get('gefunden'):
                if validation_result.get('abweichung'):
                    st.warning(f"Abweichung gefunden! Vorschlag: {validation_result.get('display_name', '')}")
                    if st.button("Vorschlag übernehmen", key=f"accept_addr_{expose.expose_id}"):
                        expose.strasse = validation_result.get('strasse', strasse)
                        expose.hausnummer = validation_result.get('hausnummer', hausnummer)
                        expose.plz = validation_result.get('plz', plz)
                        expose.ort = validation_result.get('ort', ort)
                        expose.adresse_validiert = True
                        st.session_state.expose_data[expose.expose_id] = expose
                        st.rerun()
                else:
                    st.success("Adresse validiert!")
                    expose.adresse_validiert = True
            else:
                st.error(validation_result.get('nachricht', 'Adresse nicht gefunden'))

    # ===== NUTZUNGSART =====
    st.markdown("#### Nutzungsart / Erlaubnisse")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        nutzungsart = st.selectbox(
            "Hauptnutzung",
            options=["Keine Angabe", "Dauerwohnen", "Ferienvermietung", "Zweitwohnung", "Gemischt"],
            index=["Keine Angabe", "Dauerwohnen", "Ferienvermietung", "Zweitwohnung", "Gemischt"].index(expose.nutzungsart) if expose.nutzungsart in ["Keine Angabe", "Dauerwohnen", "Ferienvermietung", "Zweitwohnung", "Gemischt"] else 0,
            key=f"expose_nutzung_{expose.expose_id}"
        )
    with col2:
        ferienvermietung_erlaubt = st.selectbox(
            "Ferienvermietung erlaubt?",
            options=["Keine Angabe", "Ja", "Nein"],
            index=["Keine Angabe", "Ja", "Nein"].index(expose.ferienvermietung_erlaubt) if expose.ferienvermietung_erlaubt in ["Keine Angabe", "Ja", "Nein"] else 0,
            key=f"expose_ferien_{expose.expose_id}"
        )
    with col3:
        dauerwohnen_erlaubt = st.selectbox(
            "Dauerwohnen erlaubt?",
            options=["Keine Angabe", "Ja", "Nein"],
            index=["Keine Angabe", "Ja", "Nein"].index(expose.dauerwohnen_erlaubt) if expose.dauerwohnen_erlaubt in ["Keine Angabe", "Ja", "Nein"] else 0,
            key=f"expose_dauer_{expose.expose_id}"
        )
    with col4:
        zweitwohnung_erlaubt = st.selectbox(
            "Zweitwohnung erlaubt?",
            options=["Keine Angabe", "Ja", "Nein"],
            index=["Keine Angabe", "Ja", "Nein"].index(expose.zweitwohnung_erlaubt) if expose.zweitwohnung_erlaubt in ["Keine Angabe", "Ja", "Nein"] else 0,
            key=f"expose_zweit_{expose.expose_id}"
        )

    # Basis-Informationen
    st.markdown("#### Basis-Informationen")
    col1, col2 = st.columns(2)
    with col1:
        objekttitel = st.text_input("Objekt-Titel*", value=expose.objekttitel, key=f"expose_titel_{expose.expose_id}")
        lage_beschreibung = st.text_area("Lage-Beschreibung", value=expose.lage_beschreibung, height=100, key=f"expose_lage_{expose.expose_id}")
    with col2:
        objektbeschreibung = st.text_area("Objekt-Beschreibung*", value=expose.objektbeschreibung, height=100, key=f"expose_beschr_{expose.expose_id}")
        ausstattung = st.text_area("Ausstattung", value=expose.ausstattung, height=100, key=f"expose_ausst_{expose.expose_id}")

    # Objektdaten
    st.markdown("#### Objektdaten")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        wohnflaeche = st.number_input("Wohnfläche (m²)", value=float(expose.wohnflaeche), min_value=0.0, step=1.0, key=f"expose_wfl_{expose.expose_id}")
        anzahl_zimmer = st.number_input("Anzahl Zimmer", value=float(expose.anzahl_zimmer), min_value=0.0, step=0.5, key=f"expose_zim_{expose.expose_id}")
    with col2:
        grundstuecksflaeche = st.number_input("Grundstücksfläche (m²)", value=float(expose.grundstuecksflaeche), min_value=0.0, step=1.0, key=f"expose_gfl_{expose.expose_id}")
        anzahl_schlafzimmer = st.number_input("Schlafzimmer", value=expose.anzahl_schlafzimmer, min_value=0, step=1, key=f"expose_schlaf_{expose.expose_id}")
    with col3:
        anzahl_badezimmer = st.number_input("Badezimmer", value=expose.anzahl_badezimmer, min_value=0, step=1, key=f"expose_bad_{expose.expose_id}")
        anzahl_etagen = st.number_input("Anzahl Etagen", value=expose.anzahl_etagen, min_value=0, step=1, key=f"expose_etagen_{expose.expose_id}")
    with col4:
        etage = st.text_input("Etage", value=expose.etage, key=f"expose_etage_{expose.expose_id}")
        baujahr = st.number_input("Baujahr", value=expose.baujahr if expose.baujahr > 0 else 2020, min_value=1800, max_value=2030, step=1, key=f"expose_bj_{expose.expose_id}")

    col1, col2 = st.columns(2)
    with col1:
        zustand = st.selectbox("Zustand", options=["", "Erstbezug", "Neuwertig", "Renoviert", "Gepflegt", "Sanierungsbedürftig"], index=0 if not expose.zustand else ["", "Erstbezug", "Neuwertig", "Renoviert", "Gepflegt", "Sanierungsbedürftig"].index(expose.zustand) if expose.zustand in ["", "Erstbezug", "Neuwertig", "Renoviert", "Gepflegt", "Sanierungsbedürftig"] else 0, key=f"expose_zust_{expose.expose_id}")
    with col2:
        verfuegbar_ab = st.date_input("Verfügbar ab", value=expose.verfuegbar_ab if expose.verfuegbar_ab else date.today(), key=f"expose_verf_{expose.expose_id}")

    # Preise und Kosten
    st.markdown("#### Preise und Kosten")

    # Kaufpreis-Vorschlag berechnen (auf Basis der bisherigen Daten)
    # Aktualisiere expose temporär für Vorschlagsberechnung
    temp_expose = ExposeData(
        expose_id="temp",
        projekt_id="temp",
        objektart=property_type,
        wohnflaeche=expose.wohnflaeche,
        grundstuecksflaeche=expose.grundstuecksflaeche,
        baujahr=expose.baujahr,
        zustand=expose.zustand,
        hat_meerblick=expose.hat_meerblick,
        hat_fahrstuhl=expose.hat_fahrstuhl,
        hat_balkon=expose.hat_balkon,
        hat_terrasse=expose.hat_terrasse,
        hat_garage=expose.hat_garage,
        hat_tiefgarage=expose.hat_tiefgarage,
        hat_schwimmbad=expose.hat_schwimmbad,
        hat_gemeinschaftspool=expose.hat_gemeinschaftspool,
        energieeffizienzklasse=expose.energieeffizienzklasse
    )
    preis_vorschlag = calculate_price_suggestion(temp_expose)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kaufpreis = st.number_input("Kaufpreis (€)*", value=float(expose.kaufpreis), min_value=0.0, step=1000.0, key=f"expose_kp_{expose.expose_id}")
        # Preis-Vorschlag anzeigen
        if preis_vorschlag > 0:
            diff = kaufpreis - preis_vorschlag
            diff_prozent = (diff / preis_vorschlag * 100) if preis_vorschlag > 0 else 0
            if diff_prozent > 10:
                st.warning(f"Vorschlag: {preis_vorschlag:,.0f} € (+{diff_prozent:.1f}% über Markt)")
            elif diff_prozent < -10:
                st.info(f"Vorschlag: {preis_vorschlag:,.0f} € ({diff_prozent:.1f}% unter Markt)")
            else:
                st.success(f"Vorschlag: {preis_vorschlag:,.0f} € (marktgerecht)")
    with col2:
        provision = st.text_input("Provision", value=expose.provision, placeholder="z.B. 3,57% inkl. MwSt.", key=f"expose_prov_{expose.expose_id}")
    with col3:
        hausgeld = st.number_input("Hausgeld (€/Monat)", value=float(expose.hausgeld), min_value=0.0, step=10.0, key=f"expose_hg_{expose.expose_id}")
    with col4:
        grundsteuer = st.number_input("Grundsteuer (€/Jahr)", value=float(expose.grundsteuer), min_value=0.0, step=10.0, key=f"expose_gst_{expose.expose_id}")

    # WEG-spezifisch (nur für Wohnungen)
    if property_type == PropertyType.WOHNUNG.value:
        st.markdown("#### WEG-Daten (Wohnungseigentümergemeinschaft)")
        col1, col2 = st.columns(2)
        with col1:
            weg_verwaltung = st.text_input("WEG-Verwaltung", value=expose.weg_verwaltung, key=f"expose_weg_{expose.expose_id}")
        with col2:
            ruecklage = st.number_input("Rücklage (€)", value=float(expose.ruecklage), min_value=0.0, step=100.0, key=f"expose_rl_{expose.expose_id}")

    # Energieausweis
    st.markdown("#### Energieausweis")
    col1, col2, col3 = st.columns(3)
    with col1:
        energieausweis_typ = st.selectbox("Typ", options=["", "Verbrauch", "Bedarf"], index=0 if not expose.energieausweis_typ else ["", "Verbrauch", "Bedarf"].index(expose.energieausweis_typ) if expose.energieausweis_typ in ["", "Verbrauch", "Bedarf"] else 0, key=f"expose_ea_typ_{expose.expose_id}")
        endenergieverbrauch = st.number_input("Endenergieverbrauch (kWh/m²a)", value=float(expose.endenergieverbrauch), min_value=0.0, step=1.0, key=f"expose_eev_{expose.expose_id}")
    with col2:
        energieeffizienzklasse = st.selectbox("Energieeffizienzklasse", options=["", "A+", "A", "B", "C", "D", "E", "F", "G", "H"], index=0 if not expose.energieeffizienzklasse else ["", "A+", "A", "B", "C", "D", "E", "F", "G", "H"].index(expose.energieeffizienzklasse) if expose.energieeffizienzklasse in ["", "A+", "A", "B", "C", "D", "E", "F", "G", "H"] else 0, key=f"expose_eek_{expose.expose_id}")
        baujahr_energieausweis = st.number_input("Baujahr Energieausweis", value=expose.baujahr_energieausweis if expose.baujahr_energieausweis > 0 else 2020, min_value=1990, max_value=2030, step=1, key=f"expose_ea_bj_{expose.expose_id}")
    with col3:
        wesentliche_energietraeger = st.text_input("Wesentliche Energieträger", value=expose.wesentliche_energietraeger, placeholder="z.B. Gas, Fernwärme", key=f"expose_et_{expose.expose_id}")
        gueltig_bis = st.date_input("Gültig bis", value=expose.gueltig_bis if expose.gueltig_bis else date.today(), key=f"expose_gb_{expose.expose_id}")

    # ===== AUSSTATTUNGSMERKMALE =====
    st.markdown("#### Ausstattungsmerkmale")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        hat_balkon = st.checkbox("Balkon", value=expose.hat_balkon, key=f"expose_balkon_{expose.expose_id}")
        hat_terrasse = st.checkbox("Terrasse", value=expose.hat_terrasse, key=f"expose_terrasse_{expose.expose_id}")
        hat_garten = st.checkbox("Garten", value=expose.hat_garten, key=f"expose_garten_{expose.expose_id}")
        hat_fahrstuhl = st.checkbox("Fahrstuhl", value=expose.hat_fahrstuhl, key=f"expose_fahrstuhl_{expose.expose_id}")
    with col2:
        hat_garage = st.checkbox("Garage", value=expose.hat_garage, key=f"expose_garage_{expose.expose_id}")
        hat_tiefgarage = st.checkbox("Tiefgarage", value=expose.hat_tiefgarage, key=f"expose_tiefgarage_{expose.expose_id}")
        hat_stellplatz = st.checkbox("Stellplatz", value=expose.hat_stellplatz, key=f"expose_stellplatz_{expose.expose_id}")
        nichtraucher = st.checkbox("Nichtraucher-Objekt", value=expose.nichtraucher, key=f"expose_nichtraucher_{expose.expose_id}")
    with col3:
        hat_sauna = st.checkbox("Sauna (privat)", value=expose.hat_sauna, key=f"expose_sauna_{expose.expose_id}")
        hat_gemeinschaftssauna = st.checkbox("Gemeinschafts-Sauna", value=expose.hat_gemeinschaftssauna, key=f"expose_gem_sauna_{expose.expose_id}")
        hat_schwimmbad = st.checkbox("Schwimmbad (privat)", value=expose.hat_schwimmbad, key=f"expose_pool_{expose.expose_id}")
        hat_gemeinschaftspool = st.checkbox("Gemeinschafts-Pool", value=expose.hat_gemeinschaftspool, key=f"expose_gem_pool_{expose.expose_id}")
    with col4:
        hat_meerblick = st.checkbox("Meerblick", value=expose.hat_meerblick, key=f"expose_meerblick_{expose.expose_id}")
        hat_bergblick = st.checkbox("Bergblick", value=expose.hat_bergblick, key=f"expose_bergblick_{expose.expose_id}")
        hat_seeblick = st.checkbox("Seeblick", value=expose.hat_seeblick, key=f"expose_seeblick_{expose.expose_id}")
        haustiere_erlaubt = st.selectbox(
            "Haustiere erlaubt?",
            options=["Keine Angabe", "Ja", "Nein", "Auf Anfrage"],
            index=["Keine Angabe", "Ja", "Nein", "Auf Anfrage"].index(expose.haustiere_erlaubt) if expose.haustiere_erlaubt in ["Keine Angabe", "Ja", "Nein", "Auf Anfrage"] else 0,
            key=f"expose_tiere_{expose.expose_id}"
        )

    # ===== ENTFERNUNGEN =====
    st.markdown("#### Entfernungen")
    col1, col2, col3 = st.columns(3)
    with col1:
        entfernung_strand_m = st.number_input("Strand (Meter)", value=expose.entfernung_strand_m, min_value=0, step=50, key=f"expose_strand_{expose.expose_id}")
        entfernung_zentrum_m = st.number_input("Ortszentrum (Meter)", value=expose.entfernung_zentrum_m, min_value=0, step=50, key=f"expose_zentrum_{expose.expose_id}")
    with col2:
        entfernung_stadt_m = st.number_input("Nächste Stadt (Meter)", value=expose.entfernung_stadt_m, min_value=0, step=100, key=f"expose_stadt_{expose.expose_id}")
        entfernung_supermarkt_m = st.number_input("Supermarkt (Meter)", value=expose.entfernung_supermarkt_m, min_value=0, step=50, key=f"expose_supermarkt_{expose.expose_id}")
    with col3:
        entfernung_arzt_m = st.number_input("Arzt/Apotheke (Meter)", value=expose.entfernung_arzt_m, min_value=0, step=50, key=f"expose_arzt_{expose.expose_id}")
        entfernung_flughafen_km = st.number_input("Flughafen (km)", value=expose.entfernung_flughafen_km, min_value=0, step=5, key=f"expose_flughafen_{expose.expose_id}")

    # Besonderheiten (Freitext für Sonstiges)
    st.markdown("#### Sonstige Besonderheiten")
    besonderheiten = st.text_area("Weitere Besonderheiten", value=expose.besonderheiten, height=100, placeholder="z.B. Dachterrasse, Kamin, Smart Home, etc.", key=f"expose_bes_{expose.expose_id}")

    # ===== MARKTANALYSE MIT VERGLEICHSOBJEKTEN =====
    st.markdown("#### 📊 Marktanalyse - Vergleichsobjekte")
    st.caption("Fügen Sie Links zu vergleichbaren Objekten hinzu, um die Preisfindung zu unterstützen.")

    # Bestehende Vergleichsobjekte anzeigen
    if expose.vergleichsobjekte:
        for i, vgl in enumerate(expose.vergleichsobjekte):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.markdown(f"[{vgl.get('titel', 'Vergleichsobjekt')}]({vgl.get('url', '#')})")
            with col2:
                st.write(f"{vgl.get('preis', 0):,.0f} €")
            with col3:
                st.write(f"{vgl.get('flaeche', 0)} m² • {vgl.get('zimmer', 0)} Zi.")
            with col4:
                if st.button("🗑️", key=f"del_vgl_{expose.expose_id}_{i}"):
                    expose.vergleichsobjekte.pop(i)
                    st.session_state.expose_data[expose.expose_id] = expose
                    st.rerun()

    # Neues Vergleichsobjekt hinzufügen
    with st.expander("➕ Vergleichsobjekt hinzufügen"):
        vgl_col1, vgl_col2 = st.columns(2)
        with vgl_col1:
            vgl_titel = st.text_input("Titel", placeholder="z.B. Schöne 3-Zi-Wohnung", key=f"vgl_titel_{expose.expose_id}")
            vgl_url = st.text_input("URL zum Inserat", placeholder="https://www.immobilienscout24.de/...", key=f"vgl_url_{expose.expose_id}")
        with vgl_col2:
            vgl_preis = st.number_input("Preis (€)", min_value=0.0, step=1000.0, key=f"vgl_preis_{expose.expose_id}")
            vgl_col2a, vgl_col2b = st.columns(2)
            with vgl_col2a:
                vgl_flaeche = st.number_input("Fläche (m²)", min_value=0.0, step=1.0, key=f"vgl_flaeche_{expose.expose_id}")
            with vgl_col2b:
                vgl_zimmer = st.number_input("Zimmer", min_value=0.0, step=0.5, key=f"vgl_zimmer_{expose.expose_id}")

        vgl_notiz = st.text_input("Notiz (optional)", placeholder="z.B. Ähnliche Lage, bessere Ausstattung", key=f"vgl_notiz_{expose.expose_id}")

        if st.button("Vergleichsobjekt hinzufügen", key=f"add_vgl_{expose.expose_id}"):
            if vgl_url:
                neues_vgl = {
                    'titel': vgl_titel if vgl_titel else "Vergleichsobjekt",
                    'url': vgl_url,
                    'preis': vgl_preis,
                    'flaeche': vgl_flaeche,
                    'zimmer': vgl_zimmer,
                    'notiz': vgl_notiz,
                    'hinzugefuegt_am': datetime.now().isoformat()
                }
                if not expose.vergleichsobjekte:
                    expose.vergleichsobjekte = []
                expose.vergleichsobjekte.append(neues_vgl)
                st.session_state.expose_data[expose.expose_id] = expose
                st.success("✅ Vergleichsobjekt hinzugefügt!")
                st.rerun()
            else:
                st.warning("Bitte geben Sie mindestens eine URL ein.")

    # Marktvergleich-Zusammenfassung anzeigen
    if expose.vergleichsobjekte and len(expose.vergleichsobjekte) >= 2:
        preise = [v.get('preis', 0) for v in expose.vergleichsobjekte if v.get('preis', 0) > 0]
        flaechen = [v.get('flaeche', 0) for v in expose.vergleichsobjekte if v.get('flaeche', 0) > 0]

        if preise and flaechen:
            avg_preis = sum(preise) / len(preise)
            avg_flaeche = sum(flaechen) / len(flaechen)
            avg_qm_preis = avg_preis / avg_flaeche if avg_flaeche > 0 else 0

            st.info(f"""
            **Marktvergleich ({len(expose.vergleichsobjekte)} Objekte):**
            - Ø Preis: {avg_preis:,.0f} €
            - Ø Fläche: {avg_flaeche:.0f} m²
            - Ø Preis/m²: {avg_qm_preis:,.0f} €
            """)

            # Vergleich mit eigenem Objekt
            if expose.kaufpreis > 0 and expose.wohnflaeche > 0:
                eigener_qm_preis = expose.kaufpreis / expose.wohnflaeche
                diff_prozent = ((eigener_qm_preis - avg_qm_preis) / avg_qm_preis * 100) if avg_qm_preis > 0 else 0

                if diff_prozent > 5:
                    st.warning(f"Ihr Objekt: {eigener_qm_preis:,.0f} €/m² (+{diff_prozent:.1f}% über Markt)")
                elif diff_prozent < -5:
                    st.success(f"Ihr Objekt: {eigener_qm_preis:,.0f} €/m² ({diff_prozent:.1f}% unter Markt)")
                else:
                    st.success(f"Ihr Objekt: {eigener_qm_preis:,.0f} €/m² (marktgerecht)")

    # Bilder
    st.markdown("#### Bilder und Dokumente")
    col1, col2 = st.columns(2)
    with col1:
        titelbild = st.file_uploader("Titelbild", type=["png", "jpg", "jpeg"], key=f"expose_titelbild_{expose.expose_id}")
        if expose.titelbild:
            st.image(expose.titelbild, width=200, caption="Aktuelles Titelbild")
        elif titelbild:
            st.image(titelbild, width=200)
    with col2:
        weitere_bilder = st.file_uploader("Weitere Bilder", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key=f"expose_bilder_{expose.expose_id}")
        if expose.weitere_bilder:
            st.write(f"Bereits {len(expose.weitere_bilder)} Bilder hochgeladen")

    grundrisse = st.file_uploader("Grundrisse", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True, key=f"expose_grundrisse_{expose.expose_id}")
    if expose.grundrisse:
        st.write(f"Bereits {len(expose.grundrisse)} Grundrisse hochgeladen")

    lageplan = st.file_uploader("Lageplan", type=["png", "jpg", "jpeg", "pdf"], key=f"expose_lageplan_{expose.expose_id}")

    # Speichern
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Exposé speichern", key=f"expose_save_{expose.expose_id}", type="primary"):
            # Alle Daten aktualisieren
            expose.objektart = property_type
            expose.objekttitel = objekttitel
            expose.objektbeschreibung = objektbeschreibung
            expose.lage_beschreibung = lage_beschreibung
            expose.ausstattung = ausstattung

            expose.wohnflaeche = wohnflaeche
            expose.grundstuecksflaeche = grundstuecksflaeche
            expose.anzahl_zimmer = anzahl_zimmer
            expose.anzahl_schlafzimmer = anzahl_schlafzimmer
            expose.anzahl_badezimmer = anzahl_badezimmer
            expose.anzahl_etagen = anzahl_etagen
            expose.etage = etage
            expose.baujahr = baujahr
            expose.zustand = zustand
            expose.verfuegbar_ab = verfuegbar_ab

            expose.kaufpreis = kaufpreis
            expose.provision = provision
            expose.hausgeld = hausgeld
            expose.grundsteuer = grundsteuer

            if property_type == PropertyType.WOHNUNG.value:
                expose.weg_verwaltung = weg_verwaltung
                expose.ruecklage = ruecklage

            expose.energieausweis_typ = energieausweis_typ
            expose.energieeffizienzklasse = energieeffizienzklasse
            expose.endenergieverbrauch = endenergieverbrauch
            expose.wesentliche_energietraeger = wesentliche_energietraeger
            expose.baujahr_energieausweis = baujahr_energieausweis
            expose.gueltig_bis = gueltig_bis

            expose.besonderheiten = besonderheiten

            # Bilder verarbeiten
            if titelbild:
                expose.titelbild = titelbild.read()
            if weitere_bilder:
                expose.weitere_bilder = [img.read() for img in weitere_bilder]
            if grundrisse:
                expose.grundrisse = [gr.read() for gr in grundrisse]
            if lageplan:
                expose.lageplan = lageplan.read()

            # Neue Felder: Adresse
            expose.strasse = strasse
            expose.hausnummer = hausnummer
            expose.plz = plz
            expose.ort = ort
            expose.land = land

            # Neue Felder: Nutzungsart
            expose.nutzungsart = nutzungsart
            expose.ferienvermietung_erlaubt = ferienvermietung_erlaubt
            expose.dauerwohnen_erlaubt = dauerwohnen_erlaubt
            expose.zweitwohnung_erlaubt = zweitwohnung_erlaubt

            # Neue Felder: Ausstattungsmerkmale
            expose.hat_balkon = hat_balkon
            expose.hat_terrasse = hat_terrasse
            expose.hat_garten = hat_garten
            expose.hat_garage = hat_garage
            expose.hat_tiefgarage = hat_tiefgarage
            expose.hat_stellplatz = hat_stellplatz
            expose.hat_sauna = hat_sauna
            expose.hat_gemeinschaftssauna = hat_gemeinschaftssauna
            expose.hat_schwimmbad = hat_schwimmbad
            expose.hat_gemeinschaftspool = hat_gemeinschaftspool
            expose.hat_fahrstuhl = hat_fahrstuhl
            expose.hat_meerblick = hat_meerblick
            expose.hat_bergblick = hat_bergblick
            expose.hat_seeblick = hat_seeblick
            expose.nichtraucher = nichtraucher
            expose.haustiere_erlaubt = haustiere_erlaubt

            # Neue Felder: Entfernungen
            expose.entfernung_strand_m = entfernung_strand_m
            expose.entfernung_zentrum_m = entfernung_zentrum_m
            expose.entfernung_stadt_m = entfernung_stadt_m
            expose.entfernung_supermarkt_m = entfernung_supermarkt_m
            expose.entfernung_arzt_m = entfernung_arzt_m
            expose.entfernung_flughafen_km = entfernung_flughafen_km

            expose.updated_at = datetime.now()

            # Speichern
            st.session_state.expose_data[expose.expose_id] = expose
            projekt.property_type = property_type
            st.session_state.projekte[projekt.projekt_id] = projekt

            st.success("✅ Exposé erfolgreich gespeichert!")
            # Nicht mehr return True - damit die anderen Buttons sichtbar bleiben
            st.session_state[f"expose_saved_{expose.expose_id}"] = True

    with col2:
        if st.button("📄 Web-Exposé Vorschau", key=f"expose_preview_{expose.expose_id}"):
            st.session_state[f"show_web_preview_{expose.expose_id}"] = True

    with col3:
        if st.button("📥 PDF generieren", key=f"expose_pdf_{expose.expose_id}"):
            st.info("PDF-Generierung würde hier mit reportlab/weasyprint erfolgen")

    # Web-Exposé Vorschau
    if st.session_state.get(f"show_web_preview_{expose.expose_id}", False):
        st.markdown("---")
        st.markdown("### 🌐 Web-Exposé Vorschau")

        # Simpler HTML-basierter Exposé-Preview
        preview_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: white; border: 1px solid #ddd;">
            <h1 style="color: #333;">{expose.objekttitel}</h1>
            <p style="font-size: 1.2em; color: #e74c3c;"><strong>Kaufpreis: {expose.kaufpreis:,.2f} €</strong></p>

            <h2>Objektbeschreibung</h2>
            <p>{expose.objektbeschreibung}</p>

            <h2>Objektdaten</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Objektart:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{expose.objektart}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Wohnfläche:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{expose.wohnflaeche} m²</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Zimmer:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{expose.anzahl_zimmer}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Baujahr:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{expose.baujahr if expose.baujahr > 0 else 'N/A'}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Zustand:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{expose.zustand if expose.zustand else 'N/A'}</td></tr>
            </table>

            <h2>Energieausweis</h2>
            <p><strong>Energieeffizienzklasse:</strong> {expose.energieeffizienzklasse if expose.energieeffizienzklasse else 'N/A'}</p>
            <p><strong>Endenergieverbrauch:</strong> {expose.endenergieverbrauch} kWh/m²a</p>

            <h2>Kosten</h2>
            <p><strong>Hausgeld:</strong> {expose.hausgeld} € / Monat</p>
            <p><strong>Grundsteuer:</strong> {expose.grundsteuer} € / Jahr</p>
            <p><strong>Provision:</strong> {expose.provision if expose.provision else 'N/A'}</p>
        </div>
        """

        import streamlit.components.v1 as components
        components.html(preview_html, height=800, scrolling=True)


# ============================================================================
# TIMELINE-KOMPONENTE
# ============================================================================

def render_timeline(projekt_id: str, role: str):
    """Rendert die grafische Timeline"""
    projekt = st.session_state.projekte.get(projekt_id)
    if not projekt:
        return

    st.markdown("### 📊 Projekt-Timeline")

    # Timeline-Events für dieses Projekt
    events = []
    for event_id in projekt.timeline_events:
        event = st.session_state.timeline_events.get(event_id)
        if event:
            events.append(event)

    events.sort(key=lambda e: e.position)

    if not events:
        st.info("Noch keine Timeline-Events vorhanden.")
        return

    # Finde aktuellen Schritt
    current_step = None
    for event in events:
        if not event.completed:
            current_step = event
            break

    # Timeline mit st.components rendern (robuster als pure markdown)
    import streamlit.components.v1 as components

    # Komplettes HTML mit embedded CSS
    full_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    body {
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    .timeline-container {
        position: relative;
        padding: 20px 10px;
    }
    .timeline-item {
        display: flex;
        margin-bottom: 30px;
        position: relative;
    }
    .timeline-marker {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        flex-shrink: 0;
        margin-right: 20px;
        z-index: 1;
        font-size: 18px;
    }
    .timeline-marker-completed {
        background: #28a745;
        color: white;
    }
    .timeline-marker-current {
        background: #ffc107;
        color: black;
        animation: pulse 2s infinite;
    }
    .timeline-marker-pending {
        background: #6c757d;
        color: white;
    }
    .timeline-line {
        position: absolute;
        left: 19px;
        top: 40px;
        bottom: -30px;
        width: 2px;
        background: #dee2e6;
    }
    .timeline-content {
        flex: 1;
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #dee2e6;
    }
    .timeline-content-completed {
        border-left-color: #28a745;
    }
    .timeline-content-current {
        border-left-color: #ffc107;
        background: #fff3cd;
    }
    .timeline-content-pending {
        border-left-color: #6c757d;
    }
    .timeline-title {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 5px;
    }
    .timeline-description {
        color: #6c757d;
        margin-bottom: 10px;
    }
    .timeline-waiting {
        background: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        border-left: 3px solid #ffc107;
    }
    .timeline-date {
        font-size: 0.9em;
        color: #6c757d;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    </style>
    </head>
    <body>
    <div class="timeline-container">
    """

    for i, event in enumerate(events):
        is_completed = event.completed
        is_current = (current_step and event.event_id == current_step.event_id)

        # Marker-Klasse und Icon
        if is_completed:
            marker_class = "timeline-marker-completed"
            content_class = "timeline-content-completed"
            icon = "✓"
        elif is_current:
            marker_class = "timeline-marker-current"
            content_class = "timeline-content-current"
            icon = "⏳"
        else:
            marker_class = "timeline-marker-pending"
            content_class = "timeline-content-pending"
            icon = str(event.position)

        # Timeline Item
        full_html += f'''
        <div class="timeline-item">
            {"" if i == len(events) - 1 else '<div class="timeline-line"></div>'}
            <div class="timeline-marker {marker_class}">{icon}</div>
            <div class="timeline-content {content_class}">
                <div class="timeline-title">{event.titel}</div>
                <div class="timeline-description">{event.beschreibung}</div>
        '''

        if is_completed and event.completed_at:
            full_html += f'<div class="timeline-date">✅ Abgeschlossen am {event.completed_at.strftime("%d.%m.%Y %H:%M")}</div>'

        if is_current and event.wartet_auf:
            full_html += f'''
            <div class="timeline-waiting">
                <strong>⏰ Wartet auf:</strong><br>
                {event.wartet_auf}
            </div>
            '''

        full_html += '''
            </div>
        </div>
        '''

    full_html += """
    </div>
    </body>
    </html>
    """

    # Render mit components.html (mehr Kontrolle über HTML)
    components.html(full_html, height=len(events) * 120 + 100, scrolling=False)

    # Aktuelle Warteinfo prominent anzeigen
    if current_step and current_step.wartet_auf:
        st.warning(f"**⏰ Aktueller Status:** {current_step.titel}\n\n**Nächster Schritt:** {current_step.wartet_auf}")

# ============================================================================
# AUTHENTIFIZIERUNG
# ============================================================================

def login_page():
    """Login-Seite"""
    st.title("🏠 Immobilien-Transaktionsplattform")
    st.subheader("Anmeldung")

    with st.form("login_form"):
        email = st.text_input("E-Mail")
        password = st.text_input("Passwort", type="password")
        submit = st.form_submit_button("Anmelden")

        if submit:
            user = None
            mitarbeiter = None

            # Zuerst normale Benutzer prüfen
            for u in st.session_state.users.values():
                if u.email == email and u.password_hash == hash_password(password):
                    user = u
                    break

            # Falls kein normaler Benutzer, Notar-Mitarbeiter prüfen
            if not user:
                for ma in st.session_state.notar_mitarbeiter.values():
                    if ma.email == email and ma.password_hash == hash_password(password):
                        if ma.aktiv:
                            mitarbeiter = ma
                            break
                        else:
                            st.error("❌ Ihr Account wurde deaktiviert. Kontaktieren Sie Ihren Notar.")
                            return

            if user:
                st.session_state.current_user = user
                st.session_state.is_notar_mitarbeiter = False
                create_notification(
                    user.user_id,
                    "Willkommen zurück!",
                    f"Sie haben sich erfolgreich angemeldet als {user.role}.",
                    NotificationType.SUCCESS.value
                )
                st.rerun()
            elif mitarbeiter:
                # Für Mitarbeiter ein pseudo-User-Objekt erstellen
                st.session_state.current_user = mitarbeiter
                st.session_state.is_notar_mitarbeiter = True
                st.success(f"✅ Willkommen zurück, {mitarbeiter.name}! Sie sind angemeldet als Notar-Mitarbeiter.")
                st.rerun()
            else:
                st.error("❌ Ungültige Anmeldedaten")

    with st.expander("📋 Demo-Zugangsdaten"):
        st.markdown("""
        **Makler:** `makler@demo.de` | `makler123`

        **Käufer:** `kaeufer@demo.de` | `kaeufer123`

        **Verkäufer:** `verkaeufer@demo.de` | `verkaeufer123`

        **Finanzierer:** `finanz@demo.de` | `finanz123`

        **Notar:** `notar@demo.de` | `notar123`
        """)

def logout():
    """Benutzer abmelden"""
    st.session_state.current_user = None
    st.session_state.is_notar_mitarbeiter = False
    st.rerun()

# ============================================================================
# MAKLER-BEREICH
# ============================================================================

def makler_dashboard():
    """Dashboard für Makler"""
    st.title("📊 Makler-Dashboard")

    tabs = st.tabs([
        "📋 Timeline",
        "📁 Projekte",
        "👤 Profil",
        "💼 Bankenmappe",
        "⚖️ Rechtliche Dokumente",
        "👥 Teilnehmer-Status",
        "✉️ Einladungen",
        "💬 Kommentare"
    ])

    with tabs[0]:
        makler_timeline_view()

    with tabs[1]:
        makler_projekte_view()

    with tabs[2]:
        makler_profil_view()

    with tabs[3]:
        render_bank_folder_view()

    with tabs[4]:
        makler_rechtliche_dokumente()

    with tabs[5]:
        makler_teilnehmer_status()

    with tabs[6]:
        makler_einladungen()

    with tabs[7]:
        makler_kommentare()

def makler_timeline_view():
    """Timeline-Ansicht für Makler"""
    st.subheader("📊 Projekt-Übersicht mit Timeline")

    makler_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.makler_id == makler_id]

    if not projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name} - Status: {projekt.status}", expanded=True):
            render_timeline(projekt.projekt_id, UserRole.MAKLER.value)

def makler_projekte_view():
    """Projekt-Verwaltung für Makler"""
    st.subheader("📁 Meine Projekte")

    makler_projekte = [p for p in st.session_state.projekte.values()
                       if p.makler_id == st.session_state.current_user.user_id]

    if st.button("➕ Neues Projekt anlegen"):
        st.session_state.show_new_projekt = True

    if st.session_state.get("show_new_projekt", False):
        with st.form("new_projekt_form"):
            st.markdown("### Neues Projekt anlegen")

            name = st.text_input("Projekt-Name*", placeholder="z.B. Eigentumswohnung München-Schwabing")
            beschreibung = st.text_area("Beschreibung*", placeholder="Kurze Beschreibung der Immobilie")
            adresse = st.text_input("Adresse", placeholder="Straße, PLZ Ort")
            kaufpreis = st.number_input("Kaufpreis (€)", min_value=0.0, value=0.0, step=1000.0)

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Projekt erstellen", type="primary")
            with col2:
                cancel = st.form_submit_button("❌ Abbrechen")

            if submit and name and beschreibung:
                projekt_id = f"projekt_{len(st.session_state.projekte)}"

                projekt = Projekt(
                    projekt_id=projekt_id,
                    name=name,
                    beschreibung=beschreibung,
                    adresse=adresse,
                    kaufpreis=kaufpreis,
                    makler_id=st.session_state.current_user.user_id
                )

                st.session_state.projekte[projekt_id] = projekt

                # Timeline initialisieren
                create_timeline_for_projekt(projekt_id)

                st.session_state.show_new_projekt = False
                st.success(f"✅ Projekt '{name}' erfolgreich erstellt!")
                st.rerun()

            if cancel:
                st.session_state.show_new_projekt = False
                st.rerun()

    st.markdown("---")

    for projekt in makler_projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Beschreibung:** {projekt.beschreibung}")
                if projekt.adresse:
                    st.markdown(f"**Adresse:** {projekt.adresse}")
                if projekt.kaufpreis > 0:
                    st.markdown(f"**Kaufpreis:** {projekt.kaufpreis:,.2f} €")
                st.markdown(f"**Status:** {projekt.status}")
                st.markdown(f"**Erstellt:** {projekt.created_at.strftime('%d.%m.%Y')}")

            with col2:
                st.markdown("**Teilnehmer:**")
                st.write(f"👥 Käufer: {len(projekt.kaeufer_ids)}")
                st.write(f"👥 Verkäufer: {len(projekt.verkaeufer_ids)}")
                st.write(f"💼 Finanzierer: {len(projekt.finanzierer_ids)}")
                st.write(f"⚖️ Notar: {'Ja' if projekt.notar_id else 'Nein'}")

            st.markdown("---")

            # ===== EXPOSÉ-VERWALTUNG (DIREKT SICHTBAR) =====
            st.markdown("#### 📄 Exposé-Daten")

            # Exposé-Status anzeigen
            if projekt.expose_data_id:
                expose = st.session_state.expose_data.get(projekt.expose_data_id)
                if expose and expose.objekttitel:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Objektart:** {expose.objektart}")
                        st.write(f"**Wohnfläche:** {expose.wohnflaeche} m²")
                    with col2:
                        st.write(f"**Zimmer:** {expose.anzahl_zimmer}")
                        st.write(f"**Kaufpreis:** {expose.kaufpreis:,.2f} €")
                    with col3:
                        st.write(f"**Letzte Änderung:** {expose.updated_at.strftime('%d.%m.%Y %H:%M')}")
                        if expose.adresse_validiert:
                            st.success("✅ Adresse validiert")

            # Exposé-Editor immer in einem Expander anzeigen (standardmäßig eingeklappt wenn Daten vorhanden)
            expose_exists = bool(projekt.expose_data_id and
                                st.session_state.expose_data.get(projekt.expose_data_id) and
                                st.session_state.expose_data.get(projekt.expose_data_id).objekttitel)

            with st.expander("📝 Exposé bearbeiten" if expose_exists else "📝 Exposé-Daten eingeben", expanded=not expose_exists):
                render_expose_editor(projekt)

            st.markdown("---")

            # ===== TERMIN-VERWALTUNG =====
            with st.expander("📅 Terminverwaltung", expanded=False):
                render_termin_verwaltung(projekt, UserRole.MAKLER.value)

                # Bestätigte Beurkundungstermine hervorheben
                beurkundungstermine = [st.session_state.termine.get(tid) for tid in projekt.termine
                                       if st.session_state.termine.get(tid) and
                                       st.session_state.termine.get(tid).termin_typ == TerminTyp.BEURKUNDUNG.value and
                                       st.session_state.termine.get(tid).status == TerminStatus.BESTAETIGT.value]

                if beurkundungstermine:
                    for termin in beurkundungstermine:
                        st.success(f"🟢 **Notartermin bestätigt:** {termin.datum.strftime('%d.%m.%Y')} um {termin.uhrzeit_start} Uhr")

def create_timeline_for_projekt(projekt_id: str):
    """Erstellt Timeline-Events für ein neues Projekt"""
    events = [
        ("Projekt erstellt", "Projekt wurde vom Makler angelegt", ProjektStatus.VORBEREITUNG.value, True, 1, None),
        ("Exposé hochgeladen", "Exposé wurde bereitgestellt", ProjektStatus.EXPOSE_ERSTELLT.value, False, 2, "Makler muss Exposé-PDF hochladen"),
        ("Teilnehmer eingeladen", "Käufer und Verkäufer wurden eingeladen", ProjektStatus.TEILNEHMER_EINGELADEN.value, False, 3, "Makler muss Käufer und Verkäufer einladen"),
        ("Onboarding-Dokumente akzeptieren", "Käufer und Verkäufer müssen rechtliche Dokumente akzeptieren", ProjektStatus.ONBOARDING_LAUFEND.value, False, 4, "Käufer und Verkäufer müssen alle rechtlichen Dokumente akzeptieren"),
        ("Wirtschaftsdaten hochladen", "Käufer lädt Bonitätsunterlagen hoch", ProjektStatus.WIRTSCHAFTSDATEN_HOCHGELADEN.value, False, 5, "Käufer muss Bonitätsunterlagen hochladen"),
        ("Finanzierungsanfrage", "Finanzierer prüft Unterlagen", ProjektStatus.FINANZIERUNG_ANGEFRAGT.value, False, 6, "Finanzierer muss Finanzierungsangebot erstellen"),
        ("Finanzierung gesichert", "Käufer nimmt Angebot an", ProjektStatus.FINANZIERUNG_GESICHERT.value, False, 7, "Käufer muss Finanzierungsangebot annehmen"),
        ("Notartermin vereinbaren", "Notartermin wird festgelegt", ProjektStatus.NOTARTERMIN_VEREINBART.value, False, 8, "Notar muss Termin festlegen"),
        ("Kaufvertrag unterzeichnen", "Unterzeichnung beim Notar", ProjektStatus.KAUFVERTRAG_UNTERZEICHNET.value, False, 9, "Alle Parteien beim Notartermin"),
        ("Transaktion abgeschlossen", "Übergabe und Grundbuch", ProjektStatus.ABGESCHLOSSEN.value, False, 10, "Notar bestätigt Abschluss"),
    ]

    projekt = st.session_state.projekte.get(projekt_id)
    if not projekt:
        return

    for i, (titel, beschreibung, status, completed, position, wartet_auf) in enumerate(events):
        event_id = f"evt_{projekt_id}_{i}"

        event = TimelineEvent(
            event_id=event_id,
            projekt_id=projekt_id,
            titel=titel,
            beschreibung=beschreibung,
            status=status,
            completed=completed,
            completed_at=datetime.now() if completed else None,
            position=position,
            wartet_auf=wartet_auf
        )

        st.session_state.timeline_events[event_id] = event
        projekt.timeline_events.append(event_id)

def makler_profil_view():
    """Makler-Profil-Verwaltung"""
    st.subheader("👤 Mein Makler-Profil")

    makler_id = st.session_state.current_user.user_id

    # Profil suchen oder erstellen
    profile = None
    for p in st.session_state.makler_profiles.values():
        if p.makler_id == makler_id:
            profile = p
            break

    if not profile:
        st.info("Sie haben noch kein Profil erstellt. Erstellen Sie jetzt Ihr Makler-Profil!")
        if st.button("➕ Profil erstellen"):
            profile_id = f"profile_{len(st.session_state.makler_profiles)}"
            profile = MaklerProfile(
                profile_id=profile_id,
                makler_id=makler_id,
                firmenname="",
                adresse="",
                telefon="",
                email=""
            )
            st.session_state.makler_profiles[profile_id] = profile
            st.rerun()
        return

    # Profil bearbeiten
    with st.form("profil_bearbeiten"):
        st.markdown("### Firmendaten")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**Logo**")
            logo_file = st.file_uploader("Firmenlogo hochladen", type=["png", "jpg", "jpeg"], key="logo_upload")
            if profile.logo:
                st.image(profile.logo, width=150)
            elif logo_file:
                st.image(logo_file, width=150)

        with col2:
            firmenname = st.text_input("Firmenname*", value=profile.firmenname)
            adresse = st.text_area("Adresse*", value=profile.adresse, height=100)

            col_tel, col_email = st.columns(2)
            with col_tel:
                telefon = st.text_input("Telefon*", value=profile.telefon)
            with col_email:
                email = st.text_input("E-Mail*", value=profile.email)

            website = st.text_input("Website", value=profile.website)

        st.markdown("---")
        st.markdown("### Backoffice-Kontakt")
        col1, col2, col3 = st.columns(3)
        with col1:
            backoffice_kontakt = st.text_input("Name", value=profile.backoffice_kontakt)
        with col2:
            backoffice_email = st.text_input("E-Mail", value=profile.backoffice_email)
        with col3:
            backoffice_telefon = st.text_input("Telefon", value=profile.backoffice_telefon)

        st.markdown("---")

        if st.form_submit_button("💾 Profil speichern", type="primary"):
            profile.firmenname = firmenname
            profile.adresse = adresse
            profile.telefon = telefon
            profile.email = email
            profile.website = website
            profile.backoffice_kontakt = backoffice_kontakt
            profile.backoffice_email = backoffice_email
            profile.backoffice_telefon = backoffice_telefon

            if logo_file:
                profile.logo = logo_file.read()

            st.session_state.makler_profiles[profile.profile_id] = profile
            st.success("✅ Profil erfolgreich gespeichert!")

    st.markdown("---")
    st.markdown("### 👥 Team-Mitglieder")

    # Team-Mitglieder anzeigen
    if profile.team_mitglieder:
        for agent in profile.team_mitglieder:
            with st.expander(f"👤 {agent.name} - {agent.position}"):
                col1, col2 = st.columns([1, 3])

                with col1:
                    if agent.foto:
                        st.image(agent.foto, width=100)
                    else:
                        st.write("Kein Foto")

                with col2:
                    st.write(f"**Position:** {agent.position}")
                    st.write(f"**Telefon:** {agent.telefon}")
                    st.write(f"**E-Mail:** {agent.email}")

                if st.button(f"🗑️ Entfernen", key=f"remove_{agent.agent_id}"):
                    profile.team_mitglieder = [a for a in profile.team_mitglieder if a.agent_id != agent.agent_id]
                    st.session_state.makler_profiles[profile.profile_id] = profile
                    st.success(f"Team-Mitglied {agent.name} entfernt!")
                    st.rerun()
    else:
        st.info("Noch keine Team-Mitglieder hinzugefügt.")

    # Neues Team-Mitglied hinzufügen
    with st.expander("➕ Team-Mitglied hinzufügen"):
        with st.form("neues_team_mitglied"):
            col1, col2 = st.columns([1, 2])

            with col1:
                foto_file = st.file_uploader("Foto", type=["png", "jpg", "jpeg"], key="agent_foto")
                if foto_file:
                    st.image(foto_file, width=100)

            with col2:
                agent_name = st.text_input("Name*")
                agent_position = st.text_input("Position*", placeholder="z.B. Immobilienberater")
                agent_telefon = st.text_input("Telefon*")
                agent_email = st.text_input("E-Mail*")

            if st.form_submit_button("➕ Hinzufügen"):
                if agent_name and agent_position and agent_telefon and agent_email:
                    agent_id = f"agent_{len(profile.team_mitglieder)}"
                    foto_bytes = foto_file.read() if foto_file else None

                    new_agent = MaklerAgent(
                        agent_id=agent_id,
                        name=agent_name,
                        position=agent_position,
                        telefon=agent_telefon,
                        email=agent_email,
                        foto=foto_bytes
                    )

                    profile.team_mitglieder.append(new_agent)
                    st.session_state.makler_profiles[profile.profile_id] = profile
                    st.success(f"✅ {agent_name} wurde zum Team hinzugefügt!")
                    st.rerun()
                else:
                    st.error("Bitte alle Pflichtfelder ausfüllen!")

def makler_rechtliche_dokumente():
    """Verwaltung rechtlicher Dokumente"""
    st.subheader("⚖️ Rechtliche Dokumente / Mandanten-Setup")
    st.markdown("""
    Hier hinterlegen Sie die rechtlichen Standarddokumente, die Käufer und Verkäufer
    **vor Einsicht ins Exposé** akzeptieren müssen.
    """)

    doc_types = [
        DocumentType.MAKLERAUFTRAG.value,
        DocumentType.DATENSCHUTZ.value,
        DocumentType.WIDERRUFSBELEHRUNG.value,
        DocumentType.WIDERRUFSVERZICHT.value
    ]

    for doc_type in doc_types:
        with st.expander(f"📄 {doc_type}", expanded=False):
            doc_key = f"{st.session_state.current_user.user_id}_{doc_type}"
            existing_doc = st.session_state.legal_documents.get(doc_key)

            if existing_doc:
                st.success(f"✅ Version {existing_doc.version} vom {existing_doc.created_at.strftime('%d.%m.%Y %H:%M')}")
                st.text_area("Aktueller Inhalt", existing_doc.content_text, height=150, disabled=True, key=f"view_{doc_key}")

                if st.button("🔄 Neue Version erstellen", key=f"update_{doc_key}"):
                    st.session_state[f"edit_mode_{doc_key}"] = True
                    st.rerun()

            if existing_doc is None or st.session_state.get(f"edit_mode_{doc_key}", False):
                with st.form(f"form_{doc_key}"):
                    text_content = st.text_area(
                        "Dokumenten-Text",
                        value=existing_doc.content_text if existing_doc else "",
                        height=200
                    )
                    pdf_file = st.file_uploader("PDF-Version (optional)", type=['pdf'], key=f"pdf_{doc_key}")

                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("💾 Speichern")
                    with col2:
                        cancel = st.form_submit_button("❌ Abbrechen")

                    if submit and text_content:
                        if existing_doc:
                            old_version = float(existing_doc.version.replace('v', ''))
                            new_version = f"v{old_version + 0.1:.1f}"
                        else:
                            new_version = "v1.0"

                        pdf_data = pdf_file.read() if pdf_file else None
                        doc = LegalDocument(
                            doc_type=doc_type,
                            version=new_version,
                            content_text=text_content,
                            pdf_data=pdf_data
                        )
                        st.session_state.legal_documents[doc_key] = doc
                        if f"edit_mode_{doc_key}" in st.session_state:
                            del st.session_state[f"edit_mode_{doc_key}"]
                        st.success(f"✅ {doc_type} {new_version} gespeichert!")
                        st.rerun()

                    if cancel:
                        if f"edit_mode_{doc_key}" in st.session_state:
                            del st.session_state[f"edit_mode_{doc_key}"]
                        st.rerun()

def makler_teilnehmer_status():
    """Zeigt Status der Dokumenten-Akzeptanz aller Teilnehmer"""
    st.subheader("👥 Teilnehmer-Status")

    for projekt in st.session_state.projekte.values():
        if projekt.makler_id != st.session_state.current_user.user_id:
            continue

        st.markdown(f"### 🏘️ {projekt.name}")

        teilnehmer_ids = projekt.kaeufer_ids + projekt.verkaeufer_ids

        if not teilnehmer_ids:
            st.info("Noch keine Teilnehmer eingeladen.")
            continue

        status_data = []
        for user_id in teilnehmer_ids:
            user = st.session_state.users.get(user_id)
            if not user:
                continue

            acceptances = {acc.document_type: acc for acc in user.document_acceptances}

            row = {
                "Name": user.name,
                "Rolle": user.role,
                "Maklerauftrag": "✅" if DocumentType.MAKLERAUFTRAG.value in acceptances else "❌",
                "Datenschutz": "✅" if DocumentType.DATENSCHUTZ.value in acceptances else "❌",
                "Widerrufsbelehrung": "✅" if DocumentType.WIDERRUFSBELEHRUNG.value in acceptances else "❌",
                "Widerrufsverzicht": "✅" if DocumentType.WIDERRUFSVERZICHT.value in acceptances else "❌",
                "Onboarding": "✅" if user.onboarding_complete else "❌"
            }
            status_data.append(row)

        if status_data:
            import pandas as pd
            df = pd.DataFrame(status_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")

def makler_einladungen():
    """Einladungs-Verwaltung"""
    st.subheader("✉️ Teilnehmer einladen")

    makler_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.makler_id == makler_id]

    if not projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    with st.form("invitation_form"):
        st.markdown("### Neue Einladung")

        projekt_options = {p.name: p.projekt_id for p in projekte}
        selected_projekt_name = st.selectbox("Projekt auswählen", list(projekt_options.keys()))
        projekt_id = projekt_options[selected_projekt_name]

        email = st.text_input("E-Mail-Adresse")
        rolle = st.selectbox("Rolle", [UserRole.KAEUFER.value, UserRole.VERKAEUFER.value, UserRole.FINANZIERER.value, UserRole.NOTAR.value])

        submit = st.form_submit_button("📧 Einladung senden")

        if submit and email:
            # Token generieren
            token = hashlib.sha256(f"{email}{projekt_id}{datetime.now()}".encode()).hexdigest()[:16]

            invitation_id = f"inv_{len(st.session_state.invitations)}"
            invitation = Invitation(
                invitation_id=invitation_id,
                projekt_id=projekt_id,
                email=email,
                rolle=rolle,
                eingeladen_von=makler_id,
                token=token,
                created_at=datetime.now()
            )

            st.session_state.invitations[invitation_id] = invitation

            st.success(f"✅ Einladung an {email} wurde versendet!")
            st.info(f"**Einladungslink (Demo):** `https://plattform.immobilien/invite/{token}`")

            st.rerun()

    # Offene Einladungen anzeigen
    st.markdown("---")
    st.markdown("### Versendete Einladungen")

    invitations = [inv for inv in st.session_state.invitations.values()
                   if inv.eingeladen_von == makler_id and not inv.verwendet]

    if invitations:
        for inv in invitations:
            projekt = st.session_state.projekte.get(inv.projekt_id)
            projekt_name = projekt.name if projekt else "Unbekannt"

            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"📧 {inv.email}")
            with col2:
                st.write(f"🏘️ {projekt_name} | {inv.rolle}")
            with col3:
                st.caption(inv.created_at.strftime("%d.%m.%Y"))
    else:
        st.info("Keine offenen Einladungen.")

def makler_kommentare():
    """Kommentar-Bereich"""
    st.subheader("💬 Kommentare & Nachrichten")

    makler_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.makler_id == makler_id]

    if not projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            # Kommentare anzeigen
            projekt_comments = [c for c in st.session_state.comments.values()
                              if c.projekt_id == projekt.projekt_id]
            projekt_comments.sort(key=lambda c: c.created_at, reverse=True)

            if projekt_comments:
                for comment in projekt_comments:
                    user = st.session_state.users.get(comment.user_id)
                    user_name = user.name if user else "Unbekannt"

                    st.markdown(f"""
                    <div style='background:#f0f0f0; padding:10px; border-radius:5px; margin:10px 0;'>
                        <strong>{user_name}</strong> <small>({comment.created_at.strftime('%d.%m.%Y %H:%M')})</small><br>
                        {comment.nachricht}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Noch keine Kommentare.")

            # Neuer Kommentar
            with st.form(f"comment_form_{projekt.projekt_id}"):
                nachricht = st.text_area("Nachricht schreiben", key=f"msg_{projekt.projekt_id}")

                sichtbar = st.multiselect(
                    "Sichtbar für",
                    ["Käufer", "Verkäufer", "Finanzierer", "Notar"],
                    default=["Käufer", "Verkäufer"]
                )

                if st.form_submit_button("📤 Senden"):
                    if nachricht:
                        comment_id = f"comment_{len(st.session_state.comments)}"
                        comment = Comment(
                            comment_id=comment_id,
                            projekt_id=projekt.projekt_id,
                            user_id=makler_id,
                            nachricht=nachricht,
                            created_at=datetime.now(),
                            sichtbar_fuer=sichtbar
                        )
                        st.session_state.comments[comment_id] = comment

                        # Benachrichtigungen
                        for rolle in sichtbar:
                            if rolle == "Käufer":
                                for kid in projekt.kaeufer_ids:
                                    create_notification(kid, "Neue Nachricht", f"Neue Nachricht im Projekt {projekt.name}", NotificationType.INFO.value)
                            elif rolle == "Verkäufer":
                                for vid in projekt.verkaeufer_ids:
                                    create_notification(vid, "Neue Nachricht", f"Neue Nachricht im Projekt {projekt.name}", NotificationType.INFO.value)

                        st.success("✅ Nachricht gesendet!")
                        st.rerun()

# ============================================================================
# KÄUFER/VERKÄUFER ONBOARDING
# ============================================================================

def onboarding_flow():
    """Onboarding-Flow für Käufer/Verkäufer"""
    st.title("👋 Willkommen!")
    st.markdown("""
    Bevor wir Ihnen das Exposé und die Projektdaten anzeigen,
    bitten wir Sie, die folgenden Unterlagen zu prüfen und zu bestätigen.
    """)

    makler_id = "makler1"

    doc_types = [
        DocumentType.MAKLERAUFTRAG.value,
        DocumentType.DATENSCHUTZ.value,
        DocumentType.WIDERRUFSBELEHRUNG.value,
        DocumentType.WIDERRUFSVERZICHT.value
    ]

    user = st.session_state.current_user
    accepted_docs = {acc.document_type for acc in user.document_acceptances}

    all_accepted = True
    acceptances_to_save = []

    st.markdown("---")

    for doc_type in doc_types:
        doc_key = f"{makler_id}_{doc_type}"
        doc = st.session_state.legal_documents.get(doc_key)

        if not doc:
            st.warning(f"⚠️ {doc_type} wurde vom Makler noch nicht hinterlegt.")
            all_accepted = False
            continue

        st.subheader(f"📄 {doc_type}")
        st.caption(f"Version {doc.version}")

        with st.expander("📖 Volltext anzeigen", expanded=False):
            st.text_area("", doc.content_text, height=200, disabled=True, key=f"read_{doc_type}")

        if doc.pdf_data:
            st.download_button(
                "📥 PDF herunterladen",
                doc.pdf_data,
                file_name=f"{doc_type}_{doc.version}.pdf",
                mime="application/pdf",
                key=f"dl_{doc_type}"
            )

        already_accepted = doc_type in accepted_docs

        if already_accepted:
            st.success(f"✅ Bereits akzeptiert")
        else:
            accept_key = f"accept_{doc_type}"
            if st.checkbox(
                f"Hiermit akzeptiere ich {doc_type.lower()}.",
                key=accept_key,
                value=False
            ):
                acceptances_to_save.append(
                    DocumentAcceptance(
                        user_id=user.user_id,
                        document_type=doc_type,
                        document_version=doc.version,
                        accepted_at=datetime.now(),
                        role=user.role
                    )
                )
            else:
                all_accepted = False

        st.markdown("---")

    if all_accepted or len(acceptances_to_save) == len([dt for dt in doc_types if f"{makler_id}_{dt}" in st.session_state.legal_documents]):
        if st.button("✅ Fortfahren & Exposé anzeigen", type="primary", use_container_width=True):
            for acc in acceptances_to_save:
                user.document_acceptances.append(acc)
            user.onboarding_complete = True

            # Timeline aktualisieren
            for projekt_id in user.projekt_ids:
                projekt = st.session_state.projekte.get(projekt_id)
                if projekt:
                    # Prüfe ob alle Teilnehmer fertig sind
                    all_onboarded = True
                    for uid in projekt.kaeufer_ids + projekt.verkaeufer_ids:
                        u = st.session_state.users.get(uid)
                        if u and not u.onboarding_complete:
                            all_onboarded = False
                            break

                    if all_onboarded:
                        for event_id in projekt.timeline_events:
                            event = st.session_state.timeline_events.get(event_id)
                            if event and event.titel == "Onboarding-Dokumente akzeptieren" and not event.completed:
                                event.completed = True
                                event.completed_at = datetime.now()
                        update_projekt_status(projekt_id)

            st.success("✅ Alle Dokumente akzeptiert!")
            st.rerun()
    else:
        st.info("⏳ Bitte akzeptieren Sie alle Dokumente, um fortzufahren.")

# ============================================================================
# KÄUFER-BEREICH
# ============================================================================

def kaeufer_dashboard():
    """Dashboard für Käufer"""
    st.title("🏠 Käufer-Dashboard")

    if not st.session_state.current_user.onboarding_complete:
        onboarding_flow()
        return

    tabs = st.tabs(["📊 Timeline", "📋 Projekte", "💰 Finanzierung", "🪪 Ausweis", "💬 Nachrichten", "📄 Dokumente", "📅 Termine"])

    with tabs[0]:
        kaeufer_timeline_view()

    with tabs[1]:
        kaeufer_projekte_view()

    with tabs[2]:
        kaeufer_finanzierung_view()

    with tabs[3]:
        # Personalausweis-Upload mit OCR
        st.subheader("🪪 Ausweisdaten erfassen")
        render_ausweis_upload(st.session_state.current_user.user_id, UserRole.KAEUFER.value)

    with tabs[4]:
        kaeufer_nachrichten()

    with tabs[5]:
        kaeufer_dokumente_view()

    with tabs[6]:
        # Termin-Übersicht für Käufer
        st.subheader("📅 Meine Termine")
        user_id = st.session_state.current_user.user_id
        projekte = [p for p in st.session_state.projekte.values() if user_id in p.kaeufer_ids]
        if projekte:
            for projekt in projekte:
                with st.expander(f"🏘️ {projekt.name}", expanded=True):
                    render_termin_verwaltung(projekt, UserRole.KAEUFER.value)
        else:
            st.info("Noch keine Projekte vorhanden.")

def kaeufer_timeline_view():
    """Timeline für Käufer"""
    st.subheader("📊 Projekt-Fortschritt")

    user_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if user_id in p.kaeufer_ids]

    if not projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            render_timeline(projekt.projekt_id, UserRole.KAEUFER.value)

def kaeufer_projekte_view():
    """Projekt-Ansicht für Käufer"""
    st.subheader("📋 Meine Projekte")

    user_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if user_id in p.kaeufer_ids]

    if not projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            st.markdown(f"**Beschreibung:** {projekt.beschreibung}")
            if projekt.adresse:
                st.markdown(f"**Adresse:** {projekt.adresse}")
            if projekt.kaufpreis > 0:
                st.markdown(f"**Kaufpreis:** {projekt.kaufpreis:,.2f} €")

            if projekt.expose_pdf:
                st.download_button(
                    "📥 Exposé herunterladen",
                    projekt.expose_pdf,
                    file_name=f"Expose_{projekt.name}.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("Exposé wird vom Makler noch bereitgestellt.")

def kaeufer_finanzierung_view():
    """Finanzierungs-Bereich für Käufer"""
    st.subheader("💰 Finanzierung")

    tabs = st.tabs(["📊 Finanzierungsangebote", "📤 Wirtschaftsdaten hochladen"])

    with tabs[0]:
        kaeufer_finanzierungsangebote()

    with tabs[1]:
        kaeufer_wirtschaftsdaten_upload()

def kaeufer_finanzierungsangebote():
    """Liste der Finanzierungsangebote für Käufer"""
    st.markdown("### 📊 Eingegangene Finanzierungsangebote")

    user_id = st.session_state.current_user.user_id

    relevante_angebote = []
    for offer in st.session_state.financing_offers.values():
        projekt = st.session_state.projekte.get(offer.projekt_id)
        if projekt and user_id in projekt.kaeufer_ids:
            if offer.status in [FinanzierungsStatus.GESENDET.value, FinanzierungsStatus.ANGENOMMEN.value]:
                relevante_angebote.append(offer)

    if not relevante_angebote:
        st.info("📭 Noch keine Finanzierungsangebote vorhanden.")
        return

    for offer in relevante_angebote:
        finanzierer = st.session_state.users.get(offer.finanzierer_id)
        finanzierer_name = finanzierer.name if finanzierer else "Unbekannt"

        status_icon = "✅" if offer.status == FinanzierungsStatus.ANGENOMMEN.value else "📧"

        with st.expander(f"{status_icon} Angebot von {finanzierer_name} - {offer.zinssatz}% Zinssatz",
                        expanded=(offer.status == FinanzierungsStatus.GESENDET.value)):

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Darlehensbetrag", f"{offer.darlehensbetrag:,.2f} €")
                st.metric("Zinssatz", f"{offer.zinssatz:.2f} %")
                st.metric("Tilgungssatz", f"{offer.tilgungssatz:.2f} %")

            with col2:
                st.metric("Monatliche Rate", f"{offer.monatliche_rate:,.2f} €")
                st.metric("Sollzinsbindung", f"{offer.sollzinsbindung} Jahre")
                st.metric("Gesamtlaufzeit", f"{offer.gesamtlaufzeit} Jahre")

            if offer.besondere_bedingungen:
                st.markdown("**Besondere Bedingungen:**")
                st.info(offer.besondere_bedingungen)

            if offer.pdf_data:
                st.download_button(
                    "📥 Angebot als PDF herunterladen",
                    offer.pdf_data,
                    file_name=f"Finanzierungsangebot_{offer.offer_id}.pdf",
                    mime="application/pdf",
                    key=f"dl_offer_{offer.offer_id}"
                )

            if offer.status == FinanzierungsStatus.GESENDET.value:
                st.markdown("---")
                st.markdown("### 🎯 Angebot annehmen")

                notar_checkbox = st.checkbox(
                    "Dieses Angebot soll für den Notar als Finanzierungsnachweis markiert werden",
                    key=f"notar_{offer.offer_id}"
                )

                if st.button("✅ Finanzierungsangebot annehmen",
                           type="primary",
                           key=f"accept_{offer.offer_id}",
                           use_container_width=True):
                    offer.status = FinanzierungsStatus.ANGENOMMEN.value
                    offer.accepted_at = datetime.now()
                    offer.fuer_notar_markiert = notar_checkbox

                    # Timeline aktualisieren
                    projekt = st.session_state.projekte.get(offer.projekt_id)
                    if projekt:
                        for event_id in projekt.timeline_events:
                            event = st.session_state.timeline_events.get(event_id)
                            if event and event.titel == "Finanzierung gesichert" and not event.completed:
                                event.completed = True
                                event.completed_at = datetime.now()
                        update_projekt_status(offer.projekt_id)

                    # Benachrichtigungen
                    create_notification(offer.finanzierer_id, "Angebot angenommen", "Ihr Finanzierungsangebot wurde angenommen!", NotificationType.SUCCESS.value)
                    if projekt and projekt.makler_id:
                        create_notification(projekt.makler_id, "Finanzierung gesichert", f"Käufer hat Finanzierungsangebot angenommen für {projekt.name}", NotificationType.SUCCESS.value)

                    st.success("✅ Finanzierungsangebot erfolgreich angenommen!")
                    st.balloons()
                    st.rerun()

            elif offer.status == FinanzierungsStatus.ANGENOMMEN.value:
                st.success(f"✅ Angenommen am {offer.accepted_at.strftime('%d.%m.%Y %H:%M')}")
                if offer.fuer_notar_markiert:
                    st.info("📋 Als Finanzierungsnachweis für Notar markiert")

def kaeufer_wirtschaftsdaten_upload():
    """Upload-Bereich für Wirtschaftsdaten"""
    st.markdown("### 📤 Wirtschaftsdaten hochladen")
    st.info("Laden Sie hier Ihre Bonitätsunterlagen für die Finanzierung hoch. Die Dokumente werden automatisch per OCR analysiert und kategorisiert.")

    with st.form("wirtschaftsdaten_upload"):
        uploaded_files = st.file_uploader(
            "Dokumente auswählen (PDF, JPG, PNG)",
            type=['pdf', 'jpg', 'png'],
            accept_multiple_files=True
        )

        doc_type = st.selectbox(
            "Dokumenten-Typ (optional - wird automatisch erkannt)",
            [
                "Automatisch erkennen",
                DocumentType.BWA.value,
                DocumentType.STEUERBESCHEID.value,
                DocumentType.GEHALTSABRECHNUNG.value,
                DocumentType.VERMOEGENSNACHWEIS.value,
                DocumentType.SONSTIGE.value
            ]
        )

        submit = st.form_submit_button("📤 Hochladen & Analysieren")

        if submit and uploaded_files:
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, file in enumerate(uploaded_files):
                status_text.text(f"Verarbeite {file.name}...")
                progress_bar.progress((i + 1) / len(uploaded_files))

                file_data = file.read()

                # OCR-Simulation
                ocr_text, kategorie = simulate_ocr(file_data, file.name)

                # Dokument speichern
                doc_id = f"wirt_{st.session_state.current_user.user_id}_{len(st.session_state.wirtschaftsdaten)}"

                doc = WirtschaftsdatenDokument(
                    doc_id=doc_id,
                    kaeufer_id=st.session_state.current_user.user_id,
                    doc_type=doc_type if doc_type != "Automatisch erkennen" else kategorie,
                    filename=file.name,
                    upload_date=datetime.now(),
                    pdf_data=file_data,
                    kategorie=kategorie,
                    ocr_text=ocr_text
                )

                st.session_state.wirtschaftsdaten[doc_id] = doc

            # Timeline aktualisieren
            for projekt_id in st.session_state.current_user.projekt_ids:
                projekt = st.session_state.projekte.get(projekt_id)
                if projekt:
                    for event_id in projekt.timeline_events:
                        event = st.session_state.timeline_events.get(event_id)
                        if event and event.titel == "Wirtschaftsdaten hochladen" and not event.completed:
                            event.completed = True
                            event.completed_at = datetime.now()
                    update_projekt_status(projekt_id)

            st.success(f"✅ {len(uploaded_files)} Dokument(e) erfolgreich hochgeladen und analysiert!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Hochgeladene Dokumente")

    user_docs = [d for d in st.session_state.wirtschaftsdaten.values()
                 if d.kaeufer_id == st.session_state.current_user.user_id]

    if user_docs:
        # Nach Kategorie gruppieren
        kategorien = {}
        for doc in user_docs:
            if doc.kategorie not in kategorien:
                kategorien[doc.kategorie] = []
            kategorien[doc.kategorie].append(doc)

        for kategorie, docs in kategorien.items():
            with st.expander(f"📁 {kategorie} ({len(docs)} Dokument(e))", expanded=True):
                for doc in docs:
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    with col1:
                        st.write(f"📄 **{doc.filename}**")
                    with col2:
                        st.caption(f"Hochgeladen: {doc.upload_date.strftime('%d.%m.%Y')}")
                    with col3:
                        if st.button("👁️", key=f"view_{doc.doc_id}", help="OCR-Text anzeigen"):
                            st.session_state[f"show_ocr_{doc.doc_id}"] = not st.session_state.get(f"show_ocr_{doc.doc_id}", False)
                    with col4:
                        st.download_button(
                            "📥",
                            doc.pdf_data,
                            file_name=doc.filename,
                            key=f"dl_{doc.doc_id}"
                        )

                    if st.session_state.get(f"show_ocr_{doc.doc_id}", False):
                        st.text_area("OCR-Ergebnis", doc.ocr_text, height=150, disabled=True, key=f"ocr_text_{doc.doc_id}")

                    st.markdown("---")
    else:
        st.info("Noch keine Dokumente hochgeladen.")

def kaeufer_nachrichten():
    """Nachrichten für Käufer"""
    st.subheader("💬 Nachrichten")

    user_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if user_id in p.kaeufer_ids]

    if not projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            # Kommentare anzeigen (nur die für Käufer sichtbar sind)
            projekt_comments = [c for c in st.session_state.comments.values()
                              if c.projekt_id == projekt.projekt_id and "Käufer" in c.sichtbar_fuer]
            projekt_comments.sort(key=lambda c: c.created_at, reverse=True)

            if projekt_comments:
                for comment in projekt_comments:
                    user = st.session_state.users.get(comment.user_id)
                    user_name = user.name if user else "Unbekannt"

                    st.markdown(f"""
                    <div style='background:#f0f0f0; padding:10px; border-radius:5px; margin:10px 0;'>
                        <strong>{user_name}</strong> <small>({comment.created_at.strftime('%d.%m.%Y %H:%M')})</small><br>
                        {comment.nachricht}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Noch keine Nachrichten.")

def kaeufer_dokumente_view():
    """Dokumenten-Übersicht für Käufer"""
    st.subheader("📄 Akzeptierte Dokumente")

    user = st.session_state.current_user
    if user.document_acceptances:
        for acc in user.document_acceptances:
            st.write(f"✅ {acc.document_type} (Version {acc.document_version}) - akzeptiert am {acc.accepted_at.strftime('%d.%m.%Y %H:%M')}")
    else:
        st.info("Noch keine Dokumente akzeptiert.")

# ============================================================================
# VERKÄUFER-BEREICH
# ============================================================================

def verkaeufer_dashboard():
    """Dashboard für Verkäufer"""
    st.title("🏡 Verkäufer-Dashboard")

    if not st.session_state.current_user.onboarding_complete:
        onboarding_flow()
        return

    tabs = st.tabs(["📊 Timeline", "📋 Projekte", "🔍 Makler finden", "🪪 Ausweis", "📄 Dokumente hochladen", "📋 Dokumentenanforderungen", "💬 Nachrichten", "📅 Termine"])

    with tabs[0]:
        verkaeufer_timeline_view()

    with tabs[1]:
        verkaeufer_projekte_view()

    with tabs[2]:
        verkaeufer_makler_finden()

    with tabs[3]:
        # Personalausweis-Upload mit OCR
        st.subheader("🪪 Ausweisdaten erfassen")
        render_ausweis_upload(st.session_state.current_user.user_id, UserRole.VERKAEUFER.value)

    with tabs[4]:
        verkaeufer_dokumente_view()

    with tabs[5]:
        render_document_requests_view(st.session_state.current_user.user_id, UserRole.VERKAEUFER.value)

    with tabs[6]:
        verkaeufer_nachrichten()

    with tabs[7]:
        # Termin-Übersicht für Verkäufer
        st.subheader("📅 Meine Termine")
        user_id = st.session_state.current_user.user_id
        projekte = [p for p in st.session_state.projekte.values() if user_id in p.verkaeufer_ids]
        if projekte:
            for projekt in projekte:
                with st.expander(f"🏘️ {projekt.name}", expanded=True):
                    render_termin_verwaltung(projekt, UserRole.VERKAEUFER.value)
        else:
            st.info("Noch keine Projekte vorhanden.")

def verkaeufer_makler_finden():
    """Makler-Suche für Verkäufer - zeigt vom Notar empfohlene Makler"""
    st.subheader("🔍 Makler finden")
    st.info("""
    Hier finden Sie vom Notar geprüfte und empfohlene Makler.
    Diese Makler wurden sorgfältig ausgewählt und sind spezialisiert auf Ihre Region.
    """)

    # Alle freigegebenen Makler-Empfehlungen holen
    freigegebene_makler = [e for e in st.session_state.makler_empfehlungen.values()
                          if e.status == MaklerEmpfehlungStatus.FREIGEGEBEN.value]

    if not freigegebene_makler:
        st.warning("Derzeit sind keine empfohlenen Makler verfügbar. Bitte wenden Sie sich an den Notar.")
        return

    # Filter-Optionen
    st.markdown("### 🎯 Filter")
    col1, col2 = st.columns(2)

    with col1:
        # Regionen sammeln
        alle_regionen = set()
        for m in freigegebene_makler:
            alle_regionen.update(m.regionen)
        region_filter = st.multiselect("Region", sorted(alle_regionen), default=[])

    with col2:
        # Spezialisierungen sammeln
        alle_spezialisierungen = set()
        for m in freigegebene_makler:
            alle_spezialisierungen.update(m.spezialisierung)
        spez_filter = st.multiselect("Spezialisierung", sorted(alle_spezialisierungen), default=[])

    # Filter anwenden
    gefilterte_makler = freigegebene_makler
    if region_filter:
        gefilterte_makler = [m for m in gefilterte_makler
                           if any(r in m.regionen for r in region_filter)]
    if spez_filter:
        gefilterte_makler = [m for m in gefilterte_makler
                           if any(s in m.spezialisierung for s in spez_filter)]

    st.markdown("---")
    st.markdown(f"### 👥 Empfohlene Makler ({len(gefilterte_makler)})")

    if not gefilterte_makler:
        st.info("Keine Makler entsprechen Ihren Filterkriterien.")
        return

    for makler in gefilterte_makler:
        with st.container():
            # Makler-Karte
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"## {makler.firmenname or makler.makler_name}")

                # Logo wenn vorhanden
                if makler.logo:
                    try:
                        st.image(makler.logo, width=150)
                    except:
                        pass

                # Kurzvita
                if makler.kurzvita:
                    st.markdown(f"*{makler.kurzvita}*")

                # Spezialisierung und Regionen
                if makler.spezialisierung:
                    st.markdown(f"**Spezialisierung:** {', '.join(makler.spezialisierung)}")
                if makler.regionen:
                    st.markdown(f"**Tätig in:** {', '.join(makler.regionen)}")

            with col2:
                # Kontaktdaten
                st.markdown("**📞 Kontakt**")
                if makler.telefon:
                    st.write(f"Tel: {makler.telefon}")
                if makler.makler_email:
                    st.write(f"✉️ {makler.makler_email}")
                if makler.website:
                    st.markdown(f"🌐 [{makler.website}](https://{makler.website})")
                if makler.adresse:
                    st.write(f"📍 {makler.adresse}")

            # Konditionen
            with st.expander("💰 Konditionen & Details"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Provision:**")
                    if makler.provision_verkaeufer_prozent > 0:
                        st.write(f"- Verkäufer: {makler.provision_verkaeufer_prozent}% inkl. MwSt.")
                    else:
                        st.write("- Verkäufer: Auf Anfrage")
                    if makler.provision_kaeufer_prozent > 0:
                        st.write(f"- Käufer: {makler.provision_kaeufer_prozent}% inkl. MwSt.")
                    else:
                        st.write("- Käufer: Auf Anfrage")

                with col2:
                    st.markdown("**Rechtliche Dokumente:**")
                    if makler.agb_text:
                        with st.expander("📄 AGB"):
                            st.text_area("", makler.agb_text, height=200, disabled=True, key=f"agb_{makler.empfehlung_id}")
                    if makler.widerrufsbelehrung_text:
                        with st.expander("📄 Widerrufsbelehrung"):
                            st.text_area("", makler.widerrufsbelehrung_text, height=200, disabled=True, key=f"widerruf_{makler.empfehlung_id}")

            # Kontakt-Button
            st.markdown("---")
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                if st.button(f"📧 Makler kontaktieren", key=f"contact_{makler.empfehlung_id}", type="primary"):
                    st.session_state[f"show_contact_form_{makler.empfehlung_id}"] = True

            # Kontaktformular anzeigen
            if st.session_state.get(f"show_contact_form_{makler.empfehlung_id}", False):
                st.markdown("#### 📝 Kontaktanfrage senden")
                with st.form(f"contact_form_{makler.empfehlung_id}"):
                    user = st.session_state.current_user

                    st.write(f"**An:** {makler.firmenname or makler.makler_name}")

                    # Vorausgefüllte Daten
                    name = st.text_input("Ihr Name", value=user.name if user else "")
                    email = st.text_input("Ihre E-Mail", value=user.email if user else "")
                    telefon = st.text_input("Ihre Telefonnummer (optional)")

                    nachricht = st.text_area("Ihre Nachricht", value=f"""Sehr geehrte Damen und Herren,

ich interessiere mich für Ihre Maklerdienstleistungen und möchte meine Immobilie verkaufen.

Bitte kontaktieren Sie mich für ein unverbindliches Beratungsgespräch.

Mit freundlichen Grüßen,
{user.name if user else ''}""", height=200)

                    submit = st.form_submit_button("📤 Anfrage senden")

                    if submit:
                        # Simulierte E-Mail-Benachrichtigung
                        st.success(f"""
                        ✅ Ihre Anfrage wurde gesendet!

                        **Simulierte E-Mail an:** {makler.makler_email}

                        Der Makler wird sich in Kürze bei Ihnen melden.
                        """)

                        # Benachrichtigung an Notar
                        create_notification(
                            "notar1",  # Demo-Notar
                            "Neue Makleranfrage",
                            f"Verkäufer {user.name if user else 'Unbekannt'} hat Makler {makler.firmenname or makler.makler_name} kontaktiert.",
                            NotificationType.INFO.value
                        )

                        del st.session_state[f"show_contact_form_{makler.empfehlung_id}"]
                        st.rerun()

            st.markdown("---")


def verkaeufer_timeline_view():
    """Timeline für Verkäufer"""
    st.subheader("📊 Projekt-Fortschritt")

    user_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if user_id in p.verkaeufer_ids]

    if not projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            render_timeline(projekt.projekt_id, UserRole.VERKAEUFER.value)

def verkaeufer_projekte_view():
    """Projekt-Ansicht für Verkäufer"""
    st.subheader("📋 Meine Projekte")

    user_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if user_id in p.verkaeufer_ids]

    if not projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            st.markdown(f"**Beschreibung:** {projekt.beschreibung}")
            st.markdown(f"**Objektart:** {projekt.property_type}")
            if projekt.adresse:
                st.markdown(f"**Adresse:** {projekt.adresse}")
            if projekt.kaufpreis > 0:
                st.markdown(f"**Kaufpreis:** {projekt.kaufpreis:,.2f} €")
            st.markdown(f"**Status:** {projekt.status}")

            # Anzeige hochgeladener Dokumente für dieses Projekt
            projekt_docs = [d for d in st.session_state.verkaeufer_dokumente.values()
                           if d.verkaeufer_id == user_id and d.projekt_id == projekt.projekt_id]

            st.markdown("---")
            st.markdown("**📂 Meine hochgeladenen Dokumente:**")
            if projekt_docs:
                st.write(f"✅ {len(projekt_docs)} Dokument(e) hochgeladen")
            else:
                st.info("Noch keine Dokumente hochgeladen. Gehen Sie zum Tab 'Dokumente hochladen'.")

def verkaeufer_dokumente_view():
    """Dokumenten-Upload für Verkäufer"""
    st.subheader("📄 Dokumente hochladen")

    st.info("""
    Als Verkäufer stellen Sie die meisten Dokumente für den Verkaufsprozess bereit.
    Diese Dokumente werden von Makler, Notar und Finanzierer benötigt.
    """)

    user_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if user_id in p.verkaeufer_ids]

    if not projekte:
        st.warning("Sie sind keinem Projekt zugeordnet.")
        return

    # Projekt auswählen
    projekt_options = {f"{p.name} ({p.property_type})": p.projekt_id for p in projekte}
    selected_projekt_label = st.selectbox("Für welches Projekt möchten Sie Dokumente hochladen?", list(projekt_options.keys()))
    selected_projekt_id = projekt_options[selected_projekt_label]
    selected_projekt = st.session_state.projekte[selected_projekt_id]

    st.markdown("---")

    # Bereits hochgeladene Dokumente anzeigen
    projekt_docs = [d for d in st.session_state.verkaeufer_dokumente.values()
                   if d.verkaeufer_id == user_id and d.projekt_id == selected_projekt_id]

    if projekt_docs:
        st.markdown("### 📂 Bereits hochgeladene Dokumente")

        # Nach Typ gruppieren
        docs_by_type = {}
        for doc in projekt_docs:
            if doc.dokument_typ not in docs_by_type:
                docs_by_type[doc.dokument_typ] = []
            docs_by_type[doc.dokument_typ].append(doc)

        for doc_typ, docs in docs_by_type.items():
            with st.expander(f"📋 {doc_typ} ({len(docs)} Dokument(e))", expanded=False):
                for doc in docs:
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.write(f"📄 **{doc.dateiname}**")
                        if doc.beschreibung:
                            st.caption(doc.beschreibung)

                    with col2:
                        st.caption(f"Hochgeladen: {doc.upload_datum.strftime('%d.%m.%Y')}")
                        st.caption(f"Status: {doc.status}")

                        # Freigaben anzeigen
                        freigaben = []
                        if doc.freigegeben_fuer_makler:
                            freigaben.append("Makler")
                        if doc.freigegeben_fuer_notar:
                            freigaben.append("Notar")
                        if doc.freigegeben_fuer_finanzierer:
                            freigaben.append("Finanzierer")
                        if doc.freigegeben_fuer_kaeufer:
                            freigaben.append("Käufer")

                        if freigaben:
                            st.caption(f"✅ Freigegeben für: {', '.join(freigaben)}")
                        else:
                            st.caption("⚠️ Noch nicht freigegeben")

                    with col3:
                        if st.button("🗑️", key=f"delete_doc_{doc.dokument_id}"):
                            del st.session_state.verkaeufer_dokumente[doc.dokument_id]
                            st.success("Dokument gelöscht!")
                            st.rerun()

                    st.markdown("---")

        st.markdown("---")

    # Neues Dokument hochladen
    st.markdown("### ➕ Neues Dokument hochladen")

    with st.form("dokument_upload"):
        # Dokumenttyp auswählen (abhängig von Objektart)
        st.markdown("**Dokumenttyp auswählen:**")

        # Empfohlene Dokumente basierend auf Objektart
        empfohlene_docs = []
        if selected_projekt.property_type == PropertyType.WOHNUNG.value:
            empfohlene_docs = [
                VerkäuferDokumentTyp.GRUNDBUCHAUSZUG.value,
                VerkäuferDokumentTyp.TEILUNGSERKLARUNG.value,
                VerkäuferDokumentTyp.WEG_PROTOKOLLE.value,
                VerkäuferDokumentTyp.ENERGIEAUSWEIS.value,
                VerkäuferDokumentTyp.WIRTSCHAFTSPLAN.value,
                VerkäuferDokumentTyp.HAUSVERWALTUNG_BESCHEINIGUNG.value,
            ]
        elif selected_projekt.property_type == PropertyType.HAUS.value:
            empfohlene_docs = [
                VerkäuferDokumentTyp.GRUNDBUCHAUSZUG.value,
                VerkäuferDokumentTyp.ENERGIEAUSWEIS.value,
                VerkäuferDokumentTyp.GRUNDRISS.value,
                VerkäuferDokumentTyp.LAGEPLAN.value,
                VerkäuferDokumentTyp.BAUGENEHMIGUNG.value,
                VerkäuferDokumentTyp.WOHNFLACHENBERECHNUNG.value,
            ]
        elif selected_projekt.property_type == PropertyType.LAND.value:
            empfohlene_docs = [
                VerkäuferDokumentTyp.GRUNDBUCHAUSZUG.value,
                VerkäuferDokumentTyp.FLURKARTE.value,
                VerkäuferDokumentTyp.LAGEPLAN.value,
                VerkäuferDokumentTyp.BAUGENEHMIGUNG.value,
            ]
        else:  # MFH
            empfohlene_docs = [
                VerkäuferDokumentTyp.GRUNDBUCHAUSZUG.value,
                VerkäuferDokumentTyp.ENERGIEAUSWEIS.value,
                VerkäuferDokumentTyp.MIETVERTRÄGE.value,
                VerkäuferDokumentTyp.NEBENKOSTENABRECHNUNG.value,
                VerkäuferDokumentTyp.WIRTSCHAFTSPLAN.value,
            ]

        # Alle Dokumenttypen als Optionen
        alle_doc_typen = [t.value for t in VerkäuferDokumentTyp]

        # Empfohlene Dokumente hervorheben
        st.info(f"📌 Empfohlene Dokumente für {selected_projekt.property_type}: " + ", ".join(empfohlene_docs))

        dokument_typ = st.selectbox("Dokumenttyp*", options=alle_doc_typen)
        beschreibung = st.text_area("Beschreibung (optional)", placeholder="z.B. Aktuell vom 01.12.2024")
        gueltig_bis = st.date_input("Gültig bis (optional)", value=None)

        st.markdown("**Freigaben:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            freigabe_makler = st.checkbox("Für Makler", value=True)
        with col2:
            freigabe_notar = st.checkbox("Für Notar", value=True)
        with col3:
            freigabe_finanzierer = st.checkbox("Für Finanzierer", value=False)
        with col4:
            freigabe_kaeufer = st.checkbox("Für Käufer", value=False)

        datei = st.file_uploader("Datei hochladen*", type=["pdf", "jpg", "jpeg", "png"])

        submit = st.form_submit_button("📤 Dokument hochladen", type="primary")

        if submit and datei and dokument_typ:
            # Dokument speichern
            dokument_id = f"vdoc_{len(st.session_state.verkaeufer_dokumente)}"
            datei_bytes = datei.read()

            neues_dokument = VerkäuferDokument(
                dokument_id=dokument_id,
                verkaeufer_id=user_id,
                projekt_id=selected_projekt_id,
                dokument_typ=dokument_typ,
                dateiname=datei.name,
                dateigröße=len(datei_bytes),
                pdf_data=datei_bytes,
                beschreibung=beschreibung,
                gueltig_bis=gueltig_bis,
                freigegeben_fuer_makler=freigabe_makler,
                freigegeben_fuer_notar=freigabe_notar,
                freigegeben_fuer_finanzierer=freigabe_finanzierer,
                freigegeben_fuer_kaeufer=freigabe_kaeufer
            )

            st.session_state.verkaeufer_dokumente[dokument_id] = neues_dokument

            # Benachrichtigungen an alle freigegebenen Parteien
            if freigabe_makler and selected_projekt.makler_id:
                create_notification(
                    selected_projekt.makler_id,
                    "Neues Verkäufer-Dokument",
                    f"{st.session_state.current_user.name} hat '{dokument_typ}' hochgeladen.",
                    NotificationType.INFO.value
                )
            if freigabe_notar and selected_projekt.notar_id:
                create_notification(
                    selected_projekt.notar_id,
                    "Neues Verkäufer-Dokument",
                    f"{st.session_state.current_user.name} hat '{dokument_typ}' hochgeladen.",
                    NotificationType.INFO.value
                )

            st.success(f"✅ Dokument '{datei.name}' erfolgreich hochgeladen!")
            st.rerun()
        elif submit:
            st.error("Bitte füllen Sie alle Pflichtfelder aus und laden Sie eine Datei hoch!")

def verkaeufer_nachrichten():
    """Nachrichten für Verkäufer"""
    st.subheader("💬 Nachrichten")

    user_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if user_id in p.verkaeufer_ids]

    if not projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            projekt_comments = [c for c in st.session_state.comments.values()
                              if c.projekt_id == projekt.projekt_id and "Verkäufer" in c.sichtbar_fuer]
            projekt_comments.sort(key=lambda c: c.created_at, reverse=True)

            if projekt_comments:
                for comment in projekt_comments:
                    user = st.session_state.users.get(comment.user_id)
                    user_name = user.name if user else "Unbekannt"

                    st.markdown(f"""
                    <div style='background:#f0f0f0; padding:10px; border-radius:5px; margin:10px 0;'>
                        <strong>{user_name}</strong> <small>({comment.created_at.strftime('%d.%m.%Y %H:%M')})</small><br>
                        {comment.nachricht}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Noch keine Nachrichten.")

# ============================================================================
# FINANZIERER-BEREICH
# ============================================================================

def finanzierer_dashboard():
    """Dashboard für Finanzierer"""
    st.title("💼 Finanzierer-Dashboard")

    tabs = st.tabs([
        "📊 Timeline",
        "📋 Wirtschaftsdaten Käufer",
        "💰 Finanzierungsangebote erstellen",
        "📜 Meine Angebote"
    ])

    with tabs[0]:
        finanzierer_timeline_view()

    with tabs[1]:
        finanzierer_wirtschaftsdaten_view()

    with tabs[2]:
        finanzierer_angebote_erstellen()

    with tabs[3]:
        finanzierer_angebote_liste()

def finanzierer_timeline_view():
    """Timeline für Finanzierer"""
    st.subheader("📊 Projekt-Fortschritt")

    finanzierer_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if finanzierer_id in p.finanzierer_ids]

    if not projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            render_timeline(projekt.projekt_id, UserRole.FINANZIERER.value)

def finanzierer_wirtschaftsdaten_view():
    """Einsicht in Wirtschaftsdaten der Käufer"""
    st.subheader("📊 Wirtschaftsdaten Käufer")

    finanzierer_id = st.session_state.current_user.user_id
    relevante_projekte = [p for p in st.session_state.projekte.values()
                         if finanzierer_id in p.finanzierer_ids]

    if not relevante_projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    for projekt in relevante_projekte:
        st.markdown(f"### 🏘️ {projekt.name}")

        kaeufer_docs = {}
        for doc in st.session_state.wirtschaftsdaten.values():
            if doc.kaeufer_id in projekt.kaeufer_ids:
                if doc.kaeufer_id not in kaeufer_docs:
                    kaeufer_docs[doc.kaeufer_id] = []
                kaeufer_docs[doc.kaeufer_id].append(doc)

        if not kaeufer_docs:
            st.info("Noch keine Wirtschaftsdaten von Käufern hochgeladen.")
            continue

        for kaeufer_id, docs in kaeufer_docs.items():
            kaeufer = st.session_state.users.get(kaeufer_id)
            kaeufer_name = kaeufer.name if kaeufer else "Unbekannt"

            with st.expander(f"👤 {kaeufer_name} ({len(docs)} Dokument(e))", expanded=True):
                kategorien = {}
                for doc in docs:
                    if doc.kategorie not in kategorien:
                        kategorien[doc.kategorie] = []
                    kategorien[doc.kategorie].append(doc)

                for kategorie, kategorie_docs in kategorien.items():
                    st.markdown(f"**📁 {kategorie}** ({len(kategorie_docs)} Dokument(e))")

                    for doc in kategorie_docs:
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.write(f"📄 {doc.filename}")
                        with col2:
                            st.caption(f"Hochgeladen: {doc.upload_date.strftime('%d.%m.%Y %H:%M')}")
                            if st.button("👁️ OCR", key=f"fin_ocr_{doc.doc_id}"):
                                st.session_state[f"show_fin_ocr_{doc.doc_id}"] = not st.session_state.get(f"show_fin_ocr_{doc.doc_id}", False)
                        with col3:
                            st.download_button(
                                "📥",
                                doc.pdf_data,
                                file_name=doc.filename,
                                key=f"fin_dl_{doc.doc_id}"
                            )

                        if st.session_state.get(f"show_fin_ocr_{doc.doc_id}", False):
                            st.text_area("OCR-Text", doc.ocr_text, height=100, disabled=True, key=f"fin_ocr_text_{doc.doc_id}")

                        st.markdown("---")

        st.markdown("---")

def finanzierer_angebote_erstellen():
    """Formular zum Erstellen von Finanzierungsangeboten"""
    st.subheader("💰 Neues Finanzierungsangebot erstellen")

    finanzierer_id = st.session_state.current_user.user_id
    relevante_projekte = [p for p in st.session_state.projekte.values()
                         if finanzierer_id in p.finanzierer_ids]

    if not relevante_projekte:
        st.warning("Sie sind noch keinem Projekt zugeordnet.")
        return

    with st.form("neues_angebot"):
        projekt_options = {p.name: p.projekt_id for p in relevante_projekte}
        selected_projekt_name = st.selectbox("Projekt", list(projekt_options.keys()))
        projekt_id = projekt_options[selected_projekt_name]

        st.markdown("### 📋 Konditionen")

        col1, col2 = st.columns(2)
        with col1:
            darlehensbetrag = st.number_input("Darlehensbetrag (€)", min_value=0.0, value=300000.0, step=1000.0)
            zinssatz = st.number_input("Zinssatz (%)", min_value=0.0, max_value=20.0, value=3.5, step=0.1)
            tilgungssatz = st.number_input("Tilgungssatz (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1)

        with col2:
            sollzinsbindung = st.number_input("Sollzinsbindung (Jahre)", min_value=1, max_value=40, value=10)
            gesamtlaufzeit = st.number_input("Gesamtlaufzeit (Jahre)", min_value=1, max_value=40, value=30)
            monatliche_rate = st.number_input("Monatliche Rate (€)", min_value=0.0, value=1375.0, step=10.0)

        besondere_bedingungen = st.text_area(
            "Besondere Bedingungen",
            placeholder="z.B. Sondertilgung bis 5% p.a., bereitstellungszinsfreie Zeit 6 Monate",
            height=100
        )

        pdf_upload = st.file_uploader("Angebot als PDF anhängen (optional)", type=['pdf'])

        col1, col2 = st.columns(2)
        with col1:
            als_entwurf = st.form_submit_button("💾 Als Entwurf speichern")
        with col2:
            an_kaeufer = st.form_submit_button("📧 An Käufer senden", type="primary")

        if als_entwurf or an_kaeufer:
            offer_id = f"offer_{len(st.session_state.financing_offers)}"
            status = FinanzierungsStatus.ENTWURF.value if als_entwurf else FinanzierungsStatus.GESENDET.value

            offer = FinancingOffer(
                offer_id=offer_id,
                finanzierer_id=finanzierer_id,
                projekt_id=projekt_id,
                darlehensbetrag=darlehensbetrag,
                zinssatz=zinssatz,
                sollzinsbindung=sollzinsbindung,
                tilgungssatz=tilgungssatz,
                gesamtlaufzeit=gesamtlaufzeit,
                monatliche_rate=monatliche_rate,
                besondere_bedingungen=besondere_bedingungen,
                status=status,
                pdf_data=pdf_upload.read() if pdf_upload else None
            )

            st.session_state.financing_offers[offer_id] = offer

            if an_kaeufer:
                # Timeline aktualisieren
                projekt = st.session_state.projekte.get(projekt_id)
                if projekt:
                    for event_id in projekt.timeline_events:
                        event = st.session_state.timeline_events.get(event_id)
                        if event and event.titel == "Finanzierungsanfrage" and not event.completed:
                            event.completed = True
                            event.completed_at = datetime.now()
                    update_projekt_status(projekt_id)

                    # Benachrichtigungen
                    for kaeufer_id in projekt.kaeufer_ids:
                        create_notification(kaeufer_id, "Neues Finanzierungsangebot", f"Sie haben ein neues Finanzierungsangebot für {projekt.name}", NotificationType.INFO.value)

            if als_entwurf:
                st.success("✅ Angebot als Entwurf gespeichert!")
            else:
                st.success("✅ Angebot wurde an Käufer gesendet!")

            st.rerun()

def finanzierer_angebote_liste():
    """Liste aller Angebote des Finanzierers"""
    st.subheader("📜 Meine Finanzierungsangebote")

    finanzierer_id = st.session_state.current_user.user_id
    meine_angebote = [o for o in st.session_state.financing_offers.values()
                     if o.finanzierer_id == finanzierer_id]

    if not meine_angebote:
        st.info("Noch keine Angebote erstellt.")
        return

    status_gruppen = {}
    for offer in meine_angebote:
        if offer.status not in status_gruppen:
            status_gruppen[offer.status] = []
        status_gruppen[offer.status].append(offer)

    for status, offers in status_gruppen.items():
        st.markdown(f"### {status} ({len(offers)})")

        for offer in offers:
            projekt = st.session_state.projekte.get(offer.projekt_id)
            projekt_name = projekt.name if projekt else "Unbekannt"

            with st.expander(f"💰 {projekt_name} - {offer.darlehensbetrag:,.0f} € | {offer.zinssatz}%"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Darlehensbetrag", f"{offer.darlehensbetrag:,.2f} €")
                    st.metric("Zinssatz", f"{offer.zinssatz:.2f} %")
                with col2:
                    st.metric("Monatliche Rate", f"{offer.monatliche_rate:,.2f} €")
                    st.metric("Laufzeit", f"{offer.gesamtlaufzeit} Jahre")
                with col3:
                    st.write(f"**Status:** {offer.status}")
                    st.write(f"**Erstellt:** {offer.created_at.strftime('%d.%m.%Y')}")
                    if offer.accepted_at:
                        st.write(f"**Angenommen:** {offer.accepted_at.strftime('%d.%m.%Y')}")

                if offer.status == FinanzierungsStatus.ENTWURF.value:
                    if st.button("📧 An Käufer senden", key=f"send_{offer.offer_id}"):
                        offer.status = FinanzierungsStatus.GESENDET.value

                        # Benachrichtigungen
                        projekt = st.session_state.projekte.get(offer.projekt_id)
                        if projekt:
                            for kaeufer_id in projekt.kaeufer_ids:
                                create_notification(kaeufer_id, "Neues Finanzierungsangebot", f"Sie haben ein neues Finanzierungsangebot für {projekt.name}", NotificationType.INFO.value)

                        st.success("✅ Angebot wurde gesendet!")
                        st.rerun()

# ============================================================================
# NOTAR-BEREICH
# ============================================================================

def notar_dashboard():
    """Dashboard für Notar"""
    st.title("⚖️ Notar-Dashboard")

    tabs = st.tabs([
        "📊 Timeline",
        "📋 Projekte",
        "📝 Checklisten",
        "📋 Dokumentenanforderungen",
        "👥 Mitarbeiter",
        "💰 Finanzierungsnachweise",
        "📄 Dokumenten-Freigaben",
        "📅 Termine",
        "🤝 Maklerempfehlung"
    ])

    with tabs[0]:
        notar_timeline_view()

    with tabs[1]:
        notar_projekte_view()

    with tabs[2]:
        notar_checklisten_view()

    with tabs[3]:
        render_document_requests_view(st.session_state.current_user.user_id, UserRole.NOTAR.value)

    with tabs[4]:
        notar_mitarbeiter_view()

    with tabs[5]:
        notar_finanzierungsnachweise()

    with tabs[6]:
        notar_dokumenten_freigaben()

    with tabs[7]:
        notar_termine()

    with tabs[8]:
        notar_makler_empfehlung_view()

def notar_timeline_view():
    """Timeline für Notar"""
    st.subheader("📊 Projekt-Fortschritt")

    notar_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]

    if not projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            render_timeline(projekt.projekt_id, UserRole.NOTAR.value)

def notar_projekte_view():
    """Projekt-Übersicht für Notar"""
    st.subheader("📋 Meine Projekte")

    notar_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]

    if not projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Beschreibung:** {projekt.beschreibung}")
                if projekt.adresse:
                    st.markdown(f"**Adresse:** {projekt.adresse}")
                if projekt.kaufpreis > 0:
                    st.markdown(f"**Kaufpreis:** {projekt.kaufpreis:,.2f} €")

            with col2:
                st.markdown("**Parteien:**")
                for kid in projekt.kaeufer_ids:
                    kaeufer = st.session_state.users.get(kid)
                    if kaeufer:
                        st.write(f"🏠 Käufer: {kaeufer.name}")

                for vid in projekt.verkaeufer_ids:
                    verkaeufer = st.session_state.users.get(vid)
                    if verkaeufer:
                        st.write(f"🏡 Verkäufer: {verkaeufer.name}")

def notar_checklisten_view():
    """Notarielle Checklisten-Verwaltung"""
    st.subheader("📝 Notarielle Checklisten")

    notar_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]

    if not projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    # Projekt auswählen
    projekt_options = {f"{p.name} (ID: {p.projekt_id})": p.projekt_id for p in projekte}
    selected_projekt_label = st.selectbox("Projekt auswählen:", list(projekt_options.keys()))
    selected_projekt_id = projekt_options[selected_projekt_label]
    selected_projekt = st.session_state.projekte[selected_projekt_id]

    st.markdown("---")

    # Checklisten für dieses Projekt anzeigen
    projekt_checklists = [c for c in st.session_state.notar_checklists.values()
                         if c.projekt_id == selected_projekt_id]

    # Neue Checkliste erstellen
    with st.expander("➕ Neue Checkliste erstellen", expanded=len(projekt_checklists) == 0):
        col1, col2 = st.columns(2)
        with col1:
            checklist_typ = st.selectbox("Checklisten-Typ:", [t.value for t in ChecklistType])
        with col2:
            # Partei auswählen (Käufer oder Verkäufer)
            parteien = []
            for kid in selected_projekt.kaeufer_ids:
                kaeufer = st.session_state.users.get(kid)
                if kaeufer:
                    parteien.append(f"Käufer: {kaeufer.name}")
            for vid in selected_projekt.verkaeufer_ids:
                verkaeufer = st.session_state.users.get(vid)
                if verkaeufer:
                    parteien.append(f"Verkäufer: {verkaeufer.name}")

            if parteien:
                partei = st.selectbox("Für Partei:", parteien)
            else:
                st.warning("Keine Parteien im Projekt vorhanden")
                partei = None

        if st.button("Checkliste erstellen") and partei:
            checklist_id = f"checklist_{len(st.session_state.notar_checklists)}"
            new_checklist = NotarChecklist(
                checklist_id=checklist_id,
                projekt_id=selected_projekt_id,
                checklist_typ=checklist_typ,
                partei=partei
            )
            st.session_state.notar_checklists[checklist_id] = new_checklist
            st.success(f"Checkliste '{checklist_typ}' für {partei} erstellt!")
            st.rerun()

    st.markdown("---")

    # Bestehende Checklisten anzeigen
    if projekt_checklists:
        st.markdown("### Bestehende Checklisten")

        for checklist in projekt_checklists:
            with st.expander(f"📋 {checklist.checklist_typ} - {checklist.partei}", expanded=False):
                render_checklist_form(checklist)
    else:
        st.info("Noch keine Checklisten für dieses Projekt erstellt.")

def notar_mitarbeiter_view():
    """Mitarbeiter-Verwaltung für Notar"""
    st.subheader("👥 Mitarbeiter-Verwaltung")

    notar_id = st.session_state.current_user.user_id

    # Bestehende Mitarbeiter anzeigen
    mitarbeiter = [m for m in st.session_state.notar_mitarbeiter.values() if m.notar_id == notar_id]

    if mitarbeiter:
        st.markdown("### 👤 Meine Mitarbeiter")

        for ma in mitarbeiter:
            status_icon = "✅" if ma.aktiv else "❌"
            with st.expander(f"{status_icon} {ma.name} - {ma.rolle}", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**E-Mail:** {ma.email}")
                    st.write(f"**Rolle:** {ma.rolle}")
                    st.write(f"**Status:** {'Aktiv' if ma.aktiv else 'Inaktiv'}")
                    st.write(f"**Erstellt am:** {ma.created_at.strftime('%d.%m.%Y')}")

                with col2:
                    st.write("**Berechtigungen:**")
                    st.write(f"{'✅' if ma.kann_checklisten_bearbeiten else '❌'} Checklisten bearbeiten")
                    st.write(f"{'✅' if ma.kann_dokumente_freigeben else '❌'} Dokumente freigeben")
                    st.write(f"{'✅' if ma.kann_termine_verwalten else '❌'} Termine verwalten")
                    st.write(f"{'✅' if ma.kann_finanzierung_sehen else '❌'} Finanzierung einsehen")

                st.markdown("---")

                # Zugewiesene Projekte
                st.markdown("**Zugewiesene Projekte:**")
                if ma.projekt_ids:
                    for projekt_id in ma.projekt_ids:
                        projekt = st.session_state.projekte.get(projekt_id)
                        if projekt:
                            st.write(f"🏘️ {projekt.name}")
                else:
                    st.info("Keine Projekte zugewiesen")

                st.markdown("---")

                # Mitarbeiter bearbeiten
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✏️ Berechtigungen ändern", key=f"edit_ma_{ma.mitarbeiter_id}"):
                        st.session_state[f"edit_mitarbeiter_{ma.mitarbeiter_id}"] = True
                        st.rerun()
                with col2:
                    if ma.aktiv:
                        if st.button("❌ Deaktivieren", key=f"deact_ma_{ma.mitarbeiter_id}"):
                            ma.aktiv = False
                            st.session_state.notar_mitarbeiter[ma.mitarbeiter_id] = ma
                            st.success(f"{ma.name} wurde deaktiviert.")
                            st.rerun()
                    else:
                        if st.button("✅ Aktivieren", key=f"act_ma_{ma.mitarbeiter_id}"):
                            ma.aktiv = True
                            st.session_state.notar_mitarbeiter[ma.mitarbeiter_id] = ma
                            st.success(f"{ma.name} wurde aktiviert.")
                            st.rerun()
                with col3:
                    if st.button("🗑️ Löschen", key=f"del_ma_{ma.mitarbeiter_id}"):
                        del st.session_state.notar_mitarbeiter[ma.mitarbeiter_id]
                        st.success(f"{ma.name} wurde gelöscht.")
                        st.rerun()

                # Berechtigungen ändern (Modal)
                if st.session_state.get(f"edit_mitarbeiter_{ma.mitarbeiter_id}", False):
                    st.markdown("---")
                    st.markdown("#### Berechtigungen ändern")

                    with st.form(f"edit_form_{ma.mitarbeiter_id}"):
                        neue_rolle = st.selectbox("Rolle:", [r.value for r in NotarMitarbeiterRolle],
                                                 index=[r.value for r in NotarMitarbeiterRolle].index(ma.rolle) if ma.rolle in [r.value for r in NotarMitarbeiterRolle] else 0)

                        kann_checklisten = st.checkbox("Checklisten bearbeiten", value=ma.kann_checklisten_bearbeiten)
                        kann_dokumente = st.checkbox("Dokumente freigeben", value=ma.kann_dokumente_freigeben)
                        kann_termine = st.checkbox("Termine verwalten", value=ma.kann_termine_verwalten)
                        kann_finanzierung = st.checkbox("Finanzierung einsehen", value=ma.kann_finanzierung_sehen)

                        # Projekte zuweisen
                        st.markdown("**Projekte zuweisen:**")
                        alle_projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]
                        projekt_options = {p.name: p.projekt_id for p in alle_projekte}

                        zugewiesene_projekte = st.multiselect(
                            "Projekte auswählen:",
                            options=list(projekt_options.keys()),
                            default=[p.name for p in alle_projekte if p.projekt_id in ma.projekt_ids]
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Speichern", type="primary"):
                                ma.rolle = neue_rolle
                                ma.kann_checklisten_bearbeiten = kann_checklisten
                                ma.kann_dokumente_freigeben = kann_dokumente
                                ma.kann_termine_verwalten = kann_termine
                                ma.kann_finanzierung_sehen = kann_finanzierung
                                ma.projekt_ids = [projekt_options[p_name] for p_name in zugewiesene_projekte]

                                st.session_state.notar_mitarbeiter[ma.mitarbeiter_id] = ma
                                st.session_state[f"edit_mitarbeiter_{ma.mitarbeiter_id}"] = False
                                st.success("Berechtigungen aktualisiert!")
                                st.rerun()

                        with col2:
                            if st.form_submit_button("❌ Abbrechen"):
                                st.session_state[f"edit_mitarbeiter_{ma.mitarbeiter_id}"] = False
                                st.rerun()

        st.markdown("---")
    else:
        st.info("Noch keine Mitarbeiter angelegt.")

    # Neuen Mitarbeiter hinzufügen
    st.markdown("### ➕ Neuen Mitarbeiter hinzufügen")

    with st.form("neuer_mitarbeiter"):
        col1, col2 = st.columns(2)

        with col1:
            ma_name = st.text_input("Name*")
            ma_email = st.text_input("E-Mail*")
            ma_passwort = st.text_input("Passwort*", type="password")

        with col2:
            ma_rolle = st.selectbox("Rolle*", [r.value for r in NotarMitarbeiterRolle])

            # Vordefinierte Berechtigungen basierend auf Rolle
            if ma_rolle == NotarMitarbeiterRolle.VOLLZUGRIFF.value:
                default_checklisten = True
                default_dokumente = True
                default_termine = True
                default_finanzierung = True
            elif ma_rolle == NotarMitarbeiterRolle.SACHBEARBEITER.value:
                default_checklisten = True
                default_dokumente = False
                default_termine = True
                default_finanzierung = False
            elif ma_rolle == NotarMitarbeiterRolle.CHECKLISTEN_VERWALTER.value:
                default_checklisten = True
                default_dokumente = False
                default_termine = False
                default_finanzierung = False
            else:  # NUR_LESEN
                default_checklisten = False
                default_dokumente = False
                default_termine = False
                default_finanzierung = False

        st.markdown("**Berechtigungen:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            kann_checklisten = st.checkbox("Checklisten bearbeiten", value=default_checklisten, key="new_ma_checklisten")
        with col2:
            kann_dokumente = st.checkbox("Dokumente freigeben", value=default_dokumente, key="new_ma_dokumente")
        with col3:
            kann_termine = st.checkbox("Termine verwalten", value=default_termine, key="new_ma_termine")
        with col4:
            kann_finanzierung = st.checkbox("Finanzierung einsehen", value=default_finanzierung, key="new_ma_finanzierung")

        # Projekte zuweisen
        st.markdown("**Projekte zuweisen (optional):**")
        alle_projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]
        if alle_projekte:
            projekt_options = {p.name: p.projekt_id for p in alle_projekte}
            zugewiesene_projekte = st.multiselect("Projekte auswählen:", list(projekt_options.keys()))
        else:
            zugewiesene_projekte = []
            st.info("Noch keine Projekte vorhanden")

        if st.form_submit_button("➕ Mitarbeiter hinzufügen", type="primary"):
            if ma_name and ma_email and ma_passwort:
                mitarbeiter_id = f"notarma_{len(st.session_state.notar_mitarbeiter)}"

                neuer_mitarbeiter = NotarMitarbeiter(
                    mitarbeiter_id=mitarbeiter_id,
                    notar_id=notar_id,
                    name=ma_name,
                    email=ma_email,
                    password_hash=hash_password(ma_passwort),
                    rolle=ma_rolle,
                    kann_checklisten_bearbeiten=kann_checklisten,
                    kann_dokumente_freigeben=kann_dokumente,
                    kann_termine_verwalten=kann_termine,
                    kann_finanzierung_sehen=kann_finanzierung,
                    projekt_ids=[projekt_options[p_name] for p_name in zugewiesene_projekte] if alle_projekte else []
                )

                st.session_state.notar_mitarbeiter[mitarbeiter_id] = neuer_mitarbeiter
                st.success(f"✅ Mitarbeiter {ma_name} wurde erfolgreich hinzugefügt!")
                st.info(f"🔑 Login: {ma_email} / {ma_passwort}")
                st.rerun()
            else:
                st.error("Bitte füllen Sie alle Pflichtfelder aus!")

def notar_finanzierungsnachweise():
    """Finanzierungsnachweise für Notar"""
    st.subheader("💰 Finanzierungsnachweise")

    notar_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]

    if not projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    for projekt in projekte:
        st.markdown(f"### 🏘️ {projekt.name}")

        # Angenommene Finanzierungsangebote suchen
        finanzierungen = [o for o in st.session_state.financing_offers.values()
                         if o.projekt_id == projekt.projekt_id
                         and o.status == FinanzierungsStatus.ANGENOMMEN.value]

        if finanzierungen:
            for offer in finanzierungen:
                finanzierer = st.session_state.users.get(offer.finanzierer_id)
                finanzierer_name = finanzierer.name if finanzierer else "Unbekannt"

                icon = "⭐" if offer.fuer_notar_markiert else "✅"

                with st.expander(f"{icon} Finanzierung von {finanzierer_name}", expanded=offer.fuer_notar_markiert):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Darlehensbetrag", f"{offer.darlehensbetrag:,.2f} €")
                        st.metric("Zinssatz", f"{offer.zinssatz:.2f} %")
                    with col2:
                        st.metric("Monatliche Rate", f"{offer.monatliche_rate:,.2f} €")
                        st.metric("Angenommen am", offer.accepted_at.strftime("%d.%m.%Y"))

                    if offer.fuer_notar_markiert:
                        st.success("⭐ Als offizieller Finanzierungsnachweis markiert")

                    if offer.pdf_data:
                        st.download_button(
                            "📥 Finanzierungsangebot als PDF",
                            offer.pdf_data,
                            file_name=f"Finanzierung_{projekt.name}.pdf",
                            mime="application/pdf",
                            key=f"notar_fin_{offer.offer_id}"
                        )
        else:
            st.info("Noch keine Finanzierung gesichert.")

        st.markdown("---")

def notar_dokumenten_freigaben():
    """Dokumenten-Freigaben für Notar"""
    st.subheader("📄 Dokumenten-Freigaben")

    notar_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]

    if not projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    for projekt in projekte:
        st.markdown(f"### 🏘️ {projekt.name}")

        # Wirtschaftsdaten mit Freigabe
        freigegeben_docs = [d for d in st.session_state.wirtschaftsdaten.values()
                           if d.kaeufer_id in projekt.kaeufer_ids and d.freigegeben_fuer_notar]

        if freigegeben_docs:
            st.success(f"✅ {len(freigegeben_docs)} freigegebene Wirtschaftsdaten-Dokumente")

            for doc in freigegeben_docs:
                kaeufer = st.session_state.users.get(doc.kaeufer_id)
                kaeufer_name = kaeufer.name if kaeufer else "Unbekannt"

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📄 {doc.filename} (von {kaeufer_name})")
                with col2:
                    st.download_button(
                        "📥",
                        doc.pdf_data,
                        file_name=doc.filename,
                        key=f"notar_doc_{doc.doc_id}"
                    )
        else:
            st.info("Noch keine Dokumente freigegeben.")

        st.markdown("---")

def notar_termine():
    """Erweiterte Termin-Verwaltung für Notar mit Outlook-Kalender-Integration"""
    st.subheader("📅 Notartermine")

    notar_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]

    # Outlook-Kalender-Simulation
    st.markdown("### 📆 Mein Outlook-Kalender")
    st.info("💡 Der Kalender zeigt Ihre anstehenden Beurkundungstermine. Termine werden automatisch mit Ihrem Outlook synchronisiert.")

    # Alle bestätigten Termine anzeigen
    alle_termine = []
    for projekt in projekte:
        for termin_id in projekt.termine:
            termin = st.session_state.termine.get(termin_id)
            if termin and termin.termin_typ == TerminTyp.BEURKUNDUNG.value:
                alle_termine.append((termin, projekt))

    if alle_termine:
        for termin, projekt in sorted(alle_termine, key=lambda x: x[0].datum):
            status_icon = "🟢" if termin.status == TerminStatus.BESTAETIGT.value else "🟡" if termin.status == TerminStatus.TEILWEISE_BESTAETIGT.value else "🟠"
            outlook_status = f"[{termin.outlook_status}]" if termin.outlook_status else ""

            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"{status_icon} **{termin.datum.strftime('%d.%m.%Y')}** - {termin.uhrzeit_start} Uhr")
                st.caption(termin.beschreibung)
            with col2:
                st.write(f"Projekt: {projekt.name}")
                st.write(f"Status: {termin.status} {outlook_status}")
            with col3:
                if termin.status == TerminStatus.BESTAETIGT.value:
                    ics_content = generate_ics_file(termin, projekt)
                    st.download_button("📥 .ics", data=ics_content, file_name=f"beurkundung_{projekt.projekt_id}.ics", mime="text/calendar", key=f"notar_ics_{termin.termin_id}")
    else:
        st.info("Keine Beurkundungstermine vorhanden.")

    st.markdown("---")
    st.markdown("### 📋 Terminvorschläge für Projekte")

    if not projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            # Prüfe ob Kaufvertragsentwurf gesendet wurde
            entwurf_gesendet = check_kaufvertrag_entwurf_status(projekt.projekt_id)

            if not entwurf_gesendet:
                st.warning("⚠️ Kaufvertragsentwurf muss erst versendet werden, bevor Beurkundungstermine vorgeschlagen werden können.")

                # Manuell als erledigt markieren
                if st.checkbox("Kaufvertragsentwurf wurde versendet", key=f"entwurf_ok_{projekt.projekt_id}"):
                    # Timeline-Event als erledigt markieren
                    for event_id in projekt.timeline_events:
                        event = st.session_state.timeline_events.get(event_id)
                        if event and "Kaufvertrag" in event.titel and not event.completed:
                            event.completed = True
                            event.completed_at = datetime.now()
                            st.session_state.timeline_events[event_id] = event
                    st.success("Status aktualisiert!")
                    st.rerun()
                continue

            # Bestehende Beurkundungstermine anzeigen
            beurkundungstermine = [st.session_state.termine.get(tid) for tid in projekt.termine
                                   if st.session_state.termine.get(tid) and
                                   st.session_state.termine.get(tid).termin_typ == TerminTyp.BEURKUNDUNG.value]

            if beurkundungstermine:
                for termin in beurkundungstermine:
                    status_icon = "🟢" if termin.status == TerminStatus.BESTAETIGT.value else "🟡"
                    st.markdown(f"{status_icon} **Termin:** {termin.datum.strftime('%d.%m.%Y')} um {termin.uhrzeit_start} Uhr")
                    st.write(f"Status: {termin.status}")

                    # Bestätigungsstatus anzeigen
                    bestaetigung = check_termin_bestaetigung(termin, projekt)
                    if not bestaetigung['alle_bestaetigt']:
                        ausstehend = []
                        if not bestaetigung['makler_bestaetigt'] and projekt.makler_id:
                            ausstehend.append("Makler")
                        if bestaetigung['kaeufer_ausstehend']:
                            ausstehend.append(f"Käufer ({len(bestaetigung['kaeufer_ausstehend'])})")
                        if bestaetigung['verkaeufer_ausstehend']:
                            ausstehend.append(f"Verkäufer ({len(bestaetigung['verkaeufer_ausstehend'])})")
                        st.caption(f"Ausstehende Bestätigungen: {', '.join(ausstehend)}")
            else:
                st.info("Noch keine Beurkundungstermine.")

            # Offene Vorschläge anzeigen
            offene_vorschlaege = [v for v in st.session_state.terminvorschlaege.values()
                                 if v.projekt_id == projekt.projekt_id and
                                 v.termin_typ == TerminTyp.BEURKUNDUNG.value and
                                 v.status == "offen"]

            if offene_vorschlaege:
                st.markdown("##### 📨 Bereits gesendete Vorschläge")
                for vorschlag in offene_vorschlaege:
                    st.write(f"Gesendet am: {vorschlag.erstellt_am.strftime('%d.%m.%Y %H:%M')}")
                    for i, slot in enumerate(vorschlag.vorschlaege):
                        st.write(f"  Option {i+1}: {slot['datum'].strftime('%d.%m.%Y')} ({slot['tageszeit']}) {slot['uhrzeit_start']}-{slot['uhrzeit_ende']} Uhr")

            # Button zum Erstellen neuer Vorschläge
            st.markdown("##### ➕ Neue Terminvorschläge generieren")
            st.caption("Basierend auf Ihrem Outlook-Kalender werden 3 verfügbare Termine vorgeschlagen.")

            col1, col2 = st.columns(2)
            with col1:
                tageszeit_filter = st.selectbox("Bevorzugte Tageszeit", ["Alle", "Vormittag", "Nachmittag"], key=f"tageszeit_{projekt.projekt_id}")

            if st.button("🗓️ 3 Terminvorschläge generieren", key=f"gen_vorschlag_{projekt.projekt_id}", type="primary"):
                vorschlag = create_termin_vorschlaege(projekt.projekt_id, notar_id, TerminTyp.BEURKUNDUNG.value)
                if vorschlag:
                    st.success("✅ 3 Terminvorschläge wurden erstellt und an Makler/Käufer/Verkäufer gesendet!")

                    # Benachrichtigungen senden
                    if projekt.makler_id:
                        create_notification(
                            projekt.makler_id,
                            "Neue Terminvorschläge",
                            f"Der Notar hat 3 Terminvorschläge für die Beurkundung von '{projekt.name}' erstellt.",
                            NotificationType.INFO.value
                        )
                    for kid in projekt.kaeufer_ids:
                        create_notification(kid, "Neue Terminvorschläge", f"Der Notar hat Terminvorschläge für die Beurkundung erstellt.", NotificationType.INFO.value)
                    for vid in projekt.verkaeufer_ids:
                        create_notification(vid, "Neue Terminvorschläge", f"Der Notar hat Terminvorschläge für die Beurkundung erstellt.", NotificationType.INFO.value)

                    st.rerun()
                else:
                    st.error("Keine verfügbaren Termine in den nächsten 4 Wochen gefunden.")

            st.markdown("---")

            # Alle Termine für dieses Projekt (alle Typen)
            st.markdown("##### 📋 Alle Termine")
            render_termin_verwaltung(projekt, UserRole.NOTAR.value)

def notar_makler_empfehlung_view():
    """Makler-Empfehlungen für Verkäufer verwalten"""
    import uuid

    st.subheader("🤝 Maklerempfehlung für Verkäufer")
    st.info("""
    Empfehlen Sie geprüfte Makler an Verkäufer weiter. Eingeladene Makler erhalten
    einen Link zur Dateneingabe und werden nach Ihrer Freigabe für Verkäufer sichtbar.
    """)

    notar_id = st.session_state.current_user.user_id

    # Neuen Makler einladen
    st.markdown("### ➕ Neuen Makler einladen")

    with st.form("invite_makler_form"):
        col1, col2 = st.columns(2)
        with col1:
            makler_email = st.text_input("E-Mail-Adresse des Maklers*")
            makler_name = st.text_input("Name/Firma des Maklers")
        with col2:
            notiz = st.text_area("Interne Notiz (nur für Sie sichtbar)", height=100)

        submit = st.form_submit_button("📧 Einladung senden", type="primary")

        if submit and makler_email:
            # Prüfen ob bereits eingeladen
            existing = [e for e in st.session_state.makler_empfehlungen.values()
                       if e.makler_email.lower() == makler_email.lower() and e.notar_id == notar_id]

            if existing:
                st.warning("⚠️ Dieser Makler wurde bereits eingeladen.")
            else:
                # Neue Empfehlung erstellen
                empfehlung_id = f"emp_{len(st.session_state.makler_empfehlungen) + 1}"
                onboarding_token = str(uuid.uuid4())

                neue_empfehlung = MaklerEmpfehlung(
                    empfehlung_id=empfehlung_id,
                    notar_id=notar_id,
                    makler_email=makler_email,
                    makler_name=makler_name,
                    status=MaklerEmpfehlungStatus.EINGELADEN.value,
                    onboarding_token=onboarding_token,
                    notiz_notar=notiz
                )
                st.session_state.makler_empfehlungen[empfehlung_id] = neue_empfehlung

                # Simulierte E-Mail-Benachrichtigung
                st.success(f"""
                ✅ Einladung gesendet!

                **Simulierte E-Mail an:** {makler_email}

                **Betreff:** Einladung zur Makler-Plattform

                **Inhalt:**
                Sehr geehrte(r) {makler_name or 'Makler'},

                Sie wurden von Notariat {st.session_state.current_user.name} eingeladen,
                sich auf unserer Immobilien-Transaktionsplattform zu registrieren.

                Bitte füllen Sie Ihre Firmendaten unter folgendem Link aus:
                **https://plattform.example.com/makler-onboarding?token={onboarding_token}**

                Mit freundlichen Grüßen,
                {st.session_state.current_user.name}
                """)
                st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Eingeladene Makler")

    # Makler nach Status gruppieren
    meine_empfehlungen = [e for e in st.session_state.makler_empfehlungen.values()
                         if e.notar_id == notar_id]

    if not meine_empfehlungen:
        st.info("Noch keine Makler eingeladen.")
        return

    # Tabs für Status
    status_tabs = st.tabs(["⏳ Ausstehend", "✅ Freigegeben", "❌ Abgelehnt/Deaktiviert"])

    # Ausstehend (Eingeladen + Daten eingegeben)
    with status_tabs[0]:
        ausstehend = [e for e in meine_empfehlungen
                      if e.status in [MaklerEmpfehlungStatus.EINGELADEN.value,
                                     MaklerEmpfehlungStatus.DATEN_EINGEGEBEN.value]]

        if not ausstehend:
            st.info("Keine ausstehenden Einladungen.")
        else:
            for emp in ausstehend:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])

                    with col1:
                        st.markdown(f"**{emp.firmenname or emp.makler_name or emp.makler_email}**")
                        st.caption(f"📧 {emp.makler_email}")
                        if emp.kurzvita:
                            st.write(emp.kurzvita[:100] + "..." if len(emp.kurzvita) > 100 else emp.kurzvita)

                    with col2:
                        status_icon = "📨" if emp.status == MaklerEmpfehlungStatus.EINGELADEN.value else "📝"
                        st.write(f"{status_icon} **{emp.status}**")
                        st.caption(f"Eingeladen: {emp.eingeladen_am.strftime('%d.%m.%Y')}")
                        if emp.telefon:
                            st.write(f"📞 {emp.telefon}")

                    with col3:
                        if emp.status == MaklerEmpfehlungStatus.DATEN_EINGEGEBEN.value:
                            # Makler hat Daten eingegeben - Freigabe möglich
                            if st.button("✅ Freigeben", key=f"approve_{emp.empfehlung_id}", type="primary"):
                                emp.status = MaklerEmpfehlungStatus.FREIGEGEBEN.value
                                emp.freigegeben_am = datetime.now()
                                st.session_state.makler_empfehlungen[emp.empfehlung_id] = emp
                                st.success("Makler freigegeben!")
                                st.rerun()

                            if st.button("❌ Ablehnen", key=f"reject_{emp.empfehlung_id}"):
                                emp.status = MaklerEmpfehlungStatus.ABGELEHNT.value
                                st.session_state.makler_empfehlungen[emp.empfehlung_id] = emp
                                st.rerun()
                        else:
                            # Noch keine Daten - Erinnerung senden
                            if st.button("📧 Erneut senden", key=f"resend_{emp.empfehlung_id}"):
                                st.info(f"Erinnerung an {emp.makler_email} gesendet (simuliert)")

                        # Details anzeigen
                        if emp.kurzvita or emp.spezialisierung:
                            with st.expander("📄 Details"):
                                if emp.kurzvita:
                                    st.write(f"**Kurzvita:** {emp.kurzvita}")
                                if emp.spezialisierung:
                                    st.write(f"**Spezialisierung:** {', '.join(emp.spezialisierung)}")
                                if emp.regionen:
                                    st.write(f"**Regionen:** {', '.join(emp.regionen)}")
                                if emp.provision_verkaeufer_prozent > 0:
                                    st.write(f"**Provision Verkäufer:** {emp.provision_verkaeufer_prozent}%")
                                if emp.provision_kaeufer_prozent > 0:
                                    st.write(f"**Provision Käufer:** {emp.provision_kaeufer_prozent}%")

                    st.markdown("---")

    # Freigegeben
    with status_tabs[1]:
        freigegeben = [e for e in meine_empfehlungen
                       if e.status == MaklerEmpfehlungStatus.FREIGEGEBEN.value]

        if not freigegeben:
            st.info("Noch keine freigegebenen Makler.")
        else:
            for emp in freigegeben:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])

                    with col1:
                        st.markdown(f"### {emp.firmenname or emp.makler_name}")
                        st.caption(f"📧 {emp.makler_email}")
                        if emp.kurzvita:
                            st.write(emp.kurzvita)

                    with col2:
                        st.write("✅ **Freigegeben**")
                        st.caption(f"Seit: {emp.freigegeben_am.strftime('%d.%m.%Y') if emp.freigegeben_am else 'N/A'}")
                        if emp.telefon:
                            st.write(f"📞 {emp.telefon}")
                        if emp.website:
                            st.write(f"🌐 {emp.website}")

                    with col3:
                        if st.button("⏸️ Deaktivieren", key=f"deactivate_{emp.empfehlung_id}"):
                            emp.status = MaklerEmpfehlungStatus.DEAKTIVIERT.value
                            st.session_state.makler_empfehlungen[emp.empfehlung_id] = emp
                            st.rerun()

                        with st.expander("📄 Alle Details"):
                            st.write(f"**Adresse:** {emp.adresse}")
                            st.write(f"**Spezialisierung:** {', '.join(emp.spezialisierung)}")
                            st.write(f"**Regionen:** {', '.join(emp.regionen)}")
                            st.write(f"**Provision Verkäufer:** {emp.provision_verkaeufer_prozent}%")
                            st.write(f"**Provision Käufer:** {emp.provision_kaeufer_prozent}%")
                            if emp.notiz_notar:
                                st.write(f"**Ihre Notiz:** {emp.notiz_notar}")

                    st.markdown("---")

    # Abgelehnt/Deaktiviert
    with status_tabs[2]:
        inaktiv = [e for e in meine_empfehlungen
                   if e.status in [MaklerEmpfehlungStatus.ABGELEHNT.value,
                                  MaklerEmpfehlungStatus.DEAKTIVIERT.value]]

        if not inaktiv:
            st.info("Keine abgelehnten oder deaktivierten Makler.")
        else:
            for emp in inaktiv:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{emp.firmenname or emp.makler_name or emp.makler_email}** - {emp.status}")
                with col2:
                    if st.button("🔄 Reaktivieren", key=f"reactivate_{emp.empfehlung_id}"):
                        emp.status = MaklerEmpfehlungStatus.FREIGEGEBEN.value
                        emp.freigegeben_am = datetime.now()
                        st.session_state.makler_empfehlungen[emp.empfehlung_id] = emp
                        st.rerun()


# ============================================================================
# NOTAR-MITARBEITER-BEREICH
# ============================================================================

def notarmitarbeiter_dashboard():
    """Dashboard für Notar-Mitarbeiter"""
    mitarbeiter = st.session_state.current_user

    st.title("⚖️ Notar-Mitarbeiter-Dashboard")
    st.info(f"👤 {mitarbeiter.name} | Rolle: {mitarbeiter.rolle}")

    # Tab-Liste basierend auf Berechtigungen
    tab_labels = ["📊 Timeline", "📋 Projekte"]

    if mitarbeiter.kann_checklisten_bearbeiten:
        tab_labels.append("📝 Checklisten")

    if mitarbeiter.kann_dokumente_freigeben:
        tab_labels.append("📄 Dokumenten-Freigaben")

    if mitarbeiter.kann_termine_verwalten:
        tab_labels.append("📅 Termine")

    if mitarbeiter.kann_finanzierung_sehen:
        tab_labels.append("💰 Finanzierungsnachweise")

    tabs = st.tabs(tab_labels)

    tab_index = 0

    # Timeline (immer verfügbar)
    with tabs[tab_index]:
        st.subheader("📊 Projekt-Fortschritt")
        if not mitarbeiter.projekt_ids:
            st.info("Ihnen wurden noch keine Projekte zugewiesen.")
        else:
            for projekt_id in mitarbeiter.projekt_ids:
                projekt = st.session_state.projekte.get(projekt_id)
                if projekt:
                    with st.expander(f"🏘️ {projekt.name}", expanded=True):
                        render_timeline(projekt_id, "Notar-Mitarbeiter")
    tab_index += 1

    # Projekte (immer verfügbar)
    with tabs[tab_index]:
        st.subheader("📋 Meine zugewiesenen Projekte")
        if not mitarbeiter.projekt_ids:
            st.info("Ihnen wurden noch keine Projekte zugewiesen.")
        else:
            for projekt_id in mitarbeiter.projekt_ids:
                projekt = st.session_state.projekte.get(projekt_id)
                if projekt:
                    with st.expander(f"🏘️ {projekt.name}", expanded=True):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown(f"**Beschreibung:** {projekt.beschreibung}")
                            if projekt.adresse:
                                st.markdown(f"**Adresse:** {projekt.adresse}")
                            if projekt.kaufpreis > 0:
                                st.markdown(f"**Kaufpreis:** {projekt.kaufpreis:,.2f} €")

                        with col2:
                            st.markdown("**Parteien:**")
                            for kid in projekt.kaeufer_ids:
                                kaeufer = st.session_state.users.get(kid)
                                if kaeufer:
                                    st.write(f"🏠 Käufer: {kaeufer.name}")

                            for vid in projekt.verkaeufer_ids:
                                verkaeufer = st.session_state.users.get(vid)
                                if verkaeufer:
                                    st.write(f"🏡 Verkäufer: {verkaeufer.name}")
    tab_index += 1

    # Checklisten (nur wenn berechtigt)
    if mitarbeiter.kann_checklisten_bearbeiten:
        with tabs[tab_index]:
            st.subheader("📝 Checklisten bearbeiten")
            if not mitarbeiter.projekt_ids:
                st.info("Ihnen wurden noch keine Projekte zugewiesen.")
            else:
                # Projekt auswählen
                projekte = [st.session_state.projekte.get(pid) for pid in mitarbeiter.projekt_ids]
                projekte = [p for p in projekte if p is not None]

                if projekte:
                    projekt_options = {f"{p.name} (ID: {p.projekt_id})": p.projekt_id for p in projekte}
                    selected_projekt_label = st.selectbox("Projekt auswählen:", list(projekt_options.keys()), key="ma_checklist_projekt")
                    selected_projekt_id = projekt_options[selected_projekt_label]

                    # Checklisten für dieses Projekt anzeigen
                    projekt_checklists = [c for c in st.session_state.notar_checklists.values()
                                         if c.projekt_id == selected_projekt_id]

                    if projekt_checklists:
                        for checklist in projekt_checklists:
                            with st.expander(f"📋 {checklist.checklist_typ} - {checklist.partei}", expanded=False):
                                render_checklist_form(checklist)
                    else:
                        st.info("Noch keine Checklisten für dieses Projekt vorhanden.")
        tab_index += 1

    # Dokumenten-Freigaben (nur wenn berechtigt)
    if mitarbeiter.kann_dokumente_freigeben:
        with tabs[tab_index]:
            st.subheader("📄 Dokumenten-Freigaben")
            st.info("Diese Funktion würde Dokumenten-Freigaben anzeigen und verwalten.")
            # Hier könnte man die Verkäufer-Dokumente anzeigen und freigeben lassen
        tab_index += 1

    # Termine (nur wenn berechtigt)
    if mitarbeiter.kann_termine_verwalten:
        with tabs[tab_index]:
            st.subheader("📅 Termine verwalten")
            if not mitarbeiter.projekt_ids:
                st.info("Ihnen wurden noch keine Projekte zugewiesen.")
            else:
                for projekt_id in mitarbeiter.projekt_ids:
                    projekt = st.session_state.projekte.get(projekt_id)
                    if projekt:
                        with st.expander(f"🏘️ {projekt.name}", expanded=True):
                            if projekt.notartermin:
                                st.success(f"✅ Termin vereinbart: {projekt.notartermin.strftime('%d.%m.%Y %H:%M')}")
                            else:
                                st.info("Noch kein Termin vereinbart")

                                with st.form(f"ma_termin_form_{projekt.projekt_id}"):
                                    termin_datum = st.date_input("Datum", value=date.today() + timedelta(days=14))
                                    termin_zeit = st.time_input("Uhrzeit", value=datetime.now().replace(hour=10, minute=0).time())

                                    if st.form_submit_button("💾 Termin speichern", type="primary"):
                                        termin_dt = datetime.combine(termin_datum, termin_zeit)
                                        projekt.notartermin = termin_dt

                                        # Timeline aktualisieren
                                        for event_id in projekt.timeline_events:
                                            event = st.session_state.timeline_events.get(event_id)
                                            if event and event.titel == "Notartermin vereinbaren" and not event.completed:
                                                event.completed = True
                                                event.completed_at = datetime.now()
                                        update_projekt_status(projekt.projekt_id)

                                        st.success("✅ Termin gespeichert!")
                                        st.rerun()
        tab_index += 1

    # Finanzierungsnachweise (nur wenn berechtigt)
    if mitarbeiter.kann_finanzierung_sehen:
        with tabs[tab_index]:
            st.subheader("💰 Finanzierungsnachweise")
            if not mitarbeiter.projekt_ids:
                st.info("Ihnen wurden noch keine Projekte zugewiesen.")
            else:
                for projekt_id in mitarbeiter.projekt_ids:
                    projekt = st.session_state.projekte.get(projekt_id)
                    if projekt:
                        st.markdown(f"### 🏘️ {projekt.name}")

                        # Angenommene Finanzierungsangebote suchen
                        finanzierungen = [o for o in st.session_state.financing_offers.values()
                                         if o.projekt_id == projekt.projekt_id and o.status == FinanzierungsStatus.ANGENOMMEN.value]

                        if finanzierungen:
                            for offer in finanzierungen:
                                finanzierer = st.session_state.users.get(offer.finanzierer_id)
                                finanzierer_name = finanzierer.name if finanzierer else "Unbekannt"

                                with st.expander(f"💰 Angebot von {finanzierer_name}", expanded=True):
                                    col1, col2 = st.columns(2)

                                    with col1:
                                        st.write(f"**Darlehensbetrag:** {offer.darlehensbetrag:,.2f} €")
                                        st.write(f"**Zinssatz:** {offer.zinssatz}%")
                                        st.write(f"**Sollzinsbindung:** {offer.sollzinsbindung} Jahre")
                                        st.write(f"**Tilgungssatz:** {offer.tilgungssatz}%")

                                    with col2:
                                        st.write(f"**Gesamtlaufzeit:** {offer.gesamtlaufzeit} Jahre")
                                        st.write(f"**Monatliche Rate:** {offer.monatliche_rate:,.2f} €")
                                        st.write(f"**Angenommen am:** {offer.accepted_at.strftime('%d.%m.%Y') if offer.accepted_at else 'N/A'}")

                                    if offer.besondere_bedingungen:
                                        st.markdown("**Besondere Bedingungen:**")
                                        st.text(offer.besondere_bedingungen)
                        else:
                            st.info("Noch keine Finanzierung gesichert.")

                        st.markdown("---")
        tab_index += 1

# ============================================================================
# HAUPTANWENDUNG
# ============================================================================

def render_notifications():
    """Rendert Benachrichtigungen in der Sidebar"""
    if not st.session_state.current_user:
        return

    notifications = get_unread_notifications(st.session_state.current_user.user_id)

    if notifications:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 🔔 Benachrichtigungen ({len(notifications)})")

        for notif in notifications[:5]:  # Nur die 5 neuesten
            icon_map = {
                NotificationType.INFO.value: "ℹ️",
                NotificationType.SUCCESS.value: "✅",
                NotificationType.WARNING.value: "⚠️",
                NotificationType.ERROR.value: "❌"
            }
            icon = icon_map.get(notif.typ, "ℹ️")

            with st.sidebar.expander(f"{icon} {notif.titel}", expanded=False):
                st.write(notif.nachricht)
                st.caption(notif.created_at.strftime("%d.%m.%Y %H:%M"))
                if st.button("Als gelesen markieren", key=f"read_{notif.notif_id}"):
                    notif.gelesen = True
                    st.rerun()

def makler_onboarding_page(token: str):
    """Onboarding-Seite für eingeladene Makler"""
    st.title("🏢 Makler-Registrierung")

    # Finde die Empfehlung mit diesem Token
    empfehlung = None
    for emp in st.session_state.makler_empfehlungen.values():
        if emp.onboarding_token == token:
            empfehlung = emp
            break

    if not empfehlung:
        st.error("❌ Ungültiger oder abgelaufener Einladungslink.")
        st.info("Bitte wenden Sie sich an den Notar, der Sie eingeladen hat.")
        return

    if empfehlung.status == MaklerEmpfehlungStatus.FREIGEGEBEN.value:
        st.success("✅ Ihre Registrierung wurde bereits abgeschlossen und freigegeben!")
        st.info("Sie können sich jetzt mit Ihren Zugangsdaten anmelden.")
        return

    st.success(f"Willkommen, {empfehlung.makler_name or 'Makler'}!")
    st.info("""
    Sie wurden vom Notar eingeladen, sich auf unserer Plattform zu registrieren.
    Bitte füllen Sie das folgende Formular aus, um Ihre Firmendaten zu hinterlegen.
    Nach der Freigabe durch den Notar sind Sie für Verkäufer sichtbar.
    """)

    st.markdown("---")
    st.markdown("### 📝 Ihre Firmendaten")

    with st.form("makler_onboarding_form"):
        # Basis-Informationen
        st.markdown("#### Kontaktdaten")
        col1, col2 = st.columns(2)

        with col1:
            firmenname = st.text_input("Firmenname*", value=empfehlung.firmenname)
            kontaktperson = st.text_input("Kontaktperson / Ansprechpartner*", value=empfehlung.makler_name)
            email = st.text_input("E-Mail*", value=empfehlung.makler_email, disabled=True)
            telefon = st.text_input("Telefon*", value=empfehlung.telefon)

        with col2:
            website = st.text_input("Website", value=empfehlung.website, placeholder="www.beispiel.de")
            adresse = st.text_area("Geschäftsadresse*", value=empfehlung.adresse, height=100)

        # Logo-Upload
        logo_upload = st.file_uploader("Firmenlogo (optional)", type=['jpg', 'jpeg', 'png'])

        st.markdown("---")
        st.markdown("#### 📋 Kurzvita & Spezialisierung")

        kurzvita = st.text_area(
            "Kurzvita (max. 500 Zeichen)*",
            value=empfehlung.kurzvita,
            max_chars=500,
            height=150,
            help="Diese Beschreibung wird Verkäufern angezeigt. Beschreiben Sie Ihre Erfahrung und Stärken."
        )

        col1, col2 = st.columns(2)
        with col1:
            spezialisierung_optionen = [
                "Ferienimmobilien", "Luxusimmobilien", "Anlageimmobilien",
                "Neubauprojekte", "Bestandsimmobilien", "Gewerbeimmobilien",
                "Grundstücke", "Mehrfamilienhäuser"
            ]
            spezialisierung = st.multiselect(
                "Spezialisierung*",
                spezialisierung_optionen,
                default=empfehlung.spezialisierung if empfehlung.spezialisierung else []
            )

        with col2:
            regionen_optionen = [
                "Mallorca", "Ibiza", "Menorca", "Costa Brava", "Costa Blanca",
                "Algarve", "Toskana", "Côte d'Azur", "Österreich Alpen",
                "Schweiz", "Deutschland Nordsee", "Deutschland Ostsee"
            ]
            regionen = st.multiselect(
                "Tätigkeitsregionen*",
                regionen_optionen,
                default=empfehlung.regionen if empfehlung.regionen else []
            )

        st.markdown("---")
        st.markdown("#### 💰 Konditionen")

        col1, col2 = st.columns(2)
        with col1:
            provision_verkaeufer = st.number_input(
                "Provision Verkäufer (%)*",
                min_value=0.0, max_value=10.0,
                value=empfehlung.provision_verkaeufer_prozent if empfehlung.provision_verkaeufer_prozent > 0 else 3.57,
                step=0.01,
                help="Ihre Provision vom Verkäufer inkl. MwSt."
            )
        with col2:
            provision_kaeufer = st.number_input(
                "Provision Käufer (%)*",
                min_value=0.0, max_value=10.0,
                value=empfehlung.provision_kaeufer_prozent if empfehlung.provision_kaeufer_prozent > 0 else 3.57,
                step=0.01,
                help="Ihre Provision vom Käufer inkl. MwSt."
            )

        st.markdown("---")
        st.markdown("#### 📄 Rechtliche Dokumente")
        st.info("Diese Dokumente werden Verkäufern zur Verfügung gestellt.")

        agb_text = st.text_area(
            "Allgemeine Geschäftsbedingungen (AGB)*",
            value=empfehlung.agb_text or """§1 Geltungsbereich
Diese AGB gelten für alle Verträge zwischen dem Auftraggeber und dem Makler.

§2 Vertragsgegenstand
Der Makler wird beauftragt, ein geeignetes Kaufobjekt nachzuweisen oder zu vermitteln.

§3 Provision
Die Provision wird gemäß den vereinbarten Konditionen fällig.

§4 Haftung
Die Haftung des Maklers beschränkt sich auf Vorsatz und grobe Fahrlässigkeit.

§5 Schlussbestimmungen
Es gilt deutsches Recht. Gerichtsstand ist der Sitz des Maklers.""",
            height=250
        )

        widerrufsbelehrung_text = st.text_area(
            "Widerrufsbelehrung*",
            value=empfehlung.widerrufsbelehrung_text or """Widerrufsrecht

Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen.

Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag des Vertragsabschlusses.

Um Ihr Widerrufsrecht auszuüben, müssen Sie uns mittels einer eindeutigen Erklärung (z.B. ein mit der Post versandter Brief oder E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen, informieren.

Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung über die Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist absenden.

Folgen des Widerrufs:
Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir von Ihnen erhalten haben, unverzüglich und spätestens binnen vierzehn Tagen ab dem Tag zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf dieses Vertrags bei uns eingegangen ist.""",
            height=250
        )

        datenschutz_text = st.text_area(
            "Datenschutzerklärung*",
            value=empfehlung.datenschutz_text or """Datenschutzerklärung

1. Verantwortliche Stelle
Verantwortlich für die Datenverarbeitung ist der jeweilige Makler.

2. Erhebung und Speicherung personenbezogener Daten
Wir erheben personenbezogene Daten, wenn Sie uns diese im Rahmen Ihrer Anfrage mitteilen.

3. Nutzung und Weitergabe personenbezogener Daten
Die erhobenen Daten werden ausschließlich zur Vertragserfüllung verwendet.

4. Ihre Rechte
Sie haben das Recht auf Auskunft, Berichtigung, Löschung und Einschränkung der Verarbeitung Ihrer Daten.""",
            height=200
        )

        st.markdown("---")

        # Zustimmung
        zustimmung = st.checkbox(
            "Ich bestätige, dass alle Angaben korrekt sind und stimme der Veröffentlichung meiner Daten auf der Plattform zu.*"
        )

        submit = st.form_submit_button("💾 Registrierung abschließen", type="primary", use_container_width=True)

        if submit:
            # Validierung
            if not all([firmenname, kontaktperson, telefon, adresse, kurzvita, spezialisierung, regionen, agb_text, widerrufsbelehrung_text]):
                st.error("Bitte füllen Sie alle Pflichtfelder (*) aus.")
            elif not zustimmung:
                st.error("Bitte bestätigen Sie die Richtigkeit Ihrer Angaben.")
            else:
                # Daten speichern
                empfehlung.firmenname = firmenname
                empfehlung.makler_name = kontaktperson
                empfehlung.telefon = telefon
                empfehlung.website = website
                empfehlung.adresse = adresse
                empfehlung.kurzvita = kurzvita
                empfehlung.spezialisierung = spezialisierung
                empfehlung.regionen = regionen
                empfehlung.provision_verkaeufer_prozent = provision_verkaeufer
                empfehlung.provision_kaeufer_prozent = provision_kaeufer
                empfehlung.agb_text = agb_text
                empfehlung.widerrufsbelehrung_text = widerrufsbelehrung_text
                empfehlung.datenschutz_text = datenschutz_text
                empfehlung.status = MaklerEmpfehlungStatus.DATEN_EINGEGEBEN.value

                if logo_upload:
                    empfehlung.logo = logo_upload.read()

                st.session_state.makler_empfehlungen[empfehlung.empfehlung_id] = empfehlung

                # Benachrichtigung an Notar
                create_notification(
                    empfehlung.notar_id,
                    "Makler-Registrierung abgeschlossen",
                    f"Makler {firmenname} hat die Registrierung abgeschlossen und wartet auf Ihre Freigabe.",
                    NotificationType.INFO.value
                )

                st.success("""
                ✅ Vielen Dank für Ihre Registrierung!

                Ihre Daten wurden erfolgreich übermittelt.
                Der Notar wird Ihre Angaben prüfen und Sie nach der Freigabe benachrichtigen.

                Sie erhalten dann Ihre Zugangsdaten per E-Mail.
                """)
                st.balloons()


def main():
    """Hauptanwendung"""
    st.set_page_config(
        page_title="Immobilien-Transaktionsplattform",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session_state()

    # Prüfe auf Makler-Onboarding-Token in URL
    query_params = st.query_params
    if "token" in query_params:
        makler_onboarding_page(query_params["token"])
        return

    if st.session_state.current_user is None:
        login_page()
        return

    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 Angemeldet als:")
        st.write(f"**{st.session_state.current_user.name}**")

        # Unterschiedliche Anzeige für Mitarbeiter vs normale Benutzer
        if st.session_state.get("is_notar_mitarbeiter", False):
            st.caption(f"Rolle: Notar-Mitarbeiter ({st.session_state.current_user.rolle})")
            st.caption(f"E-Mail: {st.session_state.current_user.email}")
        else:
            st.caption(f"Rolle: {st.session_state.current_user.role}")
            st.caption(f"E-Mail: {st.session_state.current_user.email}")

        if st.button("🚪 Abmelden", use_container_width=True):
            logout()

        # Benachrichtigungen nur für normale Benutzer (Mitarbeiter haben keine user_id)
        if not st.session_state.get("is_notar_mitarbeiter", False):
            render_notifications()

        st.markdown("---")
        st.markdown("### ℹ️ System-Info")
        st.caption(f"Benutzer: {len(st.session_state.users)}")
        st.caption(f"Projekte: {len(st.session_state.projekte)}")
        st.caption(f"Angebote: {len(st.session_state.financing_offers)}")

    # Hauptbereich
    # Prüfe ob Mitarbeiter oder normaler Benutzer
    if st.session_state.get("is_notar_mitarbeiter", False):
        notarmitarbeiter_dashboard()
    else:
        role = st.session_state.current_user.role

        if role == UserRole.MAKLER.value:
            makler_dashboard()
        elif role == UserRole.KAEUFER.value:
            kaeufer_dashboard()
        elif role == UserRole.VERKAEUFER.value:
            verkaeufer_dashboard()
        elif role == UserRole.FINANZIERER.value:
            finanzierer_dashboard()
        elif role == UserRole.NOTAR.value:
            notar_dashboard()
        else:
            st.error("Unbekannte Rolle")

if __name__ == "__main__":
    main()
