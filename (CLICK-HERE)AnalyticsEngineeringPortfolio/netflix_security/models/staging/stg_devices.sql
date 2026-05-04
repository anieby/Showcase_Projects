with source as (
    select * from {{ source('security_raw', 'raw_devices') }}
),

renamed as (
    select
        device_id,
        user_id,
        device_type,
        os,
        browser,
        first_seen_at,
        last_seen_at,
        is_trusted,
        datediff('day', first_seen_at, last_seen_at)     as device_age_days
    from source
)

select * from renamed
