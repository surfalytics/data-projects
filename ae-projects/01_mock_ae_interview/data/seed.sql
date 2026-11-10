-- Sample data for the AE mock interview.
-- Run: duckdb vault.duckdb < data/seed.sql
-- The data is small and fictional. It has the same problems as production:
-- two flag systems, duplicate entries, one inactive row, a second experiment.
create or replace table partner_directpush_launchdarkly_events (
    event_id varchar,
    event_contextkeys_user varchar,
    event_creationdate timestamp,
    event_key varchar,
    event_variationname varchar,
    event_value varchar,
    is_active varchar
);

-- New system (LaunchDarkly), from 2025-01-03.
insert into partner_directpush_launchdarkly_events values
    ('ld-01', 'u05', '2025-01-03 09:10:00', 'vault-launch', 'treatment', 'T', 'Y'),
    ('ld-02', 'u05', '2025-01-03 18:40:00', 'vault-launch', 'treatment', 'T', 'Y'),  -- duplicate entry
    ('ld-03', 'u06', '2025-01-03 11:00:00', 'vault-launch', 'control', 'F', 'Y'),
    ('ld-04', 'u07', '2025-01-04 08:30:00', 'vault-launch', 'treatment', 't', 'Y'),  -- lower case
    ('ld-05', 'u08', '2025-01-04 12:15:00', 'vault-launch', 'control', 'f', 'Y'),
    ('ld-06', 'u08', '2025-01-05 07:45:00', 'vault-launch', 'control', 'F', 'Y'),  -- duplicate entry
    ('ld-07', 'u09', '2025-01-05 10:00:00', 'vault-launch', 'treatment', 'T', 'N'),  -- inactive, must be ignored
    ('ld-08', 'u10', '2025-01-05 16:20:00', 'vault-launch', 'treatment', 'T', 'Y'),
    ('ld-09', 'u01', '2025-01-04 09:00:00', 'vault-launch', 'treatment', 'T', 'Y'),  -- u01 also in legacy
    ('ld-10', 'u06', '2025-01-04 10:00:00', 'savings-goals', 'treatment', 'T', 'Y');  -- other experiment

create or replace table legacy_feature_flag_events (
    id varchar,
    "user" varchar,
    "timestamp" timestamp,
    key varchar,
    variation_name varchar,
    value varchar
);

-- Old system, until 2025-01-02.
insert into legacy_feature_flag_events values
    ('lg-01', 'u01', '2025-01-01 08:00:00', 'vault-launch', 'treatment', 'true'),
    ('lg-02', 'u02', '2025-01-01 09:30:00', 'vault-launch', 'control', 'false'),
    ('lg-03', 'u02', '2025-01-02 14:00:00', 'vault-launch', 'control', 'false'),  -- duplicate entry
    ('lg-04', 'u03', '2025-01-02 10:00:00', 'vault-launch', 'treatment', 'true'),
    ('lg-05', 'u04', '2025-01-02 11:45:00', 'vault-launch', 'control', 'false'),
    ('lg-06', 'u03', '2025-01-01 07:00:00', 'savings-goals', 'control', 'false');  -- other experiment

-- Extra sources for Assignment 3 (data modeling).
create or replace table users (
    user_id varchar,
    signup_date date,
    country varchar
);

insert into users values
    ('u01', '2024-11-02', 'UK'),
    ('u02', '2024-11-15', 'UK'),
    ('u03', '2024-12-01', 'DE'),
    ('u04', '2024-12-03', 'FR'),
    ('u05', '2024-12-10', 'UK'),
    ('u06', '2024-12-12', 'DE'),
    ('u07', '2024-12-20', 'FR'),
    ('u08', '2024-12-22', 'UK'),
    ('u09', '2024-12-28', 'DE'),
    ('u10', '2024-12-30', 'UK');

-- One row per tier period. valid_to is null for the current tier.
create or replace table subscriptions (
    user_id varchar,
    tier varchar,  -- Standard, Plus, Premium
    valid_from date,
    valid_to date
);

insert into subscriptions values
    ('u01', 'Standard', '2024-11-02', '2025-01-03'),
    ('u01', 'Premium', '2025-01-03', null),
    ('u02', 'Standard', '2024-11-15', null),
    ('u03', 'Plus', '2024-12-01', null),
    ('u04', 'Standard', '2024-12-03', null),
    ('u05', 'Premium', '2024-12-10', null),
    ('u06', 'Plus', '2024-12-12', null),
    ('u07', 'Standard', '2024-12-20', null),
    ('u08', 'Plus', '2024-12-22', null),
    ('u09', 'Standard', '2024-12-28', null),
    ('u10', 'Premium', '2024-12-30', null);
