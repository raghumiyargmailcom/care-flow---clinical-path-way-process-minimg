-- ============================================================
-- CareFlow Analytical Dashboard Queries using dbt Marts
-- ============================================================

-- 1. Length of stay and 4-hour target compliance by patient type
select
    patient_type,
    count(*) as total_cases,
    round(avg(total_los_minutes), 1) as avg_los_minutes,
    round(avg(total_los_hours), 2) as avg_los_hours,
    sum(case when is_4hr_target_compliant then 1 else 0 end) as compliant_cases,
    round(100.0 * sum(case when is_4hr_target_compliant then 1 else 0 end) / count(*), 1) as compliance_rate_pct
from {{ ref('fct_case_summary') }}
group by patient_type;

-- 2. Top 5 Process Variants in the Hospital
select
    variant_id,
    variant_frequency,
    variant_percentage,
    pathway_length,
    pathway_signature
from {{ ref('int_pathway_variants') }}
group by variant_id, variant_frequency, variant_percentage, pathway_length, pathway_signature
order by variant_frequency desc
limit 5;

-- 3. Top Bottleneck Transitions
select
    bottleneck_rank,
    bottleneck_stage,
    occurrence_count,
    avg_wait_minutes,
    bottleneck_severity_hours
from {{ ref('fct_bottleneck_analysis') }}
order by bottleneck_rank
limit 10;

