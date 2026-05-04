
    
    

select
    user_id as unique_field,
    count(*) as n_records

from "netflix_security"."main"."int_user_login_summary"
where user_id is not null
group by user_id
having count(*) > 1


