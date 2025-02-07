audit(name assert_positive_order_ids,)
;

select *
from @this_model
where item_id < 0
