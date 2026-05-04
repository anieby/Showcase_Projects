
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select user_id
from "netflix_security"."main"."mart_ato_signals"
where user_id is null



  
  
      
    ) dbt_internal_test