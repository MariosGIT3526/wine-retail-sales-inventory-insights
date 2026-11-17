{#
  Two small generic tests, written here instead of installing dbt_utils so the project has no package
  dependencies. Each returns the rows that FAIL; zero rows = pass.
#}

{% test unique_combination_of_columns(model, combination_of_columns) %}
    select {{ combination_of_columns | join(', ') }}, count(*) as n_rows
    from {{ model }}
    group by {{ combination_of_columns | join(', ') }}
    having count(*) > 1
{% endtest %}

{% test accepted_range(model, column_name, min_value=none, max_value=none, inclusive=true) %}
    select *
    from {{ model }}
    where {{ column_name }} is not null
      and (
        1 = 0
        {% if min_value is not none %} or {{ column_name }} {{ '<' if inclusive else '<=' }} {{ min_value }} {% endif %}
        {% if max_value is not none %} or {{ column_name }} {{ '>' if inclusive else '>=' }} {{ max_value }} {% endif %}
      )
{% endtest %}
