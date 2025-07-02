from .models import Card, UserCard
from flask_login import current_user

def _calculate_score_for_category(card, category_name):
    """
    Calculates a score for a card based on its rewards for a specific category and its annual fee.
    A higher score is better.
    """
    reward_rate = 0
    # Check if the card has reward rules and if the selected category is in those rules
    if card.reward_rules and category_name in card.reward_rules:
        reward_rate = card.reward_rules[category_name]
    # If not, check for a general "All" or "All other purchases" category
    elif card.reward_rules and 'All' in card.reward_rules:
        reward_rate = card.reward_rules['All']
    elif card.reward_rules and 'All other purchases' in card.reward_rules:
        reward_rate = card.reward_rules['All other purchases']

    # A simple scoring algorithm: the reward rate is the main driver,
    # with a small penalty for the annual fee. You can adjust this formula as needed.
    score = (reward_rate * 100) - (card.annual_fee / 10)
    return score

def get_recommendations(category_name, user_id=None):
    """
    Recommends the best credit card for a given category based on a calculated score.
    """
    all_cards = Card.query.all()

    # Get the list of card IDs owned by the current user, if they are logged in
    owned_card_ids = []
    if user_id:
        owned_card_ids = [uc.card_id for uc in UserCard.query.filter_by(user_id=user_id).all()]

    recommendations = []
    for card in all_cards:
        # We only want to recommend cards that offer some reward for the selected category
        if card.reward_rules and (category_name in card.reward_rules or 'All' in card.reward_rules or 'All other purchases' in card.reward_rules):
            score = _calculate_score_for_category(card, category_name)
            
            reward_rate_for_category = 0
            if card.reward_rules and category_name in card.reward_rules:
                reward_rate_for_category = card.reward_rules[category_name]
            elif card.reward_rules and 'All' in card.reward_rules:
                 reward_rate_for_category = card.reward_rules['All']
            elif card.reward_rules and 'All other purchases' in card.reward_rules:
                reward_rate_for_category = card.reward_rules['All other purchases']

            recommendations.append({
                'id': card.id,
                'name': card.name,
                'annual_fee': card.annual_fee,
                'img_url': card.img_url,
                'benefits': card.benefits_summary,
                'reward_rate_for_category': reward_rate_for_category,
                'score': score,
                'is_owned': card.id in owned_card_ids,
            })

    # Sort by the highest score
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    if not recommendations:
        return {"best_option": None, "other_options": []}

    best_option = recommendations[0]
    other_options = recommendations[1:]

    return {
        "best_option": best_option,
        "other_options": other_options
    }
