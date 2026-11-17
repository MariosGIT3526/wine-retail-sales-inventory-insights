{#
  Cleaning helpers used by every staging model, so each rule is written once.
#}

{# Use the custom schema name as-is (staging, marts...) instead of dbt's default "analytics_staging". #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name | trim if custom_schema_name else target.schema }}
{%- endmacro %}

{# Item codes: text, trimmed, upper-cased. Some codes contain letters (123A), so never cast to integer. #}
{% macro clean_code(col) -%}
    nullif(upper(trim({{ col }})), '')
{%- endmacro %}

{# Names: upper-case, trim, collapse repeated spaces ("ANKARA  HOSPITALITY" -> "ANKARA HOSPITALITY"). #}
{% macro clean_name(col) -%}
    nullif(regexp_replace(upper(trim({{ col }})), '\s+', ' ', 'g'), '')
{%- endmacro %}

{#
  Numbers that may arrive as API numbers ("12.5") or portal-export text ("1,035.00", "(0.17)", "$17.99").
  Parentheses mean negative. Anything still non-numeric becomes NULL instead of failing the build;
  the not_null / range tests then surface it.
#}
{% macro parse_number(col) -%}
    (case
        when {{ _clean_num(col) }} ~ '^-?[0-9]*\.?[0-9]+$'
            then (case when trim({{ col }}) like '(%)' then -1 else 1 end) * {{ _clean_num(col) }}::numeric
    end)
{%- endmacro %}

{% macro _clean_num(col) -%}
    regexp_replace(trim({{ col }}), '[$,()\s]', '', 'g')
{%- endmacro %}

{# Dates from the API ("2026-10-31T00:00:00.000") or the portal export ("10/31/2026"). #}
{% macro parse_date(col) -%}
    (case
        when trim({{ col }}) ~ '^\d{4}-\d{2}-\d{2}' then left(trim({{ col }}), 10)::date
        when trim({{ col }}) ~ '^\d{1,2}/\d{1,2}/\d{4}$' then to_date(trim({{ col }}), 'MM/DD/YYYY')
    end)
{%- endmacro %}
