"""
E-Mail-Benachrichtigungen für Löschungsbewilligungen

Versendet automatische Benachrichtigungen bei:
- Neuen Aufträgen
- Status-Änderungen
- Frist-Erinnerungen
- Erhaltenen Bewilligungen
"""

import smtplib
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Dict, Any
from uuid import UUID

from .models import LBCase, LBCaseStatus, LBOrganization


# ==================== KONFIGURATION ====================

@dataclass
class LBEmailConfig:
    """SMTP-Konfiguration für E-Mail-Versand"""
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    use_tls: bool = True

    from_email: str = "noreply@notariat.de"
    from_name: str = "Notariat - Löschungsbewilligungen"

    # Vorlagen-Einstellungen
    footer_text: str = "Diese E-Mail wurde automatisch generiert."


# ==================== BENACHRICHTIGUNGSTYPEN ====================

class LBNotificationType:
    """Typen von Benachrichtigungen"""
    NEUER_AUFTRAG = "neuer_auftrag"
    STATUS_GEAENDERT = "status_geaendert"
    BEWILLIGUNG_ERHALTEN = "bewilligung_erhalten"
    FRIST_ERINNERUNG = "frist_erinnerung"
    AUFTRAG_ABGESCHLOSSEN = "auftrag_abgeschlossen"


# ==================== E-MAIL TEMPLATES ====================

EMAIL_TEMPLATES = {
    LBNotificationType.NEUER_AUFTRAG: {
        "subject": "Neuer Löschungsbewilligungs-Auftrag: {aktenzeichen}",
        "body": """
Sehr geehrte Damen und Herren,

ein neuer Auftrag für eine Löschungsbewilligung wurde eingereicht.

**Auftragsdetails:**
- Aktenzeichen: {aktenzeichen}
- Grundbuch: {grundbuch} Blatt {gb_blatt}
- Eigentümer: {empfaenger_name}
- Zu löschendes Recht: Abt. {abteilung} lfd. Nr. {lfd_nr} - {recht_art}

Bitte bearbeiten Sie diesen Auftrag im Kanzlei-Backoffice.

Mit freundlichen Grüßen
{kanzlei_name}
        """.strip()
    },

    LBNotificationType.STATUS_GEAENDERT: {
        "subject": "Status-Änderung: {aktenzeichen} - {neuer_status}",
        "body": """
Sehr geehrte Damen und Herren,

der Status Ihres Auftrags wurde geändert.

**Auftragsdetails:**
- Aktenzeichen: {aktenzeichen}
- Grundbuch: {grundbuch} Blatt {gb_blatt}
- Alter Status: {alter_status}
- Neuer Status: {neuer_status}

{zusatz_info}

Mit freundlichen Grüßen
{kanzlei_name}
        """.strip()
    },

    LBNotificationType.BEWILLIGUNG_ERHALTEN: {
        "subject": "Löschungsbewilligung erhalten: {aktenzeichen}",
        "body": """
Sehr geehrte Damen und Herren,

für Ihren Auftrag wurde eine Löschungsbewilligung erhalten.

**Auftragsdetails:**
- Aktenzeichen: {aktenzeichen}
- Grundbuch: {grundbuch} Blatt {gb_blatt}
- Gläubiger: {glaeubiger_name}

Die Löschungsbewilligung kann nun im Rahmen der weiteren Abwicklung
verwendet werden.

Mit freundlichen Grüßen
{kanzlei_name}
        """.strip()
    },

    LBNotificationType.FRIST_ERINNERUNG: {
        "subject": "⚠️ Frist-Erinnerung: {aktenzeichen} - Frist am {frist_datum}",
        "body": """
Sehr geehrte Damen und Herren,

für folgenden Auftrag steht eine Frist an:

**Auftragsdetails:**
- Aktenzeichen: {aktenzeichen}
- Grundbuch: {grundbuch} Blatt {gb_blatt}
- Frist: {frist_datum}
- Verbleibende Tage: {verbleibende_tage}

Bitte stellen Sie sicher, dass die notwendigen Schritte rechtzeitig
erfolgen.

Mit freundlichen Grüßen
{kanzlei_name}
        """.strip()
    },

    LBNotificationType.AUFTRAG_ABGESCHLOSSEN: {
        "subject": "✅ Auftrag abgeschlossen: {aktenzeichen}",
        "body": """
Sehr geehrte Damen und Herren,

Ihr Auftrag wurde erfolgreich abgeschlossen.

**Auftragsdetails:**
- Aktenzeichen: {aktenzeichen}
- Grundbuch: {grundbuch} Blatt {gb_blatt}
- Abgeschlossen am: {abschluss_datum}

Vielen Dank für Ihr Vertrauen.

Mit freundlichen Grüßen
{kanzlei_name}
        """.strip()
    }
}


# ==================== NOTIFICATION SERVICE ====================

@dataclass
class LBNotificationResult:
    """Ergebnis einer Benachrichtigung"""
    success: bool = False
    notification_type: str = ""
    recipient: str = ""
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None


class LBNotificationService:
    """
    Service für E-Mail-Benachrichtigungen

    Verwendung:
        config = LBEmailConfig(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass"
        )
        service = LBNotificationService(config)

        result = service.send_neue_auftrag_notification(case, organization, recipient)
    """

    def __init__(self, config: LBEmailConfig):
        self.config = config

    def send_notification(
        self,
        notification_type: str,
        recipient_email: str,
        context: Dict[str, Any]
    ) -> LBNotificationResult:
        """
        Versendet eine Benachrichtigung

        Args:
            notification_type: Typ der Benachrichtigung
            recipient_email: E-Mail-Adresse des Empfängers
            context: Dictionary mit Platzhalter-Werten

        Returns:
            LBNotificationResult
        """
        result = LBNotificationResult(
            notification_type=notification_type,
            recipient=recipient_email
        )

        template = EMAIL_TEMPLATES.get(notification_type)
        if not template:
            result.error_message = f"Unbekannter Benachrichtigungstyp: {notification_type}"
            return result

        try:
            # Subject und Body mit Kontext füllen
            subject = template["subject"].format(**context)
            body = template["body"].format(**context)

            # Footer hinzufügen
            body += f"\n\n---\n{self.config.footer_text}"

            # E-Mail erstellen
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = recipient_email

            # Plain-Text und HTML
            text_part = MIMEText(body, 'plain', 'utf-8')
            html_body = self._convert_to_html(body)
            html_part = MIMEText(html_body, 'html', 'utf-8')

            msg.attach(text_part)
            msg.attach(html_part)

            # E-Mail versenden
            self._send_email(msg, recipient_email)

            result.success = True
            result.sent_at = datetime.now()

        except Exception as e:
            result.error_message = str(e)

        return result

    def _send_email(self, msg: MIMEMultipart, recipient: str) -> None:
        """Versendet E-Mail über SMTP"""
        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
            if self.config.use_tls:
                server.starttls()
            if self.config.smtp_user and self.config.smtp_password:
                server.login(self.config.smtp_user, self.config.smtp_password)
            server.send_message(msg)

    def _convert_to_html(self, text: str) -> str:
        """Konvertiert Plain-Text zu einfachem HTML"""
        # Markdown-ähnliche Formatierung
        html = text.replace("\n\n", "</p><p>")
        html = html.replace("\n", "<br>")
        html = html.replace("**", "<strong>").replace("**", "</strong>")

        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                p {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <p>{html}</p>
        </body>
        </html>
        """

    # ==================== CONVENIENCE METHODS ====================

    def send_neuer_auftrag(
        self,
        case: LBCase,
        organization: LBOrganization,
        recipient_email: str
    ) -> LBNotificationResult:
        """Sendet Benachrichtigung über neuen Auftrag"""
        context = self._build_case_context(case, organization)
        return self.send_notification(
            LBNotificationType.NEUER_AUFTRAG,
            recipient_email,
            context
        )

    def send_status_geaendert(
        self,
        case: LBCase,
        organization: LBOrganization,
        recipient_email: str,
        alter_status: str,
        neuer_status: str,
        zusatz_info: str = ""
    ) -> LBNotificationResult:
        """Sendet Benachrichtigung über Status-Änderung"""
        context = self._build_case_context(case, organization)
        context.update({
            "alter_status": alter_status,
            "neuer_status": neuer_status,
            "zusatz_info": zusatz_info
        })
        return self.send_notification(
            LBNotificationType.STATUS_GEAENDERT,
            recipient_email,
            context
        )

    def send_bewilligung_erhalten(
        self,
        case: LBCase,
        organization: LBOrganization,
        recipient_email: str
    ) -> LBNotificationResult:
        """Sendet Benachrichtigung über erhaltene Bewilligung"""
        context = self._build_case_context(case, organization)
        return self.send_notification(
            LBNotificationType.BEWILLIGUNG_ERHALTEN,
            recipient_email,
            context
        )

    def send_frist_erinnerung(
        self,
        case: LBCase,
        organization: LBOrganization,
        recipient_email: str
    ) -> LBNotificationResult:
        """Sendet Frist-Erinnerung"""
        context = self._build_case_context(case, organization)

        if case.frist_datum:
            verbleibend = (case.frist_datum - date.today()).days
            context["frist_datum"] = case.frist_datum.strftime("%d.%m.%Y")
            context["verbleibende_tage"] = verbleibend
        else:
            context["frist_datum"] = "-"
            context["verbleibende_tage"] = "-"

        return self.send_notification(
            LBNotificationType.FRIST_ERINNERUNG,
            recipient_email,
            context
        )

    def send_auftrag_abgeschlossen(
        self,
        case: LBCase,
        organization: LBOrganization,
        recipient_email: str
    ) -> LBNotificationResult:
        """Sendet Benachrichtigung über Auftragsabschluss"""
        context = self._build_case_context(case, organization)
        context["abschluss_datum"] = date.today().strftime("%d.%m.%Y")
        return self.send_notification(
            LBNotificationType.AUFTRAG_ABGESCHLOSSEN,
            recipient_email,
            context
        )

    def _build_case_context(
        self,
        case: LBCase,
        organization: LBOrganization
    ) -> Dict[str, Any]:
        """Erstellt Kontext-Dictionary aus Case und Organisation"""
        return {
            "aktenzeichen": case.aktenzeichen or str(case.id)[:8],
            "grundbuch": case.grundbuch,
            "gb_blatt": case.gb_blatt,
            "gemarkung": case.gemarkung or "-",
            "flurstueck": case.flurstueck or "-",
            "empfaenger_name": case.empfaenger_name or "-",
            "abteilung": case.abteilung or "-",
            "lfd_nr": case.laufende_nummer or "-",
            "recht_art": case.recht_art or "-",
            "recht_betrag": f"{case.recht_betrag:,.2f} {case.recht_waehrung}" if case.recht_betrag else "-",
            "glaeubiger_name": case.glaeubiger_name or "-",
            "kanzlei_name": organization.name if organization else "Notariat",
            "notar_name": organization.notar_name if organization else "-",
        }


# ==================== FRIST-PRÜFUNG ====================

def get_faellige_fristen(
    cases: List[LBCase],
    tage_vorher: int = 3
) -> List[LBCase]:
    """
    Gibt alle Fälle zurück, deren Frist in den nächsten X Tagen fällig ist

    Args:
        cases: Liste der zu prüfenden Fälle
        tage_vorher: Tage vor der Frist

    Returns:
        Liste der fälligen Fälle
    """
    heute = date.today()
    grenze = heute + timedelta(days=tage_vorher)

    faellige = []
    for case in cases:
        if case.frist_datum and case.status not in [LBCaseStatus.ABGESCHLOSSEN, LBCaseStatus.STORNIERT]:
            if heute <= case.frist_datum <= grenze:
                faellige.append(case)

    return faellige


def get_ueberfaellige_fristen(cases: List[LBCase]) -> List[LBCase]:
    """Gibt alle überfälligen Fälle zurück"""
    heute = date.today()
    ueberfaellige = []

    for case in cases:
        if case.frist_datum and case.status not in [LBCaseStatus.ABGESCHLOSSEN, LBCaseStatus.STORNIERT]:
            if case.frist_datum < heute:
                ueberfaellige.append(case)

    return ueberfaellige
