import sqlite3
from app import app, SQLITE_DATABASE_URI


# sqlite3.connect creates the db file if it doesn't exist
def _connect_db():
	conn = sqlite3.connect(SQLITE_DATABASE_URI)
	return conn


def _close_db(conn):
	conn.close()


# get a store's order date, order number, customer name, item SKU, 
# and item quantity; this is the relevant data for quality control
def _get_metadata(store: str) -> list[tuple[str, str, str, str, int]]:
	conn = _connect_db()
	cur = conn.cursor()	

	query = """
		SELECT CO.order_datetime, CO.order_number, CO.customer, Item.sku, Item.quantity
		FROM Customer_Order AS CO
		INNER JOIN Item ON Item.order_number = CO.order_number
		WHERE CO.store = ?
		ORDER BY iso_datetime DESC
	"""
	data = (store,)
	items: list[tuple[str, str, str, str, int]] = cur.execute(query, data).fetchall()

	_close_db(conn)

	return items


# create table for Orders, Items, and Notes
def create_tables():
	conn = _connect_db()

	cur = conn.cursor()
	cur.execute("DROP TABLE IF EXISTS Customer_Order")
	cur.execute("DROP TABLE IF EXISTS Item")
	cur.execute("DROP TABLE IF EXISTS Note")

	order_table = """
		CREATE TABLE Customer_Order (
			id INTEGER PRIMARY KEY,
			store TEXT,
			order_number TEXT,
			iso_datetime TEXT,
			order_datetime TEXT,
			customer TEXT
		);
	"""

	item_table = """
		CREATE TABLE Item (
			id INTEGER PRIMARY KEY,
			sku TEXT,
			quantity INTEGER,
			order_number TEXT,
			FOREIGN KEY (order_number) 
			REFERENCES Customer_Order (order_number) 
				ON DELETE CASCADE
		);
	"""

	note_table = """
		CREATE TABLE Note (
			id INTEGER PRIMARY KEY,
			note TEXT
		);
	"""
	cur.execute(order_table)
	cur.execute(item_table)
	cur.execute(note_table)

	# index store name, because it is used to query for metadata
	store_idx = """
		CREATE INDEX store_idx
		ON Customer_Order (store);
	"""

	# index customer order date, because it is used to query for metadata
	iso_dt_idx = """
		CREATE INDEX iso_dt_idx
		ON Customer_Order (iso_datetime);
	"""
	cur.execute(store_idx)
	cur.execute(iso_dt_idx)

	_close_db(conn)