from app import create_app, db
from app.models import User, Reservation

def reset_database():
    app = create_app()
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("All tables dropped.")

        # Create all tables
        db.create_all()
        print("All tables recreated.")

        # Create admin user
        admin = User(email='sy.admin@admin.com', is_admin=True)
        admin.set_password('kwalaistheshit16*')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")

        print("Database reset complete.")

if __name__ == '__main__':
    reset_database()

