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
            for u in st.session_state.users.values():
                if u.email == email and u.password_hash == hash_password(password):
                    user = u
                    break

            if user:
                st.session_state.current_user = user
                create_notification(
                    user.user_id,
                    "Willkommen zurück!",
                    f"Sie haben sich erfolgreich angemeldet als {user.role}.",
                    NotificationType.SUCCESS.value
                )
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
        makler_rechtliche_dokumente()

    with tabs[3]:
        makler_teilnehmer_status()

    with tabs[4]:
        makler_einladungen()

    with tabs[5]:
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

            # Exposé-Upload
            st.markdown("#### 📄 Exposé")
            if projekt.expose_pdf:
                st.success("✅ Exposé hochgeladen")
                st.download_button(
                    "📥 Exposé herunterladen",
                    projekt.expose_pdf,
                    file_name=f"Expose_{projekt.name}.pdf",
                    mime="application/pdf",
                    key=f"dl_expose_{projekt.projekt_id}"
                )

                if st.button("🔄 Neues Exposé hochladen", key=f"update_expose_{projekt.projekt_id}"):
                    st.session_state[f"upload_expose_{projekt.projekt_id}"] = True
                    st.rerun()
            else:
                st.info("Noch kein Exposé hochgeladen")
                st.session_state[f"upload_expose_{projekt.projekt_id}"] = True

            if st.session_state.get(f"upload_expose_{projekt.projekt_id}", False):
                expose_file = st.file_uploader(
                    "Exposé-PDF hochladen",
                    type=['pdf'],
                    key=f"expose_upload_{projekt.projekt_id}"
                )

                if expose_file:
                    if st.button("💾 Exposé speichern", key=f"save_expose_{projekt.projekt_id}"):
                        projekt.expose_pdf = expose_file.read()
                        st.session_state[f"upload_expose_{projekt.projekt_id}"] = False

                        # Timeline aktualisieren
                        for event_id in projekt.timeline_events:
                            event = st.session_state.timeline_events.get(event_id)
                            if event and event.titel == "Exposé hochgeladen" and not event.completed:
                                event.completed = True
                                event.completed_at = datetime.now()

                        update_projekt_status(projekt.projekt_id)

                        st.success("✅ Exposé erfolgreich hochgeladen!")
                        st.rerun()

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
    st.title("🏡 Verkäufer-Dashboard")

    if not st.session_state.current_user.onboarding_complete:
        onboarding_flow()
        return

    tabs = st.tabs(["📊 Timeline", "📋 Projekte", "💬 Nachrichten"])

    with tabs[0]:
        verkaeufer_timeline_view()

    with tabs[1]:
        verkaeufer_projekte_view()

    with tabs[2]:
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
            if projekt.adresse:
                st.markdown(f"**Adresse:** {projekt.adresse}")
            if projekt.kaufpreis > 0:
                st.markdown(f"**Kaufpreis:** {projekt.kaufpreis:,.2f} €")
            st.markdown(f"**Status:** {projekt.status}")

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
        "💰 Finanzierungsnachweise",
        "📄 Dokumenten-Freigaben",
        "📅 Termine"
    ])

    with tabs[0]:
        notar_timeline_view()

    with tabs[1]:
        notar_projekte_view()

    with tabs[2]:
        notar_finanzierungsnachweise()

    with tabs[3]:
        notar_dokumenten_freigaben()

    with tabs[4]:
        notar_termine()

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
        st.caption(f"Rolle: {st.session_state.current_user.role}")
        st.caption(f"E-Mail: {st.session_state.current_user.email}")

        if st.button("🚪 Abmelden", use_container_width=True):
            logout()

        render_notifications()

        st.markdown("---")
        st.markdown("### ℹ️ System-Info")
        st.caption(f"Benutzer: {len(st.session_state.users)}")
        st.caption(f"Projekte: {len(st.session_state.projekte)}")
        st.caption(f"Angebote: {len(st.session_state.financing_offers)}")

    # Hauptbereich
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
