-- Singular test: Verify all step-to-step transitions have non-negative wait times
select
    case_id,
    event_id,
    step_number,
    activity_name,
    wait_time_from_previous_minutes
from {{ ref('int_event_transitions') }}
where wait_time_from_previous_minutes < 0

