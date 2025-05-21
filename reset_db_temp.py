from backend.models import db
from backend.app import app

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database reset and initialized successfully!")
