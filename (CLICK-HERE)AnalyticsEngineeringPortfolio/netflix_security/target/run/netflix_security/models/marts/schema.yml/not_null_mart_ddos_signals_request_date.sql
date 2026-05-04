
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select request_date
from "netflix_security"."main"."mart_ddos_signals"
where request_date is null



  
  
      
    ) dbt_internal_test