{{
    config(
        materialized='table'
    )
}}

with journeys as (
    select * from {{ ref('int_case_journeys') }}
),

variants as (
    select
        case_id,
        variant_id,
        variant_rank,
        pathway_signature,
        pathway_length,
        variant_frequency,
        variant_percentage
    from {{ ref('int_pathway_variants') }}
),

final_summary as (
    select
        j.case_id,
        j.patient_type,
        j.final_disposition,
        v.variant_id,
        v.variant_rank,
        v.pathway_signature,
        v.pathway_length,
        v.variant_frequency,
        v.variant_percentage,
        j.case_start_timestamp,
        j.case_end_timestamp,
        j.case_start_date,
        j.case_end_date,
        j.total_los_minutes,
        j.total_los_hours,
        j.is_4hr_target_compliant,
        j.reg_to_triage_minutes,
        j.triage_to_doctor_minutes,
        j.reg_to_doctor_minutes,
        j.total_events_count,
        j.distinct_activities_count,
        j.has_rework,
        j.rework_events_count,
        j.has_repeat_consultation,
        j.has_lab_tests,
        j.has_imaging,
        j.first_activity,
        j.last_activity
    from journeys j
    left join variants v
        on j.case_id = v.case_id
)

select * from final_summary

