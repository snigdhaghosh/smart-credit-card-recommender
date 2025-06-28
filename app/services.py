import json
from flask import current_app
from .models import Card, UserOwnedCard, PurchaseCategory

def get_card_recommendation(purchase_category_name, user_id=None):
    """
    Recommends the best card for a given purchase category.
    Phase 1: Simple rule-based logic.
    """
    category_obj = PurchaseCategory.query.filter_by(name=purchase_category_name).first()
    if not category_obj:
        current_app.logger.warn(f"Purchase category '{purchase_category_name}' not found in database.")
        return {"error": f"Purchase category '{purchase_category_name}' not found."}, []


    owned_card_ids_set = set()
    best_owned_card_reward_rate = 0.0
    if user_id:
        owned_cards_for_user = UserOwnedCard.query.filter_by(user_id=user_id).all()
        owned_card_ids_set = {uoc.card_id for uoc in owned_cards_for_user}
        
        # Determine the user's best rate from their own cards for this category
        for uoc in owned_cards_for_user:
            card = uoc.card
            if card and card.reward_rules:
                try:
                    rules = json.loads(card.reward_rules)
                    specific_rate = 0.0
                    for key, val in rules.items():
                        if key.lower() == purchase_category_name.lower():
                            specific_rate = val
                            break
                    general_rate = rules.get("All", 0.0)
                    user_card_rate = max(specific_rate, general_rate)
                    if user_card_rate > best_owned_card_reward_rate:
                        best_owned_card_reward_rate = user_card_rate
                except (json.JSONDecodeError, AttributeError):
                    continue # Skip malformed or missing data



    best_card_details_dict = None
    highest_effective_reward_score = -1.0  # Allows any positive reward to be initially better

    eligible_cards_list = []
    all_cards_from_db = Card.query.all()

    if not all_cards_from_db:
        current_app.logger.info("No cards found in the database.")
        return {"message": "No cards available in the system yet."}, []
    
    owned_card_ids_set = set()
    if user_id:
        owned_cards_for_user = UserOwnedCard.query.filter_by(user_id=user_id).all()
        owned_card_ids_set = {uoc.card_id for uoc in owned_cards_for_user}
    

    for card_from_db in all_cards_from_db:
        try:
            rules = json.loads(card_from_db.reward_rules) if card_from_db.reward_rules else {}
        except json.JSONDecodeError:
            current_app.logger.error(f"Malformed reward_rules JSON for card: {card_from_db.name} (ID: {card_from_db.id})")
            rules = {} # Treat as no specific rules

        specific_reward_rate = 0.0
        # Normalize input purchase category name to lowercase once
        normalized_input_category_name = purchase_category_name.lower()
        
        for rule_key, rate_value in rules.items():
            if rule_key.lower() == normalized_input_category_name:
                specific_reward_rate = rate_value
                break 
        
        # Get a general or 'all purchases' rate if specific is not found or is lower
        # general_reward_rate = rules.get("all_purchases", 0.0) # Assuming "all_purchases" key in your JSON
        general_reward_rate = rules.get("All", 0.0) # Use "All" as per your data


        # The actual reward rate for this card for this category
        # For simplicity, if a specific category reward exists, use it, else use general.
        # A more complex logic could take the max, or layer them.
        if specific_reward_rate > 0:
            actual_reward_rate_for_category = specific_reward_rate
        else:
            actual_reward_rate_for_category = general_reward_rate
        
        if actual_reward_rate_for_category <= 0: # Card doesn't offer meaningful rewards for this category
            continue

        # Simple scoring for "effectiveness" - can be greatly improved later.
        # Higher reward is better. Lower annual fee is better for tie-breaking.
        # Current score is just the reward rate.
        current_card_score = actual_reward_rate_for_category
        is_owned = card_from_db.id in owned_card_ids_set # Check if owned


        comparison_note = None
        if user_id and not is_owned and actual_reward_rate_for_category > best_owned_card_reward_rate:
            if best_owned_card_reward_rate > 0:
                comparison_note = f"This is better than the {best_owned_card_reward_rate*100:.0f}% you currently get from your best owned card for this category."
            else:
                comparison_note = "This card would fill a gap in your portfolio for this spending category."


        # Prepare card information for the eligible list
        card_info_for_list = {
            "id": card_from_db.id,
            "name": card_from_db.name,
            "issuer": card_from_db.issuer,
            "reward_rate_for_category": actual_reward_rate_for_category, # The rate for the queried category
            "reward_rules_summary_text": f"Offers {actual_reward_rate_for_category*100:.0f}% for {purchase_category_name}. Full rules: {rules}", # Example summary
            "full_reward_rules": rules, # Pass all rules for detailed display if needed
            "annual_fee": card_from_db.annual_fee,
            "benefits": card_from_db.benefits_summary,
            "img_url": card_from_db.img_url,
            "is_owned": is_owned, # Add the owned flag
            "comparison_note": comparison_note # Add the note to the dictionary
        }
        eligible_cards_list.append(card_info_for_list)

        # Determine the "best" card based on score and then annual fee as a tie-breaker
        if current_card_score > highest_effective_reward_score:
            highest_effective_reward_score = current_card_score
            best_card_details_dict = card_info_for_list
        elif current_card_score == highest_effective_reward_score:
            # Tie-breaking: 1. Owned card, 2. Lower annual fee
            is_current_best_owned = best_card_details_dict.get('is_owned', False) if best_card_details_dict else False
            if is_owned and not is_current_best_owned: # Prefer owned card in a tie
                best_card_details_dict = card_info_for_list
            elif (is_owned == is_current_best_owned) and \
                (best_card_details_dict and card_from_db.annual_fee < best_card_details_dict.get('annual_fee', float('inf'))):
                best_card_details_dict = card_info_for_list # Then prefer lower annual fee

        # current_app.logger.info(f"card: {card_from_db.name}")  # Debugging output

    if not eligible_cards_list: # No cards offered any rewards for this category
        return {"message": f"No cards found offering specific rewards for '{purchase_category_name}'. Consider a general rewards card."}, []
    
    # Sort all eligible cards: Owned cards with high rewards first, then by reward rate, then by annual fee
    eligible_cards_list.sort(key=lambda x: (x['is_owned'], x['reward_rate_for_category'], -x['annual_fee']), reverse=True)
    
    # The best card is now the first one in the sorted list if any are eligible
    if eligible_cards_list and not best_card_details_dict: # Fallback if tie-breaking logic didn't set one
        best_card_details_dict = eligible_cards_list[0]
    elif not eligible_cards_list and best_card_details_dict: # This case should not happen if logic is correct
        pass # best_card_details_dict is already set

    # Later: if user_id is provided, you can check if best_card_details_dict or others are owned
    # For example, add a key: best_card_details_dict['is_owned_by_user'] = True/False

    return best_card_details_dict, eligible_cards_list




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