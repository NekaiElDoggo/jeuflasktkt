from app import create_app, db
from app.models import Item, User
import json


def test_featured_guarantee_behavior():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        # create items: one featured 5-star and one non-featured 5-star
        it1 = Item(name='5★_Feat', rarity=5)
        it1_featured = Item(name='5★_Featured', rarity=5)
        # mark second as featured via metadata_json (we don't have is_featured in DB Item yet)
        # For this test, the engine uses its own in-memory pool (gacha_cli), so we'll rely on guarantee flag
        db.session.add_all([it1, it1_featured])
        db.session.commit()

    client = app.test_client()
    # register and login
    r = client.post('/api/register', json={'username': 'bob', 'password': 'pwd'})
    assert r.status_code == 200
    r = client.post('/api/login', json={'username': 'bob', 'password': 'pwd'})
    assert r.status_code == 200

    # Simulate setting user's pity_state to guarantee True for standard pool and high pity
    with app.app_context():
        user = User.query.filter_by(username='bob').first()
        state = {'standard': 90, 'standard_guarantee': True}
        user.pity_state = json.dumps(state)
        db.session.commit()

    # Now draw (should guarantee a 5-star and because guarantee True it should be featured)
    r = client.post('/api/pool/standard/draw', json={'n': 1})
    assert r.status_code == 200
    data = r.get_json()
    results = data['results']
    assert len(results) == 1
    res = results[0]
    # res should include 'featured' flag True for 5-star guaranteed
    assert res.get('featured', False) is True

