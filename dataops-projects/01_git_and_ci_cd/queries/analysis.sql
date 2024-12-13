-- Basic analysis queries
CREATE TABLE covid_data AS SELECT * FROM read_csv_auto('/app/covid_data.csv');

-- Total cases and deaths by location
CREATE VIEW location_summary AS
SELECT
    location,
    MAX(total_cases) as max_total_cases,
    MAX(total_deaths) as max_total_deaths,
    MAX(total_cases_per_million) as max_cases_per_million
FROM covid_data
WHERE continent IS NOT NULL
GROUP BY location
ORDER BY max_total_cases DESC
LIMIT 20;

-- Output results to CSV
COPY (SELECT * FROM location_summary)
TO '/app/top_20_locations.csv'
WITH (HEADER, DELIMITER ',');

-- Generate some statistics
select
    count(distinct location) as total_locations,
    min(date) as earliest_date,
    max(date) as latest_date
from covid_data
where continent is not null
;
