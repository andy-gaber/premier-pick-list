import time
import datetime
import requests
from requests.auth import HTTPBasicAuth

from flask import render_template, flash, redirect, url_for, current_app
from app import app
from app.forms import NoteForm
#from app.models import Item, Note
from app.models import connect_db, close_db


from app.logic import (
	_refresh_stores, 
	_get_amazon_orders, 
	_get_ebay_orders, 
	_get_prem_orders, 
	_get_nsotd_orders, 
	_get_buckeroo_orders, 
	_parse_order_metadata, 
	_clean_sku
)


# AMAZON = 'Amazon'
# EBAY = 'eBay'
# PREM_SHIRTS = 'Premier Shirts'
# NSOTD = 'New Shirt of the Day'
# BUCKEROO = 'Buckeroo'


@app.route('/', methods=['GET', 'POST'])
def home():
	# display date and time of most recent update for all stores
	with app.app_context():
		try:
			update = current_app.last_update
		except:
			update = "No stores updated yet :("

	header = {'name':'Premier'}
	return render_template('home.html', title='Premier App', header=header, last_update=update)


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

		# set date and time when all stores were last updated, ex: "Jan 31 2022 11:59 PM"
		with app.app_context():
			current_app.last_update = datetime.datetime.now().strftime('%b %d %Y %I:%M %p')

		# amazon
		usa_await, usa_pend, can_await, can_pend = _get_amazon_orders()
		usa_await_order_data = _parse_order_metadata(usa_await, AMAZON)
		usa_pend_order_data = _parse_order_metadata(usa_pend, AMAZON)
		can_await_order_data = _parse_order_metadata(can_await, AMAZON)
		can_pend_order_data = _parse_order_metadata(can_pend, AMAZON)
		for k,v in usa_await_order_data.items():
			print(k)
			print(v)
			print('-'*80)

		# ebay
		ebay_orders = _get_ebay_orders()
		ebay_order_data = _parse_order_metadata(ebay_orders, EBAY, is_ebay=True)
		for k,v in ebay_order_data.items():
			print(k)
			print(v)
			print('-'*80)

		# premier shirtrs
		prem_orders = _get_prem_orders()
		prem_order_data = _parse_order_metadata(prem_orders, PREM_SHIRTS)
		for k,v in prem_order_data.items():
			print(k)
			print(v)
			print('-'*80)

		# new shirt of the day
		nsotd_orders = _get_nsotd_orders()
		nsotd_order_data = _parse_order_metadata(nsotd_orders, NSOTD)
		for k,v in nsotd_order_data.items():
			print(k)
			print(v)
			print('-'*80)

		# buckeroo
		buck_orders = _get_buckeroo_orders()
		buck_order_data = _parse_order_metadata(buck_orders, BUCKEROO)
		for k,v in buck_order_data.items():
			print(k)
			print(v)
			print('-'*80)

		return redirect(url_for('home'))
	flash(f'[Error] store refresh')
	return redirect(url_for('home'))


# order by SKU
#
# *** Need to condense each SKU and sizes
#
@app.route('/all-items')
def all_items():
	#items = Item.query.order_by(Item.sku).all()

	conn = _connect_db()
	cur = conn.cursor()
	items = cur.execute("SELECT * FROM Item ORDER BY sku").fetchall()
	_close_db(conn)

	return render_template('all-items.html', items=items)


@app.route('/amazon')
def amazon():
	#amazon_items = Item.query.filter_by(store=AMAZON).order_by(Item.order_datetime.desc()).all()
	
	conn = _connect_db()
	cur = conn.cursor()
	query = """
		SELECT * FROM Item
		WHERE store='Amazon'
		ORDER BY order_datetime DESC
	"""
	amazon_items = cur.execute(query).fetchall()
	_close_db(conn)

	return render_template('amazon.html', items=amazon_items)


@app.route('/ebay')
def ebay():
	#ebay_items = Item.query.filter_by(store=EBAY).order_by(Item.order_datetime.desc()).all()
	
	conn = _connect_db()
	cur = conn.cursor()
	query = """
		SELECT * FROM Item
		WHERE store='eBay'
		ORDER BY order_datetime DESC
	"""
	ebay_items = cur.execute(query).fetchall()
	_close_db(conn)

	return render_template('ebay.html', items=ebay_items)


@app.route('/premier-shirts')
def prem_shirts():
	#prem_items = Item.query.filter_by(store=PREM_SHIRTS).order_by(Item.order_datetime.desc()).all()
	
	conn = _connect_db()
	cur = conn.cursor()
	query = """
		SELECT * FROM Item
		WHERE store='Premier Shirts'
		ORDER BY order_datetime DESC
	"""
	prem_items = cur.execute(query).fetchall()
	_close_db(conn)

	return render_template('premier-shirts.html', items=prem_items)


@app.route('/new-shirt-of-the-day')
def nsotd():
	#nsotd_items = Item.query.filter_by(store=NSOTD).order_by(Item.order_datetime.desc()).all()
	
	conn = _connect_db()
	cur = conn.cursor()
	query = """
		SELECT * FROM Item
		WHERE store='New Shirt of the Day'
		ORDER BY order_datetime DESC
	"""
	nsotd_items = cur.execute(query).fetchall()
	_close_db(conn)

	return render_template('new-shirt-of-the-day.html', items=nsotd_items)


@app.route('/buckeroo')
def buckeroo():
	#buck_items = Item.query.filter_by(store=BUCKEROO).order_by(Item.order_datetime.desc()).all()
	
	conn = _connect_db()
	cur = conn.cursor()
	query = """
		SELECT * FROM Item
		WHERE store='Buckeroo'
		ORDER BY order_datetime DESC
	"""
	buck_items = cur.execute(query).fetchall()
	_close_db(conn)

	return render_template('buckeroo.html', items=buck_items)