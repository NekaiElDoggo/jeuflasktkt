from flask import Blueprint, render_template, current_app, jsonify, request
from flask_login import login_user, logout_user, current_user
from gacha_cli import _make_sample_pool, GachaEngine
from .gacha_service import GachaService
from . import db
from .models import User, Item, InventoryEntry, PullRecord
import json

bp = Blueprint('main', __name__)

# Create sample pool and service (in-memory)
_pool = _make_sample_pool()
_engine = GachaEngine(_pool)
_service = GachaService(_engine)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/pool/<tag>')
def pool_page(tag):
    # basic page that uses JS to call the draw API
    return render_template('pool.html', tag=tag)


@bp.route('/inventory')
def inventory_page():
    return render_template('inventory.html')


@bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'username exists'}), 400
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id, 'username': user.username})


@bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'invalid credentials'}), 401
    # login via flask-login
    login_user(user)
    return jsonify({'id': user.id, 'username': user.username})


@bp.route('/api/logout', methods=['POST'])
def api_logout():
    logout_user()
    return jsonify({'status': 'ok'})


@bp.route('/api/profile', methods=['GET'])
def api_profile():
    if not current_user or not getattr(current_user, 'is_authenticated', False):
        return jsonify({'error': 'not authenticated'}), 401
    return jsonify({'id': current_user.id, 'username': current_user.username, 'currency': current_user.currency})


@bp.route('/api/inventory', methods=['GET'])
def api_inventory():
    if not current_user or not getattr(current_user, 'is_authenticated', False):
        return jsonify({'error': 'not authenticated'}), 401
    entries = InventoryEntry.query.filter_by(user_id=current_user.id).all()
    out = []
    for e in entries:
        item = db.session.get(Item, e.item_id)
        out.append({'item_id': item.id, 'name': item.name, 'rarity': item.rarity, 'count': e.count})
    return jsonify({'inventory': out})


@bp.route('/api/pool/<tag>/draw', methods=['POST'])
def api_draw(tag):
    data = request.get_json() or {}
    n = int(data.get('n', 1))
    if n <= 0 or n > 100:
        return jsonify({'error': 'invalid n'}), 400
    start_pity = int(data.get('start_pity', 0))
    start_guarantee = False

    # if user logged in, get their stored pity state for this pool
    if current_user and getattr(current_user, 'is_authenticated', False):
        try:
            pity_state = json.loads(current_user.pity_state or '{}')
            start_pity = int(pity_state.get(tag, start_pity))
            start_guarantee = bool(pity_state.get(f"{tag}_guarantee", False))
        except Exception:
            start_pity = start_pity
            start_guarantee = False

    results, pity, guarantee = _service.draw_n(n, start_pity, start_guarantee)

    # cost handling: if user is logged in, compute cost and debit currency atomically
    if current_user and getattr(current_user, 'is_authenticated', False):
        total_cost = current_app.config.get('PULL_COST', 100) * n
        user = db.session.get(User, current_user.id)
        if user.currency < total_cost:
            return jsonify({'error': 'insufficient_funds'}), 402
        # debit and continue (we already have db.session active)
        user.currency -= total_cost
        # Note: persistence of PullRecord/inventory/pity is done below; commit there

    # If user logged in, persist PullRecord and inventory and update pity_state
    if current_user and getattr(current_user, 'is_authenticated', False):
        user = db.session.get(User, current_user.id)
        if user:
            pr = PullRecord(user_id=user.id, pool_tag=tag, num_pulls=n, results=json.dumps(results), cost=0)
            db.session.add(pr)
            db.session.flush()
            # update inventory counts
            for it in results:
                item_id = it['id']
                inv = InventoryEntry.query.filter_by(user_id=user.id, item_id=item_id).first()
                if inv:
                    inv.count += 1
                else:
                    inv = InventoryEntry(user_id=user.id, item_id=item_id, count=1)
                    db.session.add(inv)
            # update pity state
            try:
                pity_state = json.loads(user.pity_state or '{}')
            except Exception:
                pity_state = {}
            pity_state[tag] = pity
            pity_state[f"{tag}_guarantee"] = bool(guarantee)
            # persist currency change as part of same transaction
            db.session.add(user)
            user.pity_state = json.dumps(pity_state)
            db.session.commit()

    return jsonify({'results': results, 'pity': pity})


@bp.route('/admin/items', methods=['GET', 'POST', 'DELETE'])
def admin_items():
    # very simple protection: must be logged in as user 'admin'
    if not current_user or not getattr(current_user, 'is_authenticated', False) or not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'forbidden'}), 403

    if request.method == 'GET':
        items = Item.query.all()
        out = []
        for it in items:
            out.append({'id': it.id, 'name': it.name, 'rarity': it.rarity, 'is_featured': bool(it.is_featured)})
        return jsonify({'items': out})

    data = request.get_json() or {}
    if request.method == 'POST':
        name = data.get('name')
        rarity = int(data.get('rarity', 3))
        is_featured = bool(data.get('is_featured', False))
        it = Item(name=name, rarity=rarity, is_featured=is_featured)
        db.session.add(it)
        db.session.commit()
        return jsonify({'id': it.id, 'name': it.name})

    if request.method == 'DELETE':
        item_id = int(data.get('id'))
        it = Item.query.get(item_id)
        if not it:
            return jsonify({'error': 'not found'}), 404
        db.session.delete(it)
        db.session.commit()
        return jsonify({'status': 'deleted'})


@bp.route('/admin')
def admin_page():
    if not current_user or not getattr(current_user, 'is_authenticated', False) or not getattr(current_user, 'is_admin', False):
        return "Forbidden", 403
    return render_template('admin.html')

