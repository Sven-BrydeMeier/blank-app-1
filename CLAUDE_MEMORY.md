# Claude Code Memory File - Immobilien-Transaktionsplattform

**Letzte Aktualisierung:** 2025-12-13
**Branch:** `claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt`
**Letzter Commit:** Feature: Umfassende Erweiterungen - Benachrichtigungen, Gating, Fristenmanagement, Mandanten-Portal

---

## Projekt-Übersicht

Dies ist eine **Streamlit-basierte Immobilien-Transaktionsplattform** (~28.500+ Zeilen), die die Kommunikation zwischen folgenden Parteien koordiniert:
- **Makler** - Erstellt Projekte, verwaltet Exposés, koordiniert Termine, kann Ausweise scannen, Parteien-Verwaltung
- **Käufer** - Lädt Bonitätsunterlagen hoch, akzeptiert Dokumente, bestätigt Termine, muss Rechtsdokumente akzeptieren
- **Verkäufer** - Stellt Unterlagen bereit, akzeptiert Dokumente, bestätigt Termine, muss Rechtsdokumente akzeptieren
- **Finanzierer** - Prüft Bonität, erstellt Finanzierungsangebote
- **Notar** - Aktenmanagement, Vertragserstellung, Beurkundung, Datenermittlung, Gesellschaften-Verwaltung

**Streamlit App URL:** https://blank-app-1-01jm3ycngfksr1qvslfzhqrz.streamlit.app/

---

## Dateistruktur

```
/home/user/blank-app-1/
├── streamlit_app.py      # Hauptanwendung (~25.000+ Zeilen)
├── requirements.txt      # Python-Abhängigkeiten
├── CLAUDE_MEMORY.md      # Diese Datei
└── .gitignore
```

---

## Kürzlich implementierte Features (2025-12-13)

### 0. NEUESTE ERWEITERUNGEN (aktuell)

#### Benachrichtigungs-Center mit Badge
- **Badge in Sidebar**: Zeigt Anzahl ungelesener Eingänge an
- **Typen**: Nachrichten, Dokumente, Termine, Freigaben, Fristen, Anforderungen, System
- **Antwortvorlagen**: 6 System-Vorlagen für schnelle Antworten
- **Funktionen**: `render_benachrichtigungs_badge()`, `render_eingaenge_center()`

#### Finanzierungs- und Legal-Gating
- **Gating-Prüfungen**: Workflow mit Abhängigkeiten (vorgaenger_ids)
- **Status**: OFFEN, IN_PRUEFUNG, FREIGEGEBEN, ABGELEHNT, WARTET
- **8 Standard-Prüfungen**: Identitätsnachweis, Datenschutz, Bonitätsprüfung, etc.
- **Funktionen**: `render_gating_uebersicht()`, `get_gating_status()`

#### Fristenmanagement
- **Automatische Fristenberechnung**: Ab Beurkundungsdatum
- **Fristtypen**: Widerrufsfrist, Zahlungsfrist, Grundbucheintragung, etc.
- **Erinnerungen**: Konfigurierbare Tage vor Ablauf
- **Funktionen**: `render_fristenmanagement()`, `erstelle_standard_fristen()`

#### Reporting-Dashboard
- **KPIs**: Projekte, Umsatz, Beurkundungen, Durchlaufzeit
- **Visualisierungen**: Metriken, Diagramme, Trends
- **Funktionen**: `render_reporting_dashboard()`, `berechne_kpis()`

#### Dokumenten-Versionierung
- **Versionskontrolle**: Entwurf, Zur Prüfung, Freigegeben, Signiert, Archiviert
- **Wasserzeichen**: Automatisch für nicht-finale Versionen
- **Funktionen**: `render_dokument_versionen()`, `erstelle_dokument_version()`

#### Mandanten-Portal (Käufer/Verkäufer)
- **Schnellübersicht**: KPIs (Projekte, Nachrichten, Fristen, Termine)
- **Dringende Aufgaben**: Fehlende Unterlagen, ablaufende Fristen
- **Projekt-Status**: Gating-Fortschritt, beteiligte Parteien
- **Nächste Schritte**: Priorisierte Aufgabenliste
- **Funktionen**: `render_mandanten_portal()`

#### Vorlagen-Management System
- **Dokumentenvorlagen**: Kaufvertrag, Brief, E-Mail, Checkliste
- **Platzhalter-System**: `{{KAEUFER_NAME}}`, `{{KAUFPREIS}}`, etc.
- **System-Vorlagen**: 3 Standard-Vorlagen enthalten
- **Funktionen**: `render_vorlagen_management()`, `init_vorlagen_system()`

### 1. Kommunikations-Erweiterungen
- **Briefkopf-Administration**: Kanzlei-Logo, Firmenname, Adresse, Kontaktdaten, Bankverbindung, Design-Einstellungen
- **E-Mail-Signaturen**: Text- und HTML-Signaturen, Vorlagen für verschiedene Anlässe
- **Makler-Mitarbeiterverwaltung**: Mitarbeiter mit Rollen, Berechtigungen, Projekt-Zuweisungen
- **Kommunikationszentrale**: Posteingang, Postausgang, Entwürfe, Nachrichtenkategorien und -prioritäten
- **Intelligente Ordnerstruktur**: Templates für verschiedene Vertragstypen (Kaufvertrag, Testament, etc.)
- **Such- und Filterfunktionen**: Erweiterte Suche, gespeicherte Suchen, Volltextsuche
- **Sicherheitsfeatures**: Sicherheitsstufen (Öffentlich, Intern, Vertraulich, Streng vertraulich), Audit-Log

#### Neue Datenstrukturen:
```python
class NachrichtenPrioritaet(Enum): NORMAL, HOCH, DRINGEND
class NachrichtenKategorie(Enum): ANFRAGE, INFORMATION, DOKUMENT, TERMIN, FREIGABE, ERINNERUNG
class Sicherheitsstufe(Enum): OEFFENTLICH, INTERN, VERTRAULICH, STRENG_VERTRAULICH
class MaklerBerechtigungTyp(Enum): 18 verschiedene Berechtigungen
class MaklerMitarbeiterRolle(Enum): MITARBEITER, TEAMLEITER, PARTNER

@dataclass Briefkopf: Logo, Firmenname, Adresse, Kontakt, Bank, Design
@dataclass EmailSignatur: Text/HTML, Vorlagen, Standard-Kennzeichnung
@dataclass MaklerMitarbeiter: Rolle, Berechtigungen, Projekt-Zuweisungen
@dataclass KommunikationsNachricht: Empfänger, Priorität, Kategorie, Sicherheitsstufe
@dataclass KommunikationsAnlage: Dateien mit Sicherheitsklassifizierung
@dataclass AktenOrdner: Hierarchische Ordnerstruktur für Akten
@dataclass GespeicherteSuche: Wiederverwendbare Suchabfragen
@dataclass AuditLogEintrag: Protokollierung aller Aktionen
```

### 2. Akten-Management mit Gesellschaften
- **Automatische Aktenzeichen-Generierung**: Format `Nummer/Jahr Verkäufer / Käufer`
- **Gesellschaften als Vertragsparteien**: GmbH, UG, AG, KG, OHG, GbR, eG, SE, KGaA
- **Organe/Vertretungsberechtigte**: Geschäftsführer, Vorstand, Prokurist mit Einzelvertretungsbefugnis
- **Handelsregister-Abfrage**: API oder manuelle Eingabe
- **Automatische Akte-Erstellung** bei Projekt-Notar-Verknüpfung
- **Parteien-Verwaltung UI** in Makler- und Notar-Dashboard

### 2. Dynamische Unterbereich-Auswahl in Aktenanlage
- Hauptbereich außerhalb des Formulars für dynamische Aktualisierung
- Unterbereiche werden basierend auf Hauptbereich gefiltert:
  - **Erbrecht**: Einzeltestament, Gemeinschaftliches Testament, Erbvertrag, Erbausschlagung, Erbschein
  - **Zivilrecht**: Not. Kaufvertrag, Überlassungsvertrag, Ehevertrag, Scheidungsfolgenvereinbarung, Vorsorgevertrag
  - **Gesellschaftsrecht**: Gründung, Liquidation, Anteilsverkauf/-abtretung

### 3. Bug-Fixes
- Dataclass-Feldreihenfolge in `Gesellschaft` korrigiert
- Doppelte `AktenStatus` Enum-Definition entfernt und zusammengeführt

---

## Wichtige Datenstrukturen

### Neue Enums (Zeilen ~3758-3786)
```python
class Rechtsform(Enum):
    NATUERLICHE_PERSON, GMBH, UG, AG, KG, OHG, GbR, eG, SE, KGaA, GMBH_CO_KG, STIFTUNG, VEREIN

class OrganTyp(Enum):
    GESCHAEFTSFUEHRER, VORSTAND, PROKURIST, KOMPLEMENTAER, KOMMANDITIST, GESELLSCHAFTER, LIQUIDATOR
```

### Neue Dataclasses (Zeilen ~3788-3921)
```python
@dataclass
class Organ:
    organ_id, gesellschaft_id, name, vorname, geburtsdatum, organ_typ
    einzelvertretungsberechtigt: bool

@dataclass
class HandelsregisterEintrag:
    hr_id, gesellschaft_id, registergericht, registerart, registernummer

@dataclass
class Gesellschaft:
    gesellschaft_id, firma, projekt_id, rechtsform, organe, hr_abfrage_erfolgt

@dataclass
class Partei:
    partei_id, projekt_id, ist_gesellschaft, user_id, gesellschaft_id, rolle

@dataclass
class NotarAktenzeichen:
    notar_id, jahr, letzte_nummer
```

### Erweiterte Projekt-Klasse (Zeilen ~3313-3322)
```python
akte_id: str = ""           # Verweis auf ImportierteAkte beim Notar
aktenzeichen: str = ""      # z.B. "123/2025 Müller / Schmidt"
parteien: List[str]         # Liste der Partei-IDs
gesellschaften: List[str]   # Liste der Gesellschaft-IDs
vertragstyp: str = "Kaufvertrag"
```

### AktenStatus Enum (Zeile ~3713)
```python
class AktenStatus(Enum):
    IMPORTIERT, NEU, IN_BEARBEITUNG, WARTET_AUF_UNTERLAGEN, VOLLSTAENDIG
    BEURKUNDUNG_VORBEREITET, BEURKUNDET, VOLLZUG, ABGESCHLOSSEN, ARCHIVIERT, STORNIERT
```

---

## Dashboard-Struktur

### Notar-Dashboard (21 Tabs, Zeile ~17886)
| Tab | Inhalt |
|-----|--------|
| 0 | Timeline |
| 1 | Projekte (mit Parteien-Verwaltung) |
| 2 | Aktenmanagement |
| 3 | Datenermittlung (Flurkarten, Grundbuch, Baulasten) |
| 4 | Preiseinigungen |
| 5 | Vertragsarchiv |
| 6 | Vertragserstellung |
| 7 | Checklisten |
| 8 | Dokumentenanforderungen |
| 9 | Mitarbeiter |
| 10 | Finanzierungsnachweise |
| 11 | Dokumenten-Freigaben |
| 12 | Kaufvertrag |
| 13 | Termine |
| 14 | Maklerempfehlung |
| 15 | Handwerker |
| 16 | Ausweisdaten |
| 17 | Rechtsdokumente |
| 18 | Aktenimport |
| 19 | **Nachrichten (NEU)** - Kommunikationszentrale |
| 20 | Einstellungen (mit Briefkopf, E-Mail-Signaturen) |

### Makler-Dashboard (13 Tabs, Zeile ~11341)
| Tab | Inhalt |
|-----|--------|
| 0-2 | Timeline, Projekte, Marktanalyse |
| 3-5 | Profil, Bankenmappe, Rechtliche Dokumente |
| 6-8 | Teilnehmer-Status, Einladungen, Kommentare |
| 9 | Ausweisdaten erfassen |
| 10 | Termine |
| 11 | **Mitarbeiter (NEU)** - Mitarbeiterverwaltung |
| 12 | **Nachrichten (NEU)** - Kommunikationszentrale |

---

## Session State Strukturen (Zeilen ~5105-5126)

```python
st.session_state.users = {}              # User-ID -> User
st.session_state.projekte = {}           # Projekt-ID -> Projekt
st.session_state.akten = {}              # Akte-ID -> Akte
st.session_state.importierte_akten = {}  # Akte-ID -> ImportierteAkte
st.session_state.gesellschaften = {}     # Gesellschaft-ID -> Gesellschaft
st.session_state.organe = {}             # Organ-ID -> Organ
st.session_state.hr_eintraege = {}       # HR-ID -> HandelsregisterEintrag
st.session_state.parteien = {}           # Partei-ID -> Partei
st.session_state.aktenzeichen_zaehler = {}  # "notar_id_jahr" -> Nummer

# ===== KOMMUNIKATIONS-ERWEITERUNGEN (NEU) =====
st.session_state.briefkoepfe = {}        # Briefkopf-ID -> Briefkopf
st.session_state.email_signaturen = {}   # Signatur-ID -> EmailSignatur
st.session_state.makler_mitarbeiter = {} # Mitarbeiter-ID -> MaklerMitarbeiter
st.session_state.nachrichten = {}        # Nachricht-ID -> KommunikationsNachricht
st.session_state.kommunikations_anlagen = {}  # Anlage-ID -> KommunikationsAnlage
st.session_state.akten_ordner = {}       # Ordner-ID -> AktenOrdner
st.session_state.gespeicherte_suchen = {} # Suche-ID -> GespeicherteSuche
st.session_state.audit_log = []          # Liste von AuditLogEintrag
```

---

## Wichtige Funktionen

### Aktenzeichen-Generierung (Zeilen ~22812-22993)
```python
def generiere_aktenzeichen(notar_id: str) -> str
def erstelle_aktenbezeichnung(projekt: Projekt) -> str
def erstelle_akte_fuer_projekt(projekt: Projekt, notar_id: str) -> ImportierteAkte
def verknuepfe_projekt_mit_notar(projekt_id: str, notar_id: str) -> ImportierteAkte
def aktualisiere_aktenbezeichnung(projekt: Projekt) -> None
```

### Parteien-Verwaltung (Zeilen ~23005-23300)
```python
def render_parteien_verwaltung(projekt: Projekt, user_rolle: str)
def render_partei_sektion(projekt: Projekt, rolle: str, user_rolle: str)
def render_neue_partei_formular(projekt: Projekt, rolle: str)
def render_gesellschaft_formular(projekt: Projekt, rolle: str)
def render_gesellschaft_details(gesellschaft: Gesellschaft)
def render_handelsregister_abfrage(gesellschaft: Gesellschaft)
def render_organ_verwaltung(gesellschaft: Gesellschaft)
```

### Akten-Untertypen (Zeile ~5673)
```python
def get_verfuegbare_untertypen(hauptbereich: str, notar_id: str) -> List[str]
```

### Kommunikations-Funktionen (Zeilen ~25334-26313)
```python
def audit_log_eintrag(user_id: str, aktion: str, objekt_typ: str, objekt_id: str, details: str = "")
def render_briefkopf_administration(user_id: str)
def render_email_signaturen(user_id: str)
def render_makler_mitarbeiter_verwaltung(makler_id: str)
def render_kommunikationszentrale(user_id: str, projekt_id: str = None)
def _render_nachrichten_liste(user_id: str, typ: str)
def _render_neue_nachricht_form(user_id: str)
def _get_user_projekte(user_id: str) -> List[Projekt]
def _get_moegliche_empfaenger(user_id: str, projekt_id: str) -> List[User]
def render_akten_ordner_struktur(akte_id: str)
def _erstelle_ordner_struktur(akte_id: str, template_name: str)
def render_erweiterte_suche(user_id: str, kontext: str)
def render_audit_log(user_id: str = None)
```

---

## Bekannte Probleme & Lösungen

### 1. Dataclass-Feldreihenfolge
Felder ohne Default-Wert MÜSSEN vor Feldern mit Default-Wert stehen:
```python
# RICHTIG:
@dataclass
class Foo:
    required: str           # Ohne Default zuerst
    optional: str = ""      # Mit Default danach
```

### 2. Doppelte Tab-Indices
Streamlit erfordert eindeutige Keys bei `with tabs[X]:` - keine doppelten Indices!

### 3. Doppelte Enum-Definitionen
Enum-Klassen nur einmal definieren, sonst überschreibt die zweite die erste.

### 4. Dynamische Auswahl in Formularen
Selectboxen innerhalb von `st.form()` aktualisieren sich nicht dynamisch.
Lösung: Abhängige Selectboxen AUSSERHALB des Formulars platzieren.

---

## Git-Workflow

```bash
# Entwicklungs-Branch
git checkout claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt

# Push
git push -u origin claude/add-financing-legal-gating-01AEscKnmtL6eoduFCZPhBPt
```

---

## Letzte Commits

| Hash | Beschreibung |
|------|--------------|
| 4fc846f | Feature: Kommunikations-Features in Dashboards integriert |
| ca6b488 | Docs: Vorschläge für Kommunikations-Erweiterungen |
| 9906756 | Docs: Aktualisierte Gedächtnisdatei mit neuen Features |
| 2b27870 | Feature: Dynamische Unterbereich-Auswahl in Aktenanlage |
| 26cf550 | Fix: Doppelte AktenStatus Enum-Definition entfernt |
| d05f658 | Fix: Gesellschaft Dataclass-Feldreihenfolge korrigiert |

---

## Nächste mögliche Schritte

1. Integration echter Handelsregister-API
2. PDF-Export für Akten und Verträge
3. E-Mail-Benachrichtigungen
4. Erweiterte Suchfunktionen
5. Berichtswesen und Statistiken
6. Finanzierungs-Gating (Legal-Prüfung vor Finanzierung)
