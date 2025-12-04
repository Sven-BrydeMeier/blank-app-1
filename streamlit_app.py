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

class ImmobilienTyp(Enum):
    """Immobilien-Typen für Vermittlung"""
    WOHNUNG = "Wohnung"
    HAUS = "Haus"
    MEHRFAMILIENHAUS = "Mehrfamilienhaus"
    GRUNDSTUECK = "Grundstück"
    GEWERBE = "Gewerbe"
    BUERO = "Büro"
    PRAXIS = "Praxis"
    LADEN = "Laden"
    HALLE = "Halle/Lager"
    SONSTIGES = "Sonstiges"

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
    # Stammdaten (aus Personalausweis)
    vorname: str = ""
    nachname: str = ""
    geburtsdatum: str = ""
    geburtsort: str = ""
    staatsangehoerigkeit: str = ""
    anschrift: str = ""
    ausweisnummer: str = ""
    gueltig_bis: str = ""
    ausstellende_behoerde: str = ""
    stammdaten_complete: bool = False

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

    # Notar-Netzwerk
    empfohlener_notar_id: str = ""  # Makler empfiehlt Notar
    vermittelt_durch_notar: bool = False  # Notar agiert als Vermittler

    # Fallzuweisung
    zugewiesener_mitarbeiter_id: str = ""  # Zugewiesener Notar-Mitarbeiter

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
    logo_url: str = ""  # URL zum Logo (Alternative zu bytes)
    logo_aktiviert: bool = False  # Automatische Logo-Übernahme aktiviert
    logo_bestaetigt: bool = False  # Logo wurde vom Makler bestätigt
    team_mitglieder: List[MaklerAgent] = field(default_factory=list)
    backoffice_kontakt: str = ""
    backoffice_email: str = ""
    backoffice_telefon: str = ""
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class NotarProfile:
    """Notar-Profil"""
    profile_id: str
    notar_id: str
    kanzleiname: str
    notar_vorname: str
    notar_nachname: str
    notar_titel: str = ""  # z.B. "Dr.", "Dr. jur."
    adresse: str = ""
    plz: str = ""
    ort: str = ""
    telefon: str = ""
    fax: str = ""
    email: str = ""
    website: str = ""

    # Logo
    logo: Optional[bytes] = None
    logo_url: str = ""  # URL zum Logo (Alternative zu bytes)
    logo_aktiviert: bool = False  # Automatische Logo-Übernahme aktiviert
    logo_bestaetigt: bool = False  # Logo wurde vom Notar bestätigt

    # Zusätzliche Informationen
    notarkammer: str = ""  # z.B. "Notarkammer München"
    notarversicherung: str = ""  # z.B. "R+V Versicherung AG"
    handelsregister: str = ""
    steuernummer: str = ""
    ust_id: str = ""

    # Öffnungszeiten
    oeffnungszeiten: str = ""

    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ExposeData:
    """Exposé-Daten für PDF und Web-Generierung"""
    expose_id: str
    projekt_id: str

    # Basis-Informationen
    objekttitel: str = ""
    objektbeschreibung: str = ""
    lage_beschreibung: str = ""

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

    # Preise
    kaufpreis: float = 0.0
    provision: str = ""
    hausgeld: float = 0.0
    grundsteuer: float = 0.0

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

    # Zugewiesene Projekte (allgemeiner Zugriff)
    projekt_ids: List[str] = field(default_factory=list)

    # Zugewiesene Fälle (primäre Verantwortung)
    zugewiesene_faelle: List[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)
    aktiv: bool = True

@dataclass
class MaklerNetzwerkMitglied:
    """Makler im Netzwerk eines Notars"""
    netzwerk_id: str
    notar_id: str
    makler_id: str

    # Status
    eingeladen_am: datetime
    beigetreten_am: Optional[datetime] = None
    status: str = "Eingeladen"  # Eingeladen, Aktiv, Inaktiv

    # Statistiken
    letzte_empfehlung_am: Optional[datetime] = None
    anzahl_aktive_projekte: int = 0
    anzahl_empfehlungen_gesamt: int = 0

    notizen: str = ""

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

@dataclass
class PreisVerhandlung:
    """Preisverhandlung zwischen Käufer und Verkäufer"""
    verhandlung_id: str
    projekt_id: str
    ausgangspreis: float
    aktueller_preis: float
    status: str = "Aktiv"  # Aktiv, Angenommen, Abgelehnt
    nachrichten: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class MarktDaten:
    """Vergleichsdaten aus Immobilienportalen"""
    markt_id: str
    projekt_id: str
    portal: str  # ImmoScout24, Immowelt, etc.
    vergleichsobjekte: List[Dict[str, Any]] = field(default_factory=list)
    durchschnittspreis: float = 0.0
    preis_pro_qm: float = 0.0
    empfohlener_preis: float = 0.0
    abgerufen_am: datetime = field(default_factory=datetime.now)

@dataclass
class PortalZugangsdaten:
    """Zugangsdaten für Immobilienportale"""
    zugang_id: str
    makler_id: str
    portal_name: str  # ImmoScout24, Immowelt, etc.
    benutzername: str
    api_key: str = ""  # Verschlüsselt in Produktion
    aktiv: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class PortalExport:
    """Export-Status zu Immobilienportalen"""
    export_id: str
    expose_id: str
    portal_name: str
    status: str = "Ausstehend"  # Ausstehend, Exportiert, Fehler
    portal_objekt_id: str = ""
    exportiert_am: Optional[datetime] = None
    fehler_nachricht: str = ""

@dataclass
class EmailKonfiguration:
    """E-Mail-Server-Konfiguration"""
    config_id: str
    user_id: str
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""  # Verschlüsselt in Produktion
    absender_name: str = ""
    aktiv: bool = False

@dataclass
class NotarAuftrag:
    """Notarauftrag mit rechtlicher Prüfung und Workflow"""
    auftrag_id: str
    projekt_id: str
    notar_id: str
    status: str = "Eingegangen"  # Eingegangen, In Prüfung, Freigegeben, Abgeschlossen
    auftraggeber_typ: str = ""  # Käufer, Verkäufer, Makler
    auftraggeber_id: str = ""
    vertragsart: str = ""  # Kaufvertrag, Grundschuld, Vollmacht, etc.
    # Rechtliche Prüfung
    rechtlich_geprueft: bool = False
    geprueft_von: str = ""  # Mitarbeiter-ID oder Notar-ID
    geprueft_am: Optional[datetime] = None
    pruefungsergebnis: str = ""
    # Workflow-Status
    unterlagen_vollstaendig: bool = False
    termin_datum: Optional[datetime] = None
    termin_ort: str = ""
    beteiligte_personen: List[str] = field(default_factory=list)
    # Dokumente
    dokumente: List[str] = field(default_factory=list)  # Document-IDs
    entwurf_erstellt: bool = False
    entwurf_freigegeben: bool = False
    # Kosten
    geschaetzte_kosten: float = 0.0
    tatsaechliche_kosten: float = 0.0
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    abgeschlossen_am: Optional[datetime] = None
    # Notizen
    notizen: str = ""

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
        st.session_state.notar_profiles = {}
        st.session_state.expose_data = {}
        st.session_state.document_requests = {}
        st.session_state.notar_checklists = {}
        st.session_state.bank_folders = {}
        st.session_state.notar_mitarbeiter = {}
        st.session_state.verkaeufer_dokumente = {}
        st.session_state.makler_netzwerk = {}  # Makler-Netzwerk für Notare

        # Neue Features
        st.session_state.preis_verhandlungen = {}
        st.session_state.markt_daten = {}
        st.session_state.portal_zugangsdaten = {}
        st.session_state.portal_exports = {}
        st.session_state.email_konfigurationen = {}
        st.session_state.notar_auftraege = {}

        # Demo-Daten
        create_demo_users()
        create_demo_projekt()
        create_demo_timeline()

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

def extract_personalausweis_data(image_data: bytes, filename: str) -> Dict[str, str]:
    """
    Extrahiert Stammdaten aus Personalausweis
    In Produktion: OCR mit pytesseract, Google Cloud Vision oder AWS Textract
    """
    # Simulation basierend auf Dateiname/Kontext
    filename_lower = filename.lower()

    extracted_data = {
        "vorname": "",
        "nachname": "",
        "geburtsdatum": "",
        "geburtsort": "",
        "staatsangehoerigkeit": "DEUTSCH",
        "anschrift": "",
        "ausweisnummer": "",
        "gueltig_bis": "",
        "ausstellende_behoerde": ""
    }

    # Simulierte Erkennung (in Produktion: echte OCR)
    if "ausweis" in filename_lower or "personalausweis" in filename_lower or "id" in filename_lower:
        # Simuliere erkannte Daten
        extracted_data = {
            "vorname": "Max",
            "nachname": "Mustermann",
            "geburtsdatum": "01.01.1985",
            "geburtsort": "München",
            "staatsangehoerigkeit": "DEUTSCH",
            "anschrift": "Musterstraße 123, 80331 München",
            "ausweisnummer": "L01X00T471",
            "gueltig_bis": "31.12.2029",
            "ausstellende_behoerde": "Stadt München"
        }

    return extracted_data

def send_email(empfaenger_email: str, betreff: str, nachricht: str, makler_id: str = None) -> bool:
    """
    Sendet eine E-Mail über SMTP
    In Produktion: Echte SMTP-Verbindung mit smtplib
    """
    # E-Mail-Konfiguration laden
    email_config = None
    if makler_id:
        for config in st.session_state.email_konfigurationen.values():
            if config.user_id == makler_id and config.aktiv:
                email_config = config
                break

    if not email_config:
        # Simulation ohne echte Konfiguration
        return True  # Simulierter Erfolg

    # In Produktion: Echter E-Mail-Versand
    # import smtplib
    # from email.mime.text import MIMEText
    # from email.mime.multipart import MIMEMultipart
    #
    # msg = MIMEMultipart()
    # msg['From'] = f"{email_config.absender_name} <{email_config.smtp_user}>"
    # msg['To'] = empfaenger_email
    # msg['Subject'] = betreff
    # msg.attach(MIMEText(nachricht, 'html'))
    #
    # try:
    #     server = smtplib.SMTP(email_config.smtp_server, email_config.smtp_port)
    #     server.starttls()
    #     server.login(email_config.smtp_user, email_config.smtp_password)
    #     server.send_message(msg)
    #     server.quit()
    #     return True
    # except Exception as e:
    #     return False

    return True  # Simulation

def fetch_marktdaten(projekt: Any) -> Dict[str, Any]:
    """
    Holt Vergleichsdaten aus Immobilienportalen
    In Produktion: Echte API-Calls zu ImmoScout24, Immowelt, etc.
    """
    # Simulierte Vergleichsobjekte basierend auf Projektdaten
    vergleichsobjekte = []

    # Simuliere 5 Vergleichsobjekte
    basis_preis = projekt.kaufpreis if projekt.kaufpreis > 0 else 350000
    basis_qm_preis = basis_preis / projekt.wohnflaeche if projekt.wohnflaeche > 0 else 4500

    for i in range(5):
        varianz = (i - 2) * 0.1  # -20% bis +20%
        vgl_preis = basis_preis * (1 + varianz)
        vgl_qm_preis = basis_qm_preis * (1 + varianz * 0.8)

        vergleichsobjekt = {
            "titel": f"Vergleichsobjekt {i+1}",
            "adresse": f"{projekt.ort}, ähnliche Lage",
            "preis": vgl_preis,
            "wohnflaeche": projekt.wohnflaeche * (1 + varianz * 0.3),
            "preis_pro_qm": vgl_qm_preis,
            "baujahr": projekt.baujahr + (i - 2) * 5,
            "zimmer": projekt.zimmer,
            "quelle": ["ImmoScout24", "Immowelt", "Immonet", "eBay Kleinanzeigen", "ImmobilienScout24"][i]
        }
        vergleichsobjekte.append(vergleichsobjekt)

    # Durchschnittspreis berechnen
    durchschnittspreis = sum([obj["preis"] for obj in vergleichsobjekte]) / len(vergleichsobjekte)
    durchschnitt_qm = sum([obj["preis_pro_qm"] for obj in vergleichsobjekte]) / len(vergleichsobjekte)

    # Empfohlener Preis (leicht unter Durchschnitt für schnelleren Verkauf)
    empfohlener_preis = durchschnittspreis * 0.97

    return {
        "vergleichsobjekte": vergleichsobjekte,
        "durchschnittspreis": durchschnittspreis,
        "preis_pro_qm": durchschnitt_qm,
        "empfohlener_preis": empfohlener_preis
    }

def export_to_portal(expose_id: str, portal_name: str, zugangsdaten: PortalZugangsdaten) -> Dict[str, Any]:
    """
    Exportiert Exposé zu Immobilienportal
    In Produktion: Echte API-Calls mit OAuth/API-Keys
    """
    # Simulierter Export
    # In Produktion würde hier die Portal-API aufgerufen

    # Simuliere erfolgreichen Export
    result = {
        "success": True,
        "portal_objekt_id": f"{portal_name}_{expose_id}_{hash(expose_id) % 10000}",
        "message": f"Erfolgreich zu {portal_name} exportiert",
        "url": f"https://{portal_name.lower().replace(' ', '')}.de/expose/{expose_id}"
    }

    return result

def generate_portal_beschreibung(expose: ExposeData, portal_name: str) -> str:
    """
    Generiert portal-optimierte Beschreibung
    In Produktion: KI-gestützt mit GPT-4 oder Claude
    """
    # Simulierte KI-Beschreibung
    basis_text = expose.objektbeschreibung if expose.objektbeschreibung else "Attraktive Immobilie"

    # Portal-spezifische Templates
    portal_templates = {
        "ImmoScout24": f"🏡 {expose.objekttitel}\n\n{basis_text}\n\n✓ {expose.anzahl_zimmer} Zimmer\n✓ {expose.wohnflaeche} m² Wohnfläche\n✓ Baujahr {expose.baujahr}\n\nJetzt besichtigen!",
        "Immowelt": f"{expose.objekttitel}\n\n{basis_text}\n\nHighlights:\n• Wohnfläche: {expose.wohnflaeche} m²\n• Zimmer: {expose.anzahl_zimmer}\n• Zustand: {expose.zustand}\n\nKontaktieren Sie uns!",
        "Immonet": f"**{expose.objekttitel}**\n\n{basis_text}\n\nEckdaten: {expose.anzahl_zimmer} Zi., {expose.wohnflaeche} m², Bj. {expose.baujahr}",
    }

    return portal_templates.get(portal_name, basis_text)

def analyze_website(url: str) -> Dict[str, Any]:
    """
    Analysiert Website und extrahiert Logo und Betreiber-Informationen
    Verwendet WebFetch für echte Website-Analyse
    """
    if not url:
        return {"error": "Keine URL angegeben"}

    # URL normalisieren
    if not url.startswith('http'):
        url = f"https://{url}"

    try:
        from urllib.parse import urlparse
        import json
        import re

        # Basis-URL für relative Pfade
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Strukturierter Prompt für Website-Analyse
        prompt = """Analysiere diese Website und extrahiere folgende Informationen:

**1. LOGO & FAVICON:**
- Suche nach Favicon-Links: <link rel="icon">, <link rel="shortcut icon">, <link rel="apple-touch-icon">
- Suche nach Logo-Bildern: <img> Tags mit class/id/alt enthaltend: "logo", "brand", "header-logo"
- Open Graph Images: <meta property="og:image">
- SVG-Logos im Header/Navigation

**2. IMPRESSUM-DATEN:**
Suche im gesamten Text nach:
- Firmenname/Kanzleiname (oft am Anfang des Impressums)
- Vollständige Adresse (Straße, Hausnummer, PLZ, Ort)
- Telefonnummer (Format: +49... oder 0...)
- E-Mail-Adresse
- Rechtsform (GmbH, PartG mbB, Einzelunternehmen, etc.)

**3. KATEGORISIERUNG:**
Bestimme basierend auf Inhalt und Keywords:
- MAKLER: Immobilienmakler, Immobilienvermittlung
- NOTAR: Notariat, notarielle Dienstleistungen
- RECHTSANWALT: Rechtsanwaltskanzlei, Anwaltsbüro
- RECHTSANWALT_NOTAR: Kombination aus beidem
- SONSTIG: Andere

**AUSGABEFORMAT (nur valides JSON):**
{
  "logo_urls": ["url1", "url2", ...],
  "favicon_url": "...",
  "firmenname": "...",
  "strasse": "...",
  "plz": "...",
  "ort": "...",
  "telefon": "...",
  "email": "...",
  "rechtsform": "...",
  "kategorie": "..."
}

Gib alle gefundenen Logo-URLs als Array zurück. Bei relativen URLs gib die vollständige URL an."""

        # WebFetch verwenden
        try:
            # Importiere WebFetch tool - Hinweis: Dies ist eine Streamlit-App, daher müssen wir requests verwenden
            import requests
            from bs4 import BeautifulSoup

            # Website abrufen
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # HTML parsen
            soup = BeautifulSoup(response.text, 'html.parser')

            # Impressum und Datenschutz-Links finden
            impressum_links = []
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                text = link.get_text().lower()
                if any(keyword in href or keyword in text for keyword in ['impressum', 'datenschutz', 'imprint', 'privacy']):
                    full_link = link['href']
                    if full_link.startswith('http'):
                        impressum_links.append(full_link)
                    elif full_link.startswith('//'):
                        impressum_links.append('https:' + full_link)
                    elif full_link.startswith('/'):
                        impressum_links.append(base_url + full_link)
                    else:
                        impressum_links.append(base_url + '/' + full_link)

            # Logo-URLs sammeln
            logo_urls = []

            # 1. Favicon
            favicon_url = None
            favicon_tags = soup.find_all('link', rel=lambda x: x and ('icon' in x.lower() or 'shortcut' in x.lower()))
            for tag in favicon_tags:
                href = tag.get('href', '')
                if href:
                    if href.startswith('http'):
                        favicon_url = href
                    elif href.startswith('//'):
                        favicon_url = 'https:' + href
                    elif href.startswith('/'):
                        favicon_url = base_url + href
                    else:
                        favicon_url = base_url + '/' + href
                    logo_urls.append(favicon_url)
                    break

            # Fallback Favicon
            if not favicon_url:
                favicon_url = base_url + '/favicon.ico'
                logo_urls.append(favicon_url)

            # 2. Apple Touch Icon
            apple_icon = soup.find('link', rel='apple-touch-icon')
            if apple_icon and apple_icon.get('href'):
                href = apple_icon['href']
                if href.startswith('http'):
                    logo_urls.append(href)
                elif href.startswith('//'):
                    logo_urls.append('https:' + href)
                elif href.startswith('/'):
                    logo_urls.append(base_url + href)
                else:
                    logo_urls.append(base_url + '/' + href)

            # 3. OG Image
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                content = og_image['content']
                if content.startswith('http'):
                    logo_urls.append(content)
                elif content.startswith('//'):
                    logo_urls.append('https:' + content)
                elif content.startswith('/'):
                    logo_urls.append(base_url + content)

            # 4. Logo-Bilder im HTML
            logo_imgs = soup.find_all('img', class_=re.compile(r'logo|brand', re.I))
            logo_imgs += soup.find_all('img', id=re.compile(r'logo|brand', re.I))
            logo_imgs += soup.find_all('img', alt=re.compile(r'logo|brand', re.I))

            for img in logo_imgs[:5]:  # Max 5 Logo-Bilder
                src = img.get('src', '')
                if src:
                    if src.startswith('http'):
                        logo_urls.append(src)
                    elif src.startswith('//'):
                        logo_urls.append('https:' + src)
                    elif src.startswith('/'):
                        logo_urls.append(base_url + src)
                    else:
                        logo_urls.append(base_url + '/' + src)

            # 5. Häufige Logo-Pfade hinzufügen
            common_paths = [
                '/logo.svg', '/logo.png', '/images/logo.svg', '/images/logo.png',
                '/assets/logo.svg', '/assets/logo.png', '/img/logo.svg', '/img/logo.png'
            ]
            for path in common_paths:
                full_url = base_url + path
                if full_url not in logo_urls:
                    logo_urls.append(full_url)

            # Impressum-Daten extrahieren
            # Haupt-Seite + Impressum-Seiten kombinieren
            text = soup.get_text(separator=' ')

            # Impressum-Seiten zusätzlich abrufen und kombinieren
            for imp_link in impressum_links[:3]:  # Max 3 Impressum-Seiten
                try:
                    imp_response = requests.get(imp_link, headers=headers, timeout=5)
                    imp_soup = BeautifulSoup(imp_response.text, 'html.parser')
                    text += ' ' + imp_soup.get_text(separator=' ')
                except:
                    pass  # Fehler beim Abrufen ignorieren

            # E-Mail extrahieren
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            email = emails[0] if emails else ""

            # Telefon extrahieren
            phone_pattern = r'(?:\+49|0)\s*\d{2,5}[\s\-/]*\d{3,}[\s\-/]*\d{3,}'
            phones = re.findall(phone_pattern, text)
            telefon = phones[0].strip() if phones else ""

            # PLZ und Ort extrahieren (deutsches Format)
            plz_ort_pattern = r'\b(\d{5})\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)\b'
            plz_ort_matches = re.findall(plz_ort_pattern, text)
            plz = plz_ort_matches[0][0] if plz_ort_matches else ""
            ort = plz_ort_matches[0][1] if plz_ort_matches else ""

            # Straße extrahieren (vor PLZ)
            if plz:
                street_pattern = rf'([A-ZÄÖÜ][a-zäöüß]+(?:straße|str\.|weg|platz|allee)\s+\d+[a-z]?)\s+{plz}'
                street_matches = re.findall(street_pattern, text, re.I)
                strasse = street_matches[0] if street_matches else ""
            else:
                strasse = ""

            # Firmenname aus Domain ableiten
            domain = parsed.netloc.replace('www.', '')
            firmenname = domain.split('.')[0].capitalize()

            # Kategorie bestimmen
            text_lower = text.lower()
            kategorie = "SONSTIG"
            if any(kw in text_lower for kw in ["immobilien", "makler", "immobilienvermittlung"]):
                kategorie = "MAKLER"
            elif "notar" in text_lower and "rechtsanwalt" in text_lower:
                kategorie = "RECHTSANWALT_NOTAR"
            elif "notar" in text_lower:
                kategorie = "NOTAR"
            elif any(kw in text_lower for kw in ["rechtsanwalt", "anwaltskanzlei", "anwaltsbüro"]):
                kategorie = "RECHTSANWALT"

            # Notar-spezifische Daten extrahieren
            notarkammer = ""
            notarversicherung = ""
            notar_titel = ""
            notar_vorname = ""
            notar_nachname = ""

            if kategorie in ["NOTAR", "RECHTSANWALT_NOTAR"]:
                # Notarkammer extrahieren
                kammer_pattern = r'(Notarkammer\s+[A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)?)'
                kammer_matches = re.findall(kammer_pattern, text)
                if kammer_matches:
                    notarkammer = kammer_matches[0].strip()

                # Notarversicherung extrahieren
                versicherung_patterns = [
                    r'Berufshaftpflichtversicherung[:\s]+([A-ZÄÖÜ][^\n,;\.]{5,80}(?:Versicherung|AG|SE))',
                    r'Versicherung[:\s]+([A-ZÄÖÜ][^\n,;\.]{5,80}(?:Versicherung|AG|SE))',
                    r'Haftpflichtversicherung[:\s]+([A-ZÄÖÜ][^\n,;\.]{5,80}(?:Versicherung|AG|SE))'
                ]
                for pattern in versicherung_patterns:
                    vers_matches = re.findall(pattern, text)
                    if vers_matches:
                        notarversicherung = vers_matches[0].strip()
                        break

                # Notar-Name extrahieren (nach "Notar" oder "Notarin")
                name_pattern = r'Notar(?:in)?\s+(Dr\.\s+)?([A-ZÄÖÜ][a-zäöüß]+)\s+([A-ZÄÖÜ][a-zäöüß\-]+)'
                name_matches = re.findall(name_pattern, text)
                if name_matches:
                    titel_match, vorname_match, nachname_match = name_matches[0]
                    notar_titel = titel_match.strip() if titel_match else ""
                    notar_vorname = vorname_match.strip()
                    notar_nachname = nachname_match.strip()
                else:
                    # Alternative: Nach Kanzleiname mit Namen
                    alt_pattern = r'(Dr\.\s+)?([A-ZÄÖÜ][a-zäöüß]+)\s+([A-ZÄÖÜ][a-zäöüß\-]+)\s*,?\s*Notar'
                    alt_matches = re.findall(alt_pattern, text)
                    if alt_matches:
                        titel_match, vorname_match, nachname_match = alt_matches[0]
                        notar_titel = titel_match.strip() if titel_match else ""
                        notar_vorname = vorname_match.strip()
                        notar_nachname = nachname_match.strip()

            # Ergebnis zusammenstellen
            result = {
                "url": url,
                "logo": {
                    "url": logo_urls[0] if logo_urls else favicon_url,
                    "favicon_url": favicon_url,
                    "type": "png",
                    "source": "website",
                    "candidates": logo_urls[:10]  # Top 10 Kandidaten
                },
                "betreiber": {
                    "name": firmenname,
                    "kategorie": kategorie,
                    "rechtsform": "",
                    "inhaber": [],
                    "adresse": {
                        "strasse": strasse,
                        "plz": plz,
                        "ort": ort
                    },
                    "kontakt": {
                        "telefon": telefon,
                        "email": email
                    }
                },
                "notar_daten": {
                    "notarkammer": notarkammer,
                    "notarversicherung": notarversicherung,
                    "titel": notar_titel,
                    "vorname": notar_vorname,
                    "nachname": notar_nachname
                } if kategorie in ["NOTAR", "RECHTSANWALT_NOTAR"] else None,
                "confidence": 0.8 if (email and telefon) else 0.5,
                "message": f"Website erfolgreich analysiert. {len(logo_urls)} Logo-Kandidaten gefunden."
            }

            return result

        except Exception as fetch_error:
            # Fallback zur Simulation bei Fehlern
            st.warning(f"⚠️ Website konnte nicht abgerufen werden: {str(fetch_error)}. Verwende Fallback-Analyse.")
            return simulate_website_analysis(url)

    except Exception as e:
        return {
            "error": str(e),
            "logo": None,
            "betreiber": None
        }

def simulate_website_analysis(url: str) -> Dict[str, Any]:
    """
    Simuliert Website-Analyse für Demo-Zwecke
    In Produktion würde dies durch echte WebFetch-Calls ersetzt
    """
    # Basis-URL extrahieren
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    base_url = f"{parsed.scheme}://{domain}" if parsed.scheme else f"https://{domain}"

    # Intelligente Logo-URL-Generierung
    logo_candidates = [
        f"{base_url}/logo.svg",
        f"{base_url}/logo.png",
        f"{base_url}/images/logo.svg",
        f"{base_url}/images/logo.png",
        f"{base_url}/assets/logo.svg",
        f"{base_url}/assets/logo.png",
        f"{base_url}/favicon.ico",
    ]

    # Kategorisierung basierend auf Domain-Keywords
    kategorie = "SONSTIG"
    if any(keyword in domain.lower() for keyword in ["immobilien", "makler", "immo", "estate"]):
        kategorie = "MAKLER"
    elif any(keyword in domain.lower() for keyword in ["notar", "notariat"]):
        if any(keyword in domain.lower() for keyword in ["rechtsanwalt", "anwalt", "ra"]):
            kategorie = "RECHTSANWALT_NOTAR"
        else:
            kategorie = "NOTAR"
    elif any(keyword in domain.lower() for keyword in ["rechtsanwalt", "anwalt", "kanzlei", "law"]):
        kategorie = "RECHTSANWALT"

    # Firmenname aus Domain ableiten
    domain_parts = domain.replace("www.", "").replace(".de", "").replace(".com", "").split(".")
    firmenname = domain_parts[0].capitalize() if domain_parts else "Unbekannt"

    result = {
        "url": url,
        "logo": {
            "url": logo_candidates[0],
            "favicon_url": f"{base_url}/favicon.ico",
            "type": "svg",
            "source": "header",
            "candidates": logo_candidates[:5]  # Top 5 Kandidaten
        },
        "betreiber": {
            "name": f"{firmenname} {'Immobilien' if kategorie == 'MAKLER' else 'Kanzlei' if kategorie in ['RECHTSANWALT', 'NOTAR', 'RECHTSANWALT_NOTAR'] else 'GmbH'}",
            "kategorie": kategorie,
            "rechtsform": "GmbH" if "gmbh" in domain.lower() else "",
            "inhaber": [],
            "adresse": {
                "strasse": "",
                "plz": "",
                "ort": ""
            },
            "kontakt": {
                "telefon": "",
                "email": f"info@{domain}"
            }
        },
        "confidence": 0.7,
        "message": "Analyse abgeschlossen. Bitte überprüfen Sie die vorgeschlagenen Logo-URLs."
    }

    return result

# ============================================================================
# SESSION STATE INITIALISIERUNG
# ============================================================================

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

def render_expose_editor(projekt: Projekt) -> bool:
    """Rendert den Exposé-Editor und gibt True zurück wenn gespeichert wurde"""

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
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kaufpreis = st.number_input("Kaufpreis (€)*", value=float(expose.kaufpreis), min_value=0.0, step=1000.0, key=f"expose_kp_{expose.expose_id}")
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

    # Besonderheiten
    st.markdown("#### Besonderheiten")
    besonderheiten = st.text_area("Besonderheiten", value=expose.besonderheiten, height=100, placeholder="z.B. Balkon, Aufzug, Tiefgarage, etc.", key=f"expose_bes_{expose.expose_id}")

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

            expose.updated_at = datetime.now()

            # Speichern
            st.session_state.expose_data[expose.expose_id] = expose
            projekt.property_type = property_type
            st.session_state.projekte[projekt.projekt_id] = projekt

            st.success("✅ Exposé erfolgreich gespeichert!")
            return True

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

    return False

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

    # Makler-Profil für Logo laden
    makler_id = st.session_state.current_user.user_id
    profile = None
    for p in st.session_state.makler_profiles.values():
        if p.makler_id == makler_id:
            profile = p
            break

    # Titelzeile mit Logo
    if profile and profile.logo_bestaetigt and (profile.logo or profile.logo_url):
        col1, col2 = st.columns([1, 4])
        with col1:
            if profile.logo_url:
                st.image(profile.logo_url, width=120)
            elif profile.logo:
                st.image(profile.logo, width=120)
        with col2:
            st.title("📊 Makler-Dashboard")
            if profile.firmenname:
                st.markdown(f"**{profile.firmenname}**")
    else:
        st.title("📊 Makler-Dashboard")

    tabs = st.tabs([
        "📋 Timeline",
        "📁 Projekte",
        "👤 Profil",
        "💼 Bankenmappe",
        "⚖️ Rechtliche Dokumente",
        "👥 Teilnehmer-Status",
        "✉️ Einladungen",
        "💬 Kommentare",
        "🌐 Portal-Export",
        "📊 Marktdaten",
        "💬 Preisverhandlungen",
        "📧 E-Mail-Config"
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

    with tabs[8]:
        makler_portal_export_view()

    with tabs[9]:
        makler_marktdaten_view()

    with tabs[10]:
        makler_preisverhandlungen_view()

    with tabs[11]:
        makler_email_config_view()

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

            # Exposé-Verwaltung
            st.markdown("#### 📄 Exposé")

            # Zeige Exposé-Status
            if projekt.expose_data_id:
                expose = st.session_state.expose_data.get(projekt.expose_data_id)
                if expose:
                    st.success(f"✅ Exposé vorhanden: {expose.objektart}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Wohnfläche:** {expose.wohnflaeche} m²")
                        st.write(f"**Zimmer:** {expose.anzahl_zimmer}")
                    with col2:
                        st.write(f"**Kaufpreis:** {expose.kaufpreis:,.2f} €")
                        st.write(f"**Letzte Änderung:** {expose.updated_at.strftime('%d.%m.%Y')}")

            # Button zum Bearbeiten/Erstellen
            if st.button("📝 Exposé bearbeiten", key=f"edit_expose_{projekt.projekt_id}"):
                st.session_state[f"show_expose_editor_{projekt.projekt_id}"] = not st.session_state.get(f"show_expose_editor_{projekt.projekt_id}", False)

            # Exposé-Editor anzeigen
            if st.session_state.get(f"show_expose_editor_{projekt.projekt_id}", False):
                with st.expander("📝 Exposé-Editor", expanded=True):
                    render_expose_editor(projekt)

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
    # Website-Analyse für Logo (außerhalb des Forms)
    st.markdown("### 🎨 Logo-Übernahme")

    logo_uebernahme = st.checkbox(
        "🌐 Automatische Logo-Übernahme von Homepage aktivieren",
        value=False,
        help="Website wird analysiert und Logo automatisch übernommen",
        key="makler_logo_uebernahme_check"
    )

    analysis_data = None
    if logo_uebernahme:
        st.info("💡 Geben Sie Ihre Website-URL ein und klicken Sie auf 'Los', um Ihr Logo zu finden.")

        col1, col2 = st.columns([3, 1])
        with col1:
            website_input = st.text_input(
                "Website-URL",
                value=profile.website if profile.website else "",
                placeholder="z.B. https://www.ihre-immobilien.de",
                key="website_analyze_input"
            )
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("🚀 Los", type="primary", disabled=not website_input):
                with st.spinner("🔍 Analysiere Website und suche Logo..."):
                    analysis = analyze_website(website_input)
                    st.session_state[f"website_analysis_{profile.profile_id}"] = analysis
                    st.success("✅ Logo-Suche abgeschlossen!")
                    st.rerun()

        # Analyse-Ergebnisse abrufen
        analysis_data = st.session_state.get(f"website_analysis_{profile.profile_id}")

        if analysis_data and analysis_data.get("logo"):
            logo_data = analysis_data.get("logo", {})
            logo_kandidaten = logo_data.get("candidates", [])
            betreiber = analysis_data.get("betreiber", {})

            st.success(f"✅ {len(logo_kandidaten)} Logo-Kandidaten gefunden!")

            # Gefundene Kontaktdaten anzeigen
            if betreiber:
                with st.expander("📋 Gefundene Kontaktdaten ansehen", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        if betreiber.get('name'):
                            st.write(f"**Firmenname:** {betreiber['name']}")
                        if betreiber.get('kontakt', {}).get('email'):
                            st.write(f"**E-Mail:** {betreiber['kontakt']['email']}")
                        if betreiber.get('kontakt', {}).get('telefon'):
                            st.write(f"**Telefon:** {betreiber['kontakt']['telefon']}")
                    with col2:
                        adresse = betreiber.get('adresse', {})
                        if adresse.get('strasse'):
                            st.write(f"**Straße:** {adresse['strasse']}")
                        if adresse.get('plz') and adresse.get('ort'):
                            st.write(f"**Ort:** {adresse['plz']} {adresse['ort']}")
                    st.info("💡 Diese Daten wurden in die Formularfelder unten übernommen.")
        elif analysis_data and "error" in analysis_data:
            st.warning("⚠️ Website konnte nicht analysiert werden. Bitte geben Sie die Daten manuell ein.")

    st.markdown("---")

    with st.form("profil_bearbeiten"):
        st.markdown("### Firmendaten")

        # Daten aus Analyse übernehmen (falls vorhanden)
        if analysis_data and analysis_data.get("betreiber"):
            betreiber = analysis_data["betreiber"]
            default_firmenname = betreiber.get('name', profile.firmenname) or profile.firmenname
            default_email = betreiber.get('kontakt', {}).get('email', profile.email) or profile.email
            default_telefon = betreiber.get('kontakt', {}).get('telefon', profile.telefon) or profile.telefon
            default_website = analysis_data.get('url', profile.website) or profile.website

            # Adresse formatieren
            adresse_obj = betreiber.get('adresse', {})
            if adresse_obj.get('strasse') or adresse_obj.get('plz') or adresse_obj.get('ort'):
                default_adresse = f"{adresse_obj.get('strasse', '')}\n{adresse_obj.get('plz', '')} {adresse_obj.get('ort', '')}".strip()
            else:
                default_adresse = profile.adresse
        else:
            default_firmenname = profile.firmenname
            default_email = profile.email
            default_telefon = profile.telefon
            default_website = profile.website
            default_adresse = profile.adresse

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**Logo**")
            logo_file = st.file_uploader("Firmenlogo hochladen", type=["png", "jpg", "jpeg"], key="logo_upload")
            if profile.logo:
                st.image(profile.logo, width=150)
            elif logo_file:
                st.image(logo_file, width=150)

        with col2:
            firmenname = st.text_input("Firmenname*", value=default_firmenname)
            adresse = st.text_area("Adresse*", value=default_adresse, height=100)

            col_tel, col_email = st.columns(2)
            with col_tel:
                telefon = st.text_input("Telefon*", value=default_telefon)
            with col_email:
                email = st.text_input("E-Mail*", value=default_email)

            website = st.text_input("Website", value=default_website, help="z.B. https://www.ihre-immobilien.de")

        st.markdown("---")
        st.markdown("### 🎨 Logo & Design")

        # Logo-Auswahl basierend auf Analyse-Daten (falls vorhanden)
        if analysis_data and analysis_data.get("logo"):
            logo_data = analysis_data.get("logo", {})
            logo_kandidaten = logo_data.get("candidates", [])

            st.info("💡 Wählen Sie ein Logo aus den gefundenen URLs oder geben Sie eine eigene ein.")

            # Dropdown mit Logo-Kandidaten
            logo_url_input = st.selectbox(
                "Logo-URL auswählen:",
                options=logo_kandidaten if logo_kandidaten else [""],
                index=0,
                key="logo_url_select"
            )

            # Logo-Vorschau
            if logo_url_input:
                try:
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(logo_url_input, width=150, caption="Logo-Vorschau")
                    with col2:
                        st.success("✅ Logo wird übernommen")
                        if analysis_data.get("confidence"):
                            st.caption(f"Konfidenz: {int(analysis_data['confidence'] * 100)}%")
                except:
                    st.warning("⚠️ Logo konnte nicht geladen werden. Prüfen Sie die URL.")
        else:
            # Manuelle Logo-Eingabe
            logo_url_input = st.text_input(
                "Logo-URL eingeben:",
                value=profile.logo_url if profile.logo_url else "",
                placeholder="z.B. https://www.ihre-seite.de/logo.png",
                help="Aktivieren Sie oben die automatische Logo-Übernahme für Logo-Suche",
                key="manual_logo_url"
            )

            if logo_url_input:
                try:
                    st.image(logo_url_input, width=150, caption="Logo-Vorschau")
                except:
                    st.warning("⚠️ Logo konnte nicht geladen werden.")

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

            # Logo-Verwaltung
            if logo_file:
                profile.logo = logo_file.read()
                profile.logo_bestaetigt = True
                profile.logo_aktiviert = False

            # Logo-URL Verwaltung (aus Analyse oder manuell)
            if 'logo_url_input' in locals() and logo_url_input:
                profile.logo_url = logo_url_input
                profile.logo_bestaetigt = True
                profile.logo_aktiviert = True

            st.session_state.makler_profiles[profile.profile_id] = profile
            st.success("✅ Profil erfolgreich gespeichert!")
            st.rerun()

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

def makler_portal_export_view():
    """Portal-Export und Zugangsdaten-Verwaltung"""
    st.subheader("🌐 Immobilienportale - Export & Verwaltung")

    makler_id = st.session_state.current_user.user_id

    # Tab-Navigation
    portal_tabs = st.tabs(["🔑 Zugangsdaten", "📤 Exposé-Export", "📊 Export-Status"])

    with portal_tabs[0]:
        st.markdown("### 🔑 Portal-Zugangsdaten verwalten")
        st.info("Hinterlegen Sie hier Ihre Zugangsdaten für die verschiedenen Immobilienportale. Diese werden sicher gespeichert und für den automatischen Export verwendet.")

        # Verfügbare Portale
        verfuegbare_portale = ["ImmoScout24", "Immowelt", "Immonet", "eBay Kleinanzeigen", "ImmobilienScout24"]

        # Bestehende Zugangsdaten anzeigen
        makler_zugaenge = [z for z in st.session_state.portal_zugangsdaten.values() if z.makler_id == makler_id]

        if makler_zugaenge:
            st.markdown("#### Hinterlegte Zugänge:")
            for zugang in makler_zugaenge:
                with st.expander(f"{'✅' if zugang.aktiv else '❌'} {zugang.portal_name}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Benutzername:** {zugang.benutzername}")
                        st.write(f"**API-Key:** {'*' * 20 if zugang.api_key else 'Nicht hinterlegt'}")
                        st.write(f"**Status:** {'Aktiv' if zugang.aktiv else 'Inaktiv'}")
                        st.write(f"**Hinzugefügt:** {zugang.created_at.strftime('%d.%m.%Y')}")
                    with col2:
                        if st.button("🗑️ Löschen", key=f"del_zugang_{zugang.zugang_id}"):
                            del st.session_state.portal_zugangsdaten[zugang.zugang_id]
                            st.success("Zugangsdaten gelöscht!")
                            st.rerun()

                        toggle_status = st.checkbox(
                            "Aktiv",
                            value=zugang.aktiv,
                            key=f"toggle_{zugang.zugang_id}"
                        )
                        if toggle_status != zugang.aktiv:
                            zugang.aktiv = toggle_status
                            st.session_state.portal_zugangsdaten[zugang.zugang_id] = zugang
                            st.rerun()
        else:
            st.info("Noch keine Zugangsdaten hinterlegt.")

        # Neue Zugangsdaten hinzufügen
        st.markdown("---")
        st.markdown("#### ➕ Neue Zugangsdaten hinzufügen")

        with st.form("neue_portal_zugangsdaten"):
            portal_name = st.selectbox("Portal auswählen", verfuegbare_portale)
            benutzername = st.text_input("Benutzername / E-Mail*")
            api_key = st.text_input("API-Key / Passwort*", type="password", help="Wird verschlüsselt gespeichert")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Zugangsdaten speichern", type="primary"):
                    if benutzername and api_key:
                        zugang_id = f"zugang_{len(st.session_state.portal_zugangsdaten)}"
                        zugang = PortalZugangsdaten(
                            zugang_id=zugang_id,
                            makler_id=makler_id,
                            portal_name=portal_name,
                            benutzername=benutzername,
                            api_key=api_key,
                            aktiv=True
                        )
                        st.session_state.portal_zugangsdaten[zugang_id] = zugang
                        st.success(f"✅ Zugangsdaten für {portal_name} gespeichert!")
                        st.rerun()
                    else:
                        st.error("Bitte alle Pflichtfelder ausfüllen!")

    with portal_tabs[1]:
        st.markdown("### 📤 Exposé zu Portalen exportieren")

        # Projekte mit Exposé laden
        makler_projekte = [p for p in st.session_state.projekte.values() if p.makler_id == makler_id]
        projekte_mit_expose = [p for p in makler_projekte if p.expose_data_id]

        if not projekte_mit_expose:
            st.warning("Sie haben noch keine Projekte mit Exposé. Erstellen Sie zuerst ein Exposé in Ihren Projekten.")
            return

        # Projekt auswählen
        projekt_namen = {p.name: p.projekt_id for p in projekte_mit_expose}
        selected_projekt_name = st.selectbox("Projekt auswählen", list(projekt_namen.keys()))
        selected_projekt_id = projekt_namen[selected_projekt_name]
        projekt = st.session_state.projekte[selected_projekt_id]
        expose = st.session_state.expose_data.get(projekt.expose_data_id)

        if expose:
            # Exposé-Vorschau
            with st.expander("📄 Exposé-Vorschau", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Objektart:** {expose.objektart}")
                    st.write(f"**Wohnfläche:** {expose.wohnflaeche} m²")
                with col2:
                    st.write(f"**Zimmer:** {expose.anzahl_zimmer}")
                    st.write(f"**Kaufpreis:** {expose.kaufpreis:,.2f} €")
                with col3:
                    st.write(f"**Baujahr:** {expose.baujahr}")
                    st.write(f"**Zustand:** {expose.zustand}")

            st.markdown("---")

            # Portale mit Zugangsdaten
            aktive_zugaenge = [z for z in st.session_state.portal_zugangsdaten.values()
                             if z.makler_id == makler_id and z.aktiv]

            if not aktive_zugaenge:
                st.warning("⚠️ Sie haben noch keine aktiven Portal-Zugangsdaten hinterlegt. Bitte fügen Sie zuerst Zugangsdaten hinzu.")
                return

            st.markdown("#### Portale auswählen")
            st.info("Wählen Sie aus, zu welchen Portalen Sie das Exposé exportieren möchten:")

            selected_portals = []
            for zugang in aktive_zugaenge:
                if st.checkbox(f"📤 {zugang.portal_name}", key=f"export_{zugang.portal_name}"):
                    selected_portals.append(zugang)

                    # KI-generierte Beschreibung anzeigen
                    beschreibung = generate_portal_beschreibung(expose, zugang.portal_name)
                    with st.expander(f"💡 Vorschlag für {zugang.portal_name}", expanded=False):
                        st.text_area(
                            "Portal-optimierte Beschreibung",
                            value=beschreibung,
                            height=150,
                            key=f"desc_{zugang.portal_name}",
                            help="Diese Beschreibung wurde KI-optimiert für das jeweilige Portal"
                        )

            st.markdown("---")

            if selected_portals:
                if st.button("🚀 Zu ausgewählten Portalen exportieren", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for i, zugang in enumerate(selected_portals):
                        status_text.text(f"Exportiere zu {zugang.portal_name}...")

                        # Export durchführen
                        result = export_to_portal(expose.expose_id, zugang.portal_name, zugang)

                        # Export-Status speichern
                        export_id = f"export_{len(st.session_state.portal_exports)}"
                        export_record = PortalExport(
                            export_id=export_id,
                            expose_id=expose.expose_id,
                            portal_name=zugang.portal_name,
                            status="Erfolgreich" if result["success"] else "Fehlgeschlagen",
                            portal_objekt_id=result.get("portal_objekt_id", ""),
                            exportiert_am=datetime.now(),
                            fehler_nachricht="" if result["success"] else result.get("message", "Unbekannter Fehler")
                        )
                        st.session_state.portal_exports[export_id] = export_record

                        progress_bar.progress((i + 1) / len(selected_portals))

                    status_text.empty()
                    progress_bar.empty()
                    st.success(f"✅ Exposé erfolgreich zu {len(selected_portals)} Portal(en) exportiert!")
                    st.balloons()
                    st.rerun()
            else:
                st.info("👆 Wählen Sie mindestens ein Portal aus")

    with portal_tabs[2]:
        st.markdown("### 📊 Export-Status & Historie")

        # Alle Exports dieses Maklers
        all_exports = []
        for export in st.session_state.portal_exports.values():
            expose = st.session_state.expose_data.get(export.expose_id)
            if expose:
                # Finde Projekt
                for projekt in st.session_state.projekte.values():
                    if projekt.expose_data_id == expose.expose_id and projekt.makler_id == makler_id:
                        all_exports.append((projekt, expose, export))
                        break

        if all_exports:
            all_exports.sort(key=lambda x: x[2].exportiert_am if x[2].exportiert_am else datetime.now(), reverse=True)

            for projekt, expose, export in all_exports:
                status_icon = "✅" if export.status == "Erfolgreich" else "❌"
                with st.expander(f"{status_icon} {projekt.name} → {export.portal_name}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Projekt:** {projekt.name}")
                        st.write(f"**Portal:** {export.portal_name}")
                        st.write(f"**Status:** {export.status}")
                        if export.portal_objekt_id:
                            st.write(f"**Portal-ID:** {export.portal_objekt_id}")
                        if export.exportiert_am:
                            st.write(f"**Exportiert am:** {export.exportiert_am.strftime('%d.%m.%Y %H:%M')}")
                    with col2:
                        if export.status == "Erfolgreich" and export.portal_objekt_id:
                            portal_url = f"https://{export.portal_name.lower().replace(' ', '')}.de/expose/{export.portal_objekt_id}"
                            st.link_button("🔗 Portal ansehen", portal_url)

                    if export.fehler_nachricht:
                        st.error(f"⚠️ Fehler: {export.fehler_nachricht}")
        else:
            st.info("Noch keine Exports durchgeführt.")

def makler_marktdaten_view():
    """Marktdaten-Anzeige und Preisvorschläge"""
    st.subheader("📊 Marktdaten & Preisanalyse")

    makler_id = st.session_state.current_user.user_id
    makler_projekte = [p for p in st.session_state.projekte.values() if p.makler_id == makler_id]

    if not makler_projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    # Projekt auswählen
    projekt_namen = {p.name: p.projekt_id for p in makler_projekte}
    selected_projekt_name = st.selectbox("Projekt für Marktanalyse auswählen", list(projekt_namen.keys()))
    selected_projekt_id = projekt_namen[selected_projekt_name]
    projekt = st.session_state.projekte[selected_projekt_id]

    # Marktdaten abrufen Button
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### 🔍 Marktdaten abrufen")
        st.info("Analysieren Sie vergleichbare Immobilien aus deutschen Immobilienportalen (ImmoScout24, Immowelt, Immonet)")
    with col2:
        if st.button("🔄 Marktdaten aktualisieren", type="primary"):
            with st.spinner("Vergleichsobjekte werden analysiert..."):
                # Marktdaten abrufen
                markt_result = fetch_marktdaten(projekt)

                # Speichern
                markt_id = f"markt_{projekt.projekt_id}_{int(datetime.now().timestamp())}"
                markt_daten = MarktDaten(
                    markt_id=markt_id,
                    projekt_id=projekt.projekt_id,
                    portal="Verschiedene",
                    vergleichsobjekte=markt_result["vergleichsobjekte"],
                    durchschnittspreis=markt_result["durchschnittspreis"],
                    preis_pro_qm=markt_result["preis_pro_qm"],
                    empfohlener_preis=markt_result["empfohlener_preis"]
                )
                st.session_state.markt_daten[markt_id] = markt_daten

                st.success("✅ Marktdaten erfolgreich abgerufen!")
                st.rerun()

    st.markdown("---")

    # Bestehende Marktdaten anzeigen
    projekt_marktdaten = [m for m in st.session_state.markt_daten.values()
                         if m.projekt_id == projekt.projekt_id]

    if projekt_marktdaten:
        # Neueste Daten
        neueste_daten = sorted(projekt_marktdaten, key=lambda x: x.abgerufen_am, reverse=True)[0]

        st.markdown(f"#### 📈 Marktanalyse für {projekt.name}")
        st.caption(f"Letzte Aktualisierung: {neueste_daten.abgerufen_am.strftime('%d.%m.%Y %H:%M')}")

        # Preis-Übersicht
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Durchschnittspreis (Markt)",
                f"{neueste_daten.durchschnittspreis:,.0f} €",
                delta=f"{((neueste_daten.durchschnittspreis - projekt.kaufpreis) / projekt.kaufpreis * 100):.1f}%" if projekt.kaufpreis > 0 else None
            )
        with col2:
            st.metric(
                "Preis pro m²",
                f"{neueste_daten.preis_pro_qm:,.0f} €/m²"
            )
        with col3:
            st.metric(
                "💡 Empfohlener Preis",
                f"{neueste_daten.empfohlener_preis:,.0f} €",
                delta=f"{((neueste_daten.empfohlener_preis - projekt.kaufpreis) / projekt.kaufpreis * 100):.1f}%" if projekt.kaufpreis > 0 else None,
                delta_color="normal"
            )

        st.markdown("---")

        # Vergleichsobjekte
        st.markdown("#### 🏘️ Vergleichsobjekte")

        for i, obj in enumerate(neueste_daten.vergleichsobjekte):
            with st.expander(f"📍 {obj['titel']} - {obj['preis']:,.0f} €", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Adresse:** {obj['adresse']}")
                    st.write(f"**Preis:** {obj['preis']:,.0f} €")
                    st.write(f"**Preis/m²:** {obj['preis_pro_qm']:,.0f} €/m²")
                with col2:
                    st.write(f"**Wohnfläche:** {obj['wohnflaeche']:.0f} m²")
                    st.write(f"**Zimmer:** {obj['zimmer']}")
                    st.write(f"**Baujahr:** {obj['baujahr']}")
                with col3:
                    st.write(f"**Quelle:** {obj['quelle']}")

                    # Preisabweichung
                    if projekt.kaufpreis > 0:
                        abweichung = ((obj['preis'] - projekt.kaufpreis) / projekt.kaufpreis * 100)
                        if abweichung > 0:
                            st.success(f"↑ +{abweichung:.1f}% teurer")
                        elif abweichung < 0:
                            st.info(f"↓ {abweichung:.1f}% günstiger")
                        else:
                            st.info("= Gleicher Preis")

        st.markdown("---")

        # Preisempfehlung
        st.markdown("#### 💰 Preisempfehlung")

        if projekt.kaufpreis > 0:
            differenz = neueste_daten.empfohlener_preis - projekt.kaufpreis
            prozent = (differenz / projekt.kaufpreis * 100)

            if abs(prozent) < 3:
                st.success(f"✅ Ihr aktueller Preis ({projekt.kaufpreis:,.0f} €) liegt im optimalen Bereich (Abweichung: {prozent:+.1f}%)")
            elif prozent > 0:
                st.warning(f"💡 Der Markt würde einen höheren Preis unterstützen. Potenzial: +{differenz:,.0f} € ({prozent:+.1f}%)")
            else:
                st.info(f"💡 Ihr Preis liegt über dem Marktdurchschnitt. Differenz: {differenz:,.0f} € ({prozent:+.1f}%)")
        else:
            st.info(f"💡 Basierend auf den Marktdaten empfehlen wir einen Preis von {neueste_daten.empfohlener_preis:,.0f} €")
    else:
        st.info("📊 Noch keine Marktdaten abgerufen. Klicken Sie auf 'Marktdaten aktualisieren', um eine Analyse zu starten.")

def makler_preisverhandlungen_view():
    """Preisverhandlungs-Chat zwischen Käufer und Verkäufer"""
    st.subheader("💬 Preisverhandlungen")

    makler_id = st.session_state.current_user.user_id
    makler_projekte = [p for p in st.session_state.projekte.values() if p.makler_id == makler_id]

    if not makler_projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    st.info("💡 Hier können Sie Preisverhandlungen zwischen Käufer und Verkäufer moderieren und verfolgen.")

    # Projekt auswählen
    projekt_namen = {p.name: p.projekt_id for p in makler_projekte}
    selected_projekt_name = st.selectbox("Projekt auswählen", list(projekt_namen.keys()))
    selected_projekt_id = projekt_namen[selected_projekt_name]
    projekt = st.session_state.projekte[selected_projekt_id]

    st.markdown("---")

    # Bestehende Verhandlungen für dieses Projekt
    projekt_verhandlungen = [v for v in st.session_state.preis_verhandlungen.values()
                            if v.projekt_id == projekt.projekt_id]

    if not projekt_verhandlungen:
        # Neue Verhandlung starten
        st.markdown("#### 🆕 Neue Preisverhandlung starten")

        col1, col2 = st.columns(2)
        with col1:
            ausgangspreis = st.number_input(
                "Ausgangspreis (€)",
                min_value=0.0,
                value=float(projekt.kaufpreis) if projekt.kaufpreis > 0 else 300000.0,
                step=1000.0
            )
        with col2:
            st.write("")
            st.write("")
            if st.button("🚀 Verhandlung starten", type="primary"):
                verhandlung_id = f"verhandlung_{len(st.session_state.preis_verhandlungen)}"
                verhandlung = PreisVerhandlung(
                    verhandlung_id=verhandlung_id,
                    projekt_id=projekt.projekt_id,
                    ausgangspreis=ausgangspreis,
                    aktueller_preis=ausgangspreis,
                    status="Aktiv",
                    nachrichten=[]
                )
                st.session_state.preis_verhandlungen[verhandlung_id] = verhandlung
                st.success("✅ Preisverhandlung gestartet!")
                st.rerun()
    else:
        # Aktive Verhandlung anzeigen
        verhandlung = projekt_verhandlungen[0]  # Nur eine Verhandlung pro Projekt

        # Status-Anzeige
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ausgangspreis", f"{verhandlung.ausgangspreis:,.0f} €")
        with col2:
            st.metric("Aktuelles Angebot", f"{verhandlung.aktueller_preis:,.0f} €")
        with col3:
            differenz = verhandlung.aktueller_preis - verhandlung.ausgangspreis
            st.metric("Differenz", f"{differenz:+,.0f} €")

        st.markdown("---")

        # Chat-Verlauf
        st.markdown("#### 💬 Verhandlungsverlauf")

        if verhandlung.nachrichten:
            for msg in verhandlung.nachrichten:
                sender_icon = "👤" if msg["sender"] == "Verkäufer" else "🏠" if msg["sender"] == "Käufer" else "📊"

                if msg["sender"] == "Makler":
                    alignment = "center"
                    bg_color = "#e3f2fd"
                else:
                    alignment = "left" if msg["sender"] == "Verkäufer" else "right"
                    bg_color = "#f5f5f5" if msg["sender"] == "Verkäufer" else "#e8f5e9"

                st.markdown(f"""
                <div style='text-align:{alignment}; margin:10px 0;'>
                    <div style='display:inline-block; background:{bg_color}; padding:10px 15px; border-radius:10px; max-width:70%;'>
                        <strong>{sender_icon} {msg['sender']}</strong><br>
                        {msg['nachricht']}<br>
                        {'<strong>Preis: ' + f"{msg['preis']:,.0f} €" + '</strong><br>' if 'preis' in msg else ''}
                        <small>{msg['zeitpunkt']}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Noch keine Nachrichten in dieser Verhandlung.")

        st.markdown("---")

        # Neue Nachricht (nur Makler kann moderieren)
        st.markdown("#### ✍️ Als Makler moderieren")

        with st.form("verhandlung_nachricht"):
            nachricht = st.text_area("Nachricht / Kommentar", placeholder="z.B. 'Verkäufer hat Gegenangebot gemacht'")

            col1, col2, col3 = st.columns(3)
            with col1:
                sender_type = st.selectbox("Im Namen von", ["Makler", "Verkäufer (Angebot)", "Käufer (Gegenangebot)"])
            with col2:
                neuer_preis = st.number_input("Preis (€)", min_value=0.0, value=float(verhandlung.aktueller_preis), step=1000.0)
            with col3:
                st.write("")
                st.write("")
                submit = st.form_submit_button("📤 Nachricht senden", type="primary")

            if submit and nachricht:
                msg = {
                    "sender": sender_type.split(" ")[0],  # Nur "Makler", "Verkäufer" oder "Käufer"
                    "nachricht": nachricht,
                    "zeitpunkt": datetime.now().strftime('%d.%m.%Y %H:%M'),
                }

                # Preis nur bei Angeboten
                if "Angebot" in sender_type or "Gegenangebot" in sender_type:
                    msg["preis"] = neuer_preis
                    verhandlung.aktueller_preis = neuer_preis

                verhandlung.nachrichten.append(msg)
                st.session_state.preis_verhandlungen[verhandlung.verhandlung_id] = verhandlung

                st.success("✅ Nachricht hinzugefügt!")
                st.rerun()

        st.markdown("---")

        # Verhandlung abschließen
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Verhandlung erfolgreich abschließen"):
                verhandlung.status = "Abgeschlossen"
                projekt.kaufpreis = verhandlung.aktueller_preis
                st.session_state.preis_verhandlungen[verhandlung.verhandlung_id] = verhandlung
                st.session_state.projekte[projekt.projekt_id] = projekt
                st.success(f"✅ Verhandlung abgeschlossen! Finaler Preis: {verhandlung.aktueller_preis:,.0f} €")
                st.rerun()
        with col2:
            if st.button("❌ Verhandlung abbrechen"):
                verhandlung.status = "Abgebrochen"
                st.session_state.preis_verhandlungen[verhandlung.verhandlung_id] = verhandlung
                st.warning("Verhandlung wurde abgebrochen.")
                st.rerun()

def makler_email_config_view():
    """E-Mail-Konfiguration für SMTP"""
    st.subheader("📧 E-Mail-Konfiguration")

    makler_id = st.session_state.current_user.user_id

    st.info("💡 Konfigurieren Sie Ihren SMTP-Server, um automatisch E-Mail-Einladungen an Käufer und Verkäufer zu versenden.")

    # Bestehende Konfiguration laden
    email_config = None
    for config in st.session_state.email_konfigurationen.values():
        if config.user_id == makler_id:
            email_config = config
            break

    # Konfigurationsformular
    with st.form("email_config_form"):
        st.markdown("### SMTP-Server Einstellungen")

        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input(
                "SMTP-Server*",
                value=email_config.smtp_server if email_config else "smtp.gmail.com",
                help="z.B. smtp.gmail.com, smtp.office365.com"
            )
            smtp_user = st.text_input(
                "SMTP-Benutzername / E-Mail*",
                value=email_config.smtp_user if email_config else "",
                help="Ihre E-Mail-Adresse"
            )
        with col2:
            smtp_port = st.number_input(
                "SMTP-Port*",
                min_value=1,
                max_value=65535,
                value=email_config.smtp_port if email_config else 587,
                help="Standard: 587 (TLS) oder 465 (SSL)"
            )
            smtp_password = st.text_input(
                "SMTP-Passwort / App-Passwort*",
                type="password",
                value=email_config.smtp_password if email_config else "",
                help="Bei Gmail: App-Passwort verwenden"
            )

        absender_name = st.text_input(
            "Absender-Name",
            value=email_config.absender_name if email_config else "",
            help="z.B. 'Immobilien Müller GmbH'"
        )

        aktiv = st.checkbox(
            "E-Mail-Versand aktivieren",
            value=email_config.aktiv if email_config else False,
            help="Aktivieren Sie diese Option, um automatischen E-Mail-Versand zu ermöglichen"
        )

        st.markdown("---")

        col1, col2 = st.columns([2, 1])
        with col1:
            if st.form_submit_button("💾 Konfiguration speichern", type="primary"):
                if smtp_server and smtp_user and smtp_password:
                    if email_config:
                        # Update bestehend
                        email_config.smtp_server = smtp_server
                        email_config.smtp_port = smtp_port
                        email_config.smtp_user = smtp_user
                        email_config.smtp_password = smtp_password
                        email_config.absender_name = absender_name
                        email_config.aktiv = aktiv
                        st.session_state.email_konfigurationen[email_config.config_id] = email_config
                    else:
                        # Neu erstellen
                        config_id = f"emailconfig_{len(st.session_state.email_konfigurationen)}"
                        email_config = EmailKonfiguration(
                            config_id=config_id,
                            user_id=makler_id,
                            smtp_server=smtp_server,
                            smtp_port=smtp_port,
                            smtp_user=smtp_user,
                            smtp_password=smtp_password,
                            absender_name=absender_name,
                            aktiv=aktiv
                        )
                        st.session_state.email_konfigurationen[config_id] = email_config

                    st.success("✅ E-Mail-Konfiguration gespeichert!")
                    st.rerun()
                else:
                    st.error("Bitte alle Pflichtfelder ausfüllen!")

        with col2:
            if email_config and st.form_submit_button("📧 Test-E-Mail senden"):
                if email_config.smtp_user:
                    success = send_email(
                        empfaenger_email=email_config.smtp_user,
                        betreff="Test-E-Mail von Ihrer Immobilienplattform",
                        nachricht="Dies ist eine Test-E-Mail. Ihre SMTP-Konfiguration funktioniert!",
                        makler_id=makler_id
                    )
                    if success:
                        st.success("✅ Test-E-Mail gesendet!")
                    else:
                        st.error("❌ E-Mail-Versand fehlgeschlagen. Bitte Einstellungen prüfen.")
                else:
                    st.error("Bitte zuerst Konfiguration speichern!")

    # Hilfebereich
    with st.expander("❓ Hilfe & Häufige SMTP-Server"):
        st.markdown("""
        **Gmail:**
        - Server: `smtp.gmail.com`
        - Port: `587`
        - Hinweis: App-Passwort erforderlich (nicht Ihr Gmail-Passwort)
        - [App-Passwort erstellen](https://myaccount.google.com/apppasswords)

        **Outlook / Office365:**
        - Server: `smtp.office365.com`
        - Port: `587`

        **GMX:**
        - Server: `mail.gmx.net`
        - Port: `587`

        **Web.de:**
        - Server: `smtp.web.de`
        - Port: `587`

        **1&1 / IONOS:**
        - Server: `smtp.ionos.de`
        - Port: `587`
        """)

    st.markdown("---")

    # Status-Anzeige
    if email_config:
        st.markdown("### 📊 Status")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", "✅ Aktiv" if email_config.aktiv else "⏸️ Inaktiv")
        with col2:
            st.metric("Server", email_config.smtp_server)
        with col3:
            st.metric("Absender", email_config.smtp_user)

# ============================================================================
# KÄUFER/VERKÄUFER ONBOARDING
# ============================================================================

def onboarding_flow():
    """Onboarding-Flow für Käufer/Verkäufer"""
    st.title("👋 Willkommen!")

    user = st.session_state.current_user

    # Schritt 1: Stammdaten erfassen
    if not user.stammdaten_complete:
        st.markdown("""
        ### 📝 Schritt 1: Ihre Stammdaten
        Um den Prozess zu beschleunigen, können Sie Ihren Personalausweis hochladen.
        Ihre Daten werden automatisch erkannt und sicher verarbeitet.
        """)

        st.info("💡 **Optional aber empfohlen:** Laden Sie ein Foto oder Scan Ihres Personalausweises hoch, um Ihre Stammdaten automatisch zu erfassen.")

        # Personalausweis-Upload
        ausweis_file = st.file_uploader(
            "📷 Personalausweis hochladen (Vorder- oder Rückseite)",
            type=["png", "jpg", "jpeg", "pdf"],
            help="Ihre Daten werden sicher verarbeitet und nicht an Dritte weitergegeben"
        )

        ocr_data = {}
        if ausweis_file:
            with st.spinner("🔍 Dokument wird analysiert..."):
                # OCR durchführen
                file_bytes = ausweis_file.read()
                ocr_data = extract_personalausweis_data(file_bytes, ausweis_file.name)

                if ocr_data.get("vorname"):
                    st.success("✅ Personalausweis erfolgreich erkannt! Bitte überprüfen Sie die extrahierten Daten.")
                else:
                    st.warning("⚠️ Keine Daten erkannt. Bitte geben Sie Ihre Daten manuell ein.")

        st.markdown("---")
        st.markdown("#### Ihre Stammdaten")

        with st.form("stammdaten_form"):
            col1, col2 = st.columns(2)
            with col1:
                vorname = st.text_input("Vorname*", value=ocr_data.get("vorname", user.vorname))
                nachname = st.text_input("Nachname*", value=ocr_data.get("nachname", user.nachname))
                geburtsdatum = st.text_input(
                    "Geburtsdatum*",
                    value=ocr_data.get("geburtsdatum", user.geburtsdatum),
                    placeholder="TT.MM.JJJJ"
                )
                geburtsort = st.text_input("Geburtsort*", value=ocr_data.get("geburtsort", user.geburtsort))

            with col2:
                staatsangehoerigkeit = st.text_input(
                    "Staatsangehörigkeit*",
                    value=ocr_data.get("staatsangehoerigkeit", user.staatsangehoerigkeit)
                )
                anschrift = st.text_area(
                    "Anschrift*",
                    value=ocr_data.get("anschrift", user.anschrift),
                    height=100
                )
                ausweisnummer = st.text_input(
                    "Ausweisnummer",
                    value=ocr_data.get("ausweisnummer", user.ausweisnummer)
                )
                gueltig_bis = st.text_input(
                    "Gültig bis",
                    value=ocr_data.get("gueltig_bis", user.gueltig_bis),
                    placeholder="TT.MM.JJJJ"
                )

            st.markdown("---")

            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption("* Pflichtfelder")
            with col2:
                submit = st.form_submit_button("✅ Weiter zu Dokumenten", type="primary", use_container_width=True)

            if submit:
                if vorname and nachname and geburtsdatum and geburtsort and staatsangehoerigkeit and anschrift:
                    # Stammdaten speichern
                    user.vorname = vorname
                    user.nachname = nachname
                    user.geburtsdatum = geburtsdatum
                    user.geburtsort = geburtsort
                    user.staatsangehoerigkeit = staatsangehoerigkeit
                    user.anschrift = anschrift
                    user.ausweisnummer = ausweisnummer
                    user.gueltig_bis = gueltig_bis
                    user.ausstellende_behoerde = ocr_data.get("ausstellende_behoerde", "")
                    user.stammdaten_complete = True

                    # Name aktualisieren
                    user.name = f"{vorname} {nachname}"

                    st.session_state.users[user.user_id] = user
                    st.success("✅ Stammdaten erfolgreich gespeichert!")
                    st.rerun()
                else:
                    st.error("❌ Bitte füllen Sie alle Pflichtfelder aus!")

        return  # Hier stoppen, bis Stammdaten komplett sind

    # Schritt 2: Rechtliche Dokumente akzeptieren
    st.markdown("""
    ### 📄 Schritt 2: Rechtliche Dokumente
    Bitte prüfen und akzeptieren Sie die folgenden rechtlichen Dokumente.
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

    # Prüfen ob Käufer über Notar und/oder Makler vermittelt wurde
    user_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if user_id in p.kaeufer_ids]

    notar_profile = None
    makler_profile = None

    if projekte:
        # Erstes Projekt analysieren
        for projekt in projekte:
            # Notar-Profil laden
            if projekt.notar_id and not notar_profile:
                for p in st.session_state.notar_profiles.values():
                    if p.notar_id == projekt.notar_id:
                        notar_profile = p
                        break

            # Makler-Profil laden
            if projekt.makler_id and not makler_profile:
                for p in st.session_state.makler_profiles.values():
                    if p.makler_id == projekt.makler_id:
                        makler_profile = p
                        break

            if notar_profile and makler_profile:
                break

    # Titelzeile mit Logos
    notar_hat_logo = notar_profile and notar_profile.logo_bestaetigt and (notar_profile.logo or notar_profile.logo_url)
    makler_hat_logo = makler_profile and makler_profile.logo_bestaetigt and (makler_profile.logo or makler_profile.logo_url)

    if notar_hat_logo and makler_hat_logo:
        # Beide Logos anzeigen: Notar (Haupt) + Makler (Kooperation)
        col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
        with col1:
            if notar_profile.logo_url:
                st.image(notar_profile.logo_url, width=100)
            elif notar_profile.logo:
                st.image(notar_profile.logo, width=100)
            if notar_profile.kanzleiname:
                st.caption(notar_profile.kanzleiname)
        with col2:
            st.title("🏠 Käufer-Dashboard")
        with col3:
            st.markdown("##### 🤝 in Kooperation mit")
        with col4:
            if makler_profile.logo_url:
                st.image(makler_profile.logo_url, width=80)
            elif makler_profile.logo:
                st.image(makler_profile.logo, width=80)
            if makler_profile.firmenname:
                st.caption(makler_profile.firmenname)
    elif notar_hat_logo:
        # Nur Notar-Logo
        col1, col2 = st.columns([1, 4])
        with col1:
            if notar_profile.logo_url:
                st.image(notar_profile.logo_url, width=120)
            elif notar_profile.logo:
                st.image(notar_profile.logo, width=120)
            if notar_profile.kanzleiname:
                st.caption(notar_profile.kanzleiname)
        with col2:
            st.title("🏠 Käufer-Dashboard")
    elif makler_hat_logo:
        # Nur Makler-Logo
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.title("🏠 Käufer-Dashboard")
        with col2:
            st.write("")  # Spacer
        with col3:
            st.markdown("##### 🤝 in Kooperation mit")
            if makler_profile.logo_url:
                st.image(makler_profile.logo_url, width=100)
            elif makler_profile.logo:
                st.image(makler_profile.logo, width=100)
            if makler_profile.firmenname:
                st.caption(makler_profile.firmenname)
    else:
        st.title("🏠 Käufer-Dashboard")

    if not st.session_state.current_user.onboarding_complete:
        onboarding_flow()
        return

    tabs = st.tabs(["📊 Timeline", "📋 Projekte", "💰 Finanzierung", "💬 Nachrichten", "📄 Dokumente"])

    with tabs[0]:
        kaeufer_timeline_view()

    with tabs[1]:
        kaeufer_projekte_view()

    with tabs[2]:
        kaeufer_finanzierung_view()

    with tabs[3]:
        kaeufer_nachrichten()

    with tabs[4]:
        kaeufer_dokumente_view()

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

    # Prüfen ob Verkäufer über Notar und/oder Makler vermittelt wurde
    user_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if user_id in p.verkaeufer_ids]

    notar_profile = None
    makler_profile = None

    if projekte:
        # Erstes Projekt analysieren
        for projekt in projekte:
            # Notar-Profil laden
            if projekt.notar_id and not notar_profile:
                for p in st.session_state.notar_profiles.values():
                    if p.notar_id == projekt.notar_id:
                        notar_profile = p
                        break

            # Makler-Profil laden
            if projekt.makler_id and not makler_profile:
                for p in st.session_state.makler_profiles.values():
                    if p.makler_id == projekt.makler_id:
                        makler_profile = p
                        break

            if notar_profile and makler_profile:
                break

    # Titelzeile mit Logos
    notar_hat_logo = notar_profile and notar_profile.logo_bestaetigt and (notar_profile.logo or notar_profile.logo_url)
    makler_hat_logo = makler_profile and makler_profile.logo_bestaetigt and (makler_profile.logo or makler_profile.logo_url)

    if notar_hat_logo and makler_hat_logo:
        # Beide Logos anzeigen: Notar (Haupt) + Makler (Kooperation)
        col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
        with col1:
            if notar_profile.logo_url:
                st.image(notar_profile.logo_url, width=100)
            elif notar_profile.logo:
                st.image(notar_profile.logo, width=100)
            if notar_profile.kanzleiname:
                st.caption(notar_profile.kanzleiname)
        with col2:
            st.title("🏡 Verkäufer-Dashboard")
        with col3:
            st.markdown("##### 🤝 in Kooperation mit")
        with col4:
            if makler_profile.logo_url:
                st.image(makler_profile.logo_url, width=80)
            elif makler_profile.logo:
                st.image(makler_profile.logo, width=80)
            if makler_profile.firmenname:
                st.caption(makler_profile.firmenname)
    elif notar_hat_logo:
        # Nur Notar-Logo
        col1, col2 = st.columns([1, 4])
        with col1:
            if notar_profile.logo_url:
                st.image(notar_profile.logo_url, width=120)
            elif notar_profile.logo:
                st.image(notar_profile.logo, width=120)
            if notar_profile.kanzleiname:
                st.caption(notar_profile.kanzleiname)
        with col2:
            st.title("🏡 Verkäufer-Dashboard")
    elif makler_hat_logo:
        # Nur Makler-Logo
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.title("🏡 Verkäufer-Dashboard")
        with col2:
            st.write("")  # Spacer
        with col3:
            st.markdown("##### 🤝 in Kooperation mit")
            if makler_profile.logo_url:
                st.image(makler_profile.logo_url, width=100)
            elif makler_profile.logo:
                st.image(makler_profile.logo, width=100)
            if makler_profile.firmenname:
                st.caption(makler_profile.firmenname)
    else:
        st.title("🏡 Verkäufer-Dashboard")

    if not st.session_state.current_user.onboarding_complete:
        onboarding_flow()
        return

    tabs = st.tabs(["📊 Timeline", "📋 Projekte", "📄 Dokumente hochladen", "📋 Dokumentenanforderungen", "💬 Nachrichten"])

    with tabs[0]:
        verkaeufer_timeline_view()

    with tabs[1]:
        verkaeufer_projekte_view()

    with tabs[2]:
        verkaeufer_dokumente_view()

    with tabs[3]:
        render_document_requests_view(st.session_state.current_user.user_id, UserRole.VERKAEUFER.value)

    with tabs[4]:
        verkaeufer_nachrichten()

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

    # Notar-Profil für Logo laden
    notar_id = st.session_state.current_user.user_id
    profile = None
    for p in st.session_state.notar_profiles.values():
        if p.notar_id == notar_id:
            profile = p
            break

    # Titelzeile mit Logo
    if profile and profile.logo_bestaetigt and (profile.logo or profile.logo_url):
        col1, col2 = st.columns([1, 4])
        with col1:
            if profile.logo_url:
                st.image(profile.logo_url, width=120)
            elif profile.logo:
                st.image(profile.logo, width=120)
        with col2:
            st.title("⚖️ Notar-Dashboard")
            if profile.kanzleiname:
                st.markdown(f"**{profile.kanzleiname}**")
                notar_name = f"{profile.notar_titel} {profile.notar_vorname} {profile.notar_nachname}".strip()
                if notar_name:
                    st.caption(notar_name)
    else:
        st.title("⚖️ Notar-Dashboard")

    tabs = st.tabs([
        "📊 Timeline",
        "📋 Projekte",
        "📝 Checklisten",
        "📋 Dokumentenanforderungen",
        "👤 Profil",
        "👥 Mitarbeiter",
        "🤝 Makler-Netzwerk",
        "🔄 Vermittler",
        "💰 Finanzierungsnachweise",
        "📄 Dokumenten-Freigaben",
        "📅 Termine",
        "⚖️ Aufträge"
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
        notar_profil_view()

    with tabs[5]:
        notar_mitarbeiter_view()

    with tabs[6]:
        notar_makler_netzwerk_view()

    with tabs[7]:
        notar_vermittler_view()

    with tabs[8]:
        notar_finanzierungsnachweise()

    with tabs[9]:
        notar_dokumenten_freigaben()

    with tabs[10]:
        notar_termine()

    with tabs[11]:
        notar_auftraege_view()

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

def notar_profil_view():
    """Notar-Profil-Verwaltung"""
    st.subheader("👤 Mein Notar-Profil")

    notar_id = st.session_state.current_user.user_id

    # Profil suchen oder erstellen
    profile = None
    for p in st.session_state.notar_profiles.values():
        if p.notar_id == notar_id:
            profile = p
            break

    if not profile:
        st.info("Sie haben noch kein Profil erstellt. Erstellen Sie jetzt Ihr Kanzlei-Profil!")
        if st.button("➕ Profil erstellen"):
            profile_id = f"notarprofile_{len(st.session_state.notar_profiles)}"
            profile = NotarProfile(
                profile_id=profile_id,
                notar_id=notar_id,
                kanzleiname="",
                notar_vorname="",
                notar_nachname=""
            )
            st.session_state.notar_profiles[profile_id] = profile
            st.rerun()
        return

    # Profil bearbeiten
    # Website-Analyse für Logo (außerhalb des Forms)
    st.markdown("### 🎨 Logo-Übernahme")

    logo_uebernahme = st.checkbox(
        "🌐 Automatische Logo-Übernahme von Homepage aktivieren",
        value=False,
        help="Kanzlei-Website wird analysiert und Logo automatisch übernommen",
        key="notar_logo_uebernahme_check"
    )

    analysis_data = None
    if logo_uebernahme:
        st.info("💡 Geben Sie Ihre Kanzlei-Website ein und klicken Sie auf 'Los', um Ihr Logo zu finden.")

        col1, col2 = st.columns([3, 1])
        with col1:
            website_input = st.text_input(
                "Kanzlei-Website",
                value=profile.website if profile.website else "",
                placeholder="z.B. https://www.ihre-kanzlei.de",
                key="notar_website_analyze_input"
            )
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("🚀 Los", type="primary", disabled=not website_input, key="notar_analyze_btn"):
                with st.spinner("🔍 Analysiere Kanzlei-Website und suche Logo..."):
                    analysis = analyze_website(website_input)
                    st.session_state[f"website_analysis_{profile.profile_id}"] = analysis
                    st.success("✅ Logo-Suche abgeschlossen!")
                    st.rerun()

        # Analyse-Ergebnisse abrufen
        analysis_data = st.session_state.get(f"website_analysis_{profile.profile_id}")

        if analysis_data and analysis_data.get("logo"):
            logo_data = analysis_data.get("logo", {})
            logo_kandidaten = logo_data.get("candidates", [])
            betreiber = analysis_data.get("betreiber", {})

            st.success(f"✅ {len(logo_kandidaten)} Logo-Kandidaten gefunden!")

            # Gefundene Kontaktdaten anzeigen
            if betreiber:
                with st.expander("📋 Gefundene Kanzlei-Daten ansehen", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        if betreiber.get('name'):
                            st.write(f"**Kanzleiname:** {betreiber['name']}")
                        if betreiber.get('kontakt', {}).get('email'):
                            st.write(f"**E-Mail:** {betreiber['kontakt']['email']}")
                        if betreiber.get('kontakt', {}).get('telefon'):
                            st.write(f"**Telefon:** {betreiber['kontakt']['telefon']}")
                    with col2:
                        adresse_data = betreiber.get('adresse', {})
                        if adresse_data.get('strasse'):
                            st.write(f"**Straße:** {adresse_data['strasse']}")
                        if adresse_data.get('plz') and adresse_data.get('ort'):
                            st.write(f"**Ort:** {adresse_data['plz']} {adresse_data['ort']}")

                    # Notar-spezifische Daten anzeigen
                    notar_daten = analysis_data.get('notar_daten')
                    if notar_daten:
                        st.markdown("---")
                        st.markdown("**⚖️ Notar-spezifische Daten:**")
                        col1, col2 = st.columns(2)
                        with col1:
                            if notar_daten.get('titel') or notar_daten.get('vorname') or notar_daten.get('nachname'):
                                notar_name = f"{notar_daten.get('titel', '')} {notar_daten.get('vorname', '')} {notar_daten.get('nachname', '')}".strip()
                                st.write(f"**Notar:** {notar_name}")
                            if notar_daten.get('notarkammer'):
                                st.write(f"**Notarkammer:** {notar_daten['notarkammer']}")
                        with col2:
                            if notar_daten.get('notarversicherung'):
                                st.write(f"**Versicherung:** {notar_daten['notarversicherung']}")

                    st.info("💡 Diese Daten wurden in die Formularfelder unten übernommen.")
        elif analysis_data and "error" in analysis_data:
            st.warning("⚠️ Website konnte nicht analysiert werden. Bitte geben Sie die Daten manuell ein.")

    st.markdown("---")

    with st.form("notar_profil_bearbeiten"):
        st.markdown("### ⚖️ Kanzlei-Informationen")

        # Daten aus Analyse übernehmen (falls vorhanden)
        if analysis_data and analysis_data.get("betreiber"):
            betreiber = analysis_data["betreiber"]
            default_kanzleiname = betreiber.get('name', profile.kanzleiname) or profile.kanzleiname
            default_email = betreiber.get('kontakt', {}).get('email', profile.email) or profile.email
            default_telefon = betreiber.get('kontakt', {}).get('telefon', profile.telefon) or profile.telefon
            default_website = analysis_data.get('url', profile.website) or profile.website

            # Adresse aus Betreiber-Daten
            adresse_obj = betreiber.get('adresse', {})
            default_adresse = adresse_obj.get('strasse', profile.adresse) or profile.adresse
            default_plz = adresse_obj.get('plz', profile.plz) or profile.plz
            default_ort = adresse_obj.get('ort', profile.ort) or profile.ort

            # Notar-spezifische Daten aus Analyse
            notar_daten = analysis_data.get('notar_daten', {})
            if notar_daten:
                default_notar_titel = notar_daten.get('titel', profile.notar_titel) or profile.notar_titel
                default_notar_vorname = notar_daten.get('vorname', profile.notar_vorname) or profile.notar_vorname
                default_notar_nachname = notar_daten.get('nachname', profile.notar_nachname) or profile.notar_nachname
                default_notarkammer = notar_daten.get('notarkammer', profile.notarkammer) or profile.notarkammer
                default_notarversicherung = notar_daten.get('notarversicherung', profile.notarversicherung) or profile.notarversicherung
            else:
                default_notar_titel = profile.notar_titel
                default_notar_vorname = profile.notar_vorname
                default_notar_nachname = profile.notar_nachname
                default_notarkammer = profile.notarkammer
                default_notarversicherung = profile.notarversicherung
        else:
            default_kanzleiname = profile.kanzleiname
            default_email = profile.email
            default_telefon = profile.telefon
            default_website = profile.website
            default_adresse = profile.adresse
            default_plz = profile.plz
            default_ort = profile.ort
            default_notar_titel = profile.notar_titel
            default_notar_vorname = profile.notar_vorname
            default_notar_nachname = profile.notar_nachname
            default_notarkammer = profile.notarkammer
            default_notarversicherung = profile.notarversicherung

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**Kanzlei-Logo**")
            logo_file = st.file_uploader("Kanzlei-Logo hochladen", type=["png", "jpg", "jpeg"], key="notar_logo_upload")
            if profile.logo:
                st.image(profile.logo, width=150)
            elif logo_file:
                st.image(logo_file, width=150)

        with col2:
            kanzleiname = st.text_input("Kanzleiname*", value=default_kanzleiname)

            col_titel, col_vorname, col_nachname = st.columns([1, 2, 2])
            with col_titel:
                notar_titel = st.text_input("Titel", value=default_notar_titel, placeholder="Dr.")
            with col_vorname:
                notar_vorname = st.text_input("Vorname*", value=default_notar_vorname)
            with col_nachname:
                notar_nachname = st.text_input("Nachname*", value=default_notar_nachname)

        st.markdown("---")
        st.markdown("### 📍 Kontaktdaten")

        adresse = st.text_input("Straße und Hausnummer*", value=default_adresse)

        col_plz, col_ort = st.columns([1, 2])
        with col_plz:
            plz = st.text_input("PLZ*", value=default_plz)
        with col_ort:
            ort = st.text_input("Ort*", value=default_ort)

        col_tel, col_fax = st.columns(2)
        with col_tel:
            telefon = st.text_input("Telefon*", value=default_telefon)
        with col_fax:
            fax = st.text_input("Fax", value=profile.fax)

        col_email, col_web = st.columns(2)
        with col_email:
            email = st.text_input("E-Mail*", value=default_email)
        with col_web:
            website = st.text_input("Website", value=default_website, help="z.B. https://www.ihre-kanzlei.de")

        st.markdown("---")
        st.markdown("### 🎨 Logo & Design")

        # Logo-Auswahl basierend auf Analyse-Daten (falls vorhanden)
        if analysis_data and analysis_data.get("logo"):
            logo_data = analysis_data.get("logo", {})
            logo_kandidaten = logo_data.get("candidates", [])

            st.info("💡 Wählen Sie ein Kanzlei-Logo aus den gefundenen URLs oder geben Sie eine eigene ein.")

            # Dropdown mit Logo-Kandidaten
            logo_url_input = st.selectbox(
                "Logo-URL auswählen:",
                options=logo_kandidaten if logo_kandidaten else [""],
                index=0,
                key="notar_logo_url_select"
            )

            # Logo-Vorschau
            if logo_url_input:
                try:
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(logo_url_input, width=150, caption="Logo-Vorschau")
                    with col2:
                        st.success("✅ Logo wird übernommen")
                        if analysis_data.get("confidence"):
                            st.caption(f"Konfidenz: {int(analysis_data['confidence'] * 100)}%")
                except:
                    st.warning("⚠️ Logo konnte nicht geladen werden. Prüfen Sie die URL.")
        else:
            # Manuelle Logo-Eingabe
            logo_url_input = st.text_input(
                "Logo-URL eingeben:",
                value=profile.logo_url if profile.logo_url else "",
                placeholder="z.B. https://www.ihre-kanzlei.de/logo.png",
                help="Aktivieren Sie oben die automatische Logo-Übernahme für Logo-Suche",
                key="notar_manual_logo_url"
            )

            if logo_url_input:
                try:
                    st.image(logo_url_input, width=150, caption="Logo-Vorschau")
                except:
                    st.warning("⚠️ Logo konnte nicht geladen werden.")

        st.markdown("---")
        st.markdown("### 📋 Zusätzliche Informationen")

        col1, col2 = st.columns(2)
        with col1:
            notarkammer = st.text_input("Notarkammer", value=default_notarkammer, placeholder="z.B. Notarkammer München")
            notarversicherung = st.text_input("Berufshaftpflichtversicherung", value=default_notarversicherung, placeholder="z.B. R+V Versicherung AG")
            handelsregister = st.text_input("Handelsregister", value=profile.handelsregister)
        with col2:
            steuernummer = st.text_input("Steuernummer", value=profile.steuernummer)
            ust_id = st.text_input("USt-IdNr.", value=profile.ust_id)

        oeffnungszeiten = st.text_area("Öffnungszeiten", value=profile.oeffnungszeiten, height=100,
                                       placeholder="Mo-Fr: 9:00 - 17:00 Uhr\nSa: Nach Vereinbarung")

        st.markdown("---")

        if st.form_submit_button("💾 Profil speichern", type="primary"):
            profile.kanzleiname = kanzleiname
            profile.notar_titel = notar_titel
            profile.notar_vorname = notar_vorname
            profile.notar_nachname = notar_nachname
            profile.adresse = adresse
            profile.plz = plz
            profile.ort = ort
            profile.telefon = telefon
            profile.fax = fax
            profile.email = email
            profile.website = website
            profile.notarkammer = notarkammer
            profile.notarversicherung = notarversicherung
            profile.handelsregister = handelsregister
            profile.steuernummer = steuernummer
            profile.ust_id = ust_id
            profile.oeffnungszeiten = oeffnungszeiten

            # Logo-Verwaltung
            if logo_file:
                profile.logo = logo_file.read()
                profile.logo_bestaetigt = True
                profile.logo_aktiviert = False

            # Logo-URL Verwaltung (aus Analyse oder manuell)
            if 'logo_url_input' in locals() and logo_url_input:
                profile.logo_url = logo_url_input
                profile.logo_bestaetigt = True
                profile.logo_aktiviert = True

            st.session_state.notar_profiles[profile.profile_id] = profile
            st.success("✅ Kanzlei-Profil erfolgreich gespeichert!")
            st.rerun()

def notar_projekte_view():
    """Projekt-Übersicht für Notar mit Fallzuweisung"""
    st.subheader("📋 Meine Projekte & Fallzuweisung")

    notar_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]

    if not projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    # Mitarbeiter-Liste für Zuweisung vorbereiten
    mitarbeiter_liste = [m for m in st.session_state.notar_mitarbeiter.values()
                        if m.notar_id == notar_id and m.aktiv]

    for projekt in projekte:
        # Zugewiesener Mitarbeiter anzeigen
        zugewiesen_icon = "👤" if projekt.zugewiesener_mitarbeiter_id else "⚪"
        zugewiesener_name = ""
        if projekt.zugewiesener_mitarbeiter_id:
            ma = st.session_state.notar_mitarbeiter.get(projekt.zugewiesener_mitarbeiter_id)
            if ma:
                zugewiesener_name = f" - Zugewiesen an: {ma.name}"

        with st.expander(f"{zugewiesen_icon} 🏘️ {projekt.name}{zugewiesener_name}", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Beschreibung:** {projekt.beschreibung}")
                if projekt.adresse:
                    st.markdown(f"**Adresse:** {projekt.adresse}")
                if projekt.kaufpreis > 0:
                    st.markdown(f"**Kaufpreis:** {projekt.kaufpreis:,.2f} €")

                # Vermittler-Status
                if projekt.vermittelt_durch_notar:
                    st.markdown("🔄 **Als Vermittler fungierend**")

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

            st.markdown("---")

            # Fallzuweisung
            st.markdown("### 👤 Fallzuweisung")

            if mitarbeiter_liste:
                col1, col2 = st.columns([3, 1])

                with col1:
                    mitarbeiter_options = {ma.name: ma.mitarbeiter_id for ma in mitarbeiter_liste}
                    mitarbeiter_options["Nicht zugewiesen (Notar)"] = ""

                    # Aktuell zugewiesener Mitarbeiter vorauswählen
                    if projekt.zugewiesener_mitarbeiter_id:
                        ma = st.session_state.notar_mitarbeiter.get(projekt.zugewiesener_mitarbeiter_id)
                        default_index = list(mitarbeiter_options.keys()).index(ma.name) if ma else 0
                    else:
                        default_index = list(mitarbeiter_options.keys()).index("Nicht zugewiesen (Notar)")

                    neuer_mitarbeiter = st.selectbox(
                        "Fall zuweisen an:",
                        options=list(mitarbeiter_options.keys()),
                        index=default_index,
                        key=f"assign_{projekt.projekt_id}"
                    )

                with col2:
                    if st.button("💾 Speichern", key=f"save_assign_{projekt.projekt_id}"):
                        neue_mitarbeiter_id = mitarbeiter_options[neuer_mitarbeiter]

                        # Alte Zuweisung entfernen
                        if projekt.zugewiesener_mitarbeiter_id:
                            alter_ma = st.session_state.notar_mitarbeiter.get(projekt.zugewiesener_mitarbeiter_id)
                            if alter_ma and projekt.projekt_id in alter_ma.zugewiesene_faelle:
                                alter_ma.zugewiesene_faelle.remove(projekt.projekt_id)
                                st.session_state.notar_mitarbeiter[alter_ma.mitarbeiter_id] = alter_ma

                        # Neue Zuweisung setzen
                        projekt.zugewiesener_mitarbeiter_id = neue_mitarbeiter_id
                        st.session_state.projekte[projekt.projekt_id] = projekt

                        # Zu zugewiesene_faelle hinzufügen
                        if neue_mitarbeiter_id:
                            neuer_ma = st.session_state.notar_mitarbeiter.get(neue_mitarbeiter_id)
                            if neuer_ma and projekt.projekt_id not in neuer_ma.zugewiesene_faelle:
                                neuer_ma.zugewiesene_faelle.append(projekt.projekt_id)
                                st.session_state.notar_mitarbeiter[neue_mitarbeiter_id] = neuer_ma

                            # Benachrichtigung an Mitarbeiter
                            notif_id = f"notif_{len(st.session_state.notifications)}"
                            notification = Notification(
                                notification_id=notif_id,
                                user_id=neue_mitarbeiter_id,
                                titel="📋 Neuer Fall zugewiesen",
                                nachricht=f"Ihnen wurde der Fall '{projekt.name}' zur primären Bearbeitung zugewiesen.",
                                typ="Fallzuweisung",
                                timestamp=datetime.now()
                            )
                            st.session_state.notifications[notif_id] = notification

                            st.success(f"Fall wurde an {neuer_mitarbeiter} zugewiesen!")
                        else:
                            st.success("Zuweisung wurde entfernt!")

                        st.rerun()

                # Aktuell zugewiesene Information
                if projekt.zugewiesener_mitarbeiter_id:
                    ma = st.session_state.notar_mitarbeiter.get(projekt.zugewiesener_mitarbeiter_id)
                    if ma:
                        st.info(f"✅ Dieser Fall ist primär {ma.name} ({ma.rolle}) zugewiesen.")
                else:
                    st.info("⚪ Dieser Fall ist keinem Mitarbeiter zugewiesen (Sie sind verantwortlich).")
            else:
                st.info("Keine Mitarbeiter verfügbar. Erstellen Sie Mitarbeiter im Tab 'Mitarbeiter'.")

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

def notar_makler_netzwerk_view():
    """Makler-Netzwerk Verwaltung für Notar"""
    st.subheader("🤝 Makler-Netzwerk")

    notar_id = st.session_state.current_user.user_id

    # Netzwerk-Mitglieder anzeigen
    netzwerk_mitglieder = [m for m in st.session_state.makler_netzwerk.values() if m.notar_id == notar_id]

    if netzwerk_mitglieder:
        st.markdown("### 👥 Meine Makler-Netzwerk")

        # Sortiere nach Status: Aktiv zuerst, dann nach letzter Empfehlung
        aktive = [m for m in netzwerk_mitglieder if m.status == "Aktiv"]
        eingeladen = [m for m in netzwerk_mitglieder if m.status == "Eingeladen"]
        inaktive = [m for m in netzwerk_mitglieder if m.status == "Inaktiv"]

        # Aktive Makler
        if aktive:
            st.markdown("#### ✅ Aktive Makler")
            for mitglied in aktive:
                makler = st.session_state.users.get(mitglied.makler_id)
                if not makler:
                    continue

                # Status-Indikator berechnen
                hat_aktive_projekte = mitglied.anzahl_aktive_projekte > 0

                # Zeit seit letzter Empfehlung
                if mitglied.letzte_empfehlung_am:
                    tage_seit_empfehlung = (datetime.now() - mitglied.letzte_empfehlung_am).days
                    if tage_seit_empfehlung <= 30:
                        status_farbe = "🟢"  # Grün: Aktiv in letzten 30 Tagen
                        status_text = f"Letzte Empfehlung vor {tage_seit_empfehlung} Tagen"
                    elif tage_seit_empfehlung <= 90:
                        status_farbe = "🟡"  # Gelb: 30-90 Tage
                        status_text = f"Letzte Empfehlung vor {tage_seit_empfehlung} Tagen"
                    else:
                        status_farbe = "🔴"  # Rot: Länger als 90 Tage
                        status_text = f"Letzte Empfehlung vor {tage_seit_empfehlung} Tagen"
                else:
                    status_farbe = "🔴"  # Rot: Noch keine Empfehlung
                    status_text = "Noch keine Empfehlung abgegeben"

                # Aktive Projekte Indikator
                if hat_aktive_projekte:
                    projekt_status = f"🟢 {mitglied.anzahl_aktive_projekte} aktive(s) Projekt(e)"
                else:
                    projekt_status = "⚪ Keine aktiven Projekte"

                with st.expander(f"{status_farbe} {makler.name} - {projekt_status}", expanded=False):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Name:** {makler.name}")
                        st.write(f"**E-Mail:** {makler.email}")
                        st.write(f"**Beigetreten am:** {mitglied.beigetreten_am.strftime('%d.%m.%Y %H:%M') if mitglied.beigetreten_am else 'N/A'}")

                    with col2:
                        st.write(f"**Status:** {status_text}")
                        st.write(f"**Aktive Projekte:** {mitglied.anzahl_aktive_projekte}")
                        st.write(f"**Empfehlungen gesamt:** {mitglied.anzahl_empfehlungen_gesamt}")

                    # Projekte mit Empfehlung anzeigen
                    st.markdown("---")
                    st.markdown("**Projekte mit Empfehlung an mich:**")
                    empfohlene_projekte = [p for p in st.session_state.projekte.values()
                                          if p.makler_id == mitglied.makler_id
                                          and p.empfohlener_notar_id == notar_id]

                    if empfohlene_projekte:
                        for projekt in empfohlene_projekte:
                            status_icon = "🟢" if projekt.status == "Aktiv" else "⚪"
                            st.write(f"{status_icon} {projekt.name} - {projekt.ort}")
                    else:
                        st.info("Keine Projekte mit Empfehlung")

                    # Notizen
                    st.markdown("---")
                    st.markdown("**Notizen:**")
                    neue_notizen = st.text_area("Notizen bearbeiten:", value=mitglied.notizen,
                                                key=f"notizen_{mitglied.netzwerk_id}", height=100)

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Notizen speichern", key=f"save_notes_{mitglied.netzwerk_id}"):
                            mitglied.notizen = neue_notizen
                            st.session_state.makler_netzwerk[mitglied.netzwerk_id] = mitglied
                            st.success("Notizen gespeichert!")
                            st.rerun()

                    with col2:
                        if st.button("🚫 Deaktivieren", key=f"deact_netzwerk_{mitglied.netzwerk_id}"):
                            mitglied.status = "Inaktiv"
                            st.session_state.makler_netzwerk[mitglied.netzwerk_id] = mitglied
                            st.success("Makler wurde deaktiviert!")
                            st.rerun()

            st.markdown("---")

        # Eingeladene Makler
        if eingeladen:
            st.markdown("#### 📨 Eingeladene Makler (ausstehend)")
            for mitglied in eingeladen:
                makler = st.session_state.users.get(mitglied.makler_id)
                if not makler:
                    continue

                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"📧 **{makler.name}** ({makler.email})")
                with col2:
                    st.write(f"Eingeladen am: {mitglied.eingeladen_am.strftime('%d.%m.%Y')}")
                with col3:
                    if st.button("❌", key=f"cancel_{mitglied.netzwerk_id}", help="Einladung zurückziehen"):
                        del st.session_state.makler_netzwerk[mitglied.netzwerk_id]
                        st.success("Einladung zurückgezogen!")
                        st.rerun()

            st.markdown("---")

        # Inaktive Makler
        if inaktive:
            st.markdown("#### 🚫 Inaktive Makler")
            for mitglied in inaktive:
                makler = st.session_state.users.get(mitglied.makler_id)
                if not makler:
                    continue

                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"🚫 **{makler.name}** ({makler.email})")
                with col2:
                    if st.button("✅ Reaktivieren", key=f"react_{mitglied.netzwerk_id}"):
                        mitglied.status = "Aktiv"
                        st.session_state.makler_netzwerk[mitglied.netzwerk_id] = mitglied
                        st.success("Makler reaktiviert!")
                        st.rerun()

            st.markdown("---")
    else:
        st.info("Noch keine Makler im Netzwerk.")

    # Neuen Makler einladen
    st.markdown("### ➕ Makler zum Netzwerk einladen")

    # Liste aller Makler die noch nicht im Netzwerk sind
    alle_makler = [u for u in st.session_state.users.values() if u.role == UserRole.MAKLER.value]
    makler_im_netzwerk = [m.makler_id for m in netzwerk_mitglieder]
    verfuegbare_makler = [m for m in alle_makler if m.user_id not in makler_im_netzwerk]

    if verfuegbare_makler:
        with st.form("makler_einladen"):
            makler_options = {f"{m.name} ({m.email})": m.user_id for m in verfuegbare_makler}

            ausgewaehlter_makler = st.selectbox(
                "Makler auswählen:",
                options=list(makler_options.keys())
            )

            einladungs_notiz = st.text_area(
                "Persönliche Nachricht (optional):",
                placeholder="Ich würde mich freuen, Sie in meinem Netzwerk begrüßen zu dürfen...",
                height=100
            )

            if st.form_submit_button("📨 Einladung versenden", type="primary"):
                if ausgewaehlter_makler:
                    makler_id = makler_options[ausgewaehlter_makler]
                    netzwerk_id = f"netzwerk_{len(st.session_state.makler_netzwerk)}"

                    neues_mitglied = MaklerNetzwerkMitglied(
                        netzwerk_id=netzwerk_id,
                        notar_id=notar_id,
                        makler_id=makler_id,
                        eingeladen_am=datetime.now(),
                        status="Eingeladen",
                        notizen=einladungs_notiz
                    )

                    st.session_state.makler_netzwerk[netzwerk_id] = neues_mitglied

                    # Benachrichtigung an Makler senden
                    notification_id = f"notif_{len(st.session_state.notifications)}"
                    notification = Notification(
                        notification_id=notification_id,
                        user_id=makler_id,
                        titel="🤝 Netzwerk-Einladung",
                        nachricht=f"Sie wurden von {st.session_state.current_user.name} (Notar) eingeladen, dem Netzwerk beizutreten.",
                        typ="Netzwerk",
                        timestamp=datetime.now()
                    )
                    st.session_state.notifications[notification_id] = notification

                    st.success(f"✅ Einladung an {ausgewaehlter_makler} wurde versendet!")
                    st.rerun()
    else:
        st.info("Alle verfügbaren Makler sind bereits im Netzwerk oder eingeladen.")

    # Statistiken
    st.markdown("---")
    st.markdown("### 📊 Netzwerk-Statistiken")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        aktive_count = len([m for m in netzwerk_mitglieder if m.status == "Aktiv"])
        st.metric("Aktive Makler", aktive_count)
    with col2:
        eingeladen_count = len([m for m in netzwerk_mitglieder if m.status == "Eingeladen"])
        st.metric("Offene Einladungen", eingeladen_count)
    with col3:
        gesamt_empfehlungen = sum([m.anzahl_empfehlungen_gesamt for m in netzwerk_mitglieder])
        st.metric("Empfehlungen gesamt", gesamt_empfehlungen)
    with col4:
        aktive_projekte_gesamt = sum([m.anzahl_aktive_projekte for m in netzwerk_mitglieder])
        st.metric("Aktive Projekte gesamt", aktive_projekte_gesamt)

def notar_vermittler_view():
    """Notar als Vermittler - Direkte Käufer-Kontakte"""
    st.subheader("🔄 Vermittler-Funktion")

    st.info("💡 Wenn sich Käufer direkt bei Ihnen melden, können Sie hier alle notwendigen Daten erfassen und als Vermittler fungieren.")

    notar_id = st.session_state.current_user.user_id

    # Bestehende Vermittler-Projekte anzeigen
    vermittler_projekte = [p for p in st.session_state.projekte.values()
                          if p.notar_id == notar_id and p.vermittelt_durch_notar]

    if vermittler_projekte:
        st.markdown("### 📋 Meine Vermittler-Projekte")

        for projekt in vermittler_projekte:
            status_icon = "🟢" if projekt.status == "Aktiv" else "⚪"

            with st.expander(f"{status_icon} {projekt.name} - {projekt.ort}", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Käufer-Informationen:**")
                    kaeufer = st.session_state.users.get(projekt.kaeufer_id)
                    if kaeufer:
                        st.write(f"👤 {kaeufer.name}")
                        st.write(f"📧 {kaeufer.email}")

                    st.markdown("---")
                    st.markdown("**Verkäufer-Informationen:**")
                    verkaeufer = st.session_state.users.get(projekt.verkaeufer_id)
                    if verkaeufer:
                        st.write(f"👤 {verkaeufer.name}")
                        st.write(f"📧 {verkaeufer.email}")

                with col2:
                    st.markdown("**Immobilien-Details:**")
                    st.write(f"**Adresse:** {projekt.adresse}")
                    st.write(f"**Ort:** {projekt.ort}")
                    st.write(f"**Kaufpreis:** {projekt.kaufpreis:,.2f} €")
                    st.write(f"**Typ:** {projekt.immobilien_typ}")

                st.markdown("---")
                st.markdown(f"**Status:** {projekt.status}")
                st.markdown(f"**Erstellt am:** {projekt.created_at.strftime('%d.%m.%Y %H:%M')}")

                # Zugewiesener Mitarbeiter
                if projekt.zugewiesener_mitarbeiter_id:
                    mitarbeiter = st.session_state.notar_mitarbeiter.get(projekt.zugewiesener_mitarbeiter_id)
                    if mitarbeiter:
                        st.write(f"**Zugewiesener Mitarbeiter:** {mitarbeiter.name}")

        st.markdown("---")

    # Neues Vermittler-Projekt erstellen
    st.markdown("### ➕ Neues Projekt als Vermittler anlegen")

    with st.form("neues_vermittler_projekt"):
        st.markdown("#### 👤 Käufer-Daten")
        col1, col2 = st.columns(2)

        with col1:
            kaeufer_name = st.text_input("Name des Käufers*")
            kaeufer_email = st.text_input("E-Mail des Käufers*")
            kaeufer_telefon = st.text_input("Telefon des Käufers")

        with col2:
            kaeufer_adresse = st.text_input("Adresse des Käufers")
            kaeufer_budget = st.number_input("Budget des Käufers (€)", min_value=0, value=0, step=10000)
            kaeufer_finanzierung = st.selectbox("Finanzierung benötigt?", ["Ja", "Nein"])

        st.markdown("---")
        st.markdown("#### 👤 Verkäufer-Daten")

        col1, col2 = st.columns(2)

        with col1:
            verkaeufer_name = st.text_input("Name des Verkäufers*")
            verkaeufer_email = st.text_input("E-Mail des Verkäufers*")
            verkaeufer_telefon = st.text_input("Telefon des Verkäufers")

        with col2:
            verkaeufer_adresse = st.text_input("Adresse des Verkäufers")
            verkaeufer_eigentuemer_seit = st.date_input("Eigentümer seit", value=None)

        st.markdown("---")
        st.markdown("#### 🏘️ Immobilien-Daten")

        col1, col2 = st.columns(2)

        with col1:
            immobilien_adresse = st.text_input("Adresse der Immobilie*")
            immobilien_ort = st.text_input("Ort*")
            immobilien_plz = st.text_input("PLZ*")
            immobilien_typ = st.selectbox("Immobilien-Typ*", [t.value for t in ImmobilienTyp])

        with col2:
            kaufpreis = st.number_input("Kaufpreis (€)*", min_value=0, value=0, step=10000)
            wohnflaeche = st.number_input("Wohnfläche (m²)", min_value=0.0, value=0.0, step=0.1)
            grundstuecksflaeche = st.number_input("Grundstücksfläche (m²)", min_value=0.0, value=0.0, step=0.1)
            baujahr = st.number_input("Baujahr", min_value=1800, max_value=datetime.now().year, value=2000)

        col1, col2 = st.columns(2)

        with col1:
            zimmer = st.number_input("Zimmer", min_value=1, max_value=20, value=3)
            badezimmer = st.number_input("Badezimmer", min_value=1, max_value=10, value=1)

        with col2:
            parkplaetze = st.number_input("Parkplätze", min_value=0, max_value=10, value=0)
            balkon_terrasse = st.checkbox("Balkon/Terrasse vorhanden")

        beschreibung = st.text_area("Beschreibung der Immobilie", height=100)

        st.markdown("---")
        st.markdown("#### 📋 Projekt-Details")

        projekt_name = st.text_input("Projekt-Name*", value=f"Vermittlung - {immobilien_ort if immobilien_ort else 'Neues Projekt'}")

        # Mitarbeiter zuweisen (optional)
        mitarbeiter_liste = [m for m in st.session_state.notar_mitarbeiter.values()
                            if m.notar_id == notar_id and m.aktiv]

        if mitarbeiter_liste:
            mitarbeiter_options = {m.name: m.mitarbeiter_id for m in mitarbeiter_liste}
            mitarbeiter_options["Keiner"] = ""

            zugewiesener_mitarbeiter = st.selectbox(
                "Mitarbeiter zuweisen (optional):",
                options=list(mitarbeiter_options.keys())
            )
        else:
            zugewiesener_mitarbeiter = "Keiner"

        notizen = st.text_area("Notizen zum Projekt", height=100)

        if st.form_submit_button("📝 Projekt erstellen", type="primary"):
            if (kaeufer_name and kaeufer_email and verkaeufer_name and verkaeufer_email
                and immobilien_adresse and immobilien_ort and immobilien_plz and kaufpreis > 0):

                # Käufer-Account erstellen oder finden
                kaeufer_id = None
                for user in st.session_state.users.values():
                    if user.email == kaeufer_email:
                        kaeufer_id = user.user_id
                        break

                if not kaeufer_id:
                    kaeufer_id = f"kaeufer_{len([u for u in st.session_state.users.values() if u.role == UserRole.KAEUFER.value])}"
                    kaeufer_user = User(
                        user_id=kaeufer_id,
                        name=kaeufer_name,
                        email=kaeufer_email,
                        role=UserRole.KAEUFER.value,
                        password_hash=hash_password("temp123"),  # Temporäres Passwort
                        onboarding_complete=False
                    )
                    st.session_state.users[kaeufer_id] = kaeufer_user

                # Verkäufer-Account erstellen oder finden
                verkaeufer_id = None
                for user in st.session_state.users.values():
                    if user.email == verkaeufer_email:
                        verkaeufer_id = user.user_id
                        break

                if not verkaeufer_id:
                    verkaeufer_id = f"verkaeufer_{len([u for u in st.session_state.users.values() if u.role == UserRole.VERKAEUFER.value])}"
                    verkaeufer_user = User(
                        user_id=verkaeufer_id,
                        name=verkaeufer_name,
                        email=verkaeufer_email,
                        role=UserRole.VERKAEUFER.value,
                        password_hash=hash_password("temp123"),  # Temporäres Passwort
                        onboarding_complete=False
                    )
                    st.session_state.users[verkaeufer_id] = verkaeufer_user

                # Projekt erstellen
                projekt_id = f"projekt_{len(st.session_state.projekte)}"

                neues_projekt = Projekt(
                    projekt_id=projekt_id,
                    name=projekt_name,
                    makler_id="",  # Kein Makler, da Notar vermittelt
                    kaeufer_id=kaeufer_id,
                    verkaeufer_id=verkaeufer_id,
                    finanzierer_id="",  # Wird später hinzugefügt
                    notar_id=notar_id,
                    adresse=immobilien_adresse,
                    ort=immobilien_ort,
                    plz=immobilien_plz,
                    kaufpreis=kaufpreis,
                    immobilien_typ=immobilien_typ,
                    wohnflaeche=wohnflaeche,
                    grundstuecksflaeche=grundstuecksflaeche,
                    baujahr=baujahr,
                    zimmer=zimmer,
                    badezimmer=badezimmer,
                    parkplaetze=parkplaetze,
                    balkon_terrasse=balkon_terrasse,
                    beschreibung=beschreibung,
                    status="Aktiv",
                    vermittelt_durch_notar=True,  # Markierung als Vermittler-Projekt
                    zugewiesener_mitarbeiter_id=mitarbeiter_options.get(zugewiesener_mitarbeiter, "") if mitarbeiter_liste else ""
                )

                st.session_state.projekte[projekt_id] = neues_projekt

                # Projekte zu Nutzer-Profilen hinzufügen
                st.session_state.users[kaeufer_id].projekt_ids.append(projekt_id)
                st.session_state.users[verkaeufer_id].projekt_ids.append(projekt_id)

                # Timeline-Event erstellen
                event_id = f"event_{len(st.session_state.timeline_events)}"
                event = TimelineEvent(
                    event_id=event_id,
                    projekt_id=projekt_id,
                    titel="🔄 Projekt als Vermittler angelegt",
                    beschreibung=f"Notar {st.session_state.current_user.name} hat das Projekt als Vermittler angelegt.",
                    kategorie="Projektstart",
                    status="Abgeschlossen",
                    verantwortlich=notar_id,
                    timestamp=datetime.now()
                )
                st.session_state.timeline_events[event_id] = event

                # Benachrichtigungen an Käufer und Verkäufer
                for user_id in [kaeufer_id, verkaeufer_id]:
                    notif_id = f"notif_{len(st.session_state.notifications)}"
                    notification = Notification(
                        notification_id=notif_id,
                        user_id=user_id,
                        titel="🔄 Neues Projekt angelegt",
                        nachricht=f"Ein neues Projekt '{projekt_name}' wurde für Sie angelegt. Notar {st.session_state.current_user.name} fungiert als Vermittler.",
                        typ="Projekt",
                        timestamp=datetime.now()
                    )
                    st.session_state.notifications[notif_id] = notification

                st.success(f"✅ Projekt '{projekt_name}' wurde erfolgreich als Vermittler-Projekt angelegt!")
                st.info(f"🔑 Temporäre Zugangsdaten:\nKäufer: {kaeufer_email} / temp123\nVerkäufer: {verkaeufer_email} / temp123")
                st.rerun()
            else:
                st.error("Bitte füllen Sie alle Pflichtfelder (*) aus!")

    # Übersicht aller Daten für Vermittler-Projekte
    if vermittler_projekte:
        st.markdown("---")
        st.markdown("### 📊 Übersicht aller Daten")

        for projekt in vermittler_projekte:
            with st.expander(f"📋 Vollständige Datenübersicht: {projekt.name}", expanded=False):
                tabs = st.tabs(["Käufer", "Verkäufer", "Immobilie", "Dokumente", "Finanzierung"])

                with tabs[0]:
                    kaeufer = st.session_state.users.get(projekt.kaeufer_id)
                    if kaeufer:
                        st.markdown("**Käufer-Daten:**")
                        st.write(f"**Name:** {kaeufer.name}")
                        st.write(f"**E-Mail:** {kaeufer.email}")
                        st.write(f"**User ID:** {kaeufer.user_id}")
                        st.write(f"**Onboarding:** {'Abgeschlossen' if kaeufer.onboarding_complete else 'Ausstehend'}")

                with tabs[1]:
                    verkaeufer = st.session_state.users.get(projekt.verkaeufer_id)
                    if verkaeufer:
                        st.markdown("**Verkäufer-Daten:**")
                        st.write(f"**Name:** {verkaeufer.name}")
                        st.write(f"**E-Mail:** {verkaeufer.email}")
                        st.write(f"**User ID:** {verkaeufer.user_id}")
                        st.write(f"**Onboarding:** {'Abgeschlossen' if verkaeufer.onboarding_complete else 'Ausstehend'}")

                        # Verkäufer-Dokumente
                        st.markdown("---")
                        st.markdown("**Hochgeladene Dokumente:**")
                        vk_dokumente = [d for d in st.session_state.verkaeufer_dokumente.values()
                                       if d.projekt_id == projekt.projekt_id]
                        if vk_dokumente:
                            for dok in vk_dokumente:
                                st.write(f"📄 {dok.dateiname} ({dok.dokument_typ})")
                        else:
                            st.info("Noch keine Dokumente hochgeladen")

                with tabs[2]:
                    st.markdown("**Immobilien-Details:**")
                    st.write(f"**Adresse:** {projekt.adresse}")
                    st.write(f"**PLZ/Ort:** {projekt.plz} {projekt.ort}")
                    st.write(f"**Typ:** {projekt.immobilien_typ}")
                    st.write(f"**Kaufpreis:** {projekt.kaufpreis:,.2f} €")
                    st.write(f"**Wohnfläche:** {projekt.wohnflaeche} m²")
                    st.write(f"**Grundstücksfläche:** {projekt.grundstuecksflaeche} m²")
                    st.write(f"**Baujahr:** {projekt.baujahr}")
                    st.write(f"**Zimmer:** {projekt.zimmer}")
                    st.write(f"**Badezimmer:** {projekt.badezimmer}")
                    st.write(f"**Parkplätze:** {projekt.parkplaetze}")
                    st.write(f"**Balkon/Terrasse:** {'Ja' if projekt.balkon_terrasse else 'Nein'}")

                    if projekt.beschreibung:
                        st.markdown("**Beschreibung:**")
                        st.write(projekt.beschreibung)

                with tabs[3]:
                    st.markdown("**Dokumente:**")
                    # Legal Documents
                    legal_docs = [d for d in st.session_state.legal_documents.values()
                                 if d.projekt_id == projekt.projekt_id]
                    if legal_docs:
                        for doc in legal_docs:
                            st.write(f"⚖️ {doc.dokument_typ} - {doc.status}")
                    else:
                        st.info("Noch keine rechtlichen Dokumente")

                with tabs[4]:
                    st.markdown("**Finanzierung:**")
                    financing = [f for f in st.session_state.financing_offers.values()
                               if f.projekt_id == projekt.projekt_id]
                    if financing:
                        for fin in financing:
                            st.write(f"💰 {fin.bank_name}: {fin.darlehenssumme:,.2f} € - {fin.status}")
                    else:
                        st.info("Noch keine Finanzierungsangebote")

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
    """Termin-Verwaltung für Notar"""
    st.subheader("📅 Notartermine")

    notar_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]

    if not projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            if projekt.notartermin:
                st.success(f"✅ Termin vereinbart: {projekt.notartermin.strftime('%d.%m.%Y %H:%M')}")

                if st.button("🔄 Termin ändern", key=f"change_termin_{projekt.projekt_id}"):
                    st.session_state[f"edit_termin_{projekt.projekt_id}"] = True
                    st.rerun()
            else:
                st.info("Noch kein Termin vereinbart")
                st.session_state[f"edit_termin_{projekt.projekt_id}"] = True

            if st.session_state.get(f"edit_termin_{projekt.projekt_id}", False):
                with st.form(f"termin_form_{projekt.projekt_id}"):
                    termin_datum = st.date_input("Datum", value=date.today() + timedelta(days=14))
                    termin_zeit = st.time_input("Uhrzeit", value=datetime.now().replace(hour=10, minute=0).time())

                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("💾 Termin speichern", type="primary")
                    with col2:
                        cancel = st.form_submit_button("❌ Abbrechen")

                    if submit:
                        termin_dt = datetime.combine(termin_datum, termin_zeit)
                        projekt.notartermin = termin_dt

                        # Timeline aktualisieren
                        for event_id in projekt.timeline_events:
                            event = st.session_state.timeline_events.get(event_id)
                            if event and event.titel == "Notartermin vereinbaren" and not event.completed:
                                event.completed = True
                                event.completed_at = datetime.now()
                        update_projekt_status(projekt.projekt_id)

                        # Benachrichtigungen
                        for kid in projekt.kaeufer_ids:
                            create_notification(kid, "Notartermin vereinbart", f"Notartermin für {projekt.name}: {termin_dt.strftime('%d.%m.%Y %H:%M')}", NotificationType.SUCCESS.value)
                        for vid in projekt.verkaeufer_ids:
                            create_notification(vid, "Notartermin vereinbart", f"Notartermin für {projekt.name}: {termin_dt.strftime('%d.%m.%Y %H:%M')}", NotificationType.SUCCESS.value)

                        st.session_state[f"edit_termin_{projekt.projekt_id}"] = False
                        st.success("✅ Termin gespeichert!")
                        st.rerun()

                    if cancel:
                        st.session_state[f"edit_termin_{projekt.projekt_id}"] = False
                        st.rerun()

def notar_auftraege_view():
    """Notarauftrags-Workflow (Vorbereitet für zukünftige Erweiterung)"""
    st.subheader("⚖️ Notaraufträge & Rechtliche Prüfung")

    st.info("💡 Dieser Bereich befindet sich in Vorbereitung und wird erweitert, sobald weitere Anforderungen definiert sind.")

    notar_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if p.notar_id == notar_id]

    st.markdown("""
    ### 📋 Geplante Funktionen:
    - ⚖️ Auftragseingänge erfassen und verwalten
    - 🔍 Rechtliche Prüfung von Verträgen und Unterlagen
    - 📝 Vertragsentwürfe erstellen und freigeben
    - 💰 Kostenvoranschläge und Abrechnung
    - 📅 Terminkoordination mit allen Beteiligten
    - 📄 Dokumenten-Workflow mit Mitarbeitern
    - ✅ Freigabe-Prozesse und Genehmigungen
    """)

    st.markdown("---")

    # Bestehende Aufträge anzeigen (wenn vorhanden)
    auftraege = [a for a in st.session_state.notar_auftraege.values() if a.notar_id == notar_id]

    if auftraege:
        st.markdown("### 📊 Aktuelle Aufträge")
        for auftrag in auftraege:
            projekt = st.session_state.projekte.get(auftrag.projekt_id)
            projekt_name = projekt.name if projekt else "Unbekanntes Projekt"

            status_icon = {
                "Eingegangen": "📥",
                "In Prüfung": "🔍",
                "Freigegeben": "✅",
                "Abgeschlossen": "✔️"
            }.get(auftrag.status, "📋")

            with st.expander(f"{status_icon} {auftrag.vertragsart} - {projekt_name}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Status:** {auftrag.status}")
                    st.write(f"**Vertragsart:** {auftrag.vertragsart}")
                    st.write(f"**Auftraggeber:** {auftrag.auftraggeber_typ}")
                    st.write(f"**Erstellt:** {auftrag.created_at.strftime('%d.%m.%Y')}")
                with col2:
                    st.write(f"**Rechtlich geprüft:** {'✅ Ja' if auftrag.rechtlich_geprueft else '⏳ Ausstehend'}")
                    st.write(f"**Unterlagen vollständig:** {'✅ Ja' if auftrag.unterlagen_vollstaendig else '⏳ Nein'}")
                    st.write(f"**Entwurf erstellt:** {'✅ Ja' if auftrag.entwurf_erstellt else '⏳ Nein'}")
                    if auftrag.geschaetzte_kosten > 0:
                        st.write(f"**Geschätzte Kosten:** {auftrag.geschaetzte_kosten:,.2f} €")

                if auftrag.notizen:
                    st.markdown("**Notizen:**")
                    st.info(auftrag.notizen)
    else:
        st.info("Noch keine Aufträge vorhanden.")

    st.markdown("---")

    # Platzhalter für neuen Auftrag erstellen
    with st.expander("➕ Neuen Auftrag erstellen (Platzhalter)", expanded=False):
        st.info("Diese Funktion wird erweitert, sobald die genauen Anforderungen definiert sind.")

        with st.form("neuer_auftrag_form"):
            col1, col2 = st.columns(2)
            with col1:
                projekt_options = {p.name: p.projekt_id for p in projekte}
                if projekt_options:
                    selected_projekt_name = st.selectbox("Projekt auswählen", list(projekt_options.keys()))
                    selected_projekt_id = projekt_options[selected_projekt_name]
                else:
                    st.warning("Keine Projekte verfügbar")
                    selected_projekt_id = None

                vertragsart = st.selectbox(
                    "Vertragsart",
                    ["Kaufvertrag", "Grundschuld", "Vollmacht", "Beglaubigung", "Sonstiges"]
                )

            with col2:
                auftraggeber_typ = st.selectbox("Auftraggeber", ["Käufer", "Verkäufer", "Makler", "Bank"])
                geschaetzte_kosten = st.number_input("Geschätzte Kosten (€)", min_value=0.0, step=100.0)

            notizen = st.text_area("Notizen / Bemerkungen", height=100)

            submit = st.form_submit_button("💾 Auftrag erstellen", type="primary")

            if submit and selected_projekt_id:
                auftrag_id = f"auftrag_{len(st.session_state.notar_auftraege)}"
                auftrag = NotarAuftrag(
                    auftrag_id=auftrag_id,
                    projekt_id=selected_projekt_id,
                    notar_id=notar_id,
                    vertragsart=vertragsart,
                    auftraggeber_typ=auftraggeber_typ,
                    geschaetzte_kosten=geschaetzte_kosten,
                    notizen=notizen
                )
                st.session_state.notar_auftraege[auftrag_id] = auftrag
                st.success(f"✅ Auftrag '{vertragsart}' erstellt!")
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
    tab_labels = ["📊 Timeline", "📋 Meine Fälle", "👥 Vertretung"]

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

    # Vertretung - Fälle anderer Mitarbeiter (immer verfügbar)
    with tabs[tab_index]:
        st.subheader("👥 Vertretung - Fälle von Kollegen")

        # Alle anderen Mitarbeiter desselben Notars finden
        alle_mitarbeiter = [m for m in st.session_state.notar_mitarbeiter.values()
                           if m.notar_id == mitarbeiter.notar_id
                           and m.mitarbeiter_id != mitarbeiter.mitarbeiter_id
                           and m.aktiv]

        if not alle_mitarbeiter:
            st.info("Keine anderen Mitarbeiter vorhanden.")
        else:
            st.info("💡 Hier sehen Sie alle Fälle, die Ihren Kollegen zugewiesen sind, für den Fall dass Sie sie vertreten müssen.")

            for kollege in alle_mitarbeiter:
                if kollege.zugewiesene_faelle:
                    st.markdown(f"### 👤 {kollege.name} ({kollege.rolle})")
                    st.write(f"Zugewiesene Fälle: {len(kollege.zugewiesene_faelle)}")

                    for projekt_id in kollege.zugewiesene_faelle:
                        projekt = st.session_state.projekte.get(projekt_id)
                        if projekt:
                            with st.expander(f"🏘️ {projekt.name}", expanded=False):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown(f"**Beschreibung:** {projekt.beschreibung}")
                                    if projekt.adresse:
                                        st.markdown(f"**Adresse:** {projekt.adresse}")
                                    if projekt.kaufpreis > 0:
                                        st.markdown(f"**Kaufpreis:** {projekt.kaufpreis:,.2f} €")

                                    st.markdown(f"**Status:** {projekt.status}")

                                    # Vermittler-Status
                                    if projekt.vermittelt_durch_notar:
                                        st.markdown("🔄 **Als Vermittler**")

                                with col2:
                                    st.markdown("**Parteien:**")
                                    for kid in projekt.kaeufer_ids:
                                        kaeufer = st.session_state.users.get(kid)
                                        if kaeufer:
                                            st.write(f"🏠 Käufer: {kaeufer.name}")
                                            st.write(f"   📧 {kaeufer.email}")

                                    for vid in projekt.verkaeufer_ids:
                                        verkaeufer = st.session_state.users.get(vid)
                                        if verkaeufer:
                                            st.write(f"🏡 Verkäufer: {verkaeufer.name}")
                                            st.write(f"   📧 {verkaeufer.email}")

                                st.markdown("---")

                                # Checklisten Status (falls berechtigt)
                                if mitarbeiter.kann_checklisten_bearbeiten:
                                    projekt_checklists = [c for c in st.session_state.notar_checklists.values()
                                                         if c.projekt_id == projekt_id]

                                    if projekt_checklists:
                                        st.markdown("**Checklisten:**")
                                        for checklist in projekt_checklists:
                                            completed_count = len([i for i in checklist.items if i["completed"]])
                                            total_count = len(checklist.items)
                                            progress = (completed_count / total_count * 100) if total_count > 0 else 0
                                            st.write(f"📋 {checklist.checklist_typ}: {completed_count}/{total_count} ({progress:.0f}%)")

                                # Dokumente (falls berechtigt)
                                if mitarbeiter.kann_dokumente_freigeben:
                                    legal_docs = [d for d in st.session_state.legal_documents.values()
                                                 if d.projekt_id == projekt_id]

                                    if legal_docs:
                                        st.markdown("**Rechtliche Dokumente:**")
                                        for doc in legal_docs:
                                            st.write(f"⚖️ {doc.dokument_typ}: {doc.status}")

                                # Termine (falls berechtigt)
                                if mitarbeiter.kann_termine_verwalten:
                                    st.markdown("**Termine:**")
                                    if projekt.notartermin:
                                        st.write(f"📅 Notartermin: {projekt.notartermin.strftime('%d.%m.%Y %H:%M')}")
                                    else:
                                        st.write("📅 Noch kein Termin vereinbart")

                    st.markdown("---")

            # Statistik
            gesamt_faelle = sum([len(m.zugewiesene_faelle) for m in alle_mitarbeiter])
            if gesamt_faelle > 0:
                st.markdown("---")
                st.markdown("### 📊 Vertretungs-Statistik")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Fälle von Kollegen", gesamt_faelle)
                with col2:
                    st.metric("Meine Fälle", len(mitarbeiter.zugewiesene_faelle))

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

def main():
    """Hauptanwendung"""
    st.set_page_config(
        page_title="Immobilien-Transaktionsplattform",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session_state()

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
