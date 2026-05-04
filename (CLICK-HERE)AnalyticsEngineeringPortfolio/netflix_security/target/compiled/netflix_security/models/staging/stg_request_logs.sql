with source as (
    select * from "netflix_security"."main"."raw_request_logs"
),

renamed as (
    select
        request_id,
        ip_address,
        request_timestamp,
        endpoint,
        http_method,
        status_code,
        response_time_ms,
        user_agent,
        cast(request_timestamp as date)                  as request_date,
        extract(hour from request_timestamp)             as request_hour,
        case when status_code >= 400 then 1 else 0 end   as is_error
    from source
)

select * from renamed