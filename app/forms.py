from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import InputRequired


# Note
class NoteForm(FlaskForm):
    note = TextAreaField('Add note', validators=[InputRequired()])
    save = SubmitField('Save')


# Edit a note
class EditNoteForm(FlaskForm):
    note = TextAreaField('Edit note', validators=[InputRequired()])
    save = SubmitField('Save')