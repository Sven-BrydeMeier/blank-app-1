# ImmoFlow - Digitale Immobilientransaktionen

Eine umfassende Streamlit-Webanwendung zur digitalen Abwicklung von Immobilientransaktionen. ImmoFlow verbindet alle Beteiligten eines Immobilienkaufs auf einer Plattform.

## Funktionen

### Multi-Rollen-System
- **Makler** - Projektmanagement, Exposé-Erstellung, Teilnehmer-Einladung
- **Käufer** - Finanzierung, Dokumenten-Upload, Aufgaben-Tracking
- **Verkäufer** - Preisfindung, Dokumentenbereitstellung, Makler-Suche
- **Finanzierer** - Wirtschaftsdaten-Prüfung, Finanzierungsangebote
- **Notar** - Aktenverwaltung, Beurkundung, Grundbuch-Prozess

### Kernfunktionen
- Dashboard mit Widgets (Heute, Aufgaben, Nachrichten, Vorgänge, Timeline, Dokumente)
- PDF-Import mit OCR-Extraktion (Aktenvorblatt-Parser)
- Projekt-Timeline mit Fortschrittsanzeige
- Kommunikationszentrale für alle Beteiligten
- Terminverwaltung mit Kalender
- Dokumenten-Management mit Versionierung
- Aktentasche zum Sammeln von Dokumenten
- Hell/Dunkel-Design-Modus

### Design
- Einheitliches Widget-basiertes Dashboard-Design
- Fixierte Topbar mit Rolle und User-Info
- Sidebar-Navigation mit Menü, Suche und Aktionen
- Responsive Design

## Installation

1. Requirements installieren:
   ```bash
   pip install -r requirements.txt
   ```

2. App starten:
   ```bash
   streamlit run streamlit_app.py
   ```

## Demo-Zugangsdaten

| Rolle | Email | Passwort |
|-------|-------|----------|
| Makler | makler@demo.de | makler123 |
| Käufer | kaeufer@demo.de | kaeufer123 |
| Verkäufer | verkaeufer@demo.de | verkaeufer123 |
| Finanzierer | finanz@demo.de | finanz123 |
| Notar | notar@demo.de | notar123 |

## Technologie

- **Frontend:** Streamlit (Python)
- **Styling:** Custom CSS mit Navy-Gold Theme
- **OCR:** PDF-Textextraktion
- **Authentifizierung:** Session-basiert

## Lizenz

Proprietär - Alle Rechte vorbehalten.
