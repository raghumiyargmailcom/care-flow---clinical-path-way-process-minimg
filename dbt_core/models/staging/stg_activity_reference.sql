{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select
        activity_name,
        activity_category,
        standard_department,
        is_milestone,
        sla_expected_duration_minutes
    from {{ ref('activity_reference') }}
),

cleaned_data as (
    select
        trim(activity_name) as activity_name,
        trim(activity_category) as activity_category,
        trim(standard_department) as standard_department,
        cast(is_milestone as boolean) as is_milestone,
        cast(sla_expected_duration_minutes as int64) as sla_expected_duration_minutes
    from source_data
    where activity_name is not null
)

select * from cleaned_data

