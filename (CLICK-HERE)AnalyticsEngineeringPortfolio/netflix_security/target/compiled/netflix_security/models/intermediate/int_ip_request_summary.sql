with request_logs as (
    select * from "netflix_security"."main"."stg_request_logs"
),

ip_daily_stats as (
    select
        ip_address,
        request_date,
        count(*)                                                              as total_requests,
        count(distinct request_hour)                                          as active_hours,
        sum(is_error)                                                         as error_requests,
        round(cast(sum(is_error) as double) / count(*), 4)                   as error_rate,
        round(avg(response_time_ms), 2)                                       as avg_response_time_ms,
        count(distinct endpoint)                                              as distinct_endpoints,
        min(request_timestamp)                                                as first_request_at,
        max(request_timestamp)                                                as last_request_at
    from request_logs
    group by ip_address, request_date
)

select * from ip_daily_stats