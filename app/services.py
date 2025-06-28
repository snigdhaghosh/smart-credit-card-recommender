import json
from flask import current_app
from .models import Card, UserOwnedCard, PurchaseCategory

def _get_reward_rate_for_category(rules, category_name):
    """Helper function to calculate the reward rate for a specific category from a set of rules."""
    try:
        parsed_rules = json.loads(rules) if rules else {}
        # Normalize for case-insensitive matching
        normalized_category = category_name.lower()
        
        for key, value in parsed_rules.items():
            if key.lower() == normalized_category:
                return value
        
        # Return the general 'All' rate if no specific category is found
        return parsed_rules.get("All", 0.0)
    except (json.JSONDecodeError, AttributeError):
        current_app.logger.error(f"Error parsing reward rules: {rules}")
        return 0.0

def get_card_recommendation(purchase_category_name, user_id=None):
    """
    Recommends the best card for a given purchase category with improved efficiency and clarity.
    """
    category_obj = PurchaseCategory.query.filter_by(name=purchase_category_name).first()
    if not category_obj:
        current_app.logger.warn(f"Purchase category '{purchase_category_name}' not found.")
        return {"error": f"Purchase category '{purchase_category_name}' not found."}, [], None

    # Step 1: Get all necessary data in one go
    all_cards = Card.query.all()
    owned_card_ids = set()
    if user_id:
        owned_card_ids = {uoc.card_id for uoc in UserOwnedCard.query.filter_by(user_id=user_id).all()}

    if not all_cards:
        return {"message": "No cards available in the system yet."}, [], None

    # Step 2: Process all cards in a single loop
    eligible_cards = []
    best_owned_card_rate = 0.0

    for card in all_cards:
        rate = _get_reward_rate_for_category(card.reward_rules, purchase_category_name)
        if rate <= 0:
            continue

        is_owned = card.id in owned_card_ids
        if is_owned and rate > best_owned_card_rate:
            best_owned_card_rate = rate

        card_info = {
            "id": card.id,
            "name": card.name,
            "issuer": card.issuer,
            "reward_rate_for_category": rate,
            "annual_fee": card.annual_fee,
            "benefits": card.benefits_summary,
            "img_url": card.img_url,
            "is_owned": is_owned,
            "reward_rules_summary_text": f"Offers {rate*100:.0f}% for {purchase_category_name}.",
            "comparison_note": None # To be filled in later
        }
        eligible_cards.append(card_info)

    if not eligible_cards:
        return {"message": f"No cards found offering rewards for '{purchase_category_name}'."}, [], None

    # Step 3: Post-processing and final selection
    # Add comparison notes now that we have the best_owned_card_rate
    for card in eligible_cards:
        if user_id and not card['is_owned'] and card['reward_rate_for_category'] > best_owned_card_rate:
            if best_owned_card_rate > 0:
                card['comparison_note'] = f"This is better than the {best_owned_card_rate*100:.0f}% you get from your best card."
            else:
                card['comparison_note'] = "This could fill a gap in your wallet for this category."

    # Sort to find the best card and for display order
    # Prioritize: Higher reward rate -> Owned -> Lower annual fee
    eligible_cards.sort(key=lambda x: (x['reward_rate_for_category'], x['is_owned'], -x['annual_fee']), reverse=True)
    
    best_card = eligible_cards[0] if eligible_cards else None
    
    # Find the user's best owned card from the eligible list
    best_owned_card = next((card for card in eligible_cards if card['is_owned']), None)

    return best_card, eligible_cards, best_owned_card