{{
    config(
        materialized='view'
    )
}}

with transitions as (
    select
        case_id,
        step_number,
        activity_name
    from {{ ref('int_event_transitions') }}
),

case_signatures as (
    select
        case_id,
        string_agg(activity_name, ' -> ' order by step_number) as pathway_signature,
        count(activity_name) as pathway_length
    from transitions
    group by case_id
),

variant_stats as (
    select
        pathway_signature,
        count(*) as variant_frequency,
        dense_rank() over (order by count(*) desc, pathway_signature) as variant_rank
    from case_signatures
    group by pathway_signature
)

select
    cs.case_id,
    concat('Variant ', cast(vs.variant_rank as string)) as variant_id,
    vs.variant_rank,
    cs.pathway_signature,
    cs.pathway_length,
    vs.variant_frequency,
    round(100.0 * vs.variant_frequency / sum(vs.variant_frequency) over (), 2) as variant_percentage
from case_signatures cs
join variant_stats vs
    on cs.pathway_signature = vs.pathway_signature

