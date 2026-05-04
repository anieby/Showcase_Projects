
    
    

select
    device_id as unique_field,
    count(*) as n_records

from "netflix_security"."main"."stg_devices"
where device_id is not null
group by device_id
having count(*) > 1


