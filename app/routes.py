from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import NoteForm


@app.route("/")
def home():
    header = {'name':'premier'}
    return render_template("home.html", title="Premier App", header=header)


@app.route("/notes", methods=["GET", "POST"])
def notes():
    form = NoteForm()
    if form.validate_on_submit():
        flash(f'Form submitted: {form.note.data}')
        return redirect(url_for("notes"))
    return render_template("notes.html", title="Notes", form=form)