-- Phase 2 Workstream B: pg_trgm Fuzzy Search
-- Doc ref: §Offloading Fuzzy Search to the Data Tier (citations 21, 23, 24)
-- "Postgres extensions like pg_trgm allow for typo-tolerant fuzzy matching at sub-millisecond speeds"

-- Enable the trigram extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- GIN trigram indexes for sub-millisecond fuzzy matching on PII fields
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_displayname_trgm 
  ON users USING GIN ("displayName" gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_legalname_trgm 
  ON users USING GIN ("legalName" gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_kyc_fullname_trgm 
  ON kyc_sessions USING GIN ("fullName" gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_kyc_normalizedname_trgm 
  ON kyc_sessions USING GIN ("normalizedName" gin_trgm_ops);
