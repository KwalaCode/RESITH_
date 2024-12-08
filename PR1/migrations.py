from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import User, Reservation

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        upgrade()
