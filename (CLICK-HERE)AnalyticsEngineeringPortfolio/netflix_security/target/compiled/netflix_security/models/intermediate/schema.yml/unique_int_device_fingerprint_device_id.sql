
    
    

select
    device_id as unique_field,
    count(*) as n_records

from "netflix_security"."main"."int_device_fingerprint"
where device_id is not null
group by device_id
having count(*) > 1


