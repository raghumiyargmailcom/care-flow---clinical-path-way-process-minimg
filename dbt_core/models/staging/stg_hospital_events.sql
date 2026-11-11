{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select
        case_id,
        activity,
        timestamp,
        department,
        resource
    from {{ ref('raw_hospital_events') }}
),

cleaned_data as (
    select
        {{ surrogate_key(['case_id', 'activity', 'timestamp']) }} as event_id,
        upper(trim(case_id)) as case_id,
        trim(activity) as activity_name,
        cast(timestamp as timestamp) as activity_timestamp,
        trim(department) as department,
        -- Data cleaning: standardise typos in resource role (e.g., 'DoctorL' -> 'Doctor')
        case
            when trim(resource) = 'DoctorL' then 'Doctor'
            else trim(resource)
        end as resource_role,
        cast(timestamp as date) as activity_date,
        extract(hour from cast(timestamp as timestamp)) as activity_hour,
        extract(dayofweek from cast(timestamp as timestamp)) as day_of_week,
        case
            when extract(dayofweek from cast(timestamp as timestamp)) in (1, 7) then true
            else false
        end as is_weekend
    from source_data
    where case_id is not null
      and activity is not null
      and timestamp is not null
)

select * from cleaned_data

