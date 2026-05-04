with login_events as (
    select * from {{ ref('stg_login_events') }}
),

user_stats as (
    select
        user_id,
        count(*)                                                             as total_login_attempts,
        sum(case when is_failure then 1 else 0 end)                         as total_failures,
        sum(case when is_success then 1 else 0 end)                         as total_successes,
        round(
            cast(sum(case when is_failure then 1 else 0 end) as double)
            / count(*), 4
        )                                                                    as failure_rate,
        count(distinct ip_address)                                           as distinct_ips,
        count(distinct device_id)                                            as distinct_devices,
        count(distinct country_code)                                         as distinct_countries,
        min(event_timestamp)                                                 as first_seen_at,
        max(event_timestamp)                                                 as last_seen_at
    from login_events
    group by user_id
)

select * from user_stats
