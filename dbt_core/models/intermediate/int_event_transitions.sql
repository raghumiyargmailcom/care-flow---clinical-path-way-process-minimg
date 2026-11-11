{{
    config(
        materialized='view'
    )
}}

with events as (
    select
        event_id,
        case_id,
        activity_name,
        activity_timestamp,
        department,
        resource_role,
        activity_date,
        activity_hour,
        day_of_week,
        is_weekend
    from {{ ref('stg_hospital_events') }}
),

ordered_events as (
    select
        event_id,
        case_id,
        activity_name,
        activity_timestamp,
        department,
        resource_role,
        activity_date,
        activity_hour,
        day_of_week,
        is_weekend,
        row_number() over (
            partition by case_id
            order by activity_timestamp, event_id
        ) as step_number,
        lag(activity_name) over (
            partition by case_id
            order by activity_timestamp, event_id
        ) as previous_activity,
        lag(activity_timestamp) over (
            partition by case_id
            order by activity_timestamp, event_id
        ) as previous_timestamp,
        lead(activity_name) over (
            partition by case_id
            order by activity_timestamp, event_id
        ) as next_activity,
        lead(activity_timestamp) over (
            partition by case_id
            order by activity_timestamp, event_id
        ) as next_timestamp,
        row_number() over (
            partition by case_id, activity_name
            order by activity_timestamp, event_id
        ) as activity_occurrence_number
    from events
),

with_transitions as (
    select
        event_id,
        case_id,
        step_number,
        activity_name,
        activity_timestamp,
        department,
        resource_role,
        activity_date,
        activity_hour,
        day_of_week,
        is_weekend,
        previous_activity,
        previous_timestamp,
        next_activity,
        next_timestamp,
        case
            when previous_activity is not null then concat(previous_activity, ' -> ', activity_name)
            else concat('[START] -> ', activity_name)
        end as transition_from_previous,
        case
            when next_activity is not null then concat(activity_name, ' -> ', next_activity)
            else concat(activity_name, ' -> [END]')
        end as transition_to_next,
        case
            when previous_timestamp is not null then {{ datediff('previous_timestamp', 'activity_timestamp', 'minute') }}
            else 0
        end as wait_time_from_previous_minutes,
        case
            when next_timestamp is not null then {{ datediff('activity_timestamp', 'next_timestamp', 'minute') }}
            else 0
        end as dwell_time_to_next_minutes,
        activity_occurrence_number,
        case
            when activity_occurrence_number > 1 then true
            else false
        end as is_rework_event,
        case
            when previous_activity is null then true
            else false
        end as is_case_start,
        case
            when next_activity is null then true
            else false
        end as is_case_end
    from ordered_events
)

select * from with_transitions

