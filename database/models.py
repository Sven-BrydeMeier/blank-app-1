"""
SQLAlchemy-Modelle für die Immobilien-Transaktionsplattform

Dieses Modul definiert alle Datenbankmodelle für:
- Nutzer & Authentifizierung
- Immobilien & Projekte
- Preisverhandlungen & ML-Training
- Dokumente & OCR
- Analytics & Interaktionen
- Marktdaten
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
import enum

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, Date,
    ForeignKey, Enum, JSON, Numeric, UniqueConstraint, Index, LargeBinary
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

Base = declarative_base()


# ==================== ENUMS ====================

class UserRole(enum.Enum):
    """Benutzerrollen in der Plattform"""
    MAKLER = "makler"
    KAEUFER = "kaeufer"
    VERKAEUFER = "verkaeufer"
    NOTAR = "notar"
    FINANZIERER = "finanzierer"
    MITARBEITER = "mitarbeiter"
    ADMIN = "admin"


class ProjektStatus(enum.Enum):
    """Status eines Immobilienprojekts"""
    VORBEREITUNG = "vorbereitung"
    VERMARKTUNG = "vermarktung"
    RESERVIERT = "reserviert"
    FINANZIERUNG = "finanzierung"
    NOTARTERMIN = "notartermin"
    ABGESCHLOSSEN = "abgeschlossen"
    STORNIERT = "storniert"


class ImmobilienTyp(enum.Enum):
    """Typ der Immobilie"""
    WOHNUNG = "wohnung"
    EINFAMILIENHAUS = "einfamilienhaus"
    DOPPELHAUSHAELFTE = "doppelhaushaelfte"
    REIHENHAUS = "reihenhaus"
    MEHRFAMILIENHAUS = "mehrfamilienhaus"
    GRUNDSTUECK = "grundstueck"
    GEWERBE = "gewerbe"
    SONSTIGE = "sonstige"


class DokumentTyp(enum.Enum):
    """Typ eines Dokuments"""
    PERSONALAUSWEIS = "personalausweis"
    REISEPASS = "reisepass"
    GRUNDBUCHAUSZUG = "grundbuchauszug"
    EXPOSE = "expose"
    KAUFVERTRAG = "kaufvertrag"
    FINANZIERUNGSBESTAETIGUNG = "finanzierungsbestaetigung"
    BONITAETSNACHWEIS = "bonitaetsnachweis"
    ENERGIEAUSWEIS = "energieausweis"
    FLURPLAN = "flurplan"
    SONSTIGES = "sonstiges"


class PreisvorschlagStatus(enum.Enum):
    """Status eines Preisvorschlags"""
    OFFEN = "offen"
    ANGENOMMEN = "angenommen"
    ABGELEHNT = "abgelehnt"
    GEGENANGEBOT = "gegenangebot"
    ZURUECKGEZOGEN = "zurueckgezogen"


class InteraktionsTyp(enum.Enum):
    """Typ einer Benutzerinteraktion für Analytics"""
    PAGE_VIEW = "page_view"
    BUTTON_CLICK = "button_click"
    FORM_SUBMIT = "form_submit"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DOWNLOAD = "document_download"
    LOGIN = "login"
    LOGOUT = "logout"
    SEARCH = "search"
    FILTER = "filter"
    PREISVORSCHLAG = "preisvorschlag"
    TERMIN_ERSTELLT = "termin_erstellt"
    NACHRICHT_GESENDET = "nachricht_gesendet"
    PROJEKT_ERSTELLT = "projekt_erstellt"
    PROJEKT_AKTUALISIERT = "projekt_aktualisiert"
    ERROR = "error"


# ==================== NUTZER & AUTHENTIFIZIERUNG ====================

class Nutzer(Base):
    """Basismodell für alle Benutzer der Plattform"""
    __tablename__ = "nutzer"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rolle = Column(Enum(UserRole), nullable=False, index=True)

    # Stammdaten
    vorname = Column(String(100))
    nachname = Column(String(100))
    telefon = Column(String(50))

    # Adresse
    strasse = Column(String(200))
    hausnummer = Column(String(20))
    plz = Column(String(10), index=True)
    ort = Column(String(100))
    land = Column(String(100), default="Deutschland")

    # Status
    ist_aktiv = Column(Boolean, default=True)
    ist_verifiziert = Column(Boolean, default=False)
    verifiziert_am = Column(DateTime)

    # Einstellungen
    benachrichtigungen_email = Column(Boolean, default=True)
    benachrichtigungen_push = Column(Boolean, default=True)
    sprache = Column(String(10), default="de")

    # Session & Sicherheit
    letzter_login = Column(DateTime)
    login_versuche = Column(Integer, default=0)
    gesperrt_bis = Column(DateTime)
    session_token = Column(String(255))

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Beziehungen
    makler_profil = relationship("MaklerProfil", back_populates="nutzer", uselist=False)
    notar_profil = relationship("NotarProfil", back_populates="nutzer", uselist=False)
    projekt_beteiligungen = relationship("ProjektBeteiligung", back_populates="nutzer")
    dokumente = relationship("Dokument", back_populates="nutzer")
    interaktionen = relationship("Interaktion", back_populates="nutzer")
    preisvorschlaege_gesendet = relationship("Preisvorschlag", foreign_keys="Preisvorschlag.absender_id", back_populates="absender")
    preisvorschlaege_empfangen = relationship("Preisvorschlag", foreign_keys="Preisvorschlag.empfaenger_id", back_populates="empfaenger")

    __table_args__ = (
        Index('idx_nutzer_email_rolle', 'email', 'rolle'),
        Index('idx_nutzer_plz', 'plz'),
    )

    @property
    def voller_name(self):
        return f"{self.vorname or ''} {self.nachname or ''}".strip()


class MaklerProfil(Base):
    """Erweiterte Daten für Makler"""
    __tablename__ = "makler_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nutzer_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), unique=True, nullable=False)

    # Firmendaten
    firmenname = Column(String(200))
    ihk_nummer = Column(String(50))
    gewerbeerlaubnis_nummer = Column(String(100))

    # Spezialisierung
    regionen = Column(ARRAY(String))  # PLZ-Bereiche
    immobilientypen = Column(ARRAY(String))  # Spezialisierte Typen

    # Statistiken
    anzahl_verkauft = Column(Integer, default=0)
    durchschnittliche_verkaufsdauer = Column(Float)  # In Tagen
    bewertung_durchschnitt = Column(Float)
    anzahl_bewertungen = Column(Integer, default=0)

    # Provision
    standard_provision_prozent = Column(Numeric(5, 2))

    # Social/Website
    website = Column(String(255))
    linkedin = Column(String(255))
    xing = Column(String(255))

    # Logo
    logo_url = Column(String(500))

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Beziehungen
    nutzer = relationship("Nutzer", back_populates="makler_profil")


class NotarProfil(Base):
    """Erweiterte Daten für Notare"""
    __tablename__ = "notar_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nutzer_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), unique=True, nullable=False)

    # Kanzleidaten
    kanzleiname = Column(String(200))
    amtsgericht = Column(String(100))
    notarkammer = Column(String(100))

    # Kontakt Kanzlei
    kanzlei_strasse = Column(String(200))
    kanzlei_hausnummer = Column(String(20))
    kanzlei_plz = Column(String(10))
    kanzlei_ort = Column(String(100))
    kanzlei_telefon = Column(String(50))
    kanzlei_fax = Column(String(50))

    # Spezialisierung
    taetigkeitsschwerpunkte = Column(ARRAY(String))

    # Statistiken
    anzahl_beurkundungen = Column(Integer, default=0)

    # Einstellungen
    rechtsdokumente_pflichtig = Column(Boolean, default=True)
    demo_modus = Column(Boolean, default=True)

    # API Keys (verschlüsselt speichern!)
    openai_api_key_encrypted = Column(Text)
    anthropic_api_key_encrypted = Column(Text)

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Beziehungen
    nutzer = relationship("Nutzer", back_populates="notar_profil")
    mitarbeiter = relationship("NotarMitarbeiter", back_populates="notar")


class NotarMitarbeiter(Base):
    """Mitarbeiter eines Notars"""
    __tablename__ = "notar_mitarbeiter"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notar_id = Column(UUID(as_uuid=True), ForeignKey("notar_profile.id"), nullable=False)
    nutzer_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), nullable=False)

    position = Column(String(100))
    berechtigungen = Column(JSONB)  # {"projekte": true, "dokumente": true, ...}

    ist_aktiv = Column(Boolean, default=True)

    erstellt_am = Column(DateTime, default=datetime.utcnow)

    notar = relationship("NotarProfil", back_populates="mitarbeiter")


# ==================== IMMOBILIEN & PROJEKTE ====================

class Immobilie(Base):
    """Immobiliendaten für Preisanalyse und Marktstatistiken"""
    __tablename__ = "immobilien"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Adresse
    strasse = Column(String(200))
    hausnummer = Column(String(20))
    plz = Column(String(10), nullable=False, index=True)
    ort = Column(String(100), nullable=False)
    bundesland = Column(String(50))
    land = Column(String(100), default="Deutschland")

    # Geo-Koordinaten für Kartenansicht und Radius-Suche
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)

    # Typ & Zustand
    immobilientyp = Column(Enum(ImmobilienTyp), nullable=False, index=True)
    baujahr = Column(Integer, index=True)
    letzte_modernisierung = Column(Integer)  # Jahr
    zustand = Column(String(50))  # "neuwertig", "gepflegt", "renovierungsbedürftig"

    # Flächen
    wohnflaeche_qm = Column(Float, index=True)
    grundstuecksflaeche_qm = Column(Float)
    nutzflaeche_qm = Column(Float)

    # Räume
    anzahl_zimmer = Column(Float, index=True)  # Float für "2.5 Zimmer"
    anzahl_schlafzimmer = Column(Integer)
    anzahl_badezimmer = Column(Integer)
    anzahl_etagen = Column(Integer)
    etage = Column(Integer)  # Bei Wohnungen

    # Ausstattung
    hat_balkon = Column(Boolean, default=False)
    hat_terrasse = Column(Boolean, default=False)
    hat_garten = Column(Boolean, default=False)
    hat_aufzug = Column(Boolean, default=False)
    hat_garage = Column(Boolean, default=False)
    anzahl_stellplaetze = Column(Integer, default=0)
    hat_keller = Column(Boolean, default=False)
    hat_dachboden = Column(Boolean, default=False)

    # Heizung & Energie
    heizungsart = Column(String(50))  # "Gas", "Öl", "Wärmepumpe", etc.
    energieeffizienzklasse = Column(String(5))  # "A+", "A", "B", etc.
    energieverbrauch_kwh = Column(Float)
    energietraeger = Column(String(50))

    # Zusatzinfos
    barrierefrei = Column(Boolean, default=False)
    denkmalschutz = Column(Boolean, default=False)

    # Beschreibung
    titel = Column(String(200))
    beschreibung = Column(Text)
    ausstattung_text = Column(Text)
    lage_text = Column(Text)

    # Bilder (URLs oder IDs)
    bilder = Column(JSONB)  # [{"url": "...", "typ": "hauptbild"}, ...]

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Beziehungen
    projekte = relationship("Projekt", back_populates="immobilie")
    preis_historien = relationship("PreisHistorie", back_populates="immobilie")

    __table_args__ = (
        Index('idx_immobilie_geo', 'latitude', 'longitude'),
        Index('idx_immobilie_suche', 'plz', 'immobilientyp', 'wohnflaeche_qm', 'anzahl_zimmer'),
        Index('idx_immobilie_preis_ml', 'plz', 'wohnflaeche_qm', 'baujahr', 'anzahl_zimmer'),
    )


class Projekt(Base):
    """Ein Immobilienverkaufsprojekt"""
    __tablename__ = "projekte"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    immobilie_id = Column(UUID(as_uuid=True), ForeignKey("immobilien.id"), nullable=False)

    # Projektdaten
    name = Column(String(200), nullable=False)
    beschreibung = Column(Text)
    status = Column(Enum(ProjektStatus), default=ProjektStatus.VORBEREITUNG, index=True)

    # Preise
    angebotspreis = Column(Numeric(12, 2))
    mindestpreis = Column(Numeric(12, 2))  # Intern, nicht für Käufer sichtbar
    verkaufspreis = Column(Numeric(12, 2))  # Finaler Preis nach Verhandlung

    # Provision
    maklerprovision_prozent = Column(Numeric(5, 2))
    maklerprovision_kaeufer_prozent = Column(Numeric(5, 2))
    maklerprovision_verkaeufer_prozent = Column(Numeric(5, 2))

    # Einstellungen
    preisverhandlung_erlaubt = Column(Boolean, default=False)
    rechtsdokumente_erforderlich = Column(Boolean, default=True)
    expose_nach_akzeptanz = Column(Boolean, default=True)

    # Termine
    vermarktungsstart = Column(Date)
    besichtigungstermine = Column(JSONB)  # [{"datum": "...", "uhrzeit": "...", "max_teilnehmer": 10}]
    notartermin = Column(DateTime)
    uebergabetermin = Column(DateTime)

    # Interne Daten
    notizen_intern = Column(Text)

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    abgeschlossen_am = Column(DateTime)

    # Beziehungen
    immobilie = relationship("Immobilie", back_populates="projekte")
    beteiligungen = relationship("ProjektBeteiligung", back_populates="projekt")
    dokumente = relationship("Dokument", back_populates="projekt")
    preisvorschlaege = relationship("Preisvorschlag", back_populates="projekt")
    preis_historien = relationship("PreisHistorie", back_populates="projekt")

    __table_args__ = (
        Index('idx_projekt_status', 'status'),
        Index('idx_projekt_datum', 'erstellt_am'),
    )


class ProjektBeteiligung(Base):
    """Verknüpfung zwischen Nutzern und Projekten mit Rolle"""
    __tablename__ = "projekt_beteiligungen"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projekt_id = Column(UUID(as_uuid=True), ForeignKey("projekte.id"), nullable=False)
    nutzer_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), nullable=False)

    rolle = Column(Enum(UserRole), nullable=False)  # Rolle in diesem Projekt

    # Status
    ist_aktiv = Column(Boolean, default=True)
    eingeladen_am = Column(DateTime, default=datetime.utcnow)
    akzeptiert_am = Column(DateTime)

    # Rechtsdokumente
    datenschutz_akzeptiert = Column(Boolean, default=False)
    datenschutz_akzeptiert_am = Column(DateTime)
    agb_akzeptiert = Column(Boolean, default=False)
    agb_akzeptiert_am = Column(DateTime)
    widerruf_akzeptiert = Column(Boolean, default=False)
    widerruf_akzeptiert_am = Column(DateTime)

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # Beziehungen
    projekt = relationship("Projekt", back_populates="beteiligungen")
    nutzer = relationship("Nutzer", back_populates="projekt_beteiligungen")

    __table_args__ = (
        UniqueConstraint('projekt_id', 'nutzer_id', 'rolle', name='uq_projekt_nutzer_rolle'),
        Index('idx_beteiligung_projekt', 'projekt_id'),
        Index('idx_beteiligung_nutzer', 'nutzer_id'),
    )


# ==================== PREISVERHANDLUNGEN & ML ====================

class Preisvorschlag(Base):
    """Preisvorschläge für Verhandlungen und ML-Training"""
    __tablename__ = "preisvorschlaege"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projekt_id = Column(UUID(as_uuid=True), ForeignKey("projekte.id"), nullable=False)

    absender_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), nullable=False)
    empfaenger_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), nullable=False)

    # Preisdaten
    vorgeschlagener_preis = Column(Numeric(12, 2), nullable=False)
    urspruenglicher_preis = Column(Numeric(12, 2))  # Angebotspreis zum Zeitpunkt
    differenz_prozent = Column(Numeric(5, 2))  # Abweichung vom Angebotspreis

    # Status
    status = Column(Enum(PreisvorschlagStatus), default=PreisvorschlagStatus.OFFEN, index=True)

    # Kontext
    nachricht = Column(Text)
    begruendung = Column(Text)

    # Antwort
    antwort_nachricht = Column(Text)
    beantwortet_am = Column(DateTime)

    # Verkettung für Gegenangebote
    vorgaenger_id = Column(UUID(as_uuid=True), ForeignKey("preisvorschlaege.id"))

    # ML-Features (für späteres Training)
    ml_features = Column(JSONB)  # {"tage_online": 30, "anzahl_besichtigungen": 5, ...}

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow, index=True)

    # Beziehungen
    projekt = relationship("Projekt", back_populates="preisvorschlaege")
    absender = relationship("Nutzer", foreign_keys=[absender_id], back_populates="preisvorschlaege_gesendet")
    empfaenger = relationship("Nutzer", foreign_keys=[empfaenger_id], back_populates="preisvorschlaege_empfangen")
    vorgaenger = relationship("Preisvorschlag", remote_side=[id])

    __table_args__ = (
        Index('idx_preisvorschlag_projekt', 'projekt_id'),
        Index('idx_preisvorschlag_status', 'status'),
        Index('idx_preisvorschlag_ml', 'projekt_id', 'status', 'erstellt_am'),
    )


class PreisHistorie(Base):
    """Historische Preisdaten für ML-Kaufpreisvorschläge"""
    __tablename__ = "preis_historien"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    immobilie_id = Column(UUID(as_uuid=True), ForeignKey("immobilien.id"), nullable=False)
    projekt_id = Column(UUID(as_uuid=True), ForeignKey("projekte.id"))

    # Preise
    angebotspreis = Column(Numeric(12, 2), nullable=False)
    verkaufspreis = Column(Numeric(12, 2))
    preis_pro_qm = Column(Numeric(10, 2))

    # Zeitraum
    angebotsdatum = Column(Date, nullable=False, index=True)
    verkaufsdatum = Column(Date)
    tage_bis_verkauf = Column(Integer)

    # Verhandlungsdaten
    anzahl_preisvorschlaege = Column(Integer, default=0)
    preisreduktion_prozent = Column(Numeric(5, 2))  # Vom Angebot zum Verkauf

    # Immobilien-Snapshot (für ML, falls Immobilie später geändert wird)
    immobilien_snapshot = Column(JSONB)  # Kopie relevanter Felder zum Verkaufszeitpunkt

    # Marktkontext
    markt_snapshot = Column(JSONB)  # Marktdaten zum Verkaufszeitpunkt

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # Beziehungen
    immobilie = relationship("Immobilie", back_populates="preis_historien")
    projekt = relationship("Projekt", back_populates="preis_historien")

    __table_args__ = (
        Index('idx_preis_historie_plz', 'angebotsdatum'),
        Index('idx_preis_historie_ml', 'angebotsdatum', 'verkaufsdatum'),
    )


class MarktDaten(Base):
    """Externe Marktdaten nach PLZ für Preisvorschläge"""
    __tablename__ = "markt_daten"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    plz = Column(String(10), nullable=False, index=True)
    ort = Column(String(100))
    bundesland = Column(String(50))

    # Zeitraum der Daten
    gueltig_ab = Column(Date, nullable=False)
    gueltig_bis = Column(Date)

    # Durchschnittspreise
    durchschnittspreis_qm_wohnung = Column(Numeric(10, 2))
    durchschnittspreis_qm_haus = Column(Numeric(10, 2))
    median_preis_qm_wohnung = Column(Numeric(10, 2))
    median_preis_qm_haus = Column(Numeric(10, 2))

    # Mietpreise
    durchschnittsmiete_qm = Column(Numeric(8, 2))

    # Marktaktivität
    anzahl_angebote = Column(Integer)
    durchschnittliche_vermarktungsdauer = Column(Integer)  # Tage

    # Trends
    preisaenderung_1_jahr_prozent = Column(Numeric(5, 2))
    preisaenderung_5_jahre_prozent = Column(Numeric(5, 2))

    # Demografische Daten
    einwohnerzahl = Column(Integer)
    kaufkraftindex = Column(Float)
    arbeitslosenquote = Column(Numeric(4, 2))

    # Infrastruktur-Score
    infrastruktur_score = Column(Float)  # 0-100

    # Quelle
    datenquelle = Column(String(100))

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('plz', 'gueltig_ab', name='uq_markt_plz_datum'),
        Index('idx_markt_plz_datum', 'plz', 'gueltig_ab'),
    )


# ==================== DOKUMENTE & OCR ====================

class Dokument(Base):
    """Hochgeladene Dokumente mit OCR-Ergebnissen"""
    __tablename__ = "dokumente"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    nutzer_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), nullable=False)
    projekt_id = Column(UUID(as_uuid=True), ForeignKey("projekte.id"))

    # Dokumentinfo
    dokumenttyp = Column(Enum(DokumentTyp), nullable=False, index=True)
    dateiname = Column(String(255), nullable=False)
    dateityp = Column(String(50))  # "pdf", "jpg", "docx"
    dateigroesse = Column(Integer)  # Bytes

    # Speicherort
    speicher_pfad = Column(String(500))  # S3/Cloud-Pfad oder lokaler Pfad
    speicher_typ = Column(String(50))  # "s3", "local", "blob"

    # Datei-Inhalt (optional für kleine Dateien)
    datei_bytes = Column(LargeBinary)

    # OCR-Ergebnisse
    ocr_verarbeitet = Column(Boolean, default=False)
    ocr_verarbeitet_am = Column(DateTime)
    ocr_text = Column(Text)
    ocr_konfidenz = Column(Float)  # 0-1
    ocr_engine = Column(String(50))  # "tesseract", "aws_textract", "google_vision"

    # Extrahierte strukturierte Daten
    extrahierte_daten = Column(JSONB)  # {"name": "...", "geburtsdatum": "...", ...}

    # Validierung
    ist_validiert = Column(Boolean, default=False)
    validiert_von = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"))
    validiert_am = Column(DateTime)

    # Status
    ist_aktiv = Column(Boolean, default=True)
    ist_archiviert = Column(Boolean, default=False)

    # Hash für Duplikaterkennung
    datei_hash = Column(String(64), index=True)

    # Timestamps
    hochgeladen_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Beziehungen
    nutzer = relationship("Nutzer", foreign_keys=[nutzer_id], back_populates="dokumente")
    projekt = relationship("Projekt", back_populates="dokumente")

    __table_args__ = (
        Index('idx_dokument_nutzer', 'nutzer_id'),
        Index('idx_dokument_projekt', 'projekt_id'),
        Index('idx_dokument_typ', 'dokumenttyp'),
    )


# ==================== ANALYTICS & INTERAKTIONEN ====================

class Interaktion(Base):
    """Benutzerinteraktionen für Analytics und Produktverbesserung"""
    __tablename__ = "interaktionen"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    nutzer_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), index=True)
    session_id = Column(String(100), index=True)

    # Interaktionsdaten
    typ = Column(Enum(InteraktionsTyp), nullable=False, index=True)
    seite = Column(String(100))  # Dashboard-Name oder Route
    aktion = Column(String(100))  # Spezifische Aktion

    # Details
    details = Column(JSONB)  # Flexible Zusatzdaten

    # Kontext
    projekt_id = Column(UUID(as_uuid=True), ForeignKey("projekte.id"))
    referenz_typ = Column(String(50))  # "dokument", "preisvorschlag", etc.
    referenz_id = Column(UUID(as_uuid=True))

    # Geräteinformationen
    user_agent = Column(String(500))
    geraetetyp = Column(String(50))  # "desktop", "mobile", "tablet"
    browser = Column(String(50))
    betriebssystem = Column(String(50))
    bildschirmaufloesung = Column(String(20))

    # Geo (optional, anonymisiert)
    land = Column(String(100))
    region = Column(String(100))

    # Performance
    ladezeit_ms = Column(Integer)

    # Fehler
    fehler_nachricht = Column(Text)
    fehler_stacktrace = Column(Text)

    # Timestamp
    erstellt_am = Column(DateTime, default=datetime.utcnow, index=True)

    # Beziehungen
    nutzer = relationship("Nutzer", back_populates="interaktionen")

    __table_args__ = (
        Index('idx_interaktion_zeit', 'erstellt_am'),
        Index('idx_interaktion_nutzer_zeit', 'nutzer_id', 'erstellt_am'),
        Index('idx_interaktion_typ_zeit', 'typ', 'erstellt_am'),
        Index('idx_interaktion_session', 'session_id', 'erstellt_am'),
    )


# ==================== BENACHRICHTIGUNGEN ====================

class Benachrichtigung(Base):
    """Benachrichtigungen für Nutzer"""
    __tablename__ = "benachrichtigungen"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    empfaenger_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), nullable=False, index=True)
    absender_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"))

    # Inhalt
    titel = Column(String(200), nullable=False)
    nachricht = Column(Text, nullable=False)
    typ = Column(String(50))  # "info", "warnung", "erfolg", "fehler"

    # Kontext
    projekt_id = Column(UUID(as_uuid=True), ForeignKey("projekte.id"))
    link = Column(String(500))  # Link zu relevanter Seite

    # Status
    gelesen = Column(Boolean, default=False)
    gelesen_am = Column(DateTime)

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_benachrichtigung_empfaenger', 'empfaenger_id', 'gelesen', 'erstellt_am'),
    )


# ==================== TEXTBAUSTEINE & VERTRÄGE ====================

class Textbaustein(Base):
    """Textbausteine für Verträge"""
    __tablename__ = "textbausteine"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    notar_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), nullable=False, index=True)

    # Inhalt
    titel = Column(String(200), nullable=False)
    text = Column(Text, nullable=False)
    zusammenfassung = Column(Text)

    # Kategorisierung
    kategorie = Column(String(100), index=True)
    vertragstypen = Column(ARRAY(String))

    # Position
    position_im_dokument = Column(Integer)
    start_index = Column(Integer)
    end_index = Column(Integer)

    # Verkettung
    vorgaenger_id = Column(UUID(as_uuid=True), ForeignKey("textbausteine.id"))
    nachfolger_id = Column(UUID(as_uuid=True), ForeignKey("textbausteine.id"))

    # Status
    status = Column(String(50), default="entwurf")  # "entwurf", "freigegeben", "archiviert"
    freigegeben_am = Column(DateTime)
    freigegeben_von = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"))

    # KI-Metadaten
    ki_generiert = Column(Boolean, default=False)
    ki_kategorisiert = Column(Boolean, default=False)

    # Version
    version = Column(Integer, default=1)
    vorherige_version_id = Column(UUID(as_uuid=True), ForeignKey("textbausteine.id"))

    # Hash für Duplikaterkennung
    text_hash = Column(String(64), index=True)

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VertragsDokument(Base):
    """Hochgeladene Vertragsdokumente für Textbausteinextraktion"""
    __tablename__ = "vertragsdokumente"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    notar_id = Column(UUID(as_uuid=True), ForeignKey("nutzer.id"), nullable=False, index=True)

    # Datei
    dateiname = Column(String(255), nullable=False)
    dateityp = Column(String(50))
    dateigroesse = Column(Integer)
    datei_bytes = Column(LargeBinary)

    # Inhalt
    volltext = Column(Text)
    vertragstyp = Column(String(100))
    beschreibung = Column(Text)

    # Verarbeitung
    zerlegt = Column(Boolean, default=False)
    anzahl_erkannte_klauseln = Column(Integer)
    baustein_ids = Column(ARRAY(UUID(as_uuid=True)))

    # Status
    status = Column(String(50), default="hochgeladen")

    # Timestamps
    hochgeladen_am = Column(DateTime, default=datetime.utcnow)
    verarbeitet_am = Column(DateTime)
