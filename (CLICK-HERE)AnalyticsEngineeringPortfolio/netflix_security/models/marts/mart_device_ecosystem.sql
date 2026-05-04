-- Device Ecosystem analysis
-- Per-user summary of device diversity and trust status.
-- Accounts with many untrusted devices are a strong signal of compromise.
with device_fingerprint as (
    select * from {{ ref('int_device_fingerprint') }}
),

user_device_summary as (
    select
        user_id,
        count(*)                                                              as total_devices,
        sum(case when is_trusted     then 1 else 0 end)                      as trusted_devices,
        sum(case when not is_trusted then 1 else 0 end)                      as untrusted_devices,
        count(distinct os)                                                    as distinct_os,
        count(distinct device_type)                                           as distinct_device_types,
        min(first_seen_at)                                                    as oldest_device_seen,
        max(first_seen_at)                                                    as newest_device_seen,
        sum(login_attempts)                                                   as total_login_attempts,
        sum(failures)                                                         as total_device_failures
    from device_fingerprint
    group by user_id
),

device_ecosystem as (
    select
        user_id,
        total_devices,
        trusted_devices,
        untrusted_devices,
        distinct_os,
        distinct_device_types,
        oldest_device_seen,
        newest_device_seen,
        total_login_attempts,
        total_device_failures,
        round(
            cast(untrusted_devices as double) / nullif(total_devices, 0), 4
        )                                                                     as untrusted_device_rate,
        case
            when total_devices >= 10 and untrusted_devices >= 5             then 'HIGH_RISK'
            when total_devices >= 5  and untrusted_devices >= 3             then 'MEDIUM_RISK'
            when untrusted_devices >= 1                                     then 'LOW_RISK'
            else 'NORMAL'
        end as device_risk_profile
    from user_device_summary
)

select * from device_ecosystem
order by total_devices desc, untrusted_device_rate desc
