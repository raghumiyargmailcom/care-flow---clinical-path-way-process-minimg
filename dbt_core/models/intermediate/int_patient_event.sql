with events as (
    select * from {{ ref("stg_events")}}
),

sequential_event as(
    select 
    case_id,
    activity,
    event_timestamp,
    department,
    resource,

    lead(activity) over(
        partition by case_id
        order by event_timestamp, activity
    ) as next_activity,

    lead(event_timestamp) over(
        partition by case_id
        order by event_timestamp, activity
    )as next_event_timestamp
    from events
) 

select case_id,
    activity,
    event_timestamp,
    department,
    resource,
    next_activity,
    datetime_diff(next_event_timestamp,
    event_timestamp,minute) as waiting_time
from sequential_event
    