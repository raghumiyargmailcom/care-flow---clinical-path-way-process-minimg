SELECT
    activity,
    next_activity,

    COUNT(*) AS total_transitions,
    COUNT(DISTINCT case_id) AS unique_patients,

    ROUND(AVG(waiting_time), 2) AS avg_waiting_minutes,

    APPROX_QUANTILES(waiting_time, 100)[OFFSET(50)]
        AS median_waiting_minutes,

    MIN(waiting_time) AS min_waiting_minutes,
    MAX(waiting_time) AS max_waiting_minutes,

    APPROX_QUANTILES(waiting_time, 100)[OFFSET(90)]
        AS p90_waiting_minutes

FROM {{ ref('int_patient_event') }}

WHERE next_activity IS NOT NULL
  AND waiting_time IS NOT NULL

GROUP BY
    activity,
    next_activity