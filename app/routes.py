from flask import Blueprint, jsonify
from .models import CreditCard

bp = Blueprint('routes', __name__)

@bp.route('/cards', methods=['GET'])
def get_cards():
    cards = CreditCard.query.all()
    return jsonify([c.to_dict() for c in cards])
