{{
    config(
        materialized='view'
    )
}}

with transitions as (
    select * from {{ ref('int_event_transitions') }}
),

case_aggregates as (
    select
        case_id,
        min(activity_timestamp) as case_start_timestamp,
        max(activity_timestamp) as case_end_timestamp,
        cast(min(activity_timestamp) as date) as case_start_date,
        cast(max(activity_timestamp) as date) as case_end_date,
        count(distinct event_id) as total_events_count,
        count(distinct activity_name) as distinct_activities_count,
        max(case when step_number = 1 then activity_name end) as first_activity,
        max(case when is_case_end then activity_name end) as last_activity,
        max(case when is_rework_event then 1 else 0 end) = 1 as has_rework,
        sum(case when is_rework_event then 1 else 0 end) as rework_events_count,
        max(case when activity_name = 'Repeat Doctor Consultation' then 1 else 0 end) = 1 as has_repeat_consultation,
        max(case when activity_name in ('Lab Test Ordered', 'Sample Collected', 'Lab Results Available') then 1 else 0 end) = 1 as has_lab_tests,
        max(case when activity_name in ('Imaging Ordered', 'Imaging Completed') then 1 else 0 end) = 1 as has_imaging,
        case
            when max(case when activity_name = 'Patient Transferred to Ward' then 1 else 0 end) = 1 then 'Inpatient'
            else 'Outpatient'
        end as patient_type,
        case
            when max(case when activity_name = 'Patient Discharged' then 1 else 0 end) = 1 then 'Outpatient Discharged'
            when max(case when activity_name = 'Discharge Processed' then 1 else 0 end) = 1 then 'Inpatient Discharged'
            else 'In Care'
        end as final_disposition,
        min(case when activity_name = 'Patient Registration' then activity_timestamp end) as registration_timestamp,
        min(case when activity_name = 'Initial Triage' then activity_timestamp end) as triage_timestamp,
        min(case when activity_name = 'Doctor Consultation' then activity_timestamp end) as first_consultation_timestamp,
        min(case when activity_name = 'Patient Transferred to Ward' then activity_timestamp end) as admission_timestamp,
        max(case when activity_name in ('Patient Discharged', 'Discharge Processed') then activity_timestamp end) as discharge_timestamp
    from transitions
    group by case_id
),

with_kpis as (
    select
        case_id,
        case_start_timestamp,
        case_end_timestamp,
        case_start_date,
        case_end_date,
        {{ datediff('case_start_timestamp', 'case_end_timestamp', 'minute') }} as total_los_minutes,
        round({{ datediff('case_start_timestamp', 'case_end_timestamp', 'minute') }} / 60.0, 2) as total_los_hours,
        total_events_count,
        distinct_activities_count,
        first_activity,
        last_activity,
        has_rework,
        rework_events_count,
        has_repeat_consultation,
        has_lab_tests,
        has_imaging,
        patient_type,
        final_disposition,
        registration_timestamp,
        triage_timestamp,
        first_consultation_timestamp,
        admission_timestamp,
        discharge_timestamp,
        case
            when registration_timestamp is not null and triage_timestamp is not null
            then {{ datediff('registration_timestamp', 'triage_timestamp', 'minute') }}
            else null
        end as reg_to_triage_minutes,
        case
            when triage_timestamp is not null and first_consultation_timestamp is not null
            then {{ datediff('triage_timestamp', 'first_consultation_timestamp', 'minute') }}
            else null
        end as triage_to_doctor_minutes,
        case
            when registration_timestamp is not null and first_consultation_timestamp is not null
            then {{ datediff('registration_timestamp', 'first_consultation_timestamp', 'minute') }}
            else null
        end as reg_to_doctor_minutes,
        case
            when {{ datediff('case_start_timestamp', 'case_end_timestamp', 'minute') }} <= 240 then true
            else false
        end as is_4hr_target_compliant
    from case_aggregates
)

select * from with_kpis

