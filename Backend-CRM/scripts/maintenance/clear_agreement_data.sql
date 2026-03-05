-- Clear Agreement Workflow Data
-- This script safely deletes ONLY agreement-related data
-- Does NOT affect: Users, Sites, Studies, IAM, Notice Board, Site Status, or any other CRM tables

-- Delete in dependency order to respect foreign keys
DELETE FROM agreement_inline_comments;
DELETE FROM agreement_comments;
DELETE FROM agreement_documents;
DELETE FROM agreement_versions;
DELETE FROM agreements;
DELETE FROM study_templates;

-- Verify deletion
SELECT 
    'agreement_inline_comments' as table_name, COUNT(*) as remaining_rows FROM agreement_inline_comments
UNION ALL
SELECT 'agreement_comments', COUNT(*) FROM agreement_comments
UNION ALL
SELECT 'agreement_documents', COUNT(*) FROM agreement_documents
UNION ALL
SELECT 'agreement_versions', COUNT(*) FROM agreement_versions
UNION ALL
SELECT 'agreements', COUNT(*) FROM agreements
UNION ALL
SELECT 'study_templates', COUNT(*) FROM study_templates;
