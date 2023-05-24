import time
import datetime
import requests
from requests.auth import HTTPBasicAuth

from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import NoteForm

from sku_map import MAP
from config import (
	USER, 
	PASS, 
	AMZ_USA_REFRESH_ENDPOINT,
	AMZ_CAN_REFRESH_ENDPOINT,
	EBAY_REFRESH_ENDPOINT,
	PREM_SHIRTS_REFRESH_ENDPOINT,
	NSOTD_REFRESH_ENDPOINT,
	BUCK_REFRESH_ENDPOINT,
	AMZ_USA_AWAIT_ENDPOINT, 
	AMZ_USA_PEND_ENDPOINT, 
	AMZ_CAN_AWAIT_ENDPOINT, 
	AMZ_CAN_PEND_ENDPOINT, 
	EBAY_ENDPOINT, 
	PREM_SHIRTS_ENDPOINT, 
	NSOTD_ENDPOINT, 
	BUCK_ENDPOINT
)


auth = HTTPBasicAuth(USER, PASS)


@app.route('/', methods=['GET', 'POST'])
def home():
	header = {'name':'premier'} 
	return render_template('home.html', title='Premier App', header=header)


@app.route('/notes', methods=['GET', 'POST'])
def notes():
	form = NoteForm()
	if form.validate_on_submit():
		flash(f'Form submitted: {form.note.data}')
		return redirect(url_for('notes'))
	return render_template('notes.html', title='Notes', form=form)


@app.route('/update')
def update():
	if _refresh_stores():
		flash('All Stores Updated!')

		# amazon
		usa_await, usa_pend, can_await, can_pend = _get_amazon_orders()
		usa_await_order_data = _parse_order_metadata(usa_await)
		usa_pend_order_data = _parse_order_metadata(usa_pend)
		can_await_order_data = _parse_order_metadata(can_await)
		can_pend_order_data = _parse_order_metadata(can_pend)
		for k,v in usa_await_order_data.items():
			print(k)
			print(v)
			print('-'*80)

		# ebay
		ebay_orders = _get_ebay_orders()
		ebay_order_data = _parse_order_metadata(ebay_orders, is_ebay=True)
		for k,v in ebay_order_data.items():
			print(k)
			print(v)
			print('-'*80)

		# premier shirtrs
		prem_orders = _get_prem_orders()
		prem_order_data = _parse_order_metadata(prem_orders)
		for k,v in prem_order_data.items():
			print(k)
			print(v)
			print('-'*80)

		# new shirt of the day
		nsotd_orders = _get_nsotd_orders()
		nsotd_order_data = _parse_order_metadata(nsotd_orders)
		for k,v in nsotd_order_data.items():
			print(k)
			print(v)
			print('-'*80)

		# buckeroo
		buck_orders = _get_buckeroo_orders()
		buck_order_data = _parse_order_metadata(buck_orders)
		for k,v in buck_order_data.items():
			print(k)
			print(v)
			print('-'*80)

		return redirect(url_for('home'))
	flash(f'[Error] store refresh')
	return redirect(url_for('home'))


# @app.route('/all_orders')
# def all_orders():
#     pass


def _refresh_stores():
	amazon_usa = requests.post(AMZ_USA_REFRESH_ENDPOINT, auth=auth)
	amazon_can = requests.post(AMZ_CAN_REFRESH_ENDPOINT, auth=auth)
	ebay = requests.post(EBAY_REFRESH_ENDPOINT, auth=auth)
	prem = requests.post(PREM_SHIRTS_REFRESH_ENDPOINT, auth=auth)
	nsotd = requests.post(NSOTD_REFRESH_ENDPOINT, auth=auth)
	buckeroo = requests.post(BUCK_REFRESH_ENDPOINT, auth=auth)

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
	amazon_usa_await_resp = requests.get(AMZ_USA_AWAIT_ENDPOINT, auth=auth)
	# USA orders that are pending fulfillment
	amazon_usa_pend_resp = requests.get(AMZ_USA_PEND_ENDPOINT, auth=auth)
	# Canadian orders that are awaiting shipment
	amazon_can_await_resp = requests.get(AMZ_CAN_AWAIT_ENDPOINT, auth=auth)
	# Canadian orders that are pending fulfillment
	amazon_can_pend_resp = requests.get(AMZ_CAN_PEND_ENDPOINT, auth=auth)
	# Lists
	amazon_usa_await_orders = amazon_usa_await_resp.json()['orders']
	amazon_usa_pend_orders = amazon_usa_pend_resp.json()['orders']
	amazon_can_await_orders = amazon_can_await_resp.json()['orders']
	amazon_can_pend_orders = amazon_can_pend_resp.json()['orders']

	num_orders = str(len(amazon_usa_await_orders) + len(amazon_usa_pend_orders) + len(amazon_can_await_orders) + len(amazon_can_pend_orders))
	print('\n-> Amazon: ' + num_orders + ' Orders\n')

	return (amazon_usa_await_orders, amazon_usa_pend_orders, amazon_can_await_orders, amazon_can_pend_orders)


def _get_ebay_orders():
	ebay_await_resp = requests.get(EBAY_ENDPOINT, auth=auth)
	# List
	ebay_orders = ebay_await_resp.json()['orders']
	num_orders = str(len(ebay_orders))
	print('\n-> eBay: ' + num_orders + ' Orders\n')
	return ebay_orders


def _get_prem_orders():
	prem_shirts_await_resp = requests.get(PREM_SHIRTS_ENDPOINT, auth=auth)
	# List
	prem_shirts_orders = prem_shirts_await_resp.json()['orders']
	num_orders = str(len(prem_shirts_orders))
	print('\n-> Premier Shirts: ' + num_orders + ' Orders\n')
	return prem_shirts_orders


def _get_nsotd_orders():
	nsotd_await_resp = requests.get(NSOTD_ENDPOINT, auth=auth)
	# List
	nsotd_orders = nsotd_await_resp.json()['orders']
	num_orders = str(len(nsotd_orders))
	print('\n-> New Shirt of the Day: ' + num_orders + ' Orders\n')
	return nsotd_orders


def _get_buckeroo_orders():
	buck_await_resp = requests.get(BUCK_ENDPOINT, auth=auth)
	# List
	buck_orders = buck_await_resp.json()['orders']
	num_orders = str(len(buck_orders))
	print('\n-> Buckeroo: ' + num_orders + ' Orders\n')
	return buck_orders


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
			if sku is None: sku = description
			# No SKU (empty string)
			elif sku == '': sku = description
			# Revised SKU
			elif sku in MAP: sku = MAP[sku]
			# Randomly generated SKU
			elif sku[:3] == 'wi_': sku = description
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
