{{
    config(
        materialized='table'
    )
}}

with events as (
    select * from {{ ref('int_event_transitions') }}
),

activity_ref as (
    select * from {{ ref('stg_activity_reference') }}
),

enriched_events as (
    select
        e.event_id,
        e.case_id,
        e.step_number,
        e.activity_name,
        coalesce(r.activity_category, 'General') as activity_category,
        e.activity_timestamp,
        e.department,
        coalesce(r.standard_department, e.department) as standard_department,
        e.resource_role,
        coalesce(r.is_milestone, false) as is_milestone,
        r.sla_expected_duration_minutes,
        e.previous_activity,
        e.previous_timestamp,
        e.next_activity,
        e.next_timestamp,
        e.transition_from_previous,
        e.transition_to_next,
        e.wait_time_from_previous_minutes,
        e.dwell_time_to_next_minutes,
        case
            when r.sla_expected_duration_minutes is not null
            then e.wait_time_from_previous_minutes - r.sla_expected_duration_minutes
            else null
        end as sla_variance_minutes,
        case
            when r.sla_expected_duration_minutes is not null and e.wait_time_from_previous_minutes > r.sla_expected_duration_minutes
            then true
            else false
        end as is_sla_breached,
        e.activity_occurrence_number,
        e.is_rework_event,
        e.is_case_start,
        e.is_case_end,
        e.activity_date,
        e.activity_hour,
        e.day_of_week,
        e.is_weekend
    from events e
    left join activity_ref r
        on e.activity_name = r.activity_name
)

select * from enriched_events

