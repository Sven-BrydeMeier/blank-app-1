"""
Löschungsbewilligungen Modul

Automatisierte Erstellung von Löschungsbewilligungen (Anschreiben an
Eigentümer, Versorger und Gläubiger) mit Multi-Tenant-Architektur.

Komponenten:
- models: Datenmodelle und Enums
- excel_import: Excel-Import für Massenimport
- docgen: Dokumentgenerierung mit DOCX-Templates
- storage: Storage-Management für Dateien
- notifications: E-Mail-Benachrichtigungen
"""

from .models import (
    LBOrgRole,
    LBCaseStatus,
    LBDocumentType,
    LBOrganization,
    LBMembership,
    LBCase,
    LBDocument,
    LBUpload,
    LBTemplate,
    LBAuditLog,
)

from .excel_import import (
    LBExcelImporter,
    LBExcelColumnMapping,
    LBImportResult,
    LBImportError,
)

from .docgen import (
    LBDocumentGenerator,
    LBPlaceholder,
    LBGenerationResult,
)

from .notifications import (
    LBNotificationService,
    LBEmailConfig,
    LBNotificationType,
    LBNotificationResult,
    get_faellige_fristen,
    get_ueberfaellige_fristen,
)

__all__ = [
    # Models
    'LBOrgRole',
    'LBCaseStatus',
    'LBDocumentType',
    'LBOrganization',
    'LBMembership',
    'LBCase',
    'LBDocument',
    'LBUpload',
    'LBTemplate',
    'LBAuditLog',
    # Excel Import
    'LBExcelImporter',
    'LBExcelColumnMapping',
    'LBImportResult',
    'LBImportError',
    # DocGen
    'LBDocumentGenerator',
    'LBPlaceholder',
    'LBGenerationResult',
    # Notifications
    'LBNotificationService',
    'LBEmailConfig',
    'LBNotificationType',
    'LBNotificationResult',
    'get_faellige_fristen',
    'get_ueberfaellige_fristen',
]
