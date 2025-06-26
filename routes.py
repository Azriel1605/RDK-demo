from app import app, bcrypt, db, mail, Message
from flask import render_template, request, flash, session, redirect, url_for, jsonify, abort, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user
from model import User, Family, Person, PasswordResetToken
from sqlalchemy import func, asc, desc, or_, exc
from sqlalchemy.exc import IntegrityError
from api import api_bp
from psycopg2.errors import UniqueViolation
from io import BytesIO
import os
import pandas as pd
import string
import secrets
from datetime import datetime, timedelta

# Register the API blueprint
app.register_blueprint(api_bp)

def generate_reset_token(user):
    expires_at = datetime.now() + timedelta(hours=1)
    reset_token = PasswordResetToken(
        user_id=user.uid,
        token=''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)),
        created_at=datetime.now(),
        expires_at=expires_at
    )
    db.session.add(reset_token)
    db.session.commit()

    return reset_token.token

def send_reset_email(user_email, reset_token):
    """Send password reset email"""
    try:
        reset_url = url_for('reset_password', token=reset_token, _external=True)
        
        msg = Message(
            subject='🔐 Password Reset Request - CipamokolanDataKu',
            recipients=[user_email],
            html=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #f5f5dc 0%, #deb887 100%); padding: 20px; border-radius: 15px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #8d6e63; font-size: 2rem;">🏠 CipamokolanDataKu</h1>
                    <h2 style="color: #6d4c41;">Password Reset Request</h2>
                </div>
                
                <div style="background: rgba(255,255,255,0.9); padding: 25px; border-radius: 15px; margin-bottom: 20px;">
                    <p style="color: #5d4037; font-size: 1.1rem; line-height: 1.6;">
                        Hello! 👋
                    </p>
                    <p style="color: #5d4037; line-height: 1.6;">
                        We received a request to reset your password for your CipamokolanDataKu account. 
                        If you made this request, please click the button below to reset your password:
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="
                            background: linear-gradient(45deg, #8d6e63, #6d4c41);
                            color: white;
                            padding: 15px 30px;
                            text-decoration: none;
                            border-radius: 25px;
                            font-weight: 600;
                            font-size: 1.1rem;
                            display: inline-block;
                            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                        ">🔓 Reset Password</a>
                    </div>
                    
                    <p style="color: #5d4037; line-height: 1.6; font-size: 0.9rem;">
                        <strong>⏰ This link will expire in 1 hour for security reasons.</strong>
                    </p>
                    
                    <p style="color: #5d4037; line-height: 1.6; font-size: 0.9rem;">
                        If you didn't request this password reset, please ignore this email. 
                        Your password will remain unchanged.
                    </p>
                </div>
                
                <div style="text-align: center; color: #8d6e63; font-size: 0.8rem;">
                    <p>This is an automated message from Warm App</p>
                    <p>Please do not reply to this email</p>
                </div>
            </div>
            '''
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        flash(f"Error sending email: {e}")
        return False

def check_disability_and_pendidikan(family):
    """Check if any person in the family has a disability or is not educated"""

    family.disability = any(person.disability != "Tidak" for person in family.members)
    family.putus_sekolah = any(person.pendidikan == 'Tidak Sekolah' for person in family.members)

    db.session.commit()

@app.errorhandler(exc.SQLAlchemyError)
def handle_db_exceptions(error):
    #log the error:
    app.logger.error(error)
    db.session.rollback()
    
    return f'{error}'
# Error Handlers
@app.errorhandler(IntegrityError)
def handle_integrity_error(error):
    db.session.rollback()
    if isinstance(error.orig, UniqueViolation):
        flash('GAGAL MENAMBHAKAN DATA. Data sudah terdaftar!', 'error')
    else:
        flash('Database error occurred!', 'error')
    return redirect(request.url)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            session['username'] = username
            session['role'] = user.role
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/hasil-data')
@login_required
def hasil_data():
    return render_template('hasil_data.html')

@app.route('/input-data')
@login_required
def input_data():
    return render_template('input_data.html')

@app.route('/manual-input', methods=['GET', 'POST'])
@login_required
def manual_input():
    if request.method == 'POST':
        data = request.form.to_dict()
        
        if data['rw'] == '':
            flash('RW Harus Terisi!', 'error')
            return redirect(request.url)
            
        if data['kk'] == '':
            flash('KK Harus Terisi!', 'error')
            return redirect(request.url)
        
        temp_family = Family(
            kk=data['kk'],
            address=data['alamat'],
            rt=str(data['rt']).zfill(2),
            rw=str(data['rw']).zfill(2),
        )
        if data['kb']:
            temp_family.kb = data['kb']
        
        if data['hamil'] == 'ya':
            temp_family.status_hamil = True
        
        db.session.add(temp_family)
        db.session.flush()  # Ensures the family is added so Person can reference it
        
        # Step 2: Add person to that family
        family_members = []

        kepala = Person(
            name=data['kepala-nama'],
            nik=data['kepala-nik'],
            dob=data['kepala-dob'],
            gender=data['kepala-gender'],
            status='Kepala Keluarga',
            family_id=data['kk'],  # safe now that family is inserted
            disability=data['kepala-disability'],
            pendidikan=data['kepala-pendidikan'],
            menikah=data['kepala-menikah'],
            pekerjaan=data['kepala-job']
        )
        family_members.append(kepala)

        terisi = any([data.get(f'istri-nama'), data.get(f'istri-nik'), data.get(f'istri-dob'), data.get(f'istri-gender'), data.get(f'istri-disability'), data.get(f'istri-pendidikan'), data.get(f'istri-menikah'), data.get(f'istri-job')])
        tidak_terisi = any([data.get(f'istri-nama') == '', data.get(f'istri-nik') == '', data.get(f'istri-dob') == '', data.get(f'istri-gender') == '', data.get(f'istri-disability') == '', data.get(f'istri-pendidikan') == '', data.get(f'istri-menikah') == '', data.get(f'istri-job') == ''])

        if tidak_terisi and terisi:
            flash("DATA GAGAL DI-INPUT! Data Istri Harus Lengkap", 'error')
            return redirect(request.url)
        
        if terisi:
            istri = Person(
                name=data['istri-nama'],
                nik=data['istri-nik'],
                dob=data['istri-dob'],
                gender='Perempuan',
                status='Istri',
                family_id=data['kk'],  # safe now that family is inserted
                disability=data['istri-disability'],
                pendidikan=data['istri-pendidikan'],
                menikah=data['istri-menikah']
            )
            family_members.append(istri)
            
        for i in range(1, 11):
            terisi = any([data.get(f'anggota{i}-nama'), data.get(f'anggota{i}-nik'), data.get(f'anggota{i}-dob'), data.get(f'anggota{i}-gender'), data.get(f'anggota{i}-disability'), data.get(f'anggota{i}-pendidikan'), data.get(f'anggota{i}-menikah'), data.get(f'anggota{i}-job')])
            tidak_terisi = any([data.get(f'anggota{i}-nama') == '', data.get(f'anggota{i}-nik') == '', data.get(f'anggota{i}-dob') == '', data.get(f'anggota{i}-gender') == '', data.get(f'anggota{i}-disability') == '', data.get(f'anggota{i}-pendidikan') == '', data.get(f'anggota{i}-menikah') == '', data.get(f'anggota{i}-job') == ''])

            if tidak_terisi and terisi:
                flash(f'DATA GAGAL DI-INPUT! Data Anggota Keluarga ke-{i} Harus Lengkap', 'error')
                return redirect(request.url)
            
            if terisi:
                anak = Person(
                    name=data[f'anggota{i}-nama'],
                    nik=data[f'anggota{i}-nik'],
                    dob=data[f'anggota{i}-dob'],
                    gender=data[f'anggota{i}-gender'],
                    status='Anak',
                    family_id=data['kk'],  # safe now that family is inserted
                    disability=data[f'anggota{i}-disability'],
                    pendidikan=data[f'anggota{i}-pendidikan'],
                    menikah=data[f'anggota{i}-menikah'],
                    pekerjaan=data[f'anggota{i}-job']
                )
                family_members.append(anak)

        for i in family_members:
            if i.disability:
                temp_family.disability = True
            if i.pendidikan == 'Putus Sekolah':
                temp_family.putus_sekolah = True
        
        db.session.add_all(family_members)
        db.session.commit()
        flash('Data saved successfully!', 'success')
        return redirect(request.url)
    
    return render_template('manual_input.html')

@app.route('/excel-upload', methods=['GET', 'POST'])
def excel_upload():
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith(('.xlsx', '.xls')):
            # Read Excel from uploaded file (BytesIO for in-memory)
            df = pd.read_excel(BytesIO(file.read()), header=None)  # no header assumed
            # Extract column D (index 3), rows 2-55 (index 1 to 54)
            df = df.iloc[1:113, 3]  # Note: pandas is 0-indexed

            rw, rt, alamat, kk, kb, hamil = df[1], df[2], df[3], df[4], df[5], df[6]
            
            if pd.isna(rw):
                flash('RW Harus Terisi!', 'error')
                return redirect(request.url)
            
            if pd.isna(kk):
                flash('KK Harus Terisi!', 'error')
                return redirect(request.url)
            
            if pd.isna(kb):
                flash('KB Harus Terisi!', 'error')
                return redirect(request.url)
            
            if pd.isna(hamil):
                flash('Hamil Harus Terisi!', 'error')
                return redirect(request.url)

            temp_family = Family(
                kk=kk,
                address=alamat,
                rt=str(rt).zfill(2),
                rw=str(rw).zfill(2),
                kb=kb,
            )
            if hamil == 'Ya':
                temp_family.status_hamil = True
            
            db.session.add(temp_family)
            db.session.flush()  # Ensures the family is added so Person can reference it
            
            # Step 2: Add persons to that family
            family_members = []
            
            data = [df.iloc[i:i+8].values.tolist() for i in range(6, 22, 8)] + [df.iloc[i:i+9].values.tolist() for i in range(22, 111, 9)]
            for i, d in enumerate(data):
                tidak_terisi = any(pd.isna(item) for item in d)
                terisi = any(not pd.isna(item) for item in d)

                if terisi and tidak_terisi:
                    if i == 0: ## JIka kepala Keluarga
                        flash("DATA GAGAL DI-INPUT! Data Kepala Keluarga Harus Lengkap", 'error')
                        return redirect(request.url)
                    if i == 1: ## Jika istri
                        flash("DATA GAGAL DI-INPUT! Data Istri Harus Lengkap", 'error')
                        return redirect(request.url)
                    flash(f'DATA GAGAL DI-INPUT! Data Anggota Keluarga ke-{i+1} Harus Lengkap', 'error')
                    return redirect(request.url)
                if tidak_terisi:continue
                
                name, nik, dob, disability, pendidikan = d[0], d[1], d[2], d[4], d[5]
                menikah, pekerjaan = d[6], d[7]
                if len(d) > 8:
                    status, menikah, pekerjaan = d[6], d[7], d[8]
                if i == 0: ##Jika kepala keluarga
                    status = 'Kepala Keluarga'
                if i == 1: ##Jika istri
                    status = 'Istri'
                    
                person = Person(
                    name=name,
                    nik=nik,
                    dob=dob,
                    disability=disability,
                    pendidikan=pendidikan,
                    status=status,
                    menikah=menikah,
                    pekerjaan=pekerjaan,
                    family_id=kk  # safe now that family is inserted
                )
                if d[3] in ['Laki','L']:
                    person.gender = 'Laki-laki'
                else:
                    person.gender = 'Perempuan'
                
                if person.disability:
                    temp_family.disability = True
                if person.pendidikan == 'Tidak Sekolah':
                    temp_family.putus_sekolah = True
                
                db.session.add(person)
                family_members.append(person)
            
            db.session.flush()
            db.session.commit()
            flash(f'{len(family_members)} Data berhasil di-input!', 'success')
            return redirect(request.url)
            
        else:
            flash('Please upload a valid Excel file (.xlsx or .xls)', 'error')
    
    return render_template('excel_upload.html')

# Dynamic pages for the 12 buttons
@app.route('/page/<int:page_num>')
@login_required
def dynamic_page(page_num):
    if page_num < 0 or page_num > 12:
        flash('Page not found!', 'error')
        return redirect(url_for('hasil_data'))

    return render_template(f'page{page_num}.html', page_num=page_num)

@app.route('/update-person/<int:id>', methods=['GET', 'POST'])
@login_required
def update_person(id):
    person = Person.query.get_or_404(id)
    if request.method == 'POST':
        # Update person details
        person.name = request.form.get('name')
        person.nik = request.form.get('nik')
        person.dob = request.form.get('dob')
        person.gender = request.form.get('gender')
        person.disability = request.form.get('disability')
        person.pendidikan = request.form.get('pendidikan')
        person.status = request.form.get('status')
        person.pekerjaan = request.form.get('job')
        db.session.commit()
        flash('Person updated successfully!', 'success')
        check_disability_and_pendidikan(person.family)
        # Redirect to the first dynamic page
        return redirect(url_for('dynamic_page', page_num=0))
    return render_template('update_person.html', person=person)

@app.route('/delete-person/<int:id>', methods=['DELETE'])
@login_required
def delete_person(id):
    person = Person.query.get_or_404(id)
    db.session.delete(person)
    db.session.commit()
    check_disability_and_pendidikan(person.family)
    flash('Person deleted successfully!', 'success')
    return '', 204

@app.route('/update-family/<int:id>', methods=['GET', 'POST'])
@login_required
def update_family(id):
    family = Family.query.get_or_404(id)
    head = Person.query.filter_by(family_id=family.kk, status='Kepala Keluarga').first()
    if request.method == 'POST':
        family.kk = request.form.get('kk')
        family.address = request.form.get('alamat')
        family.rt = request.form.get('rt', 0).zfill(2)
        family.rw = request.form.get('rw', 0).zfill(2)
        family.kb = request.form.get('kb')
        family.status_hamil = True if request.form.get('status_hamil') == "ya" else False

        db.session.commit()
        flash('Family updated successfully!', 'success')
        return redirect(url_for('dynamic_page', page_num=0))
    return render_template('update_family.html', family=family, head=head)

@app.route('/delete-family/<int:id>', methods=['DELETE'])
@login_required
def delete_family(id):
    family = Family.query.get_or_404(id)
    persons = Person.query.filter_by(family_id=family.kk).all()
    for person in persons:
        db.session.delete(person)
    db.session.delete(family)
    db.session.commit()
    return '', 204

@app.route('/download/<filename>')
def download_file(filename):
    folder_path = os.path.join(app.root_path, 'file')
    try:
        return send_from_directory(folder_path, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)
        
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        
        if user:
            token = generate_reset_token(user)
            reset_link = url_for('reset_password', token=token, _external=True)
            
            if send_reset_email(user.email, token):
                flash(f'Link Reset Password sudah berhasil dikirimkan ke Gmail {user.email[:3]}***@gmail.com', 'success')
            else:
                flash('Gagal mengirim email reset password. Silakan coba lagi.', 'error')
        else:
            flash('Username tidak ditemukan!', 'error')

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    ## Check if token is valid
    reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset_token or reset_token.expires_at < datetime.now():
        flash('Token tidak valid atau sudah kadaluarsa!', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password == confirm_password:
            user = User.query.get(reset_token.user_id)
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            reset_token.used = True
            db.session.commit()
            flash('Password berhasil direset!', 'success')
            login_user(user)
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('index'))
        else:
            flash('Password dan konfirmasi password tidak cocok!', 'error')

    return render_template('reset_password.html', token=token)