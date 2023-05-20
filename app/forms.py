from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import ValidationError, DataRequired, InputRequired


# Notes
class NoteForm(FlaskForm):
    note = TextAreaField("Add note", validators=[InputRequired()])  # DataRequired()
    save = SubmitField("Save")
	
	# edit = SubmitField('Edit')
	# delete = SubmitField('Delete')