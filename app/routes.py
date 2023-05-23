import time
import datetime
import requests
from requests.auth import HTTPBasicAuth

from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import NoteForm, RefreshForm

from config import USER, PASS, store_ids
from sku_map import MAP


auth = HTTPBasicAuth(USER, PASS)


@app.route("/", methods=["GET", "POST"])
def home():
	header = {'name':'premier'} 
	return render_template("home.html", title="Premier App", header=header)


@app.route("/notes", methods=["GET", "POST"])
def notes():
	form = NoteForm()
	if form.validate_on_submit():
		flash(f'Form submitted: {form.note.data}')
		return redirect(url_for("notes"))
	return render_template("notes.html", title="Notes", form=form)


@app.route("/refresh")
def refresh():
	if _refresh_all():
		print("* Refreshing...")
		flash("Refresh success")

		usa_await, usa_pend, can_await, can_pend = _get_amazon_orders()

		usa_await_order_data = _parse_order_metadata(usa_await)
		usa_pend_order_data = _parse_order_metadata(usa_pend)
		can_await_order_data = _parse_order_metadata(can_await)
		can_pend_order_data = _parse_order_metadata(can_pend)

		for k,v in usa_await_order_data.items():
			print(k)
			print(v)

		return redirect(url_for("home"))
	flash(f"[Error] store refresh")
	return redirect(url_for("home"))


# @app.route("/all_orders")
# def all_orders():
#     pass


def _refresh_all():
	amazon_usa = requests.post(f'https://ssapi.shipstation.com/stores/refreshstore?storeId={store_ids["amazon_usa"]}', auth=auth)
	amazon_can = requests.post(f'https://ssapi.shipstation.com/stores/refreshstore?storeId={store_ids["amazon_can"]}', auth=auth)
	ebay = requests.post(f'https://ssapi.shipstation.com/stores/refreshstore?storeId={store_ids["ebay"]}', auth=auth)
	prem = requests.post(f'https://ssapi.shipstation.com/stores/refreshstore?storeId={store_ids["prem"]}', auth=auth)
	nsotd = requests.post(f'https://ssapi.shipstation.com/stores/refreshstore?storeId={store_ids["nsotd"]}', auth=auth)
	buckeroo = requests.post(f'https://ssapi.shipstation.com/stores/refreshstore?storeId={store_ids["buckeroo"]}', auth=auth)

	try:
		if (amazon_usa.json()['success'] == 'true' and
			amazon_can.json()['success'] == 'true' and
			ebay.json()['success'] == 'true' and
			prem.json()['success'] == 'true' and
			nsotd.json()['success'] == 'true' and
			buckeroo.json()['success'] == 'true'):

			time.sleep(10)  # sleep(120)
			return True
	except Exception as e:
		return False


def _get_amazon_orders():
	# USA orders that are awaiting shipment
	amazon_usa_await_resp = requests.get(f'https://ssapi.shipstation.com/orders?orderStatus=awaiting_shipment&storeId={store_ids["amazon_usa"]}&sortBy=OrderDate&sortDir=DESC&pageSize=500', auth=auth)
	
	# USA orders that are pending fulfillment
	amazon_usa_pend_resp = requests.get(f'https://ssapi.shipstation.com/orders?orderStatus=pending_fulfillment&storeId={store_ids["amazon_usa"]}&sortBy=OrderDate&sortDir=DESC&pageSize=500', auth=auth)
	
	# Canadian orders that are awaiting shipment
	amazon_can_await_resp = requests.get(f'https://ssapi.shipstation.com/orders?orderStatus=awaiting_shipment&storeId={store_ids["amazon_can"]}&sortBy=OrderDate&sortDir=DESC&pageSize=500', auth=auth)
	
	# Canadian orders that are pending fulfillment
	amazon_can_pend_resp = requests.get(f'https://ssapi.shipstation.com/orders?orderStatus=pending_fulfillment&storeId={store_ids["amazon_can"]}&sortBy=OrderDate&sortDir=DESC&pageSize=500', auth=auth)

	# Lists
	amazon_usa_await = amazon_usa_await_resp.json()['orders']
	amazon_usa_pend = amazon_usa_pend_resp.json()['orders']
	amazon_can_await = amazon_can_await_resp.json()['orders']
	amazon_can_pend = amazon_can_pend_resp.json()['orders']

	num_orders = str(len(amazon_usa_await) + len(amazon_usa_pend) + len(amazon_can_await) + len(amazon_can_pend))
	print("| Amazon: " + num_orders + " |")

	return (amazon_usa_await, amazon_usa_pend, amazon_can_await, amazon_can_pend)


def _get_ebay_orders():
	pass

def _get_prem_orders():
	pass

def _get_nsotd_orders():
	pass

def _get_buckeroo_orders():
	pass


# eBay's order number mapped to 'orderKey', all other order numbers mapped to 'orderNumber'
def _parse_order_metadata(orders, is_ebay=False):
	order_data = {}

	for order in orders:
		if is_ebay:
			order_num = order['orderKey']
		else:
			order_num = order['orderNumber']

		customer = order['billTo']['name']

		# strip milliseconds then split date and time
		date, _time = order['orderDate'].split('.')[0].split('T')  # YYYY-MM-DD, hh:mm:ss
		year, month, day = date.split('-')                         # YYYY, MM, DD
		hour, minute, _ = _time.split(':')                         # hh, mm, ss
		order_datetime = datetime.datetime(
			year=int(year),
			month=int(month),
			day=int(day),
			hour=int(hour),
			minute=int(minute)
		)

		# A list of dictionaries with item information.
		items_list = order['items']

		for item in items_list:
			sku = item['sku']
			description = item['name']   # description we provided
			quantity = item['quantity']  # int

			# Clean the SKU
			#  
			# No SKU (NoneType)
			if sku is None: sku = name
			# No SKU (empty string)
			elif sku == '': sku = name
			# Revised SKU
			elif sku in MAP: sku = MAP[sku]
			# Randomly generated SKU
			elif sku[:3] == 'wi_': sku = name
			# Obsolete SKU
			elif sku[-3:] == '-SL': sku = sku[:-3]
			elif sku[-4:] == '-SLL': sku = sku[:-4]
			elif sku[-2:] == '-D': sku = sku[:-2]
			

			item_data = (order_datetime, customer, sku, description, quantity)
			if order_num not in order_data:
				order_data[order_num] = [item_data]
			else:
				order_data[order_num].append(item_data)

	return order_data
