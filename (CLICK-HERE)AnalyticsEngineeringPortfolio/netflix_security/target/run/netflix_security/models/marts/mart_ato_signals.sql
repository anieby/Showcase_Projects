
  
    
    

    create  table
      "netflix_security"."main"."mart_ato_signals__dbt_tmp"
  
    as (
      -- Account Takeover (ATO) signals
-- Flags users with high failure rates and IP diversity, which together
-- suggest automated credential attacks followed by unauthorized access.
with user_summary as (
    select * from "netflix_security"."main"."int_user_login_summary"
),

login_events as (
    select * from "netflix_security"."main"."stg_login_events"
),

max_ts as (
    select max(event_timestamp) as max_event_ts from login_events
),

recent_failures as (
    select
        l.user_id,
        count(*) as failures_last_7_days
    from login_events l
    cross join max_ts m
    where l.is_failure = true
      and l.event_timestamp >= m.max_event_ts - interval '7 days'
    group by l.user_id
),

latest_success as (
    select
        user_id,
        ip_address      as latest_login_ip,
        device_id       as latest_login_device_id,
        country_code    as latest_login_country,
        event_timestamp as latest_login_at
    from (
        select
            user_id,
            ip_address,
            device_id,
            country_code,
            event_timestamp,
            row_number() over (partition by user_id order by event_timestamp desc) as rn
        from login_events
        where is_success = true
    ) ranked
    where rn = 1
),

ato_signals as (
    select
        u.user_id,
        u.total_login_attempts,
        u.total_failures,
        u.failure_rate,
        u.distinct_ips,
        u.distinct_countries,
        coalesce(rf.failures_last_7_days, 0)  as failures_last_7_days,
        ls.latest_login_at,
        ls.latest_login_ip,
        ls.latest_login_device_id,
        ls.latest_login_country,
        case
            when u.failure_rate >= 0.7 and u.distinct_ips >= 5  then 'HIGH'
            when u.failure_rate >= 0.5 and u.distinct_ips >= 3  then 'MEDIUM'
            when u.failure_rate >= 0.3 and u.distinct_ips >= 2  then 'LOW'
            else 'INFORMATIONAL'
        end as ato_risk_level
    from user_summary u
    left join recent_failures rf on u.user_id = rf.user_id
    left join latest_success  ls on u.user_id = ls.user_id
    where u.failure_rate >= 0.3
       or u.distinct_ips >= 5
)

select * from ato_signals
order by failure_rate desc, distinct_ips desc
    );
  
  