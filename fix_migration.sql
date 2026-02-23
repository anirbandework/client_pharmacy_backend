-- Mark the bad migration as applied so it gets skipped
INSERT INTO alembic_version (version_num) VALUES ('9da7a87fed6e') 
ON CONFLICT (version_num) DO NOTHING;
