#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Persons Blueprint
This blueprint handles person management functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf.csrf import validate_csrf
from backend.models import db, Person

persons_bp = Blueprint("persons", __name__)


@persons_bp.route("/", methods=["GET", "POST"])
def index():
    """Handle person management"""
    if request.method == "POST":
        # Validate CSRF token for AJAX requests
        if request.is_json:
            try:
                csrf_token = request.json.get('csrf_token')
                if not csrf_token:
                    csrf_token = request.headers.get('X-CSRFToken')
                if not csrf_token:
                    return jsonify({
                        'error': "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.",
                        'details': "400 Bad Request: The CSRF session token is missing."
                    }), 400
                validate_csrf(csrf_token)
            except:
                return jsonify({
                    'error': "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.",
                    'details': "400 Bad Request: Invalid CSRF token."
                }), 400

        action = request.form.get("action")

        if action == "add":
            name = request.form.get("name", "").strip()
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()

            if not name:
                flash("Bitte geben Sie einen Namen ein.", "warning")
                return redirect(url_for("persons.manage_persons"))

            # Check for duplicate
            existing = Person.query.filter_by(name=name).first()
            if existing:
                flash(f'Eine Person mit dem Namen "{name}" existiert bereits.', "warning")
                return redirect(url_for("persons.manage_persons"))

            # Create new person
            person = Person(name=name, first_name=first_name, last_name=last_name)

            db.session.add(person)
            db.session.commit()

            flash(f'Person "{name}" erfolgreich hinzugefügt.', "success")
            return redirect(url_for("persons.manage_persons"))

        elif action == "delete":
            person_id = request.form.get("person_id")
            if not person_id:
                flash("Keine Person zum Löschen ausgewählt.", "warning")
                return redirect(url_for("persons.manage_persons"))

            person = Person.query.get(person_id)
            if not person:
                flash("Person nicht gefunden.", "danger")
                return redirect(url_for("persons.manage_persons"))

            db.session.delete(person)
            db.session.commit()

            flash(f'Person "{person.name}" erfolgreich gelöscht.', "success")
            return redirect(url_for("persons.manage_persons"))

        elif action == "edit":
            person_id = request.form.get("person_id")
            if not person_id:
                flash("Keine Person zum Bearbeiten ausgewählt.", "warning")
                return redirect(url_for("persons.manage_persons"))

            person = Person.query.get(person_id)
            if not person:
                flash("Person nicht gefunden.", "danger")
                return redirect(url_for("persons.manage_persons"))

            name = request.form.get("name", "").strip()
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()

            if not name:
                flash("Bitte geben Sie einen Namen ein.", "warning")
                return redirect(url_for("persons.manage_persons"))

            # Check for duplicate (excluding current person)
            existing = Person.query.filter(Person.name == name, Person.id != person.id).first()
            if existing:
                flash(f'Eine Person mit dem Namen "{name}" existiert bereits.', "warning")
                return redirect(url_for("persons.manage_persons"))

            person.name = name
            person.first_name = first_name
            person.last_name = last_name

            db.session.commit()

            flash(f'Person "{name}" erfolgreich aktualisiert.', "success")
            return redirect(url_for("persons.manage_persons"))

    # GET request - show persons list
    persons = Person.query.all()
    return render_template("persons.html", persons=persons)


@persons_bp.route("/api/persons", methods=["GET"])
def get_persons():
    """API endpoint to get all persons"""
    persons = Person.query.all()
    return jsonify([person.to_dict() for person in persons])
