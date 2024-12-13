This private API was developed for an eCommerce business that receives approximately 200 daily online orders. The items from every order must be physically picked from the company’s sizable inventory warehouse before being packed and shipped. Order-picking is a time-consuming effort, yet the company strives to provide exceptional customer service by shipping orders within 24 hours of purchase.

The API parses a large volume of customer-order JSON data to generate a sorted list (i.e. pick list) of all items and their quantities ordered alphanumerically by Stock Keeping Unit (SKU). This allows items to be picked in order by warehouse location. Before the API was developed the pick list was arbitrary and unordered (example below) which resulted in inefficient order-picking and a significant waste of time and resources.

<img width="432" alt="before" src="https://github.com/andy-gaber/premier-pick-list/assets/44306593/8044c186-bf80-4258-9704-3a4094ce2a25">

The business sells apparel through five separete online stores, and each store’s customer-order JSON data is requested from a web-based order management system. The data from each store is parsed, cleaned, and normalized before collectively being sorted. Items are first grouped by SKU. Then, since every item is available in multiple sizes each SKU's sizes are sorted logically (e.g. "SML" < "MED" < "LRG"). Finally the complete pick list is sorted alphanumerically as seen in the example below.

<img width="748" alt="after" src="https://github.com/andy-gaber/premier-pick-list/assets/44306593/0f6c9af8-8b1e-4964-bcd2-2219f2e51bb5">

The API was developed with Python and implements Flask to handle HTTP requests and SQLite as the database engine. Each time a new pick list is generated the database tables are cleared of stale data then repopulated. The API also includes functionality for quality control: each individual store has its own HTTP endpoint that displays the relevant customer-order metadata for that particular store, and users have he ability to post and view notes.

This API is used daily and updated when necessary (originally when bugs were discovered, but now only when SKUs are changed or new inventory is added... no bugs in a long time!). It resulted in an optimization of order-processing and a reduction in the time to pick inventory items by approximately 50 percent.
