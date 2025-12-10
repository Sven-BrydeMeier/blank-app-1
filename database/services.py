"""
Datenbank-Services für die Immobilien-Transaktionsplattform

Dieses Modul enthält High-Level-Funktionen für:
- Nutzer-Management
- Interaktions-Tracking
- Preis-Analysen
- Dokument-Management
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
import uuid
import logging

from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session

from .models import (
    Nutzer, MaklerProfil, NotarProfil, NotarMitarbeiter,
    Immobilie, Projekt, ProjektBeteiligung,
    Preisvorschlag, PreisHistorie, MarktDaten,
    Dokument, Interaktion, Benachrichtigung,
    Textbaustein, VertragsDokument,
    UserRole, ProjektStatus, PreisvorschlagStatus, InteraktionsTyp, DokumentTyp
)
from .connection import get_session

logger = logging.getLogger(__name__)


# ==================== NUTZER-MANAGEMENT ====================

def create_nutzer(
    email: str,
    password_hash: str,
    rolle: UserRole,
    vorname: str = None,
    nachname: str = None,
    **kwargs
) -> Optional[Nutzer]:
    """
    Erstellt einen neuen Nutzer in der Datenbank.

    Args:
        email: E-Mail-Adresse (unique)
        password_hash: Gehashtes Passwort
        rolle: Benutzerrolle
        vorname: Vorname
        nachname: Nachname
        **kwargs: Weitere Felder

    Returns:
        Nutzer: Der erstellte Nutzer oder None bei Fehler
    """
    try:
        with get_session() as session:
            # Prüfe ob E-Mail bereits existiert
            existing = session.query(Nutzer).filter_by(email=email).first()
            if existing:
                logger.warning(f"Nutzer mit E-Mail {email} existiert bereits")
                return None

            nutzer = Nutzer(
                email=email,
                password_hash=password_hash,
                rolle=rolle,
                vorname=vorname,
                nachname=nachname,
                **kwargs
            )
            session.add(nutzer)
            session.commit()

            logger.info(f"Nutzer erstellt: {email}")
            return nutzer

    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Nutzers: {e}")
        return None


def get_nutzer_by_email(email: str) -> Optional[Nutzer]:
    """Findet einen Nutzer anhand der E-Mail."""
    with get_session() as session:
        return session.query(Nutzer).filter_by(email=email).first()


def get_nutzer_by_id(nutzer_id: uuid.UUID) -> Optional[Nutzer]:
    """Findet einen Nutzer anhand der ID."""
    with get_session() as session:
        return session.query(Nutzer).filter_by(id=nutzer_id).first()


def update_nutzer_last_login(nutzer_id: uuid.UUID) -> bool:
    """Aktualisiert den letzten Login-Zeitpunkt."""
    try:
        with get_session() as session:
            nutzer = session.query(Nutzer).filter_by(id=nutzer_id).first()
            if nutzer:
                nutzer.letzter_login = datetime.utcnow()
                nutzer.login_versuche = 0
                session.commit()
                return True
        return False
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren des Login: {e}")
        return False


def authenticate_nutzer(email: str, password_hash: str) -> Optional[Nutzer]:
    """
    Authentifiziert einen Nutzer.

    Returns:
        Nutzer: Der authentifizierte Nutzer oder None
    """
    with get_session() as session:
        nutzer = session.query(Nutzer).filter_by(
            email=email,
            password_hash=password_hash,
            ist_aktiv=True
        ).first()

        if nutzer:
            # Prüfe ob gesperrt
            if nutzer.gesperrt_bis and nutzer.gesperrt_bis > datetime.utcnow():
                logger.warning(f"Nutzer {email} ist gesperrt bis {nutzer.gesperrt_bis}")
                return None

            update_nutzer_last_login(nutzer.id)
            return nutzer

        # Login fehlgeschlagen - Versuche zählen
        failed_nutzer = session.query(Nutzer).filter_by(email=email).first()
        if failed_nutzer:
            failed_nutzer.login_versuche += 1
            if failed_nutzer.login_versuche >= 5:
                failed_nutzer.gesperrt_bis = datetime.utcnow() + timedelta(minutes=15)
            session.commit()

        return None


# ==================== INTERAKTIONS-TRACKING ====================

def track_interaktion(
    typ: InteraktionsTyp,
    seite: str = None,
    aktion: str = None,
    nutzer_id: uuid.UUID = None,
    session_id: str = None,
    projekt_id: uuid.UUID = None,
    details: Dict[str, Any] = None,
    user_agent: str = None,
    geraetetyp: str = None
) -> Optional[Interaktion]:
    """
    Trackt eine Benutzerinteraktion für Analytics.

    Args:
        typ: Art der Interaktion
        seite: Dashboard/Seite
        aktion: Spezifische Aktion
        nutzer_id: Optional - ID des Nutzers
        session_id: Optional - Session-ID
        projekt_id: Optional - Projekt-Kontext
        details: Optional - Zusätzliche Details als Dict
        user_agent: Optional - Browser User Agent
        geraetetyp: Optional - desktop/mobile/tablet

    Returns:
        Interaktion: Die erstellte Interaktion
    """
    try:
        with get_session() as session:
            interaktion = Interaktion(
                typ=typ,
                seite=seite,
                aktion=aktion,
                nutzer_id=nutzer_id,
                session_id=session_id,
                projekt_id=projekt_id,
                details=details,
                user_agent=user_agent,
                geraetetyp=geraetetyp
            )
            session.add(interaktion)
            session.commit()
            return interaktion

    except Exception as e:
        logger.error(f"Fehler beim Tracken der Interaktion: {e}")
        return None


def get_interaktionen_stats(
    zeitraum_tage: int = 30,
    nutzer_id: uuid.UUID = None
) -> Dict[str, Any]:
    """
    Gibt Statistiken über Interaktionen zurück.

    Args:
        zeitraum_tage: Zeitraum für die Statistiken
        nutzer_id: Optional - Filter auf Nutzer

    Returns:
        Dict mit Statistiken
    """
    try:
        with get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=zeitraum_tage)

            query = session.query(Interaktion).filter(
                Interaktion.erstellt_am >= start_date
            )

            if nutzer_id:
                query = query.filter(Interaktion.nutzer_id == nutzer_id)

            # Gesamt
            total = query.count()

            # Nach Typ gruppiert
            by_type = session.query(
                Interaktion.typ,
                func.count(Interaktion.id)
            ).filter(
                Interaktion.erstellt_am >= start_date
            ).group_by(Interaktion.typ).all()

            # Nach Seite gruppiert
            by_page = session.query(
                Interaktion.seite,
                func.count(Interaktion.id)
            ).filter(
                Interaktion.erstellt_am >= start_date
            ).group_by(Interaktion.seite).all()

            return {
                "total": total,
                "by_type": {str(t): c for t, c in by_type},
                "by_page": {p or "unknown": c for p, c in by_page},
                "zeitraum_tage": zeitraum_tage
            }

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
        return {}


# ==================== PROJEKT-MANAGEMENT ====================

def create_projekt(
    immobilie_id: uuid.UUID,
    name: str,
    angebotspreis: Decimal,
    makler_id: uuid.UUID = None,
    notar_id: uuid.UUID = None,
    verkaeufer_ids: List[uuid.UUID] = None,
    **kwargs
) -> Optional[Projekt]:
    """
    Erstellt ein neues Projekt mit Beteiligungen.
    """
    try:
        with get_session() as session:
            projekt = Projekt(
                immobilie_id=immobilie_id,
                name=name,
                angebotspreis=angebotspreis,
                **kwargs
            )
            session.add(projekt)
            session.flush()  # Um projekt.id zu erhalten

            # Makler hinzufügen
            if makler_id:
                beteiligung = ProjektBeteiligung(
                    projekt_id=projekt.id,
                    nutzer_id=makler_id,
                    rolle=UserRole.MAKLER,
                    akzeptiert_am=datetime.utcnow()
                )
                session.add(beteiligung)

            # Notar hinzufügen
            if notar_id:
                beteiligung = ProjektBeteiligung(
                    projekt_id=projekt.id,
                    nutzer_id=notar_id,
                    rolle=UserRole.NOTAR,
                    akzeptiert_am=datetime.utcnow()
                )
                session.add(beteiligung)

            # Verkäufer hinzufügen
            if verkaeufer_ids:
                for vid in verkaeufer_ids:
                    beteiligung = ProjektBeteiligung(
                        projekt_id=projekt.id,
                        nutzer_id=vid,
                        rolle=UserRole.VERKAEUFER
                    )
                    session.add(beteiligung)

            session.commit()
            logger.info(f"Projekt erstellt: {name}")
            return projekt

    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Projekts: {e}")
        return None


def get_projekte_by_nutzer(nutzer_id: uuid.UUID) -> List[Projekt]:
    """Gibt alle Projekte zurück, an denen ein Nutzer beteiligt ist."""
    with get_session() as session:
        return session.query(Projekt).join(
            ProjektBeteiligung
        ).filter(
            ProjektBeteiligung.nutzer_id == nutzer_id,
            ProjektBeteiligung.ist_aktiv == True
        ).all()


# ==================== PREISVERHANDLUNG ====================

def create_preisvorschlag(
    projekt_id: uuid.UUID,
    absender_id: uuid.UUID,
    empfaenger_id: uuid.UUID,
    vorgeschlagener_preis: Decimal,
    nachricht: str = None,
    vorgaenger_id: uuid.UUID = None
) -> Optional[Preisvorschlag]:
    """
    Erstellt einen neuen Preisvorschlag.
    """
    try:
        with get_session() as session:
            # Hole aktuellen Angebotspreis
            projekt = session.query(Projekt).filter_by(id=projekt_id).first()
            if not projekt:
                return None

            urspruenglicher_preis = projekt.angebotspreis
            differenz = ((vorgeschlagener_preis - urspruenglicher_preis) / urspruenglicher_preis * 100) if urspruenglicher_preis else 0

            vorschlag = Preisvorschlag(
                projekt_id=projekt_id,
                absender_id=absender_id,
                empfaenger_id=empfaenger_id,
                vorgeschlagener_preis=vorgeschlagener_preis,
                urspruenglicher_preis=urspruenglicher_preis,
                differenz_prozent=differenz,
                nachricht=nachricht,
                vorgaenger_id=vorgaenger_id
            )
            session.add(vorschlag)
            session.commit()

            # Interaktion tracken
            track_interaktion(
                typ=InteraktionsTyp.PREISVORSCHLAG,
                nutzer_id=absender_id,
                projekt_id=projekt_id,
                details={
                    "preis": float(vorgeschlagener_preis),
                    "differenz_prozent": float(differenz)
                }
            )

            return vorschlag

    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Preisvorschlags: {e}")
        return None


def respond_to_preisvorschlag(
    vorschlag_id: uuid.UUID,
    status: PreisvorschlagStatus,
    antwort_nachricht: str = None,
    gegenangebot_preis: Decimal = None
) -> bool:
    """
    Beantwortet einen Preisvorschlag.
    """
    try:
        with get_session() as session:
            vorschlag = session.query(Preisvorschlag).filter_by(id=vorschlag_id).first()
            if not vorschlag:
                return False

            vorschlag.status = status
            vorschlag.antwort_nachricht = antwort_nachricht
            vorschlag.beantwortet_am = datetime.utcnow()

            # Bei Annahme: Verkaufspreis aktualisieren
            if status == PreisvorschlagStatus.ANGENOMMEN:
                projekt = session.query(Projekt).filter_by(id=vorschlag.projekt_id).first()
                if projekt:
                    projekt.verkaufspreis = vorschlag.vorgeschlagener_preis

            session.commit()
            return True

    except Exception as e:
        logger.error(f"Fehler beim Beantworten des Preisvorschlags: {e}")
        return False


def get_preisverhandlungs_historie(projekt_id: uuid.UUID) -> List[Preisvorschlag]:
    """Gibt die Preisverhandlungs-Historie für ein Projekt zurück."""
    with get_session() as session:
        return session.query(Preisvorschlag).filter_by(
            projekt_id=projekt_id
        ).order_by(Preisvorschlag.erstellt_am).all()


# ==================== PREIS-ANALYSE FÜR ML ====================

def get_preis_training_data(
    plz_prefix: str = None,
    immobilientyp: str = None,
    min_verkaufsdatum: datetime = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Gibt Trainingsdaten für ML-Preisvorhersage zurück.

    Args:
        plz_prefix: Filter auf PLZ-Bereich (z.B. "80" für München)
        immobilientyp: Filter auf Immobilientyp
        min_verkaufsdatum: Nur Verkäufe nach diesem Datum
        limit: Maximale Anzahl Datensätze

    Returns:
        Liste von Feature-Dictionaries für ML-Training
    """
    try:
        with get_session() as session:
            query = session.query(
                PreisHistorie, Immobilie
            ).join(
                Immobilie, PreisHistorie.immobilie_id == Immobilie.id
            ).filter(
                PreisHistorie.verkaufspreis.isnot(None)
            )

            if plz_prefix:
                query = query.filter(Immobilie.plz.startswith(plz_prefix))

            if immobilientyp:
                query = query.filter(Immobilie.immobilientyp == immobilientyp)

            if min_verkaufsdatum:
                query = query.filter(PreisHistorie.verkaufsdatum >= min_verkaufsdatum)

            results = query.order_by(desc(PreisHistorie.verkaufsdatum)).limit(limit).all()

            training_data = []
            for historie, immobilie in results:
                training_data.append({
                    # Target
                    "verkaufspreis": float(historie.verkaufspreis),
                    "preis_pro_qm": float(historie.preis_pro_qm) if historie.preis_pro_qm else None,

                    # Features - Immobilie
                    "plz": immobilie.plz,
                    "wohnflaeche_qm": immobilie.wohnflaeche_qm,
                    "grundstuecksflaeche_qm": immobilie.grundstuecksflaeche_qm,
                    "anzahl_zimmer": immobilie.anzahl_zimmer,
                    "baujahr": immobilie.baujahr,
                    "immobilientyp": str(immobilie.immobilientyp.value) if immobilie.immobilientyp else None,

                    # Features - Ausstattung
                    "hat_balkon": immobilie.hat_balkon,
                    "hat_garten": immobilie.hat_garten,
                    "hat_garage": immobilie.hat_garage,
                    "hat_aufzug": immobilie.hat_aufzug,

                    # Features - Verhandlung
                    "angebotspreis": float(historie.angebotspreis),
                    "preisreduktion_prozent": float(historie.preisreduktion_prozent) if historie.preisreduktion_prozent else 0,
                    "tage_bis_verkauf": historie.tage_bis_verkauf,
                    "anzahl_preisvorschlaege": historie.anzahl_preisvorschlaege,

                    # Zeitstempel
                    "verkaufsdatum": historie.verkaufsdatum.isoformat() if historie.verkaufsdatum else None,
                })

            return training_data

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Trainingsdaten: {e}")
        return []


def get_markt_referenzpreise(
    plz: str,
    immobilientyp: str,
    wohnflaeche_qm: float
) -> Dict[str, Any]:
    """
    Gibt Markt-Referenzpreise für eine Immobilie zurück.

    Returns:
        Dict mit Durchschnittspreisen und Vergleichswerten
    """
    try:
        with get_session() as session:
            # Aktuelle Marktdaten für PLZ
            markt = session.query(MarktDaten).filter(
                MarktDaten.plz == plz,
                or_(
                    MarktDaten.gueltig_bis.is_(None),
                    MarktDaten.gueltig_bis >= datetime.utcnow().date()
                )
            ).order_by(desc(MarktDaten.gueltig_ab)).first()

            # Ähnliche verkaufte Immobilien
            plz_prefix = plz[:3]  # Gleiche Region
            aehnliche = session.query(
                func.avg(PreisHistorie.preis_pro_qm),
                func.min(PreisHistorie.preis_pro_qm),
                func.max(PreisHistorie.preis_pro_qm),
                func.count(PreisHistorie.id)
            ).join(
                Immobilie
            ).filter(
                Immobilie.plz.startswith(plz_prefix),
                Immobilie.immobilientyp == immobilientyp,
                Immobilie.wohnflaeche_qm.between(wohnflaeche_qm * 0.8, wohnflaeche_qm * 1.2),
                PreisHistorie.verkaufspreis.isnot(None),
                PreisHistorie.verkaufsdatum >= datetime.utcnow().date() - timedelta(days=365)
            ).first()

            result = {
                "plz": plz,
                "immobilientyp": immobilientyp,
                "wohnflaeche_qm": wohnflaeche_qm,
            }

            if markt:
                preis_qm = markt.durchschnittspreis_qm_wohnung if "wohnung" in immobilientyp.lower() else markt.durchschnittspreis_qm_haus
                result["markt_preis_qm"] = float(preis_qm) if preis_qm else None
                result["markt_geschaetzter_preis"] = float(preis_qm * Decimal(str(wohnflaeche_qm))) if preis_qm else None
                result["preisaenderung_1_jahr"] = float(markt.preisaenderung_1_jahr_prozent) if markt.preisaenderung_1_jahr_prozent else None

            if aehnliche[0]:
                result["vergleich_durchschnitt_qm"] = float(aehnliche[0])
                result["vergleich_min_qm"] = float(aehnliche[1])
                result["vergleich_max_qm"] = float(aehnliche[2])
                result["vergleich_anzahl"] = aehnliche[3]
                result["vergleich_geschaetzter_preis"] = float(aehnliche[0]) * wohnflaeche_qm

            return result

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Referenzpreise: {e}")
        return {}


# ==================== DOKUMENT-MANAGEMENT ====================

def create_dokument(
    nutzer_id: uuid.UUID,
    dokumenttyp: DokumentTyp,
    dateiname: str,
    datei_bytes: bytes = None,
    projekt_id: uuid.UUID = None,
    **kwargs
) -> Optional[Dokument]:
    """
    Speichert ein Dokument in der Datenbank.
    """
    try:
        with get_session() as session:
            # Hash für Duplikaterkennung
            datei_hash = hashlib.md5(datei_bytes).hexdigest() if datei_bytes else None

            dokument = Dokument(
                nutzer_id=nutzer_id,
                projekt_id=projekt_id,
                dokumenttyp=dokumenttyp,
                dateiname=dateiname,
                datei_bytes=datei_bytes,
                dateigroesse=len(datei_bytes) if datei_bytes else 0,
                datei_hash=datei_hash,
                **kwargs
            )
            session.add(dokument)
            session.commit()

            # Interaktion tracken
            track_interaktion(
                typ=InteraktionsTyp.DOCUMENT_UPLOAD,
                nutzer_id=nutzer_id,
                projekt_id=projekt_id,
                details={
                    "dokumenttyp": dokumenttyp.value,
                    "dateiname": dateiname
                }
            )

            return dokument

    except Exception as e:
        logger.error(f"Fehler beim Speichern des Dokuments: {e}")
        return None


def update_dokument_ocr(
    dokument_id: uuid.UUID,
    ocr_text: str,
    ocr_konfidenz: float,
    extrahierte_daten: Dict[str, Any] = None,
    ocr_engine: str = "tesseract"
) -> bool:
    """
    Aktualisiert ein Dokument mit OCR-Ergebnissen.
    """
    try:
        with get_session() as session:
            dokument = session.query(Dokument).filter_by(id=dokument_id).first()
            if dokument:
                dokument.ocr_verarbeitet = True
                dokument.ocr_verarbeitet_am = datetime.utcnow()
                dokument.ocr_text = ocr_text
                dokument.ocr_konfidenz = ocr_konfidenz
                dokument.extrahierte_daten = extrahierte_daten
                dokument.ocr_engine = ocr_engine
                session.commit()
                return True
        return False

    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der OCR-Daten: {e}")
        return False


# ==================== BENACHRICHTIGUNGEN ====================

def create_benachrichtigung(
    empfaenger_id: uuid.UUID,
    titel: str,
    nachricht: str,
    typ: str = "info",
    absender_id: uuid.UUID = None,
    projekt_id: uuid.UUID = None,
    link: str = None
) -> Optional[Benachrichtigung]:
    """
    Erstellt eine Benachrichtigung für einen Nutzer.
    """
    try:
        with get_session() as session:
            benachrichtigung = Benachrichtigung(
                empfaenger_id=empfaenger_id,
                absender_id=absender_id,
                titel=titel,
                nachricht=nachricht,
                typ=typ,
                projekt_id=projekt_id,
                link=link
            )
            session.add(benachrichtigung)
            session.commit()
            return benachrichtigung

    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Benachrichtigung: {e}")
        return None


def get_ungelesene_benachrichtigungen(nutzer_id: uuid.UUID) -> List[Benachrichtigung]:
    """Gibt alle ungelesenen Benachrichtigungen für einen Nutzer zurück."""
    with get_session() as session:
        return session.query(Benachrichtigung).filter_by(
            empfaenger_id=nutzer_id,
            gelesen=False
        ).order_by(desc(Benachrichtigung.erstellt_am)).all()


def mark_benachrichtigung_gelesen(benachrichtigung_id: uuid.UUID) -> bool:
    """Markiert eine Benachrichtigung als gelesen."""
    try:
        with get_session() as session:
            benachrichtigung = session.query(Benachrichtigung).filter_by(
                id=benachrichtigung_id
            ).first()
            if benachrichtigung:
                benachrichtigung.gelesen = True
                benachrichtigung.gelesen_am = datetime.utcnow()
                session.commit()
                return True
        return False
    except Exception as e:
        logger.error(f"Fehler beim Markieren als gelesen: {e}")
        return False
