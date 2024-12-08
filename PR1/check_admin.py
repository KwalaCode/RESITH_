from app import create_app, db
from app.models import User

def check_admin():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(email='sy.admin@admin.com').first()
        if admin:
            print(f"User found:")
            print(f"Email: {admin.email}")
            print(f"Is admin: {admin.is_admin}")
            print(f"Password check: {admin.check_password('kwalaistheshit16*')}")
        else:
            print("User not found")

if __name__ == '__main__':
    check_admin()

