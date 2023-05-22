import time
import datetime
import requests
from requests.auth import HTTPBasicAuth

from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import NoteForm, RefreshForm

from config import USER, PASS, store_ids


@app.route("/", methods=["GET", "POST"])
def home():
	# refresh store
	# import orders
	# populate DB

	header = {'name':'premier'}

	form = RefreshForm()

	if form.validate_on_submit():
		
		if _refresh_all():
			print("Refreshing...")
			flash("Refresh success")
			return redirect(url_for("home"))  #### return redirect(url_for("all_orders"))
		flash(f"[Error] store refresh")
		return render_template("home.html", title="Premier App", header=header)
	
	return render_template("home.html", title="Premier App", header=header)


@app.route("/notes", methods=["GET", "POST"])
def notes():
	form = NoteForm()
	if form.validate_on_submit():
		flash(f'Form submitted: {form.note.data}')
		return redirect(url_for("notes"))
	return render_template("notes.html", title="Notes", form=form)




# @app.route("/all_orders")
# def all_orders():
#     pass


def _refresh_all():
	auth = HTTPBasicAuth(USER, PASS)

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

			time.sleep(1)  # sleep(120)
			return True
	except Exception as e:
		return False