# ImmoFlow - Projekt-Gedächtnis

## Projektübersicht

**ImmoFlow** ist eine umfassende Streamlit-Webanwendung für die digitale Abwicklung von Immobilientransaktionen. Die App verbindet alle Beteiligten eines Immobilienkaufs: Makler, Käufer, Verkäufer, Finanzierer (Banken) und Notare.

## Technische Details

- **Framework:** Streamlit (Python)
- **Hauptdatei:** `streamlit_app.py` (~37.000+ Zeilen)
- **Design:** Navy-Gold Theme mit Hell/Dunkel-Modus
- **Authentifizierung:** Session-basiert mit Cookie-Speicherung

## Demo-Zugangsdaten

| Rolle | Email | Passwort |
|-------|-------|----------|
| Makler | makler@demo.de | makler123 |
| Käufer | kaeufer@demo.de | kaeufer123 |
| Verkäufer | verkaeufer@demo.de | verkaeufer123 |
| Finanzierer | finanz@demo.de | finanz123 |
| Notar | notar@demo.de | notar123 |

## Dashboard-Struktur (Neues Design)

### Alle Rollen haben einheitliches Design mit:

**Fixierte Topbar:**
- Links: Rolle/Dashboard-Name mit Icon
- Mitte: Schnellaktionen
- Rechts: User-Info mit Abmelden-Link

**Sidebar (von oben nach unten):**
1. **Menü** - Navigation (Dashboard, Projekte, Timeline, Nachrichten, Dokumente, Termine, Einstellungen)
2. **Suche & Aktionen** - Suche, Benachrichtigungen, Neu, Design-Wechsel, Abmelden
3. **Aktentasche** - Dokumente sammeln
4. **Benachrichtigungs-Badge**

**Dashboard-Widgets:**
- Heute-Widget (Statistiken mit Badges)
- Aufgaben/Checkliste
- Nachrichten (zuletzt)
- Meine Vorgänge
- Timeline (Auszug)
- Dokumente (relevant)

### Rollen-spezifische Menüpunkte:

**Makler:**
- Dashboard, Projekte, Timeline, Nachrichten, Dokumente, Termine, Beteiligte, Bankenmappe, Einstellungen

**Käufer:**
- Dashboard, Projekte, Timeline, Finanzierung, Nachrichten, Dokumente, Termine, Einstellungen

**Verkäufer:**
- Dashboard, Projekte, Timeline, Preisfindung, Nachrichten, Dokumente, Termine, Einstellungen

**Finanzierer:**
- Dashboard, Projekte, Wirtschaftsdaten, Angebote, Termine, Einstellungen

**Notar:**
- Dashboard + erweitertes Notar-Menü (Akten, Vorgänge, Dokumente, Termine, etc.)
- **WICHTIG:** Beim Notar heißen "Projekte" immer "Akten"

### Notar-Dashboard (4-Quadranten-Layout)

Das Notar-Dashboard ist speziell auf den Notarworkflow zugeschnitten:

**Timeline am oberen Rand:**
- Zeigt Anzahl der Vorgänge pro Status-Kategorie (Vorbereitung, Finanzierung, Beurkundung, Nach Kaufvertrag, Abgeschlossen)

**4-Quadranten-Layout:**

| Links oben: Termine des Tages | Rechts oben: Posteingang |
|-------------------------------|--------------------------|
| - Datum oben angezeigt | - Neue Dokumente der Parteien |
| - Uhrzeit + Aktenzeichen + Kurzbezeichnung | - Datum, Aktenzeichen, Dokument, Absender |
| - Klick → öffnet Akte | - Status: erledigt/offen/dringend + Frist |
| | - Klick auf Dokument → direkt zum Dokument |
| | - Klick auf Aktenzeichen → zur Akte |

| Links unten: Urkundsentwurf erforderlich | Rechts unten: Beurkundete Verträge |
|------------------------------------------|-----------------------------------|
| - Akten mit allen Daten für Entwurf | - 3 Stadien als Tabs |
| - Button: Urkundenassistent (Step-by-Step) | - 1️⃣ Kaufpreisfälligkeit raus? |
| - Button: Urkunde-KI (automatischer Entwurf) | - 2️⃣ Kaufpreis Eingang bestätigt |
| | - 3️⃣ Auflassung/Grundschuld eingetragen |

**Akten-Detailansicht:**
- Zurück-Button zum Dashboard
- Timeline der Akte am oberen Rand
- Ordnerstruktur links: Entwürfe, Urkunden, Grundbuch, Parteien, Korrespondenz, Sonstiges
- Dokumente rechts (aktuell ausgewähltes Dokument wird highlighted)
- Dokumentaktionen: Als erledigt markieren, An Partei senden, In Entwurf übernehmen

**Notar-spezifische Funktionen:**
- `_render_notar_dashboard_home()` - Haupt-Dashboard mit 4-Quadranten
- `_render_notar_termine_widget()` - Termine des Tages (klickbar)
- `_render_notar_posteingang_widget()` - Posteingang (klickbar)
- `_render_notar_entwurf_widget()` - Urkundsentwurf-Akten (klickbar)
- `_render_notar_beurkundete_widget()` - Beurkundete Verträge nach 3 Stadien
- `_render_notar_akte_detail()` - Akten-Detailansicht mit Ordnerstruktur
- `_render_urkunden_assistent()` - Step-by-Step Urkundenerstellung
- `_render_urkunden_ki()` - KI-gestützte Urkundenerstellung

## Wichtige Funktionen

### Akten-Import (PDF)
- PDF-Upload mit OCR-Extraktion
- Aktenvorblatt-Parser für strukturierte Daten
- Zuordnung zu Projekten möglich
- PDF-Bytes werden im Session State gespeichert

### Design-System
- `inject_new_dashboard_css()` - Haupt-CSS für neues Design
- `render_dashboard_header()` - Header mit Titel, Suche, Profil
- `render_sidebar_menu()` - Sidebar-Menü mit aktiver Markierung
- `render_heute_widget()` - Tagesstatistiken
- `render_aufgaben_widget()` - Checkliste
- `render_nachrichten_widget()` - Nachrichten
- `render_vorgaenge_widget()` - Vorgänge
- `render_timeline_widget()` - Timeline
- `render_dokumente_widget()` - Dokumentenstatus

### Topbar-System
- `render_fixed_topbar()` - Fixierte Menüleiste oben
- `render_topbar_actions()` - Schnellaktionen in Sidebar (Suche, Design-Wechsel, Abmelden)

## Bekannte Einschränkungen

- JavaScript in `st.markdown()` wird nicht ausgeführt - alle Interaktionen müssen über native Streamlit-Komponenten laufen
- Suche und Aktionen in der HTML-Topbar sind nur visuell - echte Funktionalität über Sidebar-Buttons

## Code-Konventionen

- Deutsche Variablennamen und Kommentare
- Funktionspräfixe: `render_`, `_render_` (privat), `_get_` (Datenhelfer)
- Session State für alle persistenten Daten
- CSS-Injection via `st.markdown(unsafe_allow_html=True)`

## Letzte Änderungen

1. **Notar-Dashboard komplett überarbeitet** - 4-Quadranten-Layout mit klickbaren Widgets
2. **Termine des Tages** - Klickbare Termine mit Navigation zur Akte
3. **Posteingang** - Neue Dokumente von Parteien mit Status und Fristen
4. **Urkundsentwurf-Widget** - Akten die Entwurf benötigen mit Assistent/KI-Optionen
5. **Beurkundete Verträge** - 3 Stadien (Fälligkeit, Kaufpreis, Eingetragen)
6. **Akten-Detailansicht** - Ordnerstruktur (Entwürfe, Urkunden) mit Dokumentaktionen
7. **Timeline am oberen Rand** - Übersicht aller Vorgänge nach Status
8. **Alle Interaktionen klickbar** - Native Streamlit-Buttons statt HTML-only
