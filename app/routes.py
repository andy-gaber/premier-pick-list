import time
import datetime
import requests
from requests.auth import HTTPBasicAuth

from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import NoteForm

from logic import (
	_refresh_stores, 
	_get_amazon_orders, 
	_get_ebay_orders, 
	_get_prem_orders, 
	_get_nsotd_orders, 
	_get_buckeroo_orders, 
	_parse_order_metadata, 
	_clean_sku
)


AMAZON = 'Amazon'
EBAY = 'eBay'
PREM_SHIRTS = 'Premier Shirts'
NSOTD = 'New Shirt of the Day'
BUCKEROO = 'Buckeroo'


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


# @app.route('/all_orders')
# def all_orders():
#     pass