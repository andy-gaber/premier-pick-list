import time
import datetime
import requests
from requests.auth import HTTPBasicAuth

from app import db
from app.models import Item, Note, create_tables

from app.sku_map import MAP
from app.secrets import (
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


AUTH = HTTPBasicAuth(USER, PASS)


# get up to date order data from all stoers
# remove stale order data from db
def _refresh_stores():
	try:
		amazon_usa = requests.post(AMZ_USA_REFRESH_ENDPOINT, auth=AUTH)
		amazon_can = requests.post(AMZ_CAN_REFRESH_ENDPOINT, auth=AUTH)
		ebay = requests.post(EBAY_REFRESH_ENDPOINT, auth=AUTH)
		prem = requests.post(PREM_SHIRTS_REFRESH_ENDPOINT, auth=AUTH)
		nsotd = requests.post(NSOTD_REFRESH_ENDPOINT, auth=AUTH)
		buckeroo = requests.post(BUCK_REFRESH_ENDPOINT, auth=AUTH)
	except Exception as e:
		print(e)
		return False

	if (amazon_usa.json()['success'] == 'true' and
		amazon_can.json()['success'] == 'true' and
		ebay.json()['success'] == 'true' and
		prem.json()['success'] == 'true' and
		nsotd.json()['success'] == 'true' and
		buckeroo.json()['success'] == 'true'):

		create_tables()

		time.sleep(10)  # sleep(120)
		return True
	
	return False
	

def _get_amazon_orders():
	# USA orders that are awaiting shipment
	amazon_usa_await_resp = requests.get(AMZ_USA_AWAIT_ENDPOINT, auth=AUTH)
	# USA orders that are pending fulfillment
	amazon_usa_pend_resp = requests.get(AMZ_USA_PEND_ENDPOINT, auth=AUTH)
	# Canadian orders that are awaiting shipment
	amazon_can_await_resp = requests.get(AMZ_CAN_AWAIT_ENDPOINT, auth=AUTH)
	# Canadian orders that are pending fulfillment
	amazon_can_pend_resp = requests.get(AMZ_CAN_PEND_ENDPOINT, auth=AUTH)
	# Lists
	amazon_usa_await_orders = amazon_usa_await_resp.json()['orders']
	amazon_usa_pend_orders = amazon_usa_pend_resp.json()['orders']
	amazon_can_await_orders = amazon_can_await_resp.json()['orders']
	amazon_can_pend_orders = amazon_can_pend_resp.json()['orders']

	num_orders = str(len(amazon_usa_await_orders) + len(amazon_usa_pend_orders) + len(amazon_can_await_orders) + len(amazon_can_pend_orders))
	print('\n-> Amazon: ' + num_orders + ' Orders\n')

	return (amazon_usa_await_orders, amazon_usa_pend_orders, amazon_can_await_orders, amazon_can_pend_orders)


def _get_ebay_orders():
	ebay_await_resp = requests.get(EBAY_ENDPOINT, auth=AUTH)
	# List
	ebay_orders = ebay_await_resp.json()['orders']
	num_orders = str(len(ebay_orders))
	print('\n-> eBay: ' + num_orders + ' Orders\n')
	return ebay_orders


def _get_prem_orders():
	prem_shirts_await_resp = requests.get(PREM_SHIRTS_ENDPOINT, auth=AUTH)
	# List
	prem_shirts_orders = prem_shirts_await_resp.json()['orders']
	num_orders = str(len(prem_shirts_orders))
	print('\n-> Premier Shirts: ' + num_orders + ' Orders\n')
	return prem_shirts_orders


def _get_nsotd_orders():
	nsotd_await_resp = requests.get(NSOTD_ENDPOINT, auth=AUTH)
	# List
	nsotd_orders = nsotd_await_resp.json()['orders']
	num_orders = str(len(nsotd_orders))
	print('\n-> New Shirt of the Day: ' + num_orders + ' Orders\n')
	return nsotd_orders


def _get_buckeroo_orders():
	buck_await_resp = requests.get(BUCK_ENDPOINT, auth=AUTH)
	# List
	buck_orders = buck_await_resp.json()['orders']
	num_orders = str(len(buck_orders))
	print('\n-> Buckeroo: ' + num_orders + ' Orders\n')
	return buck_orders


# eBay's order number mapped to 'orderKey', all other order numbers mapped to 'orderNumber'
def _parse_order_metadata(orders, store, is_ebay=False):
	order_data = {}

	for order in orders:
		if is_ebay:
			order_num = order['orderKey']
		else:
			order_num = order['orderNumber']

		customer = order['billTo']['name']

		# remove milliseconds then split date and time
		# date, _time = order['orderDate'].split('.')[0].split('T')  # YYYY-MM-DD, hh:mm:ss
		# year, month, day = date.split('-')                         # YYYY, MM, DD
		# hour, minute, seconds = _time.split(':')                   # hh, mm, ss
		# order_datetime = f'{month}/{day}/{year} {hour}:{minute}:{seconds}'

		# example orderDate: 2023-05-25T14:50:07.0000000
		# remove milliseconds, split date and time, join into single string
		order_datetime = ' '.join(order['orderDate'].split('.')[0].split('T'))      # YYYY-MM-DD hh:mm:ss
		

		# A list of dictionaries with item information.
		items_list = order['items']

		for item in items_list:
			sku = item['sku']
			description = item['name']   # description we provided
			quantity = item['quantity']  # int

			# Clean the SKU
			#  
			# No SKU (NoneType / empty string), or randomly generated SKU
			if sku is None or sku == '' or sku[:3] == 'wi_': 
				sku = description
			# Revised SKU
			elif sku in MAP: 
				sku = MAP[sku]
			# Obsolete SKU
			elif sku[-3:] == '-SL': 
				sku = sku[:-3]
			elif sku[-4:] == '-SLL': 
				sku = sku[:-4]
			elif sku[-2:] == '-D': 
				sku = sku[:-2]

			sku = _clean_sku(sku)

			# insert each item into db
			for _ in range(quantity):
				itm = Item(
					store=store, 
					order_num=order_num, 
					order_datetime=order_datetime, 
					customer=customer, 
					sku=sku, 
					description=description, 
					#quantity=quantity
				)

				db.session.add(itm)
				db.session.commit()

			

			item_data = (order_datetime, store, customer, sku, description, quantity)
			if order_num not in order_data:
				order_data[order_num] = [item_data]
			else:
				order_data[order_num].append(item_data)

	return order_data


def _clean_sku(sku):
	# VS127 - VS136
	vs_map = {
	"VS127": "VS.127", "VS128": "VS.128", "VS129": "VS.129", "VS130": "VS.130", 
	"VS131": "VS.131", "VS132": "VS.132", "VS133": "VS.133", "VS134": "VS.134", 
	"VS135": "VS.135", "VS136": "VS.136", "2VS134": "VS.134"
	}

	sku_array = sku.split('-')
	brand = sku_array[0]
	brand_and_style = None
	size = None

	# PREMIER
	if brand == 'PREM':
		# PREM-646-MED, PREM-631NEW-LRG, PREM-210P-5XL
		if len(sku_array) == 3:
			premiere, style, _size = sku_array
			# PREM-631NEW-XL
			if style[-3:] == 'NEW':
				style = style[:3]
			brand_and_style = premiere + '-' + style
			size = _size
		# PREM-618-RED-MED, PREM-SS-101-LRG
		elif len(sku_array) == 4:
			premiere, index_1, index_2, _size = sku_array
			style = index_1 + '-' + index_2
			brand_and_style = premiere + '-' + style
			size = _size
	# STEX
	elif brand == 'STEX' or brand == 'STX':
		stex, color, _size = sku_array

		if color == 'WHT':      stex = 'STEX6'
		elif color == 'BRIT':   stex = 'STEX7'
		elif color == 'GRN':    stex = 'STEX5'
		elif color == 'CHAR':   stex = 'STEX4'
		elif color == 'BLK':    stex = 'STEX2'
		elif color == 'GREY':   stex = 'STEX3'
		elif color == 'RED':    stex = 'STEX8'
		elif color == 'NAVY':   stex = 'STEX1'
		elif color == 'KAK':    stex = 'STEX9'

		brand_and_style = stex + '-' + color
		size = _size
	# RODEO / ACE / PLAT
	elif brand == 'ROD' or brand == 'RODEO' or brand == 'ACE' or brand == 'PLAT':
		# RODEO-524-XL
		if len(sku_array) == 3:
			rodeo, style, _size = sku_array
			brand_and_style = rodeo + '-' + style
			size = _size
		# RODEO-BEIG-533-MED, ROD-WOM-506-XL
		elif len(sku_array) == 4:
			rodeo, color_or_women, style, _size = sku_array
			# strip 'PS400' from style number (RODEO-BRWN-PS400461N-MED)
			if style[:5] == 'PS400':
				style = style[5:]
			brand_and_style = rodeo + '-' + style + '-' + color_or_women
			size = _size
		# ACE-WOM-BLU-ES5110-SML
		elif len(sku_array) == 5:
			ace, women, color, style, _size = sku_array
			brand_and_style = ace + '-' + style + '-' + women + '-' + color
			size = _size
	# BUCKEROO
	elif brand == 'BUCK':
		# BUCK-WS6-BEGE/BRWN-LRG
		buck, style, color, _size = sku_array
		brand_and_style = buck + '-' + style + '-' + color
		size = _size
	# VASS / BENZ
	elif brand == 'VASS' or brand == 'BENZ':
		# VASS-LEOP-VS135-SML
		vass, color, style, _size = sku_array
		# change VS127 - VS136 to VS.127 - VS.136 so they show up in alphanumeric order,
		# they were in between VS03 and VS15
		if style in vs_map:
			style = vs_map[style]
		brand_and_style = vass + '-' + style + '-' + color
		size = _size
	# EVERYTHING ELSE
	else:
		# no cleaning necessary
		return sku


	if size == 'XXL':
		size = '2XL'

	cleaned_sku = brand_and_style + '-' + size
	return cleaned_sku
