import time
import datetime
import requests
from requests.auth import HTTPBasicAuth
from typing import Any

from app import SQLITE_DATABASE_URI
from app.db import create_tables, _connect_db, _close_db
from app.sku_map import MAP
from app.secrets import (
	AUTH,
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


# get up to date order data from all stores; this drops all tables 
# if they exist to remove stale data from db
def _refresh_stores() -> bool:
	try:
		amazon_usa = requests.post(AMZ_USA_REFRESH_ENDPOINT, auth=AUTH)
		amazon_can = requests.post(AMZ_CAN_REFRESH_ENDPOINT, auth=AUTH)
		ebay = requests.post(EBAY_REFRESH_ENDPOINT, auth=AUTH)
		prem = requests.post(PREM_SHIRTS_REFRESH_ENDPOINT, auth=AUTH)
		nsotd = requests.post(NSOTD_REFRESH_ENDPOINT, auth=AUTH)
		buckeroo = requests.post(BUCK_REFRESH_ENDPOINT, auth=AUTH)

		if (
			amazon_usa.json()['success'] == 'true' 
			and amazon_can.json()['success'] == 'true' 
			and ebay.json()['success'] == 'true' 
			and prem.json()['success'] == 'true' 
			and nsotd.json()['success'] == 'true' 
			and buckeroo.json()['success'] == 'true'
		):
			create_tables()
			return True

	except Exception as e:
		print(e)
		return False


def _get_amazon_orders() -> tuple[list[dict[str, Any]]]:
	# Amazon order metadata (Amazon sales restricted to United States and Canada)
	# Amazon sales data is categorized into "awaiting shipment" and "pending fulfillment" 
	amazon_usa_await_resp = requests.get(AMZ_USA_AWAIT_ENDPOINT, auth=AUTH)
	amazon_usa_pend_resp = requests.get(AMZ_USA_PEND_ENDPOINT, auth=AUTH)
	amazon_can_await_resp = requests.get(AMZ_CAN_AWAIT_ENDPOINT, auth=AUTH)
	amazon_can_pend_resp = requests.get(AMZ_CAN_PEND_ENDPOINT, auth=AUTH)

	amazon_usa_await_orders: list[dict[str, Any]] = amazon_usa_await_resp.json()['orders']
	amazon_usa_pend_orders: list[dict[str, Any]] = amazon_usa_pend_resp.json()['orders']
	amazon_can_await_orders: list[dict[str, Any]] = amazon_can_await_resp.json()['orders']
	amazon_can_pend_orders: list[dict[str, Any]] = amazon_can_pend_resp.json()['orders']

	# For debugging!
	#
	# num_orders = str(
	# 	len(amazon_usa_await_orders) + 
	# 	len(amazon_usa_pend_orders) + 
	# 	len(amazon_can_await_orders) + 
	# 	len(amazon_can_pend_orders)
	# )
	# print('\n-> Amazon: ' + num_orders + ' Orders\n')

	return (amazon_usa_await_orders, amazon_usa_pend_orders, amazon_can_await_orders, amazon_can_pend_orders)


def _get_ebay_orders() -> list[dict[str, Any]]:
	# eBay order metadata
	ebay_await_resp = requests.get(EBAY_ENDPOINT, auth=AUTH)
	ebay_orders: list[dict[str, Any]] = ebay_await_resp.json()['orders']
	
	# For debugging!
	#
	# num_orders = str(len(ebay_orders))
	# print('\n-> eBay: ' + num_orders + ' Orders\n')
	
	return ebay_orders


def _get_prem_orders() -> list[dict[str, Any]]:
	# Premier Shirts order metadata
	prem_shirts_await_resp = requests.get(PREM_SHIRTS_ENDPOINT, auth=AUTH)
	prem_shirts_orders: list[dict[str, Any]] = prem_shirts_await_resp.json()['orders']
	
	# For debugging!
	#
	# num_orders = str(len(prem_shirts_orders))
	# print('\n-> Premier Shirts: ' + num_orders + ' Orders\n')
	
	return prem_shirts_orders


def _get_nsotd_orders() -> list[dict[str, Any]]:
	# New Shirt of the Day order metadata
	nsotd_await_resp = requests.get(NSOTD_ENDPOINT, auth=AUTH)
	nsotd_orders: list[dict[str, Any]] = nsotd_await_resp.json()['orders']

	# For debugging!
	#
	# num_orders = str(len(nsotd_orders))
	# print('\n-> New Shirt of the Day: ' + num_orders + ' Orders\n')
	
	return nsotd_orders


def _get_buckeroo_orders() -> list[dict[str, Any]]:
	# Buckeroo order metadata
	buck_await_resp = requests.get(BUCK_ENDPOINT, auth=AUTH)
	buck_orders: list[dict[str, Any]] = buck_await_resp.json()['orders']
	
	# For debugging!
	#
	# num_orders = str(len(buck_orders))
	# print('\n-> Buckeroo: ' + num_orders + ' Orders\n')
	
	return buck_orders


def _parse_store_metadata(
	orders: list[dict[str, Any]], 
	store: str, 
	is_ebay: bool = False
) -> None:
	# bool is_ebay is used because eBay's order number is mapped from key 'orderKey', 
	# while all other stores order numbers are mapped from key 'orderNumber'
	
	conn = _connect_db()
	
	# For debugging!
	#
	# METADATA = {}

	for order in orders:
		if is_ebay:
			order_num: str = order['orderKey']
		else:
			order_num: str = order['orderNumber']

		customer: str = order['billTo']['name']

		# ISO datetime, ex: 2023-05-25T14:50:07.0000000
		iso_dt: str = order['orderDate']

		# remove milliseconds, split date and time
		date, _time = iso_dt.split('.')[0].split('T')  # YYYY-MM-DD, hh:mm:ss
		year, month, day = date.split('-')             # YYYY, MM, DD
		hour, minute, _ = _time.split(':')             # hh, mm, ss
		order_datetime = datetime.datetime(
			year=int(year),
			month=int(month),
			day=int(day),
			hour=int(hour),
			minute=int(minute)
		)

		# string formatted datetime, ex: "01-23-2022 11:59 PM"
		str_datetime: str = order_datetime.strftime('%m-%d-%Y %I:%M %p')	

		# insert order into Customer_Order table
		cur = conn.cursor()
		new_customer_order = """
			INSERT INTO Customer_Order (store, order_number, iso_datetime, order_datetime, customer)
			VALUES (?, ?, ?, ?, ?);
		"""
		order_data = (store, order_num, iso_dt, str_datetime, customer)
		cur.execute(new_customer_order, order_data)
		conn.commit()

		# A list of dictionaries with item information.
		items_list: list[dict[str, Any]] = order['items']

		for item in items_list:
			sku: str = item['sku']
			description: str = item['name']   # description we provided
			quantity: int = item['quantity']

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

			# insert item into Item table
			cur = conn.cursor()
			new_item = """
				INSERT INTO Item (order_number, sku, quantity)
				VALUES (?, ?, ?);
			"""
			item_data = (order_num, sku, quantity)
			cur.execute(new_item, item_data)
			conn.commit()
			
			# For debugging!
			#
			# DATA = (str_datetime, store, customer, sku, description, quantity)
			# if order_num not in METADATA:
			# 	METADATA[order_num] = [DATA]
			# else:
			# 	METADATA[order_num].append(DATA)

	_close_db(conn)
	
	# For debugging!
	#
	# return METADATA


def _clean_sku(sku: str) -> str:
	# Modify VS127 - VS136 for logical sorting
	vs_map = {
		"VS127": "VS.127", "VS128": "VS.128", "VS129": "VS.129", "VS130": "VS.130", 
		"VS131": "VS.131", "VS132": "VS.132", "VS133": "VS.133", "VS134": "VS.134", 
		"VS135": "VS.135", "VS136": "VS.136", "2VS134": "VS.134"
	}

	sku_array: list[str] = sku.split('-')
	brand: str = sku_array[0]
	brand_and_style: str
	size: str

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

		# STEX<num> to sort in order by location
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

	# WICKED SHORTS / WEAR SHORTS
	elif brand == 'WICK' or brand == 'WEAR':
		wick_or_wear, color, _size = sku_array
		brand_and_style = wick_or_wear + '-' + color
		size = _size

	# VESE / AMDS
	elif brand == 'VESE' or brand == 'AMDS':
		# AMDS-RED-01-XL / VESE-GREEN-11-LRG
		vese_or_amds, color, style, _size = sku_array
		brand_and_style = vese_or_amds + '-' + style + '-' + color
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

	# VICT / ENVY / SOCI JEANS
	elif brand == 'VIC' or brand == 'VICT' or brand == 'ENVY' or brand == 'SOCI':
		# VICT-701-XL / ENVY-5034-SML
		if len(sku_array) == 3:
			vic_or_envy, style, _size = sku_array
			brand_and_style = vic_or_envy + '-' + style
			size = _size
		# VICT-BLACK-01-38x32 / ENVY-WHIT-101-XL / SOCI-BLU-950-32x32
		elif len(sku_array) == 4:
			vic_or_envy_or_soci, color, style, _size = sku_array
			brand_and_style = vic_or_envy_or_soci + '-' + style + '-' + color
			size = _size
		# ENVY-LACE-WHT-64025-SML
		elif len(sku_array) == 5:
			envy, lace, color, style, _size = sku_array
			brand_and_style = envy + '-' + style + '-' + lace + '-' + color
			size = _size
		# VIC-500-DENIM-JACKET-DARK-INDIGO-XL
		elif len(sku_array) == 7:
			vic, style, denim, jacket, color1, color2, _size = sku_array
			brand_and_style = vic + '-' + style + '-' + denim + '-' + jacket + '-' + color1 + '-' + color2
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
	
	# EVERYTHING ELSE (no cleaning necessary)
	else:
		return sku

	if size == 'XXL':
		size = '2XL'

	return brand_and_style + '-' + size


def _create_pick_list(items: list[tuple[str, int]]):
	# sort sizes in logical order (tops: XSML to 8XL, bottoms: 30 to 54)
	size_ordering = {
		'XS': 0,
		'SM': 1, 
		'ME': 2,
		'LA': 3,  # 'LARG'
		'LR': 4,  # 'LRG'
		'XL': 5, 
		'2X': 6, 
		'3X': 7, 
		'4X': 8, 
		'5X': 9, 
		'6X': 10, 
		'7X': 11, 
		'8X': 12, 
		'30': 13, 
		'32': 14, 
		'34': 15, 
		'36': 16, 
		'38': 17, 
		'40': 18, 
		'42': 19, 
		'44': 20, 
		'46': 21, 
		'48': 22, 
		'50': 23,
		'52': 24,
		'54': 25,
	}

	# Count all SKUs, ex)
	# dict = { 
	#	'PREM-001-SML': 1, 
	#	'PREM-001-MED': 3, 
	#	'PREM-002-LRG': 2, 
	#	'PREM-002-XL': 1 
	# }
	sku_to_quantity: dict[str, int] = {}

	for item in items:
		sku: str = item[0]
		quantity: int = item[1]
		sku_to_quantity[sku] = sku_to_quantity.get(sku, 0) + quantity

	# Condense styles to their sizes, ex)
	# dict = { 
	#	'PREM-001': [SML-1, MED-3], 
	#	'PREM-002': [LRG-2, XL-1] 
	# }
	style_to_sizes: dict[str, str | list[str]] = {}

	for sku, quantity in sku_to_quantity.items():
		# split style from size, ex: 
		# 'PREM-001-SML' -> ['PREM-001', 'SML']
		array: list[str] = sku.rsplit('-', 1)

		# irregular SKU, doesn't have a size
		if len(array) == 1:
			style_to_sizes[sku] = str(quantity)
			continue

		style, size = array

		# sku was a randomly generated coupon code, do not include in pick list
		if size[:2] not in size_ordering:
			continue

		if style not in style_to_sizes:
			style_to_sizes[style] = [size + '-' + str(quantity)]
		else:
			style_to_sizes[style].append(size + '-' + str(quantity))

	# Add each condensed style to list, sort in alphanumeric order, ex)
	# list = [
	#	'PREM-001 -> SML, MED (3)',
	#	'PREM-002 -> LRG (2), XL'
	# ]
	pick_list: list[str] = []

	for style, sizes in style_to_sizes.items():
		# list of the style's sizes, ex: [SML-1, MED-3]
		if type(sizes) is list:
			sizes.sort(key=lambda x: size_ordering[x[:2]])
			for i in range(len(sizes)):
				size, quant = sizes[i].split('-')
				# transform each element of list, include quantity only if greater than 1, ex)
				# 'SML-1' -> 'SML'
				# 'MED-3' -> 'MED (3)'
				if int(quant) == 1:
					sizes[i] = size
				else:
					sizes[i] = size + ' (' + quant + ')'

			# concatenate delimeter '?', used in front end to split style from sizes 
			style = style + '?'

			# concatenate sizes to style, ex) 
			# 'PREM-001?SML, MED (3)'
			for i in range(len(sizes)):
				# last item in list, no comma necessary
				if i + 1 == len(sizes):
					style = style + str(sizes[i])
				else:
					style = style + str(sizes[i]) + ', '
			style = style + '\n'
		# sizes is not a list if a SKU was irregular, sizes is a numerical string ('1', '2', etc)
		else:
			# more than one quantity
			if int(sizes) > 1:
				style = style + ' (' + sizes + ')' + '\n'
			else:
				style = style + '\n'

		pick_list.append(style)

	pick_list.sort()

	return pick_list