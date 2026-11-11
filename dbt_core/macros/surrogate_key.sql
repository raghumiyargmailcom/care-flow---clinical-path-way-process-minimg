{#
  Generates MD5 hex hash from a list of columns for surrogate key generation.
  Supports both BigQuery (to_hex(md5(...))) and DuckDB (md5(...)).
#}
{% macro surrogate_key(field_list) %}
  {% if target.type == 'duckdb' %}
    md5(concat(
      {% for field in field_list %}
        coalesce(cast({{ field }} as string), '_null_')
        {% if not loop.last %}, '|', {% endif %}
      {% endfor %}
    ))
  {% else %}
    to_hex(md5(concat(
      {% for field in field_list %}
        coalesce(cast({{ field }} as string), '_null_')
        {% if not loop.last %}, '|', {% endif %}
      {% endfor %}
    )))
  {% endif %}
{% endmacro %}
