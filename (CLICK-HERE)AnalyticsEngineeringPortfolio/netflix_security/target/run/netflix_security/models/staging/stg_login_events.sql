
  
  create view "netflix_security"."main"."stg_login_events__dbt_tmp" as (
    with source as (
    select * from "netflix_security"."main"."raw_login_events"
),

renamed as (
    select
        event_id,
        user_id,
        ip_address,
        device_id,
        event_timestamp,
        success                                          as is_success,
        not success                                      as is_failure,
        country_code,
        user_agent,
        cast(event_timestamp as date)                    as event_date,
        extract(hour from event_timestamp)               as event_hour
    from source
)

select * from renamed
  );
