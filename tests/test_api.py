from app import create_app, db
import json


def test_draw_api():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
    client = app.test_client()

    resp = client.post('/api/pool/standard/draw', json={'n': 5})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'results' in data
    assert isinstance(data['results'], list)
    assert len(data['results']) == 5
    for r in data['results']:
        assert 'id' in r and 'rarity' in r
