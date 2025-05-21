#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from backend.models import Person
from backend.app import app, db


def main():
    with app.app_context():
        persons = db.session.query(Person).all()
        print(f"Anzahl Personen in der Datenbank: {len(persons)}")
        for p in persons:
            print(f"ID: {p.id}, Name: {p.name}, Vorname: {p.first_name}, Nachname: {p.last_name}")


if __name__ == "__main__":
    main()
