
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select ip_address
from "netflix_security"."main"."raw_request_logs"
where ip_address is null



  
  
      
    ) dbt_internal_test