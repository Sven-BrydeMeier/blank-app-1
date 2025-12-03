"""
Immobilien-Transaktionsplattform
Rollen: Makler, Käufer, Verkäufer, Finanzierer, Notar
"""

import streamlit as st
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import json
import io
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

# ============================================================================
# DATENMODELLE
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

class FinanzierungsStatus(Enum):
    ENTWURF = "Entwurf"
    GESENDET = "An Käufer gesendet"
    ANGENOMMEN = "Vom Käufer angenommen"
    ZURUECKGEZOGEN = "Zurückgezogen / gegenstandslos"

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
    sollzinsbindung: int  # Jahre
    tilgungssatz: float
    gesamtlaufzeit: int  # Jahre
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
    kategorie: str = "Noch zuzuordnen"  # Auto-Klassifizierung durch KI
    sichtbar_fuer_makler: bool = False
    sichtbar_fuer_notar: bool = False

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

@dataclass
class Projekt:
    """Immobilien-Projekt/Transaktion"""
    projekt_id: str
    name: str
    beschreibung: str
    expose_pdf: Optional[bytes] = None
    makler_id: str = ""
    kaeufer_ids: List[str] = field(default_factory=list)
    verkaeufer_ids: List[str] = field(default_factory=list)
    finanzierer_ids: List[str] = field(default_factory=list)
    notar_id: str = ""
    expose_nach_akzeptanz: bool = True
    created_at: datetime = field(default_factory=datetime.now)

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

        # Demo-Benutzer erstellen
        create_demo_users()
        create_demo_projekt()

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
        makler_id="makler1",
        kaeufer_ids=["kaeufer1"],
        verkaeufer_ids=["verkaeufer1"],
        finanzierer_ids=["finanzierer1"],
        notar_id="notar1"
    )
    st.session_state.projekte[projekt.projekt_id] = projekt

def hash_password(password: str) -> str:
    """Einfaches Password-Hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

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
            # Benutzer suchen
            user = None
            for u in st.session_state.users.values():
                if u.email == email and u.password_hash == hash_password(password):
                    user = u
                    break

            if user:
                st.session_state.current_user = user
                st.rerun()
            else:
                st.error("❌ Ungültige Anmeldedaten")

    # Demo-Zugangsdaten anzeigen
    with st.expander("📋 Demo-Zugangsdaten"):
        st.markdown("""
        **Makler:**
        E-Mail: `makler@demo.de` | Passwort: `makler123`

        **Käufer:**
        E-Mail: `kaeufer@demo.de` | Passwort: `kaeufer123`

        **Verkäufer:**
        E-Mail: `verkaeufer@demo.de` | Passwort: `verkaeufer123`

        **Finanzierer:**
        E-Mail: `finanz@demo.de` | Passwort: `finanz123`

        **Notar:**
        E-Mail: `notar@demo.de` | Passwort: `notar123`
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
        "📁 Projekte",
        "⚖️ Rechtliche Dokumente",
        "👥 Teilnehmer-Status"
    ])

    with tabs[0]:
        makler_projekte_view()

    with tabs[1]:
        makler_rechtliche_dokumente()

    with tabs[2]:
        makler_teilnehmer_status()

def makler_projekte_view():
    """Projekt-Übersicht für Makler"""
    st.subheader("Meine Projekte")

    # Projekte des Maklers
    makler_projekte = [p for p in st.session_state.projekte.values()
                       if p.makler_id == st.session_state.current_user.user_id]

    if not makler_projekte:
        st.info("Noch keine Projekte vorhanden.")
        if st.button("➕ Neues Projekt anlegen"):
            st.session_state.show_new_projekt_form = True
    else:
        for projekt in makler_projekte:
            with st.expander(f"🏘️ {projekt.name}", expanded=True):
                st.write(f"**Beschreibung:** {projekt.beschreibung}")
                st.write(f"**Käufer:** {len(projekt.kaeufer_ids)}")
                st.write(f"**Verkäufer:** {len(projekt.verkaeufer_ids)}")
                st.write(f"**Erstellt am:** {projekt.created_at.strftime('%d.%m.%Y')}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Bearbeiten", key=f"edit_{projekt.projekt_id}"):
                        st.info("Projekt-Bearbeitung (noch nicht implementiert)")
                with col2:
                    if st.button("👥 Teilnehmer verwalten", key=f"manage_{projekt.projekt_id}"):
                        st.info("Teilnehmer-Verwaltung (noch nicht implementiert)")

def makler_rechtliche_dokumente():
    """Verwaltung rechtlicher Dokumente"""
    st.subheader("⚖️ Rechtliche Dokumente / Mandanten-Setup")
    st.markdown("""
    Hier hinterlegen Sie die rechtlichen Standarddokumente, die Käufer und Verkäufer
    **vor Einsicht ins Exposé** akzeptieren müssen.
    """)

    # Dokumenten-Typen
    doc_types = [
        DocumentType.MAKLERAUFTRAG.value,
        DocumentType.DATENSCHUTZ.value,
        DocumentType.WIDERRUFSBELEHRUNG.value,
        DocumentType.WIDERRUFSVERZICHT.value
    ]

    for doc_type in doc_types:
        with st.expander(f"📄 {doc_type}", expanded=False):
            # Prüfen ob Dokument bereits existiert
            doc_key = f"{st.session_state.current_user.user_id}_{doc_type}"
            existing_doc = st.session_state.legal_documents.get(doc_key)

            if existing_doc:
                st.success(f"✅ Version {existing_doc.version} vom {existing_doc.created_at.strftime('%d.%m.%Y %H:%M')}")
                st.text_area("Aktueller Inhalt", existing_doc.content_text, height=150, disabled=True, key=f"view_{doc_key}")

                if st.button("🔄 Neue Version erstellen", key=f"update_{doc_key}"):
                    st.session_state[f"edit_mode_{doc_key}"] = True
                    st.rerun()

            # Edit-Modus oder neu
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
                        # Version berechnen
                        if existing_doc:
                            old_version = float(existing_doc.version.replace('v', ''))
                            new_version = f"v{old_version + 0.1:.1f}"
                        else:
                            new_version = "v1.0"

                        # Dokument speichern
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

    # Projekte durchgehen
    for projekt in st.session_state.projekte.values():
        if projekt.makler_id != st.session_state.current_user.user_id:
            continue

        st.markdown(f"### 🏘️ {projekt.name}")

        # Alle Teilnehmer sammeln
        teilnehmer_ids = projekt.kaeufer_ids + projekt.verkaeufer_ids

        if not teilnehmer_ids:
            st.info("Noch keine Teilnehmer eingeladen.")
            continue

        # Status-Tabelle
        status_data = []
        for user_id in teilnehmer_ids:
            user = st.session_state.users.get(user_id)
            if not user:
                continue

            # Prüfe Akzeptanz-Status
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

    makler_id = "makler1"  # In echter App: aus Projekt ermitteln

    # Dokumente laden
    doc_types = [
        DocumentType.MAKLERAUFTRAG.value,
        DocumentType.DATENSCHUTZ.value,
        DocumentType.WIDERRUFSBELEHRUNG.value,
        DocumentType.WIDERRUFSVERZICHT.value
    ]

    # Prüfen welche Dokumente noch nicht akzeptiert wurden
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

        # Dokument anzeigen
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

        # Checkbox für Akzeptanz
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

    # Fortfahren-Button
    if all_accepted or len(acceptances_to_save) == len([dt for dt in doc_types if f"{makler_id}_{dt}" in st.session_state.legal_documents]):
        if st.button("✅ Fortfahren & Exposé anzeigen", type="primary", use_container_width=True):
            # Akzeptanzen speichern
            for acc in acceptances_to_save:
                user.document_acceptances.append(acc)
            user.onboarding_complete = True
            st.success("✅ Alle Dokumente akzeptiert! Sie werden weitergeleitet...")
            st.rerun()
    else:
        st.info("⏳ Bitte akzeptieren Sie alle Dokumente, um fortzufahren.")

# ============================================================================
# KÄUFER-BEREICH
# ============================================================================

def kaeufer_dashboard():
    """Dashboard für Käufer"""
    st.title("🏠 Käufer-Dashboard")

    # Onboarding prüfen
    if not st.session_state.current_user.onboarding_complete:
        onboarding_flow()
        return

    # Hauptbereich
    tabs = st.tabs(["📋 Projekte", "💰 Finanzierung", "📄 Dokumente"])

    with tabs[0]:
        kaeufer_projekte_view()

    with tabs[1]:
        kaeufer_finanzierung_view()

    with tabs[2]:
        kaeufer_dokumente_view()

def kaeufer_projekte_view():
    """Projekt-Ansicht für Käufer"""
    st.subheader("Meine Projekte")

    user_id = st.session_state.current_user.user_id
    projekte = [p for p in st.session_state.projekte.values() if user_id in p.kaeufer_ids]

    if not projekte:
        st.info("Noch keine Projekte vorhanden.")
        return

    for projekt in projekte:
        with st.expander(f"🏘️ {projekt.name}", expanded=True):
            st.markdown(f"**Beschreibung:**  \n{projekt.beschreibung}")

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

    # Alle Angebote für Projekte des Käufers
    relevante_angebote = []
    for offer in st.session_state.financing_offers.values():
        projekt = st.session_state.projekte.get(offer.projekt_id)
        if projekt and user_id in projekt.kaeufer_ids:
            # Nur gesendete oder angenommene Angebote zeigen
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

            # Annahme-Bereich
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
                    # Angebot annehmen
                    offer.status = FinanzierungsStatus.ANGENOMMEN.value
                    offer.accepted_at = datetime.now()
                    offer.fuer_notar_markiert = notar_checkbox

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
    st.info("Laden Sie hier Ihre Bonitätsunterlagen für die Finanzierung hoch.")

    with st.form("wirtschaftsdaten_upload"):
        uploaded_files = st.file_uploader(
            "Dokumente auswählen",
            type=['pdf', 'jpg', 'png'],
            accept_multiple_files=True
        )

        doc_type = st.selectbox(
            "Dokumenten-Typ",
            [
                DocumentType.BWA.value,
                DocumentType.STEUERBESCHEID.value,
                DocumentType.GEHALTSABRECHNUNG.value,
                DocumentType.VERMOEGENSNACHWEIS.value,
                DocumentType.SONSTIGE.value
            ]
        )

        submit = st.form_submit_button("📤 Hochladen")

        if submit and uploaded_files:
            for file in uploaded_files:
                # In echter App: OCR und KI-Klassifizierung
                doc_id = f"wirt_{st.session_state.current_user.user_id}_{len(st.session_state.wirtschaftsdaten)}"

                doc = WirtschaftsdatenDokument(
                    doc_id=doc_id,
                    kaeufer_id=st.session_state.current_user.user_id,
                    doc_type=doc_type,
                    filename=file.name,
                    upload_date=datetime.now(),
                    pdf_data=file.read()
                )

                st.session_state.wirtschaftsdaten[doc_id] = doc

            st.success(f"✅ {len(uploaded_files)} Dokument(e) hochgeladen!")
            st.rerun()

    # Hochgeladene Dokumente anzeigen
    st.markdown("---")
    st.markdown("### 📋 Hochgeladene Dokumente")

    user_docs = [d for d in st.session_state.wirtschaftsdaten.values()
                 if d.kaeufer_id == st.session_state.current_user.user_id]

    if user_docs:
        for doc in user_docs:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"📄 {doc.filename}")
            with col2:
                st.caption(f"{doc.doc_type} | {doc.upload_date.strftime('%d.%m.%Y')}")
            with col3:
                st.download_button(
                    "📥",
                    doc.pdf_data,
                    file_name=doc.filename,
                    key=f"dl_{doc.doc_id}"
                )
    else:
        st.info("Noch keine Dokumente hochgeladen.")

def kaeufer_dokumente_view():
    """Dokumenten-Übersicht für Käufer"""
    st.subheader("📄 Meine Dokumente")
    st.info("Hier sehen Sie alle akzeptierten Dokumente.")

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

    # Onboarding prüfen
    if not st.session_state.current_user.onboarding_complete:
        onboarding_flow()
        return

    st.info("Verkäufer-Funktionen werden noch entwickelt.")

# ============================================================================
# FINANZIERER-BEREICH
# ============================================================================

def finanzierer_dashboard():
    """Dashboard für Finanzierer"""
    st.title("💼 Finanzierer-Dashboard")

    tabs = st.tabs([
        "📊 Wirtschaftsdaten Käufer",
        "💰 Finanzierungsangebote erstellen",
        "📋 Meine Angebote"
    ])

    with tabs[0]:
        finanzierer_wirtschaftsdaten_view()

    with tabs[1]:
        finanzierer_angebote_erstellen()

    with tabs[2]:
        finanzierer_angebote_liste()

def finanzierer_wirtschaftsdaten_view():
    """Einsicht in Wirtschaftsdaten der Käufer"""
    st.subheader("📊 Wirtschaftsdaten Käufer")

    # Alle Wirtschaftsdaten für Projekte des Finanzierers
    finanzierer_id = st.session_state.current_user.user_id
    relevante_projekte = [p for p in st.session_state.projekte.values()
                         if finanzierer_id in p.finanzierer_ids]

    if not relevante_projekte:
        st.info("Noch keine Projekte zugewiesen.")
        return

    for projekt in relevante_projekte:
        st.markdown(f"### 🏘️ {projekt.name}")

        # Wirtschaftsdaten der Käufer in diesem Projekt
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

            with st.expander(f"👤 {kaeufer_name}", expanded=True):
                # Dokumente nach Kategorie gruppieren
                kategorien = {}
                for doc in docs:
                    if doc.doc_type not in kategorien:
                        kategorien[doc.doc_type] = []
                    kategorien[doc.doc_type].append(doc)

                for kategorie, kategorie_docs in kategorien.items():
                    st.markdown(f"**{kategorie}** ({len(kategorie_docs)} Dokument(e))")
                    for doc in kategorie_docs:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"📄 {doc.filename}")
                            st.caption(f"Hochgeladen: {doc.upload_date.strftime('%d.%m.%Y %H:%M')}")
                        with col2:
                            st.download_button(
                                "📥 Download",
                                doc.pdf_data,
                                file_name=doc.filename,
                                key=f"fin_dl_{doc.doc_id}"
                            )
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
        # Projekt auswählen
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
            # Angebot erstellen
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

            if als_entwurf:
                st.success("✅ Angebot als Entwurf gespeichert!")
            else:
                st.success("✅ Angebot wurde an Käufer gesendet!")

            st.rerun()

def finanzierer_angebote_liste():
    """Liste aller Angebote des Finanzierers"""
    st.subheader("📋 Meine Finanzierungsangebote")

    finanzierer_id = st.session_state.current_user.user_id
    meine_angebote = [o for o in st.session_state.financing_offers.values()
                     if o.finanzierer_id == finanzierer_id]

    if not meine_angebote:
        st.info("Noch keine Angebote erstellt.")
        return

    # Nach Status gruppieren
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
                        st.success("✅ Angebot wurde gesendet!")
                        st.rerun()

# ============================================================================
# NOTAR-BEREICH
# ============================================================================

def notar_dashboard():
    """Dashboard für Notar"""
    st.title("⚖️ Notar-Dashboard")
    st.info("Notar-Funktionen werden noch entwickelt.")

# ============================================================================
# HAUPTANWENDUNG
# ============================================================================

def main():
    """Hauptanwendung"""
    st.set_page_config(
        page_title="Immobilien-Transaktionsplattform",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Session State initialisieren
    init_session_state()

    # Login-Check
    if st.session_state.current_user is None:
        login_page()
        return

    # Sidebar mit Benutzer-Info
    with st.sidebar:
        st.markdown("### 👤 Angemeldet als:")
        st.write(f"**{st.session_state.current_user.name}**")
        st.caption(f"Rolle: {st.session_state.current_user.role}")
        st.caption(f"E-Mail: {st.session_state.current_user.email}")

        if st.button("🚪 Abmelden", use_container_width=True):
            logout()

        st.markdown("---")
        st.markdown("### ℹ️ System-Info")
        st.caption(f"Benutzer: {len(st.session_state.users)}")
        st.caption(f"Projekte: {len(st.session_state.projekte)}")
        st.caption(f"Angebote: {len(st.session_state.financing_offers)}")

    # Hauptbereich - je nach Rolle
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
