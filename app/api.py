import time
import datetime
import requests
from requests.auth import HTTPBasicAuth

from flask import render_template, flash, redirect, url_for, current_app, request
from app import app
from app.forms import NoteForm, EditNoteForm
from app.db import _connect_db, _close_db, _get_metadata


from app.logic import (
	_refresh_stores, 
	_get_amazon_orders, 
	_get_ebay_orders, 
	_get_prem_orders, 
	_get_nsotd_orders, 
	_get_buckeroo_orders, 
	_parse_order_metadata, 
	_clean_sku,
	_create_pick_list
)


AMAZON = 'Amazon'
EBAY = 'eBay'
PREM_SHIRTS = 'Premier Shirts'
NSOTD = 'New Shirt of the Day'
BUCKEROO = 'Buckeroo'


@app.route('/', methods=['GET', 'POST'])
def home():
	# display date and time of most recent update for all stores
	with app.app_context():
		try:
			update = current_app.last_update
		except:
			update = "No stores updated yet :("

	return render_template('home.html', title='Premier Pick List', last_update=update)


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

		# ebay
		ebay_orders = _get_ebay_orders()
		ebay_order_data = _parse_order_metadata(ebay_orders, EBAY, is_ebay=True)

		# premier shirtrs
		prem_orders = _get_prem_orders()
		prem_order_data = _parse_order_metadata(prem_orders, PREM_SHIRTS)

		# new shirt of the day
		nsotd_orders = _get_nsotd_orders()
		nsotd_order_data = _parse_order_metadata(nsotd_orders, NSOTD)
	
		# buckeroo
		buck_orders = _get_buckeroo_orders()
		buck_order_data = _parse_order_metadata(buck_orders, BUCKEROO)

		return redirect(url_for('home'))
	flash(f'[Error] store refresh')
	return redirect(url_for('home'))


@app.route('/pick-list')
def pick_list():
	conn = _connect_db()
	cur = conn.cursor()
	query = """
		SELECT sku, SUM(quantity)
		FROM Item
		GROUP BY sku
	"""
	items = cur.execute(query).fetchall()
	pick_list = _create_pick_list(items)
	_close_db(conn)
	return render_template('pick-list.html', pick_list=pick_list)


@app.route('/amazon')
def amazon():
	items = _get_metadata(AMAZON)	
	return render_template('amazon.html', items=items)


@app.route('/ebay')
def ebay():
	items = _get_metadata(EBAY)
	return render_template('ebay.html', items=items)


@app.route('/premier-shirts')
def prem_shirts():
	items = _get_metadata(PREM_SHIRTS)
	return render_template('premier-shirts.html', items=items)


@app.route('/new-shirt-of-the-day')
def nsotd():
	items = _get_metadata(NSOTD)
	return render_template('new-shirt-of-the-day.html', items=items)


@app.route('/buckeroo')
def buckeroo():
	items = _get_metadata(BUCKEROO)
	return render_template('buckeroo.html', items=items)


@app.route('/notes', methods=['GET', 'POST'])
def notes():
	conn = _connect_db()

	form = NoteForm()
	# add new note
	if form.validate_on_submit():
		note = form.note.data
		
		cur = conn.cursor()
		new_note = """
			INSERT INTO Note (note)
			VALUES (?);
		"""
		data = (note,)
		cur.execute(new_note, data)
		conn.commit()
		_close_db(conn)

		flash('Note Created')
		return redirect(url_for('notes'))
 
	cur = conn.cursor()
	query = """ 
		SELECT * 
		FROM Note 
	"""
	notes = cur.execute(query).fetchall()
	_close_db(conn)

	return render_template('notes.html', title='Notes', form=form, notes=notes)


@app.route('/delete/<id>')
def delete_note(id):

	conn = _connect_db()
	cur = conn.cursor()
	query = """
		DELETE FROM Note
		WHERE id = ?
	"""
	note = (id,)
	cur.execute(query, note)
	conn.commit()

	flash('Note Deleted')
	return redirect(url_for('notes'))


@app.route('/edit/<id>')
def edit(id):
	with app.app_context():
		current_app.edit_note_id = int(id)

	return redirect(url_for('edit_note'))


@app.route('/edit-note', methods=['GET', 'POST'])
def edit_note():
	note_id = current_app.edit_note_id
	form = EditNoteForm()
	
	if form.validate_on_submit():
		note = form.note.data
		conn = _connect_db()
		cur = conn.cursor()

		edit = """
			UPDATE Note
			SET note = ?
			WHERE Note.id = ?
		"""
		data = (note, note_id)
		cur.execute(edit, data)
		conn.commit()
		_close_db(conn)

		flash(f'Note Edited')
		return redirect(url_for('notes'))

	return render_template('edit-note.html', form=form)