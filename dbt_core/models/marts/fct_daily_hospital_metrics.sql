{{
    config(
        materialized='table'
    )
}}

with case_summary as (
    select * from {{ ref('fct_case_summary') }}
),

daily_metrics as (
    select
        case_start_date as arrival_date,
        count(distinct case_id) as daily_case_count,
        sum(case when patient_type = 'Outpatient' then 1 else 0 end) as outpatient_count,
        sum(case when patient_type = 'Inpatient' then 1 else 0 end) as inpatient_count,
        sum(case when has_rework then 1 else 0 end) as rework_case_count,
        sum(case when has_lab_tests then 1 else 0 end) as cases_with_lab_tests,
        sum(case when has_imaging then 1 else 0 end) as cases_with_imaging,
        round(avg(total_los_minutes), 1) as avg_los_minutes,
        round(avg(total_los_hours), 2) as avg_los_hours,
        round(avg(triage_to_doctor_minutes), 1) as avg_triage_to_doctor_minutes,
        sum(case when is_4hr_target_compliant then 1 else 0 end) as compliant_4hr_count,
        round(100.0 * sum(case when is_4hr_target_compliant then 1 else 0 end) / count(*), 1) as four_hour_compliance_pct
    from case_summary
    group by case_start_date
)

select * from daily_metrics
order by arrival_date

