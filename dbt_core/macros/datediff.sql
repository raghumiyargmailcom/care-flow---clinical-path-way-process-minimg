{# 
  Calculates difference between two timestamps in specified datepart units.
  Defaults to minute for clinical pathway duration measurements.
  Supports both BigQuery (target: dev/prod) and DuckDB (target: local).
#}
{% macro datediff(start_timestamp, end_timestamp, datepart='minute') %}
  {% if target.type == 'duckdb' %}
    date_diff(
      '{{ datepart }}',
      cast({{ start_timestamp }} as timestamp),
      cast({{ end_timestamp }} as timestamp)
    )
  {% else %}
    timestamp_diff(
      cast({{ end_timestamp }} as timestamp),
      cast({{ start_timestamp }} as timestamp),
      {{ datepart }}
    )
  {% endif %}
{% endmacro %}
