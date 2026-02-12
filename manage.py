from app import create_app, db

app = create_app()

if __name__ == '__main__':
    print('Use flask db commands via environment:')
    print('set FLASK_APP=manage.py; flask db init')

