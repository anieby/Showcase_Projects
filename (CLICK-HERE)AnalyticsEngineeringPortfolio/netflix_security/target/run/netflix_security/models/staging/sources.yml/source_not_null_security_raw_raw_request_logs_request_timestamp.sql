
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select request_timestamp
from "netflix_security"."main"."raw_request_logs"
where request_timestamp is null



  
  
      
    ) dbt_internal_test