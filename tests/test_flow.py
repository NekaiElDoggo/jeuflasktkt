from app import create_app, db
from app.models import Item


def test_register_login_draw_flow():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        # seed items
        items = [
            Item(name='3★_Common_1', rarity=3),
            Item(name='3★_Common_2', rarity=3),
            Item(name='3★_Common_3', rarity=3),
            Item(name='4★_Rare_1', rarity=4),
            Item(name='4★_Rare_2', rarity=4),
            Item(name='5★_Legendary_1', rarity=5),
        ]
        for it in items:
            db.session.add(it)
        db.session.commit()

    client = app.test_client()
    # register
    r = client.post('/api/register', json={'username': 'alice', 'password': 'secret'})
    assert r.status_code == 200
    data = r.get_json()
    user_id = data['id']

    # login
    r = client.post('/api/login', json={'username': 'alice', 'password': 'secret'})
    assert r.status_code == 200

    # draw 5 pulls while logged in (client keeps session cookie)
    r = client.post('/api/pool/standard/draw', json={'n': 5})
    assert r.status_code == 200
    data = r.get_json()
    assert 'results' in data and len(data['results']) == 5

    # check inventory
    r = client.get('/api/inventory')
    assert r.status_code == 200
    inv = r.get_json()
    assert 'inventory' in inv
    # Some entries should exist (since we pulled 5)
    assert len(inv['inventory']) >= 1

