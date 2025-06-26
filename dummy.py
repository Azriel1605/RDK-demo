import random
from datetime import datetime, timedelta
from app import db, app  # Adjust the import to your actual project structure
from model import Person, Family  # Adjust the import to your actual project structure
from faker import Faker

with app.app_context():
    fake = Faker('en_US')

    # Configuration
    TOTAL_PERSONS = 11000
    MIN_FAMILY_SIZE = 3
    MAX_FAMILY_SIZE = 6

    def generate_nik():
        return ''.join(random.choices('0123456789', k=16))

    def generate_kk():
        return ''.join(random.choices('0123456789', k=16))

    # Step 1: Determine family groupings
    families = []
    remaining_people = TOTAL_PERSONS

    while remaining_people > 0:
        size = random.randint(MIN_FAMILY_SIZE, MAX_FAMILY_SIZE)
        if remaining_people - size < 0:
            size = remaining_people
        families.append(size)
        remaining_people -= size

    # Step 2: Generate data
    persons = []
    family_objects = []

    person_id_counter = 1

    for fam_index, family_size in enumerate(families):
        kk = generate_kk()

        # Step 1: Create Family first
        temp_family = Family(
            kk=kk,
            address=fake.address(),
            rt=str(random.randint(1, 12)).zfill(2),
            rw=str(random.randint(1, 12)).zfill(2),
            kb=random.choice(['KB Tradisional', 'Kondom', 'Pil', 'Suntik', 'Implan', 'IUD', 'MOW', 'MOP']),
            status_hamil=random.choice([True, False])
        )
        db.session.add(temp_family)
        db.session.flush()  # Ensures the family is added so Person can reference it

        # Step 2: Add persons to that family
        family_members = []
        
        disability, putus_sekolah = False, False

        for i in range(family_size):
            person = Person(
                name=fake.name(),
                nik=generate_nik(),
                dob=fake.date_between(start_date='-60y', end_date='-1y'),
                gender=random.choice(['Laki-laki', 'Perempuan']),
                disability=random.choice(['Tidak', 'Netra', 'Rungu', 'Wicara', 'Daksa', 'Intelektual', 'Psikososial', 'Ganda']),
                pendidikan=random.choice(['SD', 'SMP', 'SMA', 'S1', 'S2', 'Putus Sekolah']),
                menikah=random.choice(['Menikah', 'Belum Menikah']),
                pekerjaan=random.choice(['Belum bekerja', 'Buruh harian lepas', 'Pedagang', 'Wiraswasta', 'Pegawai swasta/honorer', 'PNS/BUMN', 'TNI/Polri', 'Pensiunan', 'Mengurus rumah tangga',]),
                family_id=kk  # safe now that family is inserted
            )
            
            if i == 0:
                person.status = 'Kepala Keluarga'
            if i == 1:
                person.status = 'Istri'
            
            if person.disability:
                disability = True
            if person.pendidikan == 'Tidak Sekolah':
                putus_sekolah = True

            db.session.add(person)
            family_members.append(person)

        db.session.flush()  # get Person IDs
        
        temp_family.disability = disability
        temp_family.putus_sekolah = putus_sekolah

    db.session.commit()

