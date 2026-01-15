-- ============================================================
-- LÖSCHUNGSBEWILLIGUNGEN - STORAGE BUCKETS
-- ============================================================
-- Diese SQL-Statements erstellen die Storage-Buckets und Policies
-- für das Löschungsbewilligungen-Modul
--
-- WICHTIG: Die Bucket-Erstellung muss über die Supabase-Konsole
-- oder die Storage-API erfolgen. Dieses Skript dokumentiert die
-- erforderlichen Policies.
-- ============================================================

-- ==================== BUCKET: lb-templates ====================
-- Für Dokumentvorlagen (DOCX)
-- Pfadstruktur: {organization_id}/{template_id}.docx
-- oder: global/{template_name}.docx für globale Vorlagen

-- Policy: SELECT (Lesen)
-- Authentifizierte User können alle Templates lesen
-- (globale + eigene Organisation)
/*
CREATE POLICY "lb_templates_select"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'lb-templates'
    AND (
        -- Globale Templates (Pfad beginnt mit 'global/')
        (storage.foldername(name))[1] = 'global'
        OR
        -- Organisations-Templates
        (storage.foldername(name))[1]::uuid IN (
            SELECT organization_id FROM lb_memberships
            WHERE user_id = auth.uid() AND is_active = true
        )
    )
);
*/

-- Policy: INSERT (Hochladen)
-- Nur User mit Vorlagen-Berechtigung
/*
CREATE POLICY "lb_templates_insert"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'lb-templates'
    AND (storage.foldername(name))[1]::uuid IN (
        SELECT organization_id FROM lb_memberships
        WHERE user_id = auth.uid()
        AND is_active = true
        AND (
            role = 'notar'
            OR (permissions->>'kann_vorlagen_verwalten')::boolean = true
        )
    )
);
*/

-- Policy: DELETE (Löschen)
-- Nur User mit Vorlagen-Berechtigung
/*
CREATE POLICY "lb_templates_delete"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'lb-templates'
    AND (storage.foldername(name))[1]::uuid IN (
        SELECT organization_id FROM lb_memberships
        WHERE user_id = auth.uid()
        AND is_active = true
        AND (
            role = 'notar'
            OR (permissions->>'kann_vorlagen_verwalten')::boolean = true
        )
    )
);
*/


-- ==================== BUCKET: lb-uploads ====================
-- Für hochgeladene Dokumente (erhaltene Bewilligungen, etc.)
-- Pfadstruktur: {organization_id}/{case_id}/{file_name}

-- Policy: SELECT (Lesen)
/*
CREATE POLICY "lb_uploads_select"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'lb-uploads'
    AND (storage.foldername(name))[1]::uuid IN (
        SELECT organization_id FROM lb_memberships
        WHERE user_id = auth.uid() AND is_active = true
    )
);
*/

-- Policy: INSERT (Hochladen)
/*
CREATE POLICY "lb_uploads_insert"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'lb-uploads'
    AND (storage.foldername(name))[1]::uuid IN (
        SELECT organization_id FROM lb_memberships
        WHERE user_id = auth.uid() AND is_active = true
    )
);
*/

-- Policy: DELETE (Löschen)
/*
CREATE POLICY "lb_uploads_delete"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'lb-uploads'
    AND (storage.foldername(name))[1]::uuid IN (
        SELECT organization_id FROM lb_memberships
        WHERE user_id = auth.uid()
        AND is_active = true
        AND (
            role = 'notar'
            OR (permissions->>'kann_faelle_loeschen')::boolean = true
        )
    )
);
*/


-- ==================== BUCKET: lb-generated ====================
-- Für generierte Dokumente (Anschreiben, etc.)
-- Pfadstruktur: {organization_id}/{case_id}/{document_id}.docx

-- Policy: SELECT (Lesen)
/*
CREATE POLICY "lb_generated_select"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'lb-generated'
    AND (storage.foldername(name))[1]::uuid IN (
        SELECT organization_id FROM lb_memberships
        WHERE user_id = auth.uid() AND is_active = true
    )
);
*/

-- Policy: INSERT (Erstellen - durch System)
/*
CREATE POLICY "lb_generated_insert"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'lb-generated'
    AND (storage.foldername(name))[1]::uuid IN (
        SELECT organization_id FROM lb_memberships
        WHERE user_id = auth.uid()
        AND is_active = true
        AND (
            role = 'notar'
            OR (permissions->>'kann_dokumente_generieren')::boolean = true
        )
    )
);
*/

-- Policy: DELETE (Löschen)
/*
CREATE POLICY "lb_generated_delete"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'lb-generated'
    AND (storage.foldername(name))[1]::uuid IN (
        SELECT organization_id FROM lb_memberships
        WHERE user_id = auth.uid()
        AND is_active = true
        AND (
            role = 'notar'
            OR (permissions->>'kann_faelle_loeschen')::boolean = true
        )
    )
);
*/


-- ============================================================
-- ANLEITUNG: Bucket-Erstellung in Supabase Console
-- ============================================================
--
-- 1. Gehe zu Storage > Buckets in der Supabase Console
--
-- 2. Erstelle folgende Buckets:
--
--    a) lb-templates
--       - Public: Nein
--       - File size limit: 10MB
--       - Allowed MIME types: application/vnd.openxmlformats-officedocument.wordprocessingml.document
--
--    b) lb-uploads
--       - Public: Nein
--       - File size limit: 50MB
--       - Allowed MIME types: */* (alle Typen)
--
--    c) lb-generated
--       - Public: Nein
--       - File size limit: 50MB
--       - Allowed MIME types: application/vnd.openxmlformats-officedocument.wordprocessingml.document, application/pdf
--
-- 3. Füge die oben kommentierten Policies für jeden Bucket hinzu
--    (unter Storage > Policies)
--
-- ============================================================


-- ==================== HELPER-FUNKTIONEN FÜR STORAGE ====================

-- Funktion: Generiert einen sicheren Dateipfad
CREATE OR REPLACE FUNCTION lb_generate_file_path(
    bucket TEXT,
    org_id UUID,
    case_id UUID DEFAULT NULL,
    file_name TEXT DEFAULT NULL
)
RETURNS TEXT AS $$
DECLARE
    path TEXT;
BEGIN
    path := org_id::text;

    IF case_id IS NOT NULL THEN
        path := path || '/' || case_id::text;
    END IF;

    IF file_name IS NOT NULL THEN
        path := path || '/' || file_name;
    END IF;

    RETURN path;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION lb_generate_file_path IS 'Generiert einen standardisierten Dateipfad für Storage-Operationen';


-- ============================================================
-- ENDE STORAGE BUCKETS DOKUMENTATION
-- ============================================================
