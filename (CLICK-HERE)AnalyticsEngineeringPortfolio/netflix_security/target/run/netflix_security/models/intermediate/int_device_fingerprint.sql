
  
  create view "netflix_security"."main"."int_device_fingerprint__dbt_tmp" as (
    with devices as (
    select * from "netflix_security"."main"."stg_devices"
),

login_events as (
    select * from "netflix_security"."main"."stg_login_events"
),

device_login_stats as (
    select
        device_id,
        count(*)                                          as login_attempts_from_device,
        sum(case when is_failure then 1 else 0 end)       as failures_from_device,
        count(distinct ip_address)                        as distinct_ips_for_device
    from login_events
    group by device_id
),

fingerprint as (
    select
        d.device_id,
        d.user_id,
        d.device_type,
        d.os,
        d.browser,
        d.first_seen_at,
        d.is_trusted,
        d.device_age_days,
        coalesce(dl.login_attempts_from_device, 0)        as login_attempts,
        coalesce(dl.failures_from_device, 0)              as failures,
        coalesce(dl.distinct_ips_for_device, 0)           as distinct_ips
    from devices d
    left join device_login_stats dl on d.device_id = dl.device_id
)

select * from fingerprint
  );
