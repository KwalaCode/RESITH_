from app import create_app, db
from app.models import User

def init_db():
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(email='sy.admin@admin.com').first()
        if not admin:
            admin = User(email='sy.admin@admin.com', is_admin=True)
            admin.set_password('kwalaistheshit16*')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    init_db()

