
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select event_id
from "netflix_security"."main"."raw_login_events"
where event_id is null



  
  
      
    ) dbt_internal_test