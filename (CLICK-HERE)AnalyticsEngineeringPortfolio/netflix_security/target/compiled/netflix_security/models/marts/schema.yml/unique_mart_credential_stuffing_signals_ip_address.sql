
    
    

select
    ip_address as unique_field,
    count(*) as n_records

from "netflix_security"."main"."mart_credential_stuffing_signals"
where ip_address is not null
group by ip_address
having count(*) > 1


