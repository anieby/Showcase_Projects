
    
    

select
    request_id as unique_field,
    count(*) as n_records

from "netflix_security"."main"."raw_request_logs"
where request_id is not null
group by request_id
having count(*) > 1


