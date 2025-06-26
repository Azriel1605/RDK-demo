from model import Person, Family
from flask import jsonify, request, Blueprint
from sqlalchemy import func, asc, desc, or_, cast, String, and_
from sqlalchemy.orm import aliased
from flask_login import login_required, current_user
from datetime import datetime

api_bp = Blueprint('api_bp', __name__)

Head = aliased(Person)

def filterByRole(query, role):
    if role == 'admin' or role == 'superadmin':
        total_records = [None]
        rw = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
        for i in rw:
            role_query = query.filter(Family.rw == i)
            total_records.append(role_query.count())
        return query, total_records

    if int(role) >= 1 and int(role) <= 12:
        return query.filter(Family.rw == role), [query.filter(Family.rw == role).count()]
    
    
    
    
@api_bp.route('/api/all-data')
def get_all_data():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')

    # Base query
    query = Family.query.join(Family.members)

    # Search logic
    if search_value:
        query = query.filter(
            or_(
                Family.kk.ilike(f"%{search_value}%"),
                Family.rt.ilike(f"%{search_value}%"),
                Family.rw.ilike(f"%{search_value}%"),
                Person.name.ilike(f"%{search_value}%"),
            )
        )
    
    # Apply role filter
    query, total_records = filterByRole(query, current_user.role)

    # Group by Family to avoid row duplication due to JOIN
    query = query.group_by(Family.id)

    # Sorting logic
    if column_name == 'head':
        head_alias = aliased(Person)
        query = query.join(
            head_alias,
            (head_alias.family_id == Family.id) & (head_alias.status == 'Kepala Keluarga')
        )
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(head_alias.name))
    else:
        sort_column = getattr(Family, column_name, None)
        if sort_column is not None:
            sort_method = asc if order_direction == 'asc' else desc
            query = query.order_by(sort_method(sort_column))

    # Total filtered records
    records_count = query.count()

    # Apply pagination after grouping
    records = query.offset(start).limit(length).all()

    data = [
        {
            'id': r.id,
            'kk': r.kk,
            'head': next((m.name for m in r.members if m.status == "Kepala Keluarga"), "Not found"),
            'rt': r.rt,
            'rw': r.rw,
            'members': [
                {
                    'id': m.id,
                    'name': m.name,
                    'status': m.status,
                    'dob': m.dob.strftime('%Y-%m-%d') if m.dob else None
                }
                for m in r.members
            ]
        }
        for r in records
    ]

    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })


@api_bp.route('/api/pus')
def get_pus():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')
    
    # Get reference date (def set to today)
    reference_date = request.args.get('reference_date', datetime.today().strftime('%Y-%m-%d'))
    try:
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Base query
    query = Family.query\
            .join(Family.members)\
            .filter(
                Person.status == 'Istri',
                func.date_part('year', func.age(reference_date, Person.dob)).between(15, 49)
            ).distinct()

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Family.kk.ilike(f"%{search_value}%"),
            Family.rt.ilike(f"%{search_value}%"),
            Family.rw.ilike(f"%{search_value}%"),
            Person.name.ilike(f"%{search_value}%"),
        )
    )
    
    query, total_records = filterByRole(query, current_user.role)

    # Sorting logic
    
    sort_column = getattr(Family, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'kk': r.kk,
            'head': next((m.name for m in r.members if m.status == "Kepala Keluarga"), "Not found"),
            'rt': r.rt,
            'rw': r.rw,
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })
    
@api_bp.route('/api/ibu-hamil')
def get_ibu_hamil():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')
    
    

    # Base query
    query = Family.query.filter(Family.status_hamil == True)

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Family.kk.ilike(f"%{search_value}%"),
            Family.rt.ilike(f"%{search_value}%"),
            Family.rw.ilike(f"%{search_value}%"),
            Person.name.ilike(f"%{search_value}%"),
        )
    )
        

    query, total_records = filterByRole(query, current_user.role)
    


    # Sorting logic
    sort_column = getattr(Family, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'kk': r.kk,
            'head': next((m.name for m in r.members if m.status == "Kepala Keluarga"), "Not found"),
            'rt': r.rt,
            'rw': r.rw,
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })

@api_bp.route('/api/balita')
def get_balita():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')
    
    # Get reference date (def set to today)
    reference_date = request.args.get('reference_date', datetime.today().strftime('%Y-%m-%d'))
    try:
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Base query
    query = Family.query\
            .join(Family.members)\
            .filter(
                func.date_part('year', func.age(reference_date, Person.dob)) < 5,
            ).distinct()

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Family.kk.ilike(f"%{search_value}%"),
            Family.rt.ilike(f"%{search_value}%"),
            Family.rw.ilike(f"%{search_value}%"),
            Person.name.ilike(f"%{search_value}%"),
        )
    )
        

    query, total_records = filterByRole(query, current_user.role)
    


    # Sorting logic
    sort_column = getattr(Family, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'kk': r.kk,
            'head': next((m.name for m in r.members if m.status == "Kepala Keluarga"), "Not found"),
            'rt': r.rt,
            'rw': r.rw,
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })
    
@api_bp.route('/api/remaja')
def get_remaja():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')
    
    # Get reference date (def set to today)
    reference_date = request.args.get('reference_date', datetime.today().strftime('%Y-%m-%d'))
    try:
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d')
    except ValueError:
        print("value error")
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Base query
    query = Family.query\
            .join(Family.members)\
            .filter(
                func.date_part('year', func.age(reference_date, Person.dob)).between(10, 24),
                Person.menikah == 'Belum Menikah'
            ).distinct()

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Family.kk.ilike(f"%{search_value}%"),
            Family.rt.ilike(f"%{search_value}%"),
            Family.rw.ilike(f"%{search_value}%"),
            Person.name.ilike(f"%{search_value}%"),
        )
    )

    query, total_records = filterByRole(query, current_user.role)
    


    # Sorting logic
    sort_column = getattr(Family, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'kk': r.kk,
            'head': next((m.name for m in r.members if m.status == "Kepala Keluarga"), "Not found"),
            'rt': r.rt,
            'rw': r.rw,
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })
    
@api_bp.route('/api/lansia')
def get_lansia():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')
    
    # Get reference date (def set to today)
    reference_date = request.args.get('reference_date', datetime.today().strftime('%Y-%m-%d'))
    try:
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Base query
    query = Family.query\
            .join(Family.members)\
            .filter(
                func.date_part('year', func.age(reference_date, Person.dob)) >= 60,
            ).distinct()

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Family.kk.ilike(f"%{search_value}%"),
            Family.rt.ilike(f"%{search_value}%"),
            Family.rw.ilike(f"%{search_value}%"),
            Person.name.ilike(f"%{search_value}%"),
        )
    )
        

    query, total_records = filterByRole(query, current_user.role)
    


    # Sorting logic
    sort_column = getattr(Family, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'kk': r.kk,
            'head': next((m.name for m in r.members if m.status == "Kepala Keluarga"), "Not found"),
            'rt': r.rt,
            'rw': r.rw,
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })
    
@api_bp.route('/api/kelompok-balita')
def get_kelompok_balita():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')
    
    # Get reference date (def set to today)
    reference_date = request.args.get('reference_date', datetime.today().strftime('%Y-%m-%d'))
    try:
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d')
    except ValueError:
        print("value error")
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Base query
    query = Person.query\
                .filter(func.date_part('year', func.age(reference_date, Person.dob)) < 5)

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Person.name.ilike(f"%{search_value}%"),
            cast(Person.dob, String).ilike(f"%{search_value}%"),
            Person.gender.ilike(f"%{search_value}%"),
            Person.disability.ilike(f"%{search_value}%"),
            Person.pendidikan.ilike(f"%{search_value}%"),
        )
    )
        

    query, total_records = filterByRole(query.join(Person.family), current_user.role)
    


    # Sorting logic
    sort_column = getattr(Person, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'nama': r.name,
            'tanggal lahir': datetime.strftime(r.dob, '%Y-%m-%d') if r.dob else None,
            'gender': r.gender,
            'disability': r.disability,
            'pendidikan': r.pendidikan
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })
    
@api_bp.route('/api/kelompok-remaja')
def get_kelompok_remaja():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')
    
    # Get reference date (def set to today)
    reference_date = request.args.get('reference_date', datetime.today().strftime('%Y-%m-%d'))
    try:
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d')
    except ValueError:
        print("value error")
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Base query
    query = Person.query\
                .filter(func.date_part('year', func.age(reference_date, Person.dob)).between(10, 24),
                        Person.menikah == 'Belum Menikah')

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Person.name.ilike(f"%{search_value}%"),
            Person.dob.ilike(f"%{search_value}%"),
            Person.gender.ilike(f"%{search_value}%"),
            Person.disability.ilike(f"%{search_value}%"),
            Person.pendidikan.ilike(f"%{search_value}%"),
        )
    )
        

    query, total_records = filterByRole(query.join(Person.family), current_user.role)
    


    # Sorting logic
    sort_column = getattr(Person, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'nama': r.name,
            'tanggal lahir': datetime.strftime(r.dob, '%Y-%m-%d') if r.dob else None,
            'gender': r.gender,
            'disability': r.disability,
            'pendidikan': r.pendidikan
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })
    
@api_bp.route('/api/kelompok-usia-subur')
def get_kelompok_usia_subur():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')
    
    # Get reference date (def set to today)
    reference_date = request.args.get('reference_date', datetime.today().strftime('%Y-%m-%d'))
    try:
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d')
    except ValueError:
        print("value error")
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Base query
    query = Person.query\
                .filter(func.date_part('year', func.age(reference_date, Person.dob)).between(15, 49),
                        Person.gender == 'Perempuan')

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Person.name.ilike(f"%{search_value}%"),
            Person.dob.ilike(f"%{search_value}%"),
            Person.gender.ilike(f"%{search_value}%"),
            Person.disability.ilike(f"%{search_value}%"),
            Person.pendidikan.ilike(f"%{search_value}%"),
        )
    )
        

    query, total_records = filterByRole(query.join(Person.family), current_user.role)
    


    # Sorting logic
    sort_column = getattr(Person, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'nama': r.name,
            'tanggal lahir': datetime.strftime(r.dob, '%Y-%m-%d') if r.dob else None,
            'gender': r.gender,
            'disability': r.disability,
            'pendidikan': r.pendidikan
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })
    
@api_bp.route('/api/kelompok-usia-lansia')
def get_kelompok_usia_lansia():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')
    
    # Get reference date (def set to today)
    reference_date = request.args.get('reference_date', datetime.today().strftime('%Y-%m-%d'))
    try:
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d')
    except ValueError:
        print("value error")
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Base query
    query = Person.query\
                .filter(func.date_part('year', func.age(reference_date, Person.dob)) >= 60)

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Person.name.ilike(f"%{search_value}%"),
            Person.dob.ilike(f"%{search_value}%"),
            Person.gender.ilike(f"%{search_value}%"),
            Person.disability.ilike(f"%{search_value}%"),
            Person.pendidikan.ilike(f"%{search_value}%"),
        )
    )
        

    query, total_records = filterByRole(query.join(Person.family), current_user.role)
    


    # Sorting logic
    sort_column = getattr(Person, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'nama': r.name,
            'tanggal lahir': datetime.strftime(r.dob, '%Y-%m-%d') if r.dob else None,
            'gender': r.gender,
            'disability': r.disability,
            'pendidikan': r.pendidikan
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })
    
@api_bp.route('/api/kelompok-kb')
def get_kelompok_kb():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')

    # Base query
    query = Family.query

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Family.kk.ilike(f"%{search_value}%"),
            Person.name.ilike(f"%{search_value}%"),
            Family.rt.ilike(f"%{search_value}%"),
            Family.rw.ilike(f"%{search_value}%"),
        )
    )
    
    if current_user.role != 'admin' and current_user.role != 'superadmin':
        query = query.filter(Family.rw == current_user.role)

    Kb_tradisional = query.filter(Family.kb=='KB tradisional').count()
    Kondom = query.filter(Family.kb=='Kondom').count()
    Pil = query.filter(Family.kb=='Pil').count()
    Suntik = query.filter(Family.kb=='Suntik').count()
    Implan = query.filter(Family.kb=='Implan').count()
    Iud = query.filter(Family.kb=='Iud').count()
    Mow = query.filter(Family.kb=='Mow').count()
    Mop = query.filter(Family.kb=='Mop').count()

    total_records = [0, Kb_tradisional, Kondom, Pil, Suntik, Implan, Iud, Mow, Mop]


    # Sorting logic
    sort_column = getattr(Family, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'kk': r.kk,
            'head': next((m.name for m in r.members if m.status == "Kepala Keluarga"), "Not found"),
            'rt': r.rt,
            'rw': r.rw,
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })

@api_bp.route('/api/keluarga-disabilitas')
def get_keluarga_disabilitas():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')

    # Base query
    query = Family.query.filter_by(disability=True)

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Family.kk.ilike(f"%{search_value}%"),
            Person.name.ilike(f"%{search_value}%"),
            Family.rt.ilike(f"%{search_value}%"),
            Family.rw.ilike(f"%{search_value}%"),
        )
    )
        

    query, total_records = filterByRole(query, current_user.role)
    


    # Sorting logic
    sort_column = getattr(Family, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'kk': r.kk,
            'head': next((m.name for m in r.members if m.status == "Kepala Keluarga"), "Not found"),
            'rt': r.rt,
            'rw': r.rw,
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })
    
@api_bp.route('/api/keluarga-putus-sekolah')
def get_keluarga_putus_sekolah():
    draw = int(request.args.get('draw', 1))
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 10))
    search_value = request.args.get('search[value]', '')

    # Get sorting info
    order_column_index = request.args.get('order[0][column]')
    order_direction = request.args.get('order[0][dir]', 'asc')
    column_name = request.args.get(f'columns[{order_column_index}][data]', 'kk')

    # Base query
    query = Family.query.filter_by(putus_sekolah=True)

    # Search logic
    if search_value:
        query = query.filter(
        or_(
            Family.kk.ilike(f"%{search_value}%"),
            Person.name.ilike(f"%{search_value}%"),
            Family.rt.ilike(f"%{search_value}%"),
            Family.rw.ilike(f"%{search_value}%"),
        )
    )
        

    query, total_records = filterByRole(query, current_user.role)
    


    # Sorting logic
    sort_column = getattr(Family, column_name, None)
    if sort_column is not None:
        sort_method = asc if order_direction == 'asc' else desc
        query = query.order_by(sort_method(sort_column))

    records = query.offset(start).limit(length).all()

    data = [
        {
            'kk': r.kk,
            'head': next((m.name for m in r.members if m.status == "Kepala Keluarga"), "Not found"),
            'rt': r.rt,
            'rw': r.rw,
        }
        for r in records
    ]

    records_count = query.count()
    print(total_records)
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': records_count,
        'data': data
    })
    
