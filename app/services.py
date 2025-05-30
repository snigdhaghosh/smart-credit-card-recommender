import json
from .models import Card, UserOwnedCard, PurchaseCategory

def get_card_recommendation(purchase_category_name, user_id=None):
    """
    Recommends the best card for a given purchase category.
    Phase 1: Simple rule-based logic.
    """
    # Find the purchase category object
    category = PurchaseCategory.query.filter_by(name=purchase_category_name).first()
    if not category:
        return {"error": "Purchase category not found."}, None

    best_card = None
    max_reward_rate = -1.0
    recommendation_reason = ""

    # Get all cards
    all_cards = Card.query.all()
    eligible_cards = []

    for card in all_cards:
        try:
            rules = json.loads(card.reward_rules) if card.reward_rules else {}
        except json.JSONDecodeError:
            rules = {} # Skip card or log error if rules are malformed

        # Check generic category match (e.g. "dining" in rules)
        # More sophisticated matching can be added later (e.g., if category.name is a sub-category)
        reward_rate = rules.get(purchase_category_name.lower(), 0.0) # Default to 0% if category not in rules

        # Consider annual fee by calculating an 'effective reward'
        # This is a placeholder; real calculation is more complex (needs estimated spend)
        # For now, let's just prioritize higher raw reward rate
        effective_reward = reward_rate # - (card.annual_fee / (12 * some_assumed_monthly_spend_in_category_or_total))

        if effective_reward > max_reward_rate:
            max_reward_rate = effective_reward
            best_card = card
            recommendation_reason = f"Offers {reward_rate*100:.0f}% back on {purchase_category_name}."
        
        if reward_rate > 0: # Only consider cards that offer some reward for the category
             eligible_cards.append({
                "name": card.name,
                "issuer": card.issuer,
                "reward_rate": reward_rate,
                "annual_fee": card.annual_fee,
                "benefits": card.benefits_summary,
                "img_url": card.img_url
            })


    # If user_id is provided, check if they own any of the top cards
    # For now, this just returns the single best card found based on raw reward rate
    if user_id:
        owned_cards = UserOwnedCard.query.filter_by(user_id=user_id).all()
        owned_card_ids = [oc.card_id for oc in owned_cards]
        if best_card and best_card.id in owned_card_ids:
            recommendation_reason += " (You own this card!)"
        # Further logic: is an owned card "good enough"? or suggest a better non-owned card?

    if not best_card:
        return {"message": f"No specific card found with high rewards for {purchase_category_name}. Consider a general rewards card."}, []
    
    # Sort eligible_cards by reward_rate descending
    eligible_cards.sort(key=lambda x: x['reward_rate'], reverse=True)

    return {
        "best_card_name": best_card.name,
        "issuer": best_card.issuer,
        "annual_fee": best_card.annual_fee,
        "reward_details": recommendation_reason,
        "benefits": best_card.benefits_summary,
        "img_url": best_card.img_url
    }, eligible_cards # Return the single best and a list of other eligible cards

# --- Placeholder for AI services ---
def get_llm_assisted_info(card_name):
    """
    Placeholder for Phase 2: Use an LLM to get/parse info about a card.
    This would involve API calls to an LLM service.
    """
    # 1. Construct a prompt for the LLM
    # 2. Call the LLM API
    # 3. Parse and validate the LLM's response
    # 4. Return structured data or insights
    return {"message": f"AI info for {card_name} not yet implemented."}