from app import db


class Item(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	store = db.Column(db.String(64), index=True)
	order_num = db.Column(db.String(64))
	order_datetime = db.Column(db.String(64))
	customer = db.Column(db.String(128))
	sku = db.Column(db.String(128))
	description = db.Column(db.String(128))
	quantity = db.Column(db.Integer)

	def __repr__(self):
		return '<Item>\n' + \
				'Order number:  ' + self.order_num + '\n' + \
				'Order date:    ' + self.order_date + '\n' + \
				'Store:         ' + self.store + '\n' + \
				'Customer:      ' + self.customer + '\n' + \
				'SKU:           ' + self.sku + '\n' + \
				'Description:   ' + self.description + '\n' + \
				'Quantity:      ' + str(self.quantity)
		

class Note(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	note = db.Column(db.String(320))

	def __repr__(self):
		return 	'<Note>\n' + \
				'Note: ' + self.note

