with raw_data as(
    select * from {{ source('raw_data','events')}}

),

log_event as (

    select
        lower(trim(cast(case_id as string))) as case_id,
        lower(trim(cast(activity as string))) as activity,
        safe_cast(timestamp as datetime) as event_timestamp,
        lower(trim(cast(department as string))) as department,
        lower(trim(cast(resource as string))) as resource
    from raw_data
)

select * from log_event