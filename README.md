This private API was developed for an eCommerce business that receives approximately 200 daily online orders. Each order contains one or more items, and every item must be physically picked from the company’s sizable inventory warehouse before being packed and shipped. Order-picking is a time-consuming effort, yet the company strives to provide exceptional customer service by shipping orders within 24 hours of purchase.

The API parses a large volume of customer-order JSON data to generate a sorted list (i.e. pick list) of all items and their quantities ordered alphanumerically by Stock Keeping Unit (SKU). This allows items to be picked in order by warehouse location. Before the API was developed the pick list was arbitrary and unordered (as seen below) which resulted in an inefficient circuitous journey throughout the warehouse and a significant waste of time and resources.

<img width="432" alt="before" src="https://github.com/andy-gaber/premier-pick-list/assets/44306593/975c2872-ca3f-4f6d-87bb-37e166f93542">

The company sells apparel through its five online stores. Each store’s customer-order JSON data is requested from the company’s web-based order management system. The data from each store is then parsed, cleaned, and normalized before collectively being sorted. Items are first grouped by SKU, however each item of clothing is available in multiple sizes, so a SKU’s sizes must then also be grouped and sorted logically as well. The sorted pick list is seen below.

<img width="748" alt="after" src="https://github.com/andy-gaber/premier-pick-list/assets/44306593/0f6c9af8-8b1e-4964-bcd2-2219f2e51bb5">

The API was developed with Python, and implements Flask to handle HTTP requests and SQLite as the database engine. Each time a pick list is generated the database tables are cleared of stale data, then repopulated with fresh customer-order data from all five online stores. In addition to the pick list, the API also includes logic for quality control — each individual store has its own HTTP endpoint that displays the relevant customer-order metadata for that particular store, and users have he ability to post and view notes.

This API is used daily and updated when necessary. It resulted in an optimization of order-processing and a reduction in the time to pick inventory items by approximately 50 percent.
