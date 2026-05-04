
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select success
from "netflix_security"."main"."raw_login_events"
where success is null



  
  
      
    ) dbt_internal_test