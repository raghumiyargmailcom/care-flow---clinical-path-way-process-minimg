{{
    config(
        materialized='table'
    )
}}

with events as (
    select * from {{ ref('int_event_transitions') }}
),

activity_stats as (
    select
        activity_name,
        department,
        count(*) as total_executions,
        count(distinct case_id) as unique_cases_count,
        round(avg(wait_time_from_previous_minutes), 2) as avg_wait_time_before_minutes,
        round(avg(dwell_time_to_next_minutes), 2) as avg_dwell_time_minutes,
        min(wait_time_from_previous_minutes) as min_wait_time_minutes,
        max(wait_time_from_previous_minutes) as max_wait_time_minutes,
        sum(case when is_rework_event then 1 else 0 end) as rework_executions_count,
        round(100.0 * sum(case when is_rework_event then 1 else 0 end) / count(*), 2) as rework_rate_pct
    from events
    group by
        activity_name,
        department
)

select
    activity_name,
    department,
    total_executions,
    unique_cases_count,
    avg_wait_time_before_minutes,
    avg_dwell_time_minutes,
    min_wait_time_minutes,
    max_wait_time_minutes,
    rework_executions_count,
    rework_rate_pct
from activity_stats
order by total_executions desc

