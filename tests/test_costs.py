from app import create_app, db
from app.models import User


def test_cost_deduction():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'PULL_COST': 10})
    with app.app_context():
        db.create_all()
    client = app.test_client()
    client.post('/api/register', json={'username': 'carol', 'password': 'pwd'})
    client.post('/api/login', json={'username': 'carol', 'password': 'pwd'})

    # initial currency default 1000
    r = client.post('/api/pool/standard/draw', json={'n': 3})
    assert r.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username='carol').first()
        assert user.currency == 1000 - 3 * 10


def test_insufficient_funds():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'PULL_COST': 500})
    with app.app_context():
        db.create_all()
    client = app.test_client()
    client.post('/api/register', json={'username': 'dave', 'password': 'pwd'})
    client.post('/api/login', json={'username': 'dave', 'password': 'pwd'})

    # user has 1000 currency by default; attempt 3 pulls at cost 500 should fail
    r = client.post('/api/pool/standard/draw', json={'n': 3})
    assert r.status_code == 402
    data = r.get_json()
    assert data.get('error') == 'insufficient_funds'

