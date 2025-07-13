from app import app

from flask import render_template, request, flash, redirect, url_for, session
from sqlalchemy import func ,or_, and_
from controllers.models import *
from datetime import datetime
import math
from zoneinfo import ZoneInfo


@app.route('/')
def home():
    is_logged = 'roles' in session
    if(is_logged):
        if('admin' in session['roles']):
            return redirect(url_for('admin_home'))
        
        elif('user' in session['roles']):
            return redirect(url_for('user_home'))
        
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('login'))
        
        if user.password != password:
            flash('Incorrect password.', 'error')
            return redirect(url_for('login'))
        
        session['email'] = user.email
        session['roles'] = [role.name for role in user.roles]
        session['user_id'] = user.id

        flash('Login successful!', 'success')
        return redirect(url_for('home'))
    
@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('roles', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/register', methods=['POST','GET'])
def register():
    if(request.method=='POST'):
        email=request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')

        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('register'))
        
        user_ = User.query.filter_by(email=email).first()

        if user_:
            flash('Email already extist', 'error')
            return redirect(url_for('register'))

        role_data = Role.query.filter_by(name='user').first()
        
        user_data = User(email=email, password=password, roles = [role_data], full_name=full_name, address=address, pin_code=pin_code)

        db.session.add(user_data)
        db.session.commit()
    
        return render_template('login.html')
    return render_template('register.html')

@app.route('/admin_user')
def admin_user():
    if 'email' not in session or 'admin' not in session.get('roles'):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))

    users = User.query.all()
    return render_template('admin_user.html', users=users)


@app.route('/add_new_parking', methods=['GET','POST'])
def add_new_parking():
    if request.method == 'POST':
        prime_location_name = request.form.get("location")
        price = request.form.get("price")
        address = request.form.get("address")
        pin_code = request.form.get("pin_code")
        maximum_number_of_spots = request.form.get("max_spots")

        new_parking_lot = ParkingLot(
            location=prime_location_name,
            address=address,
            pin_code=pin_code,
            price=price,
            max_spots=maximum_number_of_spots
        )
        
        db.session.add(new_parking_lot)
        flash('New parking lot added successfully!', 'success')
        db.session.commit()
        max_spot = int(maximum_number_of_spots)
        for i in range(max_spot):
            spot_lot = ParkingSpot(spot=f'{new_parking_lot.id}_{i+1}',
                                   lot_id = new_parking_lot.id,
                                   status = 'A'
            )
            db.session.add(spot_lot)
        db.session.commit()
        flash('Succesfully Parking added')

        
        return redirect('/')    

    return render_template('add_new_parking.html')

@app.route('/edit_parking/<int:parking_lot_id>', methods=['GET', 'POST'])
def edit_parking(parking_lot_id):
    parking_lot = ParkingLot.query.get_or_404(parking_lot_id)

    if request.method == 'POST':
        parking_lot.location = request.form.get('location')
        parking_lot.address = request.form.get('address')
        parking_lot.pin_code = request.form.get('pin_code')
        parking_lot.price = request.form.get('price')

        current_spots = ParkingSpot.query.filter_by(lot_id=parking_lot.id).all()
        
        spot_count = request.form.get('max_spots')
        if int(spot_count) > len(current_spots):
            # Add new spots if the new max_spots is greater than the current max_spots
            for i in range(len(current_spots), int(spot_count)):
                new_spot = ParkingSpot(spot=f'{parking_lot.id}_{i+1}', lot_id=parking_lot.id, status='A')
                db.session.add(new_spot)
                db.session.commit()
            parking_lot.max_spots = int(spot_count)
        elif int(spot_count) < len(current_spots):
            # Remove excess spots if the new max_spots is less than the current max_spots
            flash('Warning: Reducing the number of spots will delete existing spots.', 'warning')
            
        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect('/')

    return render_template('edit_parking.html', parking_lot=parking_lot)

@app.route('/delete_parking/<int:parking_lot_id>', methods=['GET'])
def delete_parking(parking_lot_id):
    parking_lot = ParkingLot.query.get_or_404(parking_lot_id)
    spot_ids = [spot.id for spot in parking_lot.spots]
    if spot_ids:
        reservations = Reservation.query.filter(Reservation.spot_id.in_(spot_ids)).all()
        for reservation in reservations:
            db.session.delete(reservation)
    db.session.delete(parking_lot)
    db.session.commit()
    
    flash('Parking lot deleted successfully!', 'success')
    return redirect('/')

@app.route('/admin_search', methods=['GET', 'POST'])
def admin_search():
    if request.method == 'POST':
        search_query = request.form.get('searchBy')   
        search_type  = request.form.get('search_By')  
        lot_bundles = []
        if not search_query:
            flash('Search query cannot be empty.', 'error')
            return redirect(url_for('admin_search'))

        if search_type == 'user_id':
            results = User.query.filter_by(id=search_query).all()

        elif search_type == 'location':
            results = ParkingLot.query.filter_by(location=search_query).all()
            lot_bundles = []
            for lot in results:
                available = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').all()
                occupied  = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').all()

            lot_bundles.append({
                "lot": lot,
                "available_spots": available,
                "occupied_spots": occupied,
            })
    
        elif search_type == 'pin_code':
            results = ParkingLot.query.filter_by(pin_code=search_query).all()
            lot_bundles = []
            for lot in results:
                available = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').all()
                occupied  = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').all()

            lot_bundles.append({
                "lot": lot,
                "available_spots": available,
                "occupied_spots": occupied,
            })
        else:
            results = []
        
        if not results:
            flash('No results found.', 'info')
            return redirect(url_for('admin_search'))

        return render_template('admin_search.html', results=results, search_type=search_type, search_query=search_query, lot_bundles=lot_bundles)

    return render_template('admin_search.html')

@app.route('/admin_home', methods=['GET', 'POST'])
def admin_home():
    parking_lots = ParkingLot.query.all()
    
    lot_bundles = []
    for lot in parking_lots:
        available = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').all()
        occupied  = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').all()

        lot_bundles.append({
            "lot": lot,
            "available_spots": available,
            "occupied_spots": occupied,
        })


    return render_template('/admin_home.html', parking_lots=parking_lots, lot_bundles=lot_bundles)

@app.route('/user_home', methods=['GET', 'POST'])
def user_home():
    reservations = Reservation.query.filter_by(user_id=session.get('user_id')).all()
    spot_list = [r.spot_id for r in reservations]
    if not spot_list:
        print('spot reservationssssss:', [r.spot_id for r in reservations])
        flash('No reservations found.', 'info')
        return render_template('/user_home.html', reservations=[])
    print('spot reservationsmmmm:', spot_list)
    return render_template('/user_home.html', reservations=reservations)

@app.route('/admin_view_spot/<string:spot_id>', methods=['GET', 'POST'])
def admin_view_spot(spot_id):
    parking_spot = ParkingSpot.query.filter_by(spot=spot_id).first()
    return render_template('/admin_view_spot.html', parking_spot=parking_spot)

@app.route('/user_search_parking', methods=['GET', 'POST'])
def user_search_parking():
    if request.method == 'POST':
        search_query = request.form.get('search_parking')   
        print('search query:', search_query)
        if not search_query:
            flash('Search query cannot be empty.', 'error')
            return redirect(url_for('user_search_parking'))

        results = ParkingLot.query.filter(or_(ParkingLot.location.ilike(f'%{search_query}%'),
                                              ParkingLot.pin_code.ilike(f'%{search_query}%'))).all()
        
        if not results:
            flash('No results found.', 'info')
            return redirect(url_for('user_search_parking'))

        lot_bundles = []
        for lot in results:
            available = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').all()
            occupied  = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').all()

            lot_bundles.append({
                "lot": lot,
                "available_spots": available,
                "occupied_spots": occupied,
            })

        print('results found')
        return render_template('user_search_parking.html', results=results, lot_bundles=lot_bundles)
    print('results')
    return render_template('user_search_parking.html')

@app.route('/book_parking/<int:parking_lot_id>', methods=['GET', 'POST'])
def book_parking(parking_lot_id):
    parking_lot = ParkingLot.query.get_or_404(parking_lot_id)
    spot = ParkingSpot.query.filter_by(lot_id=parking_lot.id, status='A').first()
    if not spot:
        flash('No available parking spots in this lot.', 'error')
        return redirect(url_for('user_search_parking'))

    if not parking_lot:
        flash('Parking lot not found.', 'error')
        return redirect(url_for('user_search_parking'))
    
    if request.method == 'POST':
        spot = request.form.get('spot')
        lot_id = request.form.get('lot_id')
        user_id = session.get('user_id')
        vehicle_number = request.form.get('vehicle_number')

        if not spot or not lot_id or not user_id or not vehicle_number:
            flash('All fields are required.', 'error')
            return redirect(url_for('book_parking', parking_lot_id=parking_lot_id, spot=spot))

        spot = ParkingSpot.query.filter_by(spot=spot, lot_id=lot_id, status='A').first()
        if not spot:
            flash('Parking spot is not available.', 'error')
            return redirect(url_for('book_parking', parking_lot_id=parking_lot_id))
        
        spot.status = 'O'

        reservation = Reservation(spot_id=spot.spot, user_id=user_id, parking_cost=float(parking_lot.price), vehicle_number=vehicle_number, parking_timestamp=datetime.now(ZoneInfo("Asia/Kolkata")))
        db.session.add(reservation)
        db.session.commit()
        flash('Parking spot booked successfully!', 'success')
        return redirect(url_for('user_home'))
    return render_template('book_parking.html', parking_lot=parking_lot, spot=spot)

@app.route('/release_parking/<int:reservation_id>', methods=['GET', 'POST'])
def release_parking(reservation_id):
    
    reservation = Reservation.query.get_or_404(reservation_id)
    parking_time = reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M')
    release_time = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M')
    fmt = "%Y-%m-%d %H:%M"
    start_dt = datetime.strptime(parking_time, fmt)
    end_dt   = datetime.strptime(release_time, fmt)

    delta = end_dt - start_dt
    hours = delta.total_seconds() / 3600
    hourly_cost = float(reservation.parking_cost)
    cost  = hours * hourly_cost
    cost = math.ceil(cost)

    if request.method=='POST':
        print('post')
        reservation.total_cost = cost
        reservation.leaving_timestamp = end_dt
        db.session.commit()
        spot = ParkingSpot.query.filter_by(spot=reservation.spot_id).first()
        if spot:
            spot.status = 'A'
            db.session.commit()
        flash('Parking released successfully!', 'success')
        return redirect(url_for('user_home'))

    return render_template('release_parking.html', reservation=reservation,reservation_id=reservation_id,t=release_time ,cost=cost)

@app.route('/admin_spot_view/<string:spot_id>', methods=['GET'])
def admin_spot_view(spot_id):
    spot = ParkingSpot.query.filter(and_(ParkingSpot.spot == spot_id), ParkingSpot.status== 'O').first()
    if not spot:
        flash('Parking spot not found or not occupied.', 'error')
        return redirect(url_for('admin_home'))
    print(spot_id, spot)

    reservation = Reservation.query.filter(and_(Reservation.spot_id == spot.spot, Reservation.leaving_timestamp == None)).first()

    parking_time = reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M')
    release_time = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M')
    fmt = "%Y-%m-%d %H:%M"
    start_dt = datetime.strptime(parking_time, fmt)
    end_dt   = datetime.strptime(release_time, fmt)

    delta = end_dt - start_dt                 
    hours = delta.total_seconds() / 3600      
    cost  = hours * 50
    cost = math.ceil(cost)
    

    return render_template('admin_spot_view.html', spot=spot, reservation=reservation, cost=cost)