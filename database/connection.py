"""
Datenbankverbindungsmanagement für die Immobilien-Transaktionsplattform

Dieses Modul stellt Funktionen bereit für:
- Connection Pooling mit SQLAlchemy
- Session Management als Context Manager
- Datenbankinitialisierung
- Verbindungsprüfung
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional

import streamlit as st
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from .models import Base

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== ENGINE & CONNECTION POOL ====================

@st.cache_resource
def get_engine():
    """
    Erstellt und cached die SQLAlchemy Engine mit Connection Pooling.

    Die Engine wird über st.cache_resource gecached, sodass sie
    über Streamlit-Reruns hinweg erhalten bleibt.

    Returns:
        Engine: SQLAlchemy Engine mit konfiguriertem Connection Pool
    """
    # Versuche Database URL aus verschiedenen Quellen zu laden
    database_url = None

    # 1. Versuche aus st.secrets
    try:
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            database_url = st.secrets.database.get('url')
    except Exception as e:
        logger.debug(f"Keine Database-URL in st.secrets: {e}")

    # 2. Versuche aus Umgebungsvariable
    if not database_url:
        database_url = os.environ.get('DATABASE_URL')

    # 3. Fallback für Entwicklung (SQLite)
    if not database_url:
        logger.warning("Keine DATABASE_URL gefunden. Verwende SQLite für Entwicklung.")
        database_url = "sqlite:///./notarplattform_dev.db"

    # PostgreSQL URL-Korrektur (Heroku-Stil postgres:// -> postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # Engine-Konfiguration basierend auf Datenbanktyp
    if database_url.startswith("sqlite"):
        # SQLite - keine Connection Pool-Optionen
        engine = create_engine(
            database_url,
            echo=False,  # SQL-Logging ausschalten in Produktion
            connect_args={"check_same_thread": False}  # Für SQLite Multi-Threading
        )
    else:
        # PostgreSQL mit Connection Pooling
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,  # Anzahl permanenter Verbindungen
            max_overflow=10,  # Zusätzliche Verbindungen bei Bedarf
            pool_timeout=30,  # Timeout für Verbindungsanfrage
            pool_recycle=1800,  # Verbindungen nach 30 Min erneuern
            pool_pre_ping=True,  # Verbindung vor Nutzung prüfen
            echo=False,
        )

        # Event-Listener für Verbindungsprobleme
        @event.listens_for(engine, "connect")
        def connect(dbapi_connection, connection_record):
            logger.debug("Neue Datenbankverbindung erstellt")

        @event.listens_for(engine, "checkout")
        def checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Verbindung aus Pool ausgecheckt")

    logger.info(f"Database Engine erstellt: {database_url.split('@')[-1] if '@' in database_url else 'sqlite'}")

    return engine


def get_session_factory():
    """
    Erstellt eine Session Factory für die Datenbank.

    Returns:
        sessionmaker: Konfigurierte Session Factory
    """
    engine = get_engine()
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )


# ==================== SESSION MANAGEMENT ====================

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context Manager für Datenbank-Sessions.

    Verwendung:
        with get_session() as session:
            nutzer = session.query(Nutzer).filter_by(email=email).first()
            session.add(neuer_nutzer)
            session.commit()

    Bei Fehlern wird automatisch ein Rollback durchgeführt.

    Yields:
        Session: SQLAlchemy Session
    """
    SessionFactory = get_session_factory()
    session = SessionFactory()

    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Datenbankfehler: {e}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Unerwarteter Fehler: {e}")
        raise
    finally:
        session.close()


def get_session_no_commit() -> Generator[Session, None, None]:
    """
    Context Manager für Datenbank-Sessions ohne automatisches Commit.

    Nützlich wenn mehrere Operationen manuell kontrolliert werden sollen.

    Yields:
        Session: SQLAlchemy Session
    """
    SessionFactory = get_session_factory()
    session = SessionFactory()

    try:
        yield session
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Datenbankfehler: {e}")
        raise
    finally:
        session.close()


# ==================== INITIALISIERUNG ====================

def init_database(drop_existing: bool = False) -> bool:
    """
    Initialisiert die Datenbank und erstellt alle Tabellen.

    Args:
        drop_existing: Wenn True, werden existierende Tabellen gelöscht (VORSICHT!)

    Returns:
        bool: True wenn erfolgreich, False bei Fehler
    """
    try:
        engine = get_engine()

        if drop_existing:
            logger.warning("Lösche existierende Tabellen!")
            Base.metadata.drop_all(bind=engine)

        # Erstelle alle Tabellen
        Base.metadata.create_all(bind=engine)

        logger.info("Datenbank erfolgreich initialisiert")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Fehler bei Datenbankinitialisierung: {e}")
        return False


def check_database_connection() -> dict:
    """
    Prüft die Datenbankverbindung und gibt Statusinformationen zurück.

    Returns:
        dict: Status-Dictionary mit Verbindungsinformationen
    """
    result = {
        "connected": False,
        "database_type": None,
        "database_name": None,
        "pool_size": None,
        "pool_checked_out": None,
        "error": None
    }

    try:
        engine = get_engine()

        # Datenbanktyp ermitteln
        result["database_type"] = engine.dialect.name

        # Verbindung testen
        with engine.connect() as conn:
            # Einfache Abfrage ausführen
            if engine.dialect.name == "postgresql":
                query_result = conn.execute(text("SELECT current_database(), version()"))
                row = query_result.fetchone()
                result["database_name"] = row[0]
                result["version"] = row[1]
            elif engine.dialect.name == "sqlite":
                query_result = conn.execute(text("SELECT sqlite_version()"))
                row = query_result.fetchone()
                result["database_name"] = "SQLite"
                result["version"] = row[0]

            result["connected"] = True

        # Pool-Statistiken (nur für Pool-fähige Engines)
        if hasattr(engine.pool, 'size'):
            result["pool_size"] = engine.pool.size()
        if hasattr(engine.pool, 'checkedout'):
            result["pool_checked_out"] = engine.pool.checkedout()

    except OperationalError as e:
        result["error"] = f"Verbindungsfehler: {str(e)}"
        logger.error(f"Datenbankverbindung fehlgeschlagen: {e}")
    except Exception as e:
        result["error"] = f"Unerwarteter Fehler: {str(e)}"
        logger.error(f"Unerwarteter Fehler bei Verbindungsprüfung: {e}")

    return result


# ==================== HILFSFUNKTIONEN ====================

def execute_raw_sql(sql: str, params: dict = None) -> list:
    """
    Führt rohes SQL aus und gibt Ergebnisse zurück.

    Args:
        sql: SQL-Statement
        params: Parameter für das Statement

    Returns:
        list: Liste von Ergebniszeilen
    """
    engine = get_engine()

    with engine.connect() as conn:
        if params:
            result = conn.execute(text(sql), params)
        else:
            result = conn.execute(text(sql))

        return result.fetchall()


def get_table_stats() -> dict:
    """
    Gibt Statistiken über alle Tabellen zurück.

    Returns:
        dict: Dictionary mit Tabellennamen und Zeilenanzahl
    """
    stats = {}
    engine = get_engine()

    try:
        with engine.connect() as conn:
            for table in Base.metadata.tables.keys():
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    stats[table] = result.scalar()
                except Exception:
                    stats[table] = "Fehler"
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Tabellenstatistiken: {e}")

    return stats


# ==================== MIGRATION HELPERS ====================

def run_migration(migration_sql: str) -> bool:
    """
    Führt ein Migrations-SQL-Script aus.

    Args:
        migration_sql: SQL-Script für die Migration

    Returns:
        bool: True wenn erfolgreich
    """
    try:
        engine = get_engine()

        with engine.connect() as conn:
            # Mehrere Statements ausführen
            for statement in migration_sql.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
            conn.commit()

        logger.info("Migration erfolgreich ausgeführt")
        return True

    except Exception as e:
        logger.error(f"Migrationsfehler: {e}")
        return False


def backup_table(table_name: str, backup_suffix: str = "_backup") -> bool:
    """
    Erstellt ein Backup einer Tabelle.

    Args:
        table_name: Name der zu sichernden Tabelle
        backup_suffix: Suffix für die Backup-Tabelle

    Returns:
        bool: True wenn erfolgreich
    """
    try:
        engine = get_engine()
        backup_name = f"{table_name}{backup_suffix}"

        with engine.connect() as conn:
            # Backup-Tabelle erstellen
            conn.execute(text(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}"))
            conn.commit()

        logger.info(f"Backup erstellt: {backup_name}")
        return True

    except Exception as e:
        logger.error(f"Backup-Fehler: {e}")
        return False


# ==================== SESSION STATE INTEGRATION ====================

def get_db_session_for_request():
    """
    Gibt eine Datenbank-Session für den aktuellen Streamlit-Request zurück.

    Die Session wird im Session State gespeichert und am Ende des Requests
    automatisch geschlossen.

    Returns:
        Session: SQLAlchemy Session
    """
    if 'db_session' not in st.session_state:
        SessionFactory = get_session_factory()
        st.session_state.db_session = SessionFactory()

    return st.session_state.db_session


def close_db_session():
    """
    Schließt die Datenbank-Session im Session State.
    """
    if 'db_session' in st.session_state:
        try:
            st.session_state.db_session.close()
        except Exception:
            pass
        del st.session_state.db_session


# ==================== HEALTH CHECK ====================

def health_check() -> dict:
    """
    Führt einen umfassenden Health Check der Datenbank durch.

    Returns:
        dict: Health Status mit Details
    """
    health = {
        "status": "unhealthy",
        "checks": {}
    }

    # 1. Verbindungscheck
    conn_status = check_database_connection()
    health["checks"]["connection"] = {
        "status": "pass" if conn_status["connected"] else "fail",
        "details": conn_status
    }

    if not conn_status["connected"]:
        return health

    # 2. Tabellencheck
    try:
        stats = get_table_stats()
        health["checks"]["tables"] = {
            "status": "pass",
            "count": len(stats),
            "details": stats
        }
    except Exception as e:
        health["checks"]["tables"] = {
            "status": "fail",
            "error": str(e)
        }

    # 3. Schreibtest
    try:
        with get_session() as session:
            # Dummy-Query um Schreibzugriff zu testen
            session.execute(text("SELECT 1"))
        health["checks"]["write"] = {"status": "pass"}
    except Exception as e:
        health["checks"]["write"] = {
            "status": "fail",
            "error": str(e)
        }

    # Gesamtstatus
    all_passed = all(
        check.get("status") == "pass"
        for check in health["checks"].values()
    )
    health["status"] = "healthy" if all_passed else "degraded"

    return health
