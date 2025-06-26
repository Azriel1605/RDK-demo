# User Model
from app import db, app, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime, timedelta

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    uid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=False, nullable=True)
    username = db.Column(db.VARCHAR(80), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.VARCHAR(10), default='00')
    
    def get_id(self):
        return self.uid
    
class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.uid'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now() + timedelta(hours=1))
    used = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('reset_tokens', lazy=True))
    
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(100))
    nik = db.Column(db.CHAR(16), unique=True)
    dob = db.Column(db.Date)
    gender = db.Column(db.VARCHAR(10))
    disability = db.Column(db.VARCHAR(30))
    pendidikan = db.Column(db.VARCHAR(50))
    family_id = db.Column(db.CHAR(16), db.ForeignKey('family.kk'))
    status = db.Column(db.VARCHAR(20), default='Anak')
    menikah = db.Column(db.VARCHAR(20), default='Belum Menikah')
    pekerjaan = db.Column(db.VARCHAR(50), default='Belum Bekerja')

class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kk = db.Column(db.CHAR(16), unique=True)
    address = db.Column(db.VARCHAR(200))
    rt = db.Column(db.VARCHAR(5))
    rw = db.Column(db.VARCHAR(5))
    kb = db.Column(db.VARCHAR(20))
    status_hamil = db.Column(db.Boolean, default=False)
    disability = db.Column(db.Boolean, default=False)
    putus_sekolah = db.Column(db.Boolean, default=False)

    members = db.relationship('Person', backref='family', lazy=True, foreign_keys='Person.family_id')
    
# Create tables
with app.app_context():
    db.create_all()
    
    # Create a default user if none exists
    if not User.query.first():
        all_user = []
        
        default_user = User(
            username='KELURAHAN',
            password=bcrypt.generate_password_hash('grG7DVlj').decode('utf-8'),
            role = 'superadmin'
        )
        
        key = User(
            username='Key',
            password=bcrypt.generate_password_hash('Ra_sy6a7e2').decode('utf-8'),
            role='superadmin'  # Default role for admin
        )
        # Add default user to the list
        all_user.append(default_user)
        all_user.append(key)

        listpw = ['8Q9eh2ZK',
                   'cxa2U3kV',
                   'vFe8UyWc',
                   'Ubg6bL09',
                   'rwMxsab2',
                   'mtcRqqQ6',
                   'bk4aTOQ2',
                   'uo49JF48',
                   'f2BnjcCH',
                   'q8Wl65LY',
                   'nC6rBCmE',
                   'Rd8eN7iA'
]
        for i in range(1, 13):
            user = User(
                username=f'RW{i}',
                password=bcrypt.generate_password_hash(listpw[i-1]).decode('utf-8'),
                role='{}'.format(i).zfill(2)  # Format as 'rw01', 'rw02', etc.
            )
            all_user.append(user)

        db.session.add_all(all_user)
        db.session.commit()
        print("Default user created: kelurahan/grG7DVlj")