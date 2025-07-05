from app import app

from flask import render_template, request, flash, redirect, url_for, session
from controllers.models import *

@app.route('/')
def home():
    return render_template('home.html')

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
        print(type(role_data))
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
        parking_lot.max_spots = request.form.get('max_spots')

        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect('/')

    return render_template('edit_parking.html', parking_lot=parking_lot)

@app.route('/delete_parking/<int:parking_lot_id>', methods=['POST'])
def delete_parking(parking_lot_id):
    parking_lot = ParkingLot.query.get_or_404(parking_lot_id)
    
    db.session.delete(parking_lot)
    db.session.commit()
    
    flash('Parking lot deleted successfully!', 'success')
    return redirect('/')

@app.route('/admin_search', methods=['GET', 'POST'])
def admin_search():
    if request.method == 'POST':
        search_query = request.form.get('searchBy')   
        search_type  = request.form.get('search_By')  
        if not search_query:
            flash('Search query cannot be empty.', 'error')
            return redirect(url_for('admin_search'))

        if search_type == 'user_id':
            results = User.query.filter_by(id=search_query).all()
            print([result.full_name for result in results])

        elif search_type == 'location':
            results = ParkingLot.query.filter_by(location=search_query).all()
            print([result.max_spots for result in results])
        else:
            results = []
        
        if not results:
            flash('No results found.', 'info')

        return render_template('admin_search.html', results=results)

    return render_template('admin_search.html')