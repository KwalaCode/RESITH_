from urllib.parse import urlparse
from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from app import db
from app.models import User, Reservation
from datetime import datetime, timedelta

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
booking = Blueprint('booking', __name__)
admin = Blueprint('admin', __name__)

@main.route('/')
def index():
    today = datetime.now().date()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    reservations = Reservation.query.filter(
        Reservation.date >= today,
        Reservation.date < next_monday + timedelta(days=7),
        Reservation.status == 'confirmed'
    ).order_by(Reservation.date, Reservation.time_slot).all()
    return render_template('index.html', reservations=reservations)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            current_app.logger.info(f"Login attempt for user: {email}")
            if user.check_password(password):
                login_user(user)
                current_app.logger.info(f"User {email} logged in successfully")
                flash('Logged in successfully.')
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('main.index')
                return redirect(next_page)
            else:
                current_app.logger.warning(f"Invalid password for user: {email}")
        else:
            current_app.logger.warning(f"Login attempt with non-existent email: {email}")
        flash('Invalid email or password')
    return render_template('login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
        else:
            new_user = User(email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('main.index'))
    return render_template('signup.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@booking.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        time_slot = int(request.form.get('time_slot'))
        opponent_id = request.form.get('opponent_id')
        
        today = datetime.now().date()
        if date >= today:
            # Check user type and allowed days
            if current_user.is_team_player and date.weekday() <= 2:  # Monday to Wednesday
                existing_reservation = Reservation.query.filter_by(
                    user_id=current_user.id,
                    date=date
                ).first()
                if not existing_reservation:
                    new_reservation = Reservation(user_id=current_user.id, opponent_id=opponent_id, date=date, time_slot=time_slot)
                    db.session.add(new_reservation)
                    db.session.commit()
                    flash('Reservation submitted for approval')
                else:
                    flash('You already have a reservation this week')
            elif not current_user.is_team_player and date.weekday() >= 3:  # Thursday and Friday
                existing_reservation = Reservation.query.filter_by(
                    user_id=current_user.id,
                    date=date
                ).first()
                if not existing_reservation:
                    new_reservation = Reservation(user_id=current_user.id, opponent_id=opponent_id, date=date, time_slot=time_slot)
                    db.session.add(new_reservation)
                    db.session.commit()
                    flash('Reservation submitted for approval')
                else:
                    flash('You already have a reservation this week')
            else:
                if current_user.is_team_player:
                    flash('Team players can only book from Monday to Wednesday')
                else:
                    flash('Non-team players can only book on Thursday and Friday')
        else:
            flash('Bookings are only allowed for today and future dates')
    
    # Get available slots for the upcoming week, including today
    today = datetime.now().date()
    available_slots = {}
    for i in range(7):  # Show slots for the next 7 days
        date = today + timedelta(days=i)
        if date.weekday() == 4:  # Friday
            slots = list(range(8))  # 8 slots
        else:
            slots = list(range(10))  # 10 slots
        booked_slots = Reservation.query.filter_by(date=date, status='confirmed').with_entities(Reservation.time_slot).all()
        booked_slots = [slot[0] for slot in booked_slots]
        available_slots[date] = [slot for slot in slots if slot not in booked_slots]
    
    # Get potential opponents
    if current_user.is_team_player:
        potential_opponents = User.query.filter(User.is_team_player == True, User.id != current_user.id).all()
    else:
        potential_opponents = User.query.filter(User.is_team_player == False, User.id != current_user.id).all()
    
    return render_template('booking.html', available_slots=available_slots, potential_opponents=potential_opponents)

@admin.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('main.index'))
    
    pending_reservations = Reservation.query.filter_by(status='pending').all()
    users = User.query.all()
    return render_template('admin.html', pending_reservations=pending_reservations, users=users)

@admin.route('/approve/<int:reservation_id>')
@login_required
def approve_reservation(reservation_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = 'confirmed'
    db.session.commit()
    flash('Reservation approved')
    return redirect(url_for('admin.admin_panel'))

@admin.route('/refuse/<int:reservation_id>')
@login_required
def refuse_reservation(reservation_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = 'refused'
    db.session.commit()
    flash('Reservation refused')
    return redirect(url_for('admin.admin_panel'))

@admin.route('/set_team_player/<int:user_id>')
@login_required
def set_team_player(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    user.is_team_player = not user.is_team_player
    db.session.commit()
    flash(f'User {user.email} team player status updated')
    return redirect(url_for('admin.admin_panel'))

@admin.route('/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@admin.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        is_team_player = request.form.get('is_team_player') == 'on'
        is_admin = request.form.get('is_admin') == 'on'
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
        else:
            new_user = User(email=email, is_team_player=is_team_player, is_admin=is_admin)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully')
            return redirect(url_for('admin.manage_users'))
    
    return render_template('admin_add_user.html')

@admin.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.email = request.form.get('email')
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
        user.is_team_player = request.form.get('is_team_player') == 'on'
        user.is_admin = request.form.get('is_admin') == 'on'
        db.session.commit()
        flash('User updated successfully')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin_edit_user.html', user=user)

@admin.route('/users/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully')
    return redirect(url_for('admin.manage_users'))

@admin.route('/bookings')
@login_required
def manage_bookings():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    bookings = Reservation.query.all()
    return render_template('admin_bookings.html', bookings=bookings)

@admin.route('/bookings/add', methods=['GET', 'POST'])
@login_required
def add_booking():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        time_slot = int(request.form.get('time_slot'))
        status = request.form.get('status')
        
        new_booking = Reservation(user_id=user_id, date=date, time_slot=time_slot, status=status)
        db.session.add(new_booking)
        db.session.commit()
        flash('Booking added successfully')
        return redirect(url_for('admin.manage_bookings'))
    
    users = User.query.all()
    return render_template('admin_add_booking.html', users=users)

@admin.route('/bookings/edit/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    booking = Reservation.query.get_or_404(booking_id)
    
    if request.method == 'POST':
        booking.user_id = request.form.get('user_id')
        booking.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        booking.time_slot = int(request.form.get('time_slot'))
        booking.status = request.form.get('status')
        db.session.commit()
        flash('Booking updated successfully')
        return redirect(url_for('admin.manage_bookings'))
    
    users = User.query.all()
    return render_template('admin_edit_booking.html', booking=booking, users=users)

@admin.route('/bookings/delete/<int:booking_id>')
@login_required
def delete_booking(booking_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    booking = Reservation.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash('Booking deleted successfully')
    return redirect(url_for('admin.manage_bookings'))

