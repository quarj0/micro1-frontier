# Rejected order requests leave orphan orders

`POST /api/orders/` correctly returns HTTP 400 when a nested line item has a non-positive quantity. However, an order row is still created before the request fails. Retrying then produces duplicates in downstream processing.

A rejected request must leave no order or line-item state behind. A valid request must continue to create the order and all of its items.

The supplied customer and product data are synthetic.

