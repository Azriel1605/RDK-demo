from app import db, bcrypt, app
from model import User

with app.app_context():
    key = User(
        username='admin',
        password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
        role='superadmin'  # Default role for admin
    )

    db.session.add(key)
    db.session.commit()