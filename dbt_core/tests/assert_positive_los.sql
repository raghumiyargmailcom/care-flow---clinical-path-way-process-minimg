-- Singular test: Verify all patient journeys have a non-negative Length of Stay
select
    case_id,
    total_los_minutes
from {{ ref('int_case_journeys') }}
where total_los_minutes < 0

