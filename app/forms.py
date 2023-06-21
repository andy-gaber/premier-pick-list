from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import ValidationError, DataRequired, InputRequired


# Note
class NoteForm(FlaskForm):
    note = TextAreaField('Add note', validators=[InputRequired()])  # DataRequired()
    save = SubmitField('Save')
	# edit = SubmitField('Edit')
	# delete = SubmitField('Delete')


# Edit a note
class EditNoteForm(FlaskForm):
    note = TextAreaField('New note', validators=[InputRequired()])  # DataRequired()
    save = SubmitField('Save')