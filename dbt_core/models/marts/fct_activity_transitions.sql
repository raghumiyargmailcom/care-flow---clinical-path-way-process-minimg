{{
    config(
        materialized='table'
    )
}}

with transitions as (
    select * from {{ ref('int_event_transitions') }}
),

directed_edges as (
    select
        coalesce(previous_activity, '[START]') as source_activity,
        activity_name as target_activity,
        transition_from_previous as transition_label,
        count(*) as transition_count,
        count(distinct case_id) as unique_cases_count,
        round(avg(wait_time_from_previous_minutes), 2) as avg_transition_time_minutes,
        min(wait_time_from_previous_minutes) as min_transition_time_minutes,
        max(wait_time_from_previous_minutes) as max_transition_time_minutes,
        round(stddev(wait_time_from_previous_minutes), 2) as stddev_transition_time_minutes,
        case
            when previous_activity = activity_name then true
            when activity_name = 'Repeat Doctor Consultation' then true
            else false
        end as is_rework_edge
    from transitions
    group by
        previous_activity,
        activity_name,
        transition_from_previous
)

select
    row_number() over (order by transition_count desc, avg_transition_time_minutes desc) as transition_id,
    source_activity,
    target_activity,
    transition_label,
    transition_count,
    unique_cases_count,
    avg_transition_time_minutes,
    min_transition_time_minutes,
    max_transition_time_minutes,
    stddev_transition_time_minutes,
    is_rework_edge
from directed_edges

