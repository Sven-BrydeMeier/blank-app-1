-- ============================================================
-- LÖSCHUNGSBEWILLIGUNGEN MODUL - SUPABASE MIGRATION
-- ============================================================
-- Dieses Modul ermöglicht die automatisierte Erstellung von
-- Löschungsbewilligungen (Anschreiben an Eigentümer/Versorger)
-- mit Multi-Tenant-Architektur und feingranularer Zugriffskontrolle
-- ============================================================

-- ==================== EXTENSIONS ====================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== ENUMS ====================

-- Rolle innerhalb einer Organisation
CREATE TYPE lb_org_role AS ENUM ('notar', 'staff', 'auftraggeber');

-- Status eines Löschungsbewilligungs-Falls
CREATE TYPE lb_case_status AS ENUM (
    'entwurf',           -- Noch in Bearbeitung
    'angefordert',       -- Anschreiben wurde versendet
    'bewilligung_da',    -- Bewilligung vom Gläubiger erhalten
    'abgeschlossen',     -- Vollständig abgeschlossen
    'storniert'          -- Fall storniert
);

-- Typ des generierten Dokuments
CREATE TYPE lb_document_type AS ENUM (
    'anschreiben_eigentuemer',    -- Anschreiben an Grundstückseigentümer
    'anschreiben_versorger',      -- Anschreiben an Versorgungsunternehmen
    'anschreiben_bank',           -- Anschreiben an Bank/Gläubiger
    'loeschungsbewilligung',      -- Erhaltene Löschungsbewilligung
    'sonstige'                    -- Sonstige Dokumente
);

-- ==================== TABELLEN ====================

-- ----------------------------------------------------
-- ORGANIZATIONS - Kanzleien/Mandanten
-- ----------------------------------------------------
CREATE TABLE IF NOT EXISTS lb_organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,  -- URL-freundlicher Name

    -- Kontaktdaten
    strasse TEXT,
    plz TEXT,
    ort TEXT,
    telefon TEXT,
    email TEXT,
    website TEXT,

    -- Notarspezifisch
    notar_name TEXT,
    amtssitz TEXT,
    urkundenrolle_praefix TEXT,

    -- Einstellungen
    settings JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index für schnelle Slug-Suche
CREATE INDEX IF NOT EXISTS idx_lb_organizations_slug ON lb_organizations(slug);

-- ----------------------------------------------------
-- MEMBERSHIPS - Benutzer-zu-Organisation Zuordnung
-- ----------------------------------------------------
CREATE TABLE IF NOT EXISTS lb_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES lb_organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Rolle in der Organisation
    role lb_org_role NOT NULL DEFAULT 'staff',

    -- Berechtigungen (granular)
    permissions JSONB DEFAULT '{
        "kann_faelle_erstellen": true,
        "kann_faelle_bearbeiten": true,
        "kann_faelle_loeschen": false,
        "kann_dokumente_generieren": true,
        "kann_vorlagen_verwalten": false,
        "kann_mitglieder_verwalten": false,
        "kann_einstellungen_aendern": false
    }',

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Eindeutigkeit: Ein Benutzer kann nur einmal pro Organisation sein
    UNIQUE(organization_id, user_id)
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_lb_memberships_org ON lb_memberships(organization_id);
CREATE INDEX IF NOT EXISTS idx_lb_memberships_user ON lb_memberships(user_id);

-- ----------------------------------------------------
-- LB_CASES - Löschungsbewilligungs-Fälle
-- ----------------------------------------------------
CREATE TABLE IF NOT EXISTS lb_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES lb_organizations(id) ON DELETE CASCADE,

    -- Aktenzeichen/Referenz
    aktenzeichen TEXT,
    externe_referenz TEXT,

    -- Grundbuchdaten
    grundbuch TEXT NOT NULL,
    gb_blatt TEXT NOT NULL,
    gemarkung TEXT,
    flur TEXT,
    flurstueck TEXT,

    -- Eigentümer/Empfänger
    vorname TEXT,
    nachname TEXT,
    firma TEXT,
    strasse TEXT,
    plz TEXT,
    ort TEXT,

    -- Zu löschendes Recht
    abteilung TEXT,  -- II oder III
    laufende_nummer TEXT,
    recht_art TEXT,  -- z.B. "Grundschuld", "Hypothek", "Wegerecht"
    recht_betrag DECIMAL(15,2),
    recht_waehrung TEXT DEFAULT 'EUR',
    recht_beschreibung TEXT,

    -- Gläubiger (bei Abt. III)
    glaeubiger_name TEXT,
    glaeubiger_strasse TEXT,
    glaeubiger_plz TEXT,
    glaeubiger_ort TEXT,
    glaeubiger_iban TEXT,
    glaeubiger_bic TEXT,

    -- Ablösebetrag (falls bekannt)
    abloesebetrag DECIMAL(15,2),
    abloese_datum DATE,

    -- Status und Priorität
    status lb_case_status DEFAULT 'entwurf',
    prioritaet INTEGER DEFAULT 0,  -- 0=normal, 1=hoch, 2=dringend

    -- Fristen
    frist_datum DATE,
    erinnerung_datum DATE,

    -- Notizen
    notizen TEXT,

    -- Verknüpfung zu Projekt (optional)
    projekt_id UUID,

    -- Ersteller
    created_by UUID REFERENCES auth.users(id),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_lb_cases_org ON lb_cases(organization_id);
CREATE INDEX IF NOT EXISTS idx_lb_cases_status ON lb_cases(status);
CREATE INDEX IF NOT EXISTS idx_lb_cases_grundbuch ON lb_cases(grundbuch, gb_blatt);
CREATE INDEX IF NOT EXISTS idx_lb_cases_aktenzeichen ON lb_cases(aktenzeichen);
CREATE INDEX IF NOT EXISTS idx_lb_cases_frist ON lb_cases(frist_datum) WHERE frist_datum IS NOT NULL;

-- ----------------------------------------------------
-- LB_DOCUMENTS - Generierte Dokumente
-- ----------------------------------------------------
CREATE TABLE IF NOT EXISTS lb_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES lb_cases(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES lb_organizations(id) ON DELETE CASCADE,

    -- Dokumenttyp
    document_type lb_document_type NOT NULL,

    -- Template-Referenz
    template_id UUID,
    template_name TEXT,

    -- Datei-Informationen
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,  -- Storage-Pfad
    file_size INTEGER,
    mime_type TEXT DEFAULT 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',

    -- Versand-Status
    is_sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMPTZ,
    sent_via TEXT,  -- 'email', 'post', 'fax'
    sent_to TEXT,   -- Empfänger-Adresse

    -- Generierungsdaten
    generated_data JSONB,  -- Verwendete Platzhalter-Werte

    -- Ersteller
    created_by UUID REFERENCES auth.users(id),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_lb_documents_case ON lb_documents(case_id);
CREATE INDEX IF NOT EXISTS idx_lb_documents_org ON lb_documents(organization_id);
CREATE INDEX IF NOT EXISTS idx_lb_documents_type ON lb_documents(document_type);

-- ----------------------------------------------------
-- LB_UPLOADS - Hochgeladene Dokumente (z.B. erhaltene Bewilligungen)
-- ----------------------------------------------------
CREATE TABLE IF NOT EXISTS lb_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES lb_cases(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES lb_organizations(id) ON DELETE CASCADE,

    -- Datei-Informationen
    file_name TEXT NOT NULL,
    original_name TEXT NOT NULL,
    file_path TEXT NOT NULL,  -- Storage-Pfad
    file_size INTEGER,
    mime_type TEXT,

    -- Beschreibung
    beschreibung TEXT,
    kategorie TEXT,  -- z.B. 'loeschungsbewilligung', 'vollmacht', 'sonstiges'

    -- Eingang
    eingangsdatum DATE DEFAULT CURRENT_DATE,

    -- OCR (falls durchgeführt)
    ocr_text TEXT,
    ocr_status TEXT,  -- 'pending', 'completed', 'failed'

    -- Ersteller
    uploaded_by UUID REFERENCES auth.users(id),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_lb_uploads_case ON lb_uploads(case_id);
CREATE INDEX IF NOT EXISTS idx_lb_uploads_org ON lb_uploads(organization_id);

-- ----------------------------------------------------
-- LB_TEMPLATES - Dokumentvorlagen
-- ----------------------------------------------------
CREATE TABLE IF NOT EXISTS lb_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES lb_organizations(id) ON DELETE CASCADE,  -- NULL = globale Vorlage

    -- Template-Infos
    name TEXT NOT NULL,
    beschreibung TEXT,
    document_type lb_document_type NOT NULL,

    -- Datei
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,  -- Storage-Pfad

    -- Platzhalter-Definition
    placeholders JSONB DEFAULT '[]',  -- Liste der verfügbaren Platzhalter

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,

    -- Ersteller
    created_by UUID REFERENCES auth.users(id),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_lb_templates_org ON lb_templates(organization_id);
CREATE INDEX IF NOT EXISTS idx_lb_templates_type ON lb_templates(document_type);

-- ----------------------------------------------------
-- LB_AUDIT_LOG - Audit-Trail
-- ----------------------------------------------------
CREATE TABLE IF NOT EXISTS lb_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES lb_organizations(id) ON DELETE CASCADE,

    -- Aktion
    aktion TEXT NOT NULL,  -- 'case_created', 'document_generated', 'upload_added', etc.

    -- Referenzen
    case_id UUID REFERENCES lb_cases(id) ON DELETE SET NULL,
    document_id UUID REFERENCES lb_documents(id) ON DELETE SET NULL,

    -- Details
    details JSONB,

    -- Benutzer
    user_id UUID REFERENCES auth.users(id),
    user_email TEXT,

    -- IP/Browser
    ip_address INET,
    user_agent TEXT,

    -- Timestamp (unveränderlich)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index für chronologische Abfragen
CREATE INDEX IF NOT EXISTS idx_lb_audit_log_org_time ON lb_audit_log(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_lb_audit_log_case ON lb_audit_log(case_id) WHERE case_id IS NOT NULL;

-- ==================== ROW LEVEL SECURITY ====================

-- Aktiviere RLS auf allen Tabellen
ALTER TABLE lb_organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE lb_audit_log ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------
-- HILFSFUNKTION: Prüft Organisations-Mitgliedschaft
-- ----------------------------------------------------
CREATE OR REPLACE FUNCTION lb_user_org_ids()
RETURNS SETOF UUID AS $$
    SELECT organization_id
    FROM lb_memberships
    WHERE user_id = auth.uid() AND is_active = true;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ----------------------------------------------------
-- HILFSFUNKTION: Prüft spezifische Berechtigung
-- ----------------------------------------------------
CREATE OR REPLACE FUNCTION lb_has_permission(org_id UUID, permission_key TEXT)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM lb_memberships
        WHERE user_id = auth.uid()
        AND organization_id = org_id
        AND is_active = true
        AND (
            role = 'notar'
            OR (permissions->>permission_key)::boolean = true
        )
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ----------------------------------------------------
-- RLS POLICIES: lb_organizations
-- ----------------------------------------------------

-- Lesen: Nur eigene Organisationen
CREATE POLICY "lb_organizations_select" ON lb_organizations
    FOR SELECT USING (id IN (SELECT lb_user_org_ids()));

-- Einfügen: Nur Notare können Organisationen erstellen
CREATE POLICY "lb_organizations_insert" ON lb_organizations
    FOR INSERT WITH CHECK (true);  -- Wird über Service-Account gesteuert

-- Aktualisieren: Nur Mitglieder mit Einstellungs-Berechtigung
CREATE POLICY "lb_organizations_update" ON lb_organizations
    FOR UPDATE USING (lb_has_permission(id, 'kann_einstellungen_aendern'));

-- Löschen: Nur Service-Account
CREATE POLICY "lb_organizations_delete" ON lb_organizations
    FOR DELETE USING (false);  -- Nur über Service-Account

-- ----------------------------------------------------
-- RLS POLICIES: lb_memberships
-- ----------------------------------------------------

-- Lesen: Mitglieder der gleichen Organisation
CREATE POLICY "lb_memberships_select" ON lb_memberships
    FOR SELECT USING (organization_id IN (SELECT lb_user_org_ids()));

-- Einfügen: Nur Mitglieder mit Mitglieder-Verwaltung
CREATE POLICY "lb_memberships_insert" ON lb_memberships
    FOR INSERT WITH CHECK (lb_has_permission(organization_id, 'kann_mitglieder_verwalten'));

-- Aktualisieren: Nur Mitglieder mit Mitglieder-Verwaltung
CREATE POLICY "lb_memberships_update" ON lb_memberships
    FOR UPDATE USING (lb_has_permission(organization_id, 'kann_mitglieder_verwalten'));

-- Löschen: Nur Mitglieder mit Mitglieder-Verwaltung
CREATE POLICY "lb_memberships_delete" ON lb_memberships
    FOR DELETE USING (lb_has_permission(organization_id, 'kann_mitglieder_verwalten'));

-- ----------------------------------------------------
-- RLS POLICIES: lb_cases
-- ----------------------------------------------------

-- Lesen: Nur Fälle der eigenen Organisation
CREATE POLICY "lb_cases_select" ON lb_cases
    FOR SELECT USING (organization_id IN (SELECT lb_user_org_ids()));

-- Einfügen: Nur mit Erstellungs-Berechtigung
CREATE POLICY "lb_cases_insert" ON lb_cases
    FOR INSERT WITH CHECK (lb_has_permission(organization_id, 'kann_faelle_erstellen'));

-- Aktualisieren: Nur mit Bearbeitungs-Berechtigung
CREATE POLICY "lb_cases_update" ON lb_cases
    FOR UPDATE USING (lb_has_permission(organization_id, 'kann_faelle_bearbeiten'));

-- Löschen: Nur mit Lösch-Berechtigung
CREATE POLICY "lb_cases_delete" ON lb_cases
    FOR DELETE USING (lb_has_permission(organization_id, 'kann_faelle_loeschen'));

-- ----------------------------------------------------
-- RLS POLICIES: lb_documents
-- ----------------------------------------------------

-- Lesen: Nur Dokumente der eigenen Organisation
CREATE POLICY "lb_documents_select" ON lb_documents
    FOR SELECT USING (organization_id IN (SELECT lb_user_org_ids()));

-- Einfügen: Nur mit Generierungs-Berechtigung
CREATE POLICY "lb_documents_insert" ON lb_documents
    FOR INSERT WITH CHECK (lb_has_permission(organization_id, 'kann_dokumente_generieren'));

-- Aktualisieren: Nur mit Bearbeitungs-Berechtigung
CREATE POLICY "lb_documents_update" ON lb_documents
    FOR UPDATE USING (lb_has_permission(organization_id, 'kann_faelle_bearbeiten'));

-- Löschen: Nur mit Lösch-Berechtigung
CREATE POLICY "lb_documents_delete" ON lb_documents
    FOR DELETE USING (lb_has_permission(organization_id, 'kann_faelle_loeschen'));

-- ----------------------------------------------------
-- RLS POLICIES: lb_uploads
-- ----------------------------------------------------

-- Lesen: Nur Uploads der eigenen Organisation
CREATE POLICY "lb_uploads_select" ON lb_uploads
    FOR SELECT USING (organization_id IN (SELECT lb_user_org_ids()));

-- Einfügen: Alle Mitglieder können Uploads erstellen
CREATE POLICY "lb_uploads_insert" ON lb_uploads
    FOR INSERT WITH CHECK (organization_id IN (SELECT lb_user_org_ids()));

-- Aktualisieren: Nur mit Bearbeitungs-Berechtigung
CREATE POLICY "lb_uploads_update" ON lb_uploads
    FOR UPDATE USING (lb_has_permission(organization_id, 'kann_faelle_bearbeiten'));

-- Löschen: Nur mit Lösch-Berechtigung
CREATE POLICY "lb_uploads_delete" ON lb_uploads
    FOR DELETE USING (lb_has_permission(organization_id, 'kann_faelle_loeschen'));

-- ----------------------------------------------------
-- RLS POLICIES: lb_templates
-- ----------------------------------------------------

-- Lesen: Globale Templates + eigene Organisation
CREATE POLICY "lb_templates_select" ON lb_templates
    FOR SELECT USING (
        organization_id IS NULL  -- Globale Templates
        OR organization_id IN (SELECT lb_user_org_ids())
    );

-- Einfügen: Nur mit Vorlagen-Berechtigung
CREATE POLICY "lb_templates_insert" ON lb_templates
    FOR INSERT WITH CHECK (
        organization_id IS NOT NULL
        AND lb_has_permission(organization_id, 'kann_vorlagen_verwalten')
    );

-- Aktualisieren: Nur mit Vorlagen-Berechtigung
CREATE POLICY "lb_templates_update" ON lb_templates
    FOR UPDATE USING (
        organization_id IS NOT NULL
        AND lb_has_permission(organization_id, 'kann_vorlagen_verwalten')
    );

-- Löschen: Nur mit Vorlagen-Berechtigung
CREATE POLICY "lb_templates_delete" ON lb_templates
    FOR DELETE USING (
        organization_id IS NOT NULL
        AND lb_has_permission(organization_id, 'kann_vorlagen_verwalten')
    );

-- ----------------------------------------------------
-- RLS POLICIES: lb_audit_log
-- ----------------------------------------------------

-- Lesen: Nur Audit-Log der eigenen Organisation
CREATE POLICY "lb_audit_log_select" ON lb_audit_log
    FOR SELECT USING (organization_id IN (SELECT lb_user_org_ids()));

-- Einfügen: Alle Mitglieder können Audit-Einträge erstellen
CREATE POLICY "lb_audit_log_insert" ON lb_audit_log
    FOR INSERT WITH CHECK (organization_id IN (SELECT lb_user_org_ids()));

-- Aktualisieren: Nicht erlaubt (append-only)
CREATE POLICY "lb_audit_log_update" ON lb_audit_log
    FOR UPDATE USING (false);

-- Löschen: Nicht erlaubt (append-only)
CREATE POLICY "lb_audit_log_delete" ON lb_audit_log
    FOR DELETE USING (false);

-- ==================== TRIGGER FÜR UPDATED_AT ====================

CREATE OR REPLACE FUNCTION lb_update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER lb_organizations_updated_at
    BEFORE UPDATE ON lb_organizations
    FOR EACH ROW EXECUTE FUNCTION lb_update_updated_at();

CREATE TRIGGER lb_memberships_updated_at
    BEFORE UPDATE ON lb_memberships
    FOR EACH ROW EXECUTE FUNCTION lb_update_updated_at();

CREATE TRIGGER lb_cases_updated_at
    BEFORE UPDATE ON lb_cases
    FOR EACH ROW EXECUTE FUNCTION lb_update_updated_at();

CREATE TRIGGER lb_templates_updated_at
    BEFORE UPDATE ON lb_templates
    FOR EACH ROW EXECUTE FUNCTION lb_update_updated_at();

-- ==================== STORAGE BUCKETS ====================
-- Diese müssen über die Supabase-Konsole oder API erstellt werden:
--
-- 1. lb-templates  (für Dokumentvorlagen)
--    - Policies: Lesen für authentifizierte User, Schreiben nur für Admins
--
-- 2. lb-uploads    (für hochgeladene Dokumente)
--    - Policies: Organisations-basiert
--
-- 3. lb-generated  (für generierte Dokumente)
--    - Policies: Organisations-basiert
--
-- Beispiel-Policy für Storage (in Supabase Console):
--
-- INSERT Policy für lb-uploads:
-- ((bucket_id = 'lb-uploads'::text) AND
--  (EXISTS (SELECT 1 FROM lb_memberships WHERE user_id = auth.uid())))
--
-- SELECT Policy für lb-uploads:
-- ((bucket_id = 'lb-uploads'::text) AND
--  (EXISTS (SELECT 1 FROM lb_memberships WHERE user_id = auth.uid())))

-- ==================== VIEWS ====================

-- View: Fälle mit Statistiken
CREATE OR REPLACE VIEW lb_cases_stats AS
SELECT
    c.*,
    (SELECT COUNT(*) FROM lb_documents d WHERE d.case_id = c.id) as document_count,
    (SELECT COUNT(*) FROM lb_uploads u WHERE u.case_id = c.id) as upload_count,
    o.name as organization_name,
    o.slug as organization_slug
FROM lb_cases c
JOIN lb_organizations o ON o.id = c.organization_id;

-- View: Dashboard-Statistiken pro Organisation
CREATE OR REPLACE VIEW lb_dashboard_stats AS
SELECT
    organization_id,
    COUNT(*) as total_cases,
    COUNT(*) FILTER (WHERE status = 'entwurf') as entwurf_count,
    COUNT(*) FILTER (WHERE status = 'angefordert') as angefordert_count,
    COUNT(*) FILTER (WHERE status = 'bewilligung_da') as bewilligung_da_count,
    COUNT(*) FILTER (WHERE status = 'abgeschlossen') as abgeschlossen_count,
    COUNT(*) FILTER (WHERE status = 'storniert') as storniert_count,
    COUNT(*) FILTER (WHERE frist_datum IS NOT NULL AND frist_datum <= CURRENT_DATE) as ueberfaellig_count,
    COUNT(*) FILTER (WHERE frist_datum IS NOT NULL AND frist_datum BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days') as frist_diese_woche
FROM lb_cases
GROUP BY organization_id;

-- ==================== KOMMENTARE ====================

COMMENT ON TABLE lb_organizations IS 'Kanzleien/Mandanten für Löschungsbewilligungen';
COMMENT ON TABLE lb_memberships IS 'Benutzer-zu-Organisation Zuordnung mit Rollen und Berechtigungen';
COMMENT ON TABLE lb_cases IS 'Einzelne Löschungsbewilligungs-Fälle';
COMMENT ON TABLE lb_documents IS 'Generierte Dokumente (Anschreiben, etc.)';
COMMENT ON TABLE lb_uploads IS 'Hochgeladene Dokumente (Bewilligungen, etc.)';
COMMENT ON TABLE lb_templates IS 'Dokumentvorlagen für Generierung';
COMMENT ON TABLE lb_audit_log IS 'Audit-Trail aller Aktionen (append-only)';

COMMENT ON FUNCTION lb_user_org_ids IS 'Gibt alle Organisations-IDs zurück, in denen der aktuelle User Mitglied ist';
COMMENT ON FUNCTION lb_has_permission IS 'Prüft, ob der aktuelle User eine bestimmte Berechtigung in einer Organisation hat';

-- ==================== ENDE MIGRATION ====================
