"""Script d'initialisation pour créer la DB et ajouter des items sample et un admin."""
from app import create_app, db
from app.models import Item, User

app = create_app()

with app.app_context():
    db.create_all()
    # create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('admin')
        admin.currency = 100000
        admin.is_admin = True
        db.session.add(admin)
        db.session.commit()
        print('Created admin user (username=admin, password=admin)')

    # add sample items if none
    if Item.query.count() == 0:
        items = [
            Item(name='3★_Common_1', rarity=3),
            Item(name='3★_Common_2', rarity=3),
            Item(name='3★_Common_3', rarity=3),
            Item(name='4★_Rare_1', rarity=4),
            Item(name='4★_Rare_2', rarity=4),
            Item(name='5★_Legendary_1', rarity=5, is_featured=True),
        ]
        for it in items:
            db.session.add(it)
        db.session.commit()
        print('Seeded items')
    else:
        print('Items already present')

print('DB initialized')
