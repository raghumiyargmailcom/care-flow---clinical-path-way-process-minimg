{{
    config(
        materialized='table'
    )
}}

with transitions as (
    select * from {{ ref('int_event_transitions') }}
    where previous_activity is not null
),

transition_bottlenecks as (
    select
        transition_from_previous as bottleneck_stage,
        previous_activity as from_activity,
        activity_name as to_activity,
        count(*) as occurrence_count,
        count(distinct case_id) as affected_cases_count,
        round(avg(wait_time_from_previous_minutes), 2) as avg_wait_minutes,
        min(wait_time_from_previous_minutes) as min_wait_minutes,
        max(wait_time_from_previous_minutes) as max_wait_minutes,
        sum(wait_time_from_previous_minutes) as total_cumulative_wait_minutes,
        -- Bottleneck severity: weighted product of frequency and wait duration
        round(count(*) * avg(wait_time_from_previous_minutes) / 60.0, 2) as bottleneck_severity_hours
    from transitions
    group by
        transition_from_previous,
        previous_activity,
        activity_name
)

select
    dense_rank() over (order by bottleneck_severity_hours desc) as bottleneck_rank,
    bottleneck_stage,
    from_activity,
    to_activity,
    occurrence_count,
    affected_cases_count,
    avg_wait_minutes,
    min_wait_minutes,
    max_wait_minutes,
    total_cumulative_wait_minutes,
    bottleneck_severity_hours
from transition_bottlenecks
order by bottleneck_rank

