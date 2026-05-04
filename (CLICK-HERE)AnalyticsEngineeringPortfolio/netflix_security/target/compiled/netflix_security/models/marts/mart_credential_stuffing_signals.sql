-- Credential Stuffing signals
-- IPs that attempt login across many distinct user accounts with a high
-- failure rate are strong indicators of automated credential stuffing.
with login_events as (
    select * from "netflix_security"."main"."stg_login_events"
),

ip_account_stats as (
    select
        ip_address,
        count(distinct user_id)                                               as distinct_users_targeted,
        count(*)                                                              as total_attempts,
        sum(case when is_failure then 1 else 0 end)                          as total_failures,
        sum(case when is_success then 1 else 0 end)                          as total_successes,
        round(
            cast(sum(case when is_failure then 1 else 0 end) as double)
            / count(*), 4
        )                                                                     as failure_rate,
        min(event_timestamp)                                                  as first_seen_at,
        max(event_timestamp)                                                  as last_seen_at
    from login_events
    group by ip_address
),

credential_stuffing_signals as (
    select
        ip_address,
        distinct_users_targeted,
        total_attempts,
        total_failures,
        total_successes,
        failure_rate,
        first_seen_at,
        last_seen_at,
        case
            when distinct_users_targeted >= 50 and failure_rate >= 0.8  then 'HIGH'
            when distinct_users_targeted >= 20 and failure_rate >= 0.7  then 'MEDIUM'
            when distinct_users_targeted >= 10 and failure_rate >= 0.6  then 'LOW'
            else 'INFORMATIONAL'
        end as credential_stuffing_risk
    from ip_account_stats
    where distinct_users_targeted >= 5
)

select * from credential_stuffing_signals
order by distinct_users_targeted desc, failure_rate desc