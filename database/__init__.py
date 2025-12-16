"""
Database Package für die Immobilien-Transaktionsplattform

Dieses Package stellt alle datenbankbezogenen Funktionen bereit:
- SQLAlchemy Modelle
- Verbindungsmanagement
- Session Handling
- Migrations-Utilities
- High-Level Services

Verwendung:
    from database import get_session, Nutzer, Projekt

    # Session als Context Manager
    with get_session() as session:
        nutzer = session.query(Nutzer).filter_by(email="test@test.de").first()

    # Datenbankstatus prüfen
    from database import check_database_connection
    status = check_database_connection()

    # High-Level Services
    from database import create_nutzer, track_interaktion
    nutzer = create_nutzer(email="neu@test.de", password_hash="...", rolle=UserRole.KAEUFER)
"""

# Modelle exportieren
from .models import (
    Base,
    # Enums
    UserRole,
    ProjektStatus,
    ImmobilienTyp,
    DokumentTyp,
    PreisvorschlagStatus,
    InteraktionsTyp,
    # Aktenmanagement Enums
    AktenHauptbereich,
    AktenTypErbrecht,
    AktenTypGesellschaftsrecht,
    AktenTypZivilrecht,
    AktenStatus,
    APIKeyTyp,
    # Urkundenparser Enums
    ParserBlockType,
    ParserStage,
    ParserRunStatus,
    # Nutzer & Auth
    Nutzer,
    MaklerProfil,
    NotarProfil,
    NotarMitarbeiter,
    # Immobilien & Projekte
    Immobilie,
    Projekt,
    ProjektBeteiligung,
    # Preisverhandlungen
    Preisvorschlag,
    PreisHistorie,
    MarktDaten,
    # Dokumente
    Dokument,
    # Analytics
    Interaktion,
    Benachrichtigung,
    # Verträge
    Textbaustein,
    VertragsDokument,
    # Aktenmanagement
    Akte,
    BenutzerdefiniertAktenKategorie,
    AktenDokument,
    AktenNachricht,
    AktenTextbaustein,
    # API-Keys
    APIKey,
    # Urkundenparser
    UrkundenParserRun,
    ParsedBlock,
    ParsedFact,
    ParsedTask,
    ParsedIssue,
    GenericBlockLibrary,
)

# Verbindungsfunktionen exportieren
from .connection import (
    get_engine,
    get_session,
    get_session_no_commit,
    get_session_factory,
    init_database,
    check_database_connection,
    execute_raw_sql,
    get_table_stats,
    run_migration,
    backup_table,
    get_db_session_for_request,
    close_db_session,
    health_check,
)

# Services exportieren
from .services import (
    # Nutzer
    create_nutzer,
    get_nutzer_by_email,
    get_nutzer_by_id,
    authenticate_nutzer,
    update_nutzer_last_login,
    # Interaktionen
    track_interaktion,
    get_interaktionen_stats,
    # Projekte
    create_projekt,
    get_projekte_by_nutzer,
    # Preisverhandlung
    create_preisvorschlag,
    respond_to_preisvorschlag,
    get_preisverhandlungs_historie,
    # ML/Preis-Analyse
    get_preis_training_data,
    get_markt_referenzpreise,
    # Dokumente
    create_dokument,
    update_dokument_ocr,
    # Benachrichtigungen
    create_benachrichtigung,
    get_ungelesene_benachrichtigungen,
    mark_benachrichtigung_gelesen,
)

__version__ = "1.1.0"
__all__ = [
    # Base
    "Base",
    # Enums
    "UserRole",
    "ProjektStatus",
    "ImmobilienTyp",
    "DokumentTyp",
    "PreisvorschlagStatus",
    "InteraktionsTyp",
    # Aktenmanagement Enums
    "AktenHauptbereich",
    "AktenTypErbrecht",
    "AktenTypGesellschaftsrecht",
    "AktenTypZivilrecht",
    "AktenStatus",
    "APIKeyTyp",
    # Urkundenparser Enums
    "ParserBlockType",
    "ParserStage",
    "ParserRunStatus",
    # Models
    "Nutzer",
    "MaklerProfil",
    "NotarProfil",
    "NotarMitarbeiter",
    "Immobilie",
    "Projekt",
    "ProjektBeteiligung",
    "Preisvorschlag",
    "PreisHistorie",
    "MarktDaten",
    "Dokument",
    "Interaktion",
    "Benachrichtigung",
    "Textbaustein",
    "VertragsDokument",
    # Aktenmanagement Models
    "Akte",
    "BenutzerdefiniertAktenKategorie",
    "AktenDokument",
    "AktenNachricht",
    "AktenTextbaustein",
    # API-Keys
    "APIKey",
    # Urkundenparser Models
    "UrkundenParserRun",
    "ParsedBlock",
    "ParsedFact",
    "ParsedTask",
    "ParsedIssue",
    "GenericBlockLibrary",
    # Connection functions
    "get_engine",
    "get_session",
    "get_session_no_commit",
    "get_session_factory",
    "init_database",
    "check_database_connection",
    "execute_raw_sql",
    "get_table_stats",
    "run_migration",
    "backup_table",
    "get_db_session_for_request",
    "close_db_session",
    "health_check",
    # Services
    "create_nutzer",
    "get_nutzer_by_email",
    "get_nutzer_by_id",
    "authenticate_nutzer",
    "update_nutzer_last_login",
    "track_interaktion",
    "get_interaktionen_stats",
    "create_projekt",
    "get_projekte_by_nutzer",
    "create_preisvorschlag",
    "respond_to_preisvorschlag",
    "get_preisverhandlungs_historie",
    "get_preis_training_data",
    "get_markt_referenzpreise",
    "create_dokument",
    "update_dokument_ocr",
    "create_benachrichtigung",
    "get_ungelesene_benachrichtigungen",
    "mark_benachrichtigung_gelesen",
]
