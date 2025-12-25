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

1. **Neues Dashboard-Design** - Einheitliches Widget-basiertes Design für alle Rollen
2. **Sidebar-Menü an erster Position** - Menü wird vor Suche/Aktionen angezeigt
3. **Abmelden nur im Topbar** - Abmelden-Button aus Sidebar-Menü entfernt
4. **Fixierte Topbar wiederhergestellt** - Rolle und User-Info immer sichtbar
