-- DDoS / volumetric bot signals
-- IPs whose daily request volume is statistically anomalous relative to
-- the baseline distribution (z-score and percentile thresholds).
with ip_summary as (
    select * from {{ ref('int_ip_request_summary') }}
),

baseline_stats as (
    select
        avg(total_requests)                                                    as mean_daily_requests,
        stddev(total_requests)                                                 as stddev_daily_requests,
        percentile_cont(0.95) within group (order by total_requests)          as p95_daily_requests,
        percentile_cont(0.99) within group (order by total_requests)          as p99_daily_requests
    from ip_summary
),

ddos_signals as (
    select
        i.ip_address,
        i.request_date,
        i.total_requests,
        i.active_hours,
        i.error_rate,
        i.distinct_endpoints,
        i.avg_response_time_ms,
        round(s.p95_daily_requests, 0)                                        as p95_threshold,
        round(s.p99_daily_requests, 0)                                        as p99_threshold,
        round(
            (i.total_requests - s.mean_daily_requests)
            / nullif(s.stddev_daily_requests, 0), 2
        )                                                                      as z_score,
        case
            when i.total_requests >= s.p99_daily_requests                 then 'HIGH'
            when i.total_requests >= s.p95_daily_requests                 then 'MEDIUM'
            when i.total_requests >= s.mean_daily_requests * 3            then 'LOW'
            else 'INFORMATIONAL'
        end as ddos_risk_level
    from ip_summary i
    cross join baseline_stats s
    where i.total_requests >= s.mean_daily_requests * 2
)

select * from ddos_signals
order by total_requests desc
