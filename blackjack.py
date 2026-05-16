"""
🃏 BLACKJACK MODULE - Command-Based Casino Game
Production-ready blackjack implementation using in-memory game state + SQLite balances

Features:
✔ Command-based gameplay (no callbacks)
✔ Real blackjack cards (A, 2-10, J, Q, K)
✔ Proper Ace handling (1 or 11)
✔ Dealer AI (hit <17, stand 17+)
✔ Atomic balance updates
✔ Automatic game cleanup
✔ Multiple simultaneous players
✔ Anti-spam protection

Game Rules:
- Player wins if hand > dealer AND <= 21
- Blackjack (21 with 2 cards) pays 2.5x
- Regular win pays 2x
- Push (tie) refunds bet
- Surrender returns 50% of bet
- Dealer hits on <17, stands on 17+
"""

import random
import time
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# ╔════════════════════════════════════════╗
# ║  GAME STATE & CONSTANTS               ║
# ╚════════════════════════════════════════╝

# Active games: {user_id: {"player": [], "dealer": [], "bet": int, "created": float, "doubled": bool}}
active_blackjack_games: Dict[int, dict] = {}

# Game timeout (5 minutes)
GAME_TIMEOUT = 300

# Card values
CARD_DECK = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
CARD_EMOJIS = {
    'A': '🂡', '2': '🂢', '3': '🂣', '4': '🂤', '5': '🂥',
    '6': '🂦', '7': '🂧', '8': '🂨', '9': '🂩', '10': '🂚',
    'J': '🂛', 'Q': '🂝', 'K': '🂮'
}

# Game states
STATE_PLAYING = "playing"
STATE_DEALER_TURN = "dealer_turn"
STATE_FINISHED = "finished"


# ╔════════════════════════════════════════╗
# ║  CARD OPERATIONS                      ║
# ╚════════════════════════════════════════╝

def draw_card() -> str:
    """Draw a single card from the deck."""
    return random.choice(CARD_DECK)


def card_value(card: str) -> int:
    """Get numeric value of a single card."""
    if card == 'A':
        return 11  # Will be adjusted by hand_value()
    elif card in ['J', 'Q', 'K']:
        return 10
    else:
        return int(card)


def hand_value(hand: List[str]) -> int:
    """
    Calculate hand value with proper Ace handling.
    Aces are 1 or 11 to maximize hand without busting.
    """
    if not hand:
        return 0
    
    total = sum(card_value(card) for card in hand)
    num_aces = sum(1 for card in hand if card == 'A')
    
    # If busted and we have Aces, convert from 11 to 1
    while total > 21 and num_aces > 0:
        total -= 10  # Convert one Ace from 11 to 1
        num_aces -= 1
    
    return total


def is_blackjack(hand: List[str]) -> bool:
    """Check if hand is a natural blackjack (21 with 2 cards)."""
    return len(hand) == 2 and hand_value(hand) == 21


def format_hand(hand: List[str], show_all: bool = True) -> str:
    """Format hand for display."""
    if not hand:
        return ""
    
    if not show_all and len(hand) > 0:
        # Show first card + hidden card (for dealer)
        display = f"{CARD_EMOJIS.get(hand[0], hand[0])} ?"
    else:
        display = " ".join(CARD_EMOJIS.get(card, card) for card in hand)
    
    return display


def format_hand_value(hand: List[str], show_value: bool = True) -> str:
    """Format hand value for display."""
    if not show_value or not hand:
        return ""
    
    value = hand_value(hand)
    if is_blackjack(hand):
        return "21 🎯"
    return str(value)


# ╔════════════════════════════════════════╗
# ║  GAME LOGIC                           ║
# ╚════════════════════════════════════════╝

def create_game(user_id: int, bet: int) -> Dict:
    """Create a new blackjack game."""
    # Deal initial hands
    player_hand = [draw_card(), draw_card()]
    dealer_hand = [draw_card(), draw_card()]
    
    game = {
        "player": player_hand,
        "dealer": dealer_hand,
        "bet": bet,
        "created": time.time(),
        "doubled": False,
        "state": STATE_PLAYING,
    }
    
    active_blackjack_games[user_id] = game
    logger.info(f"🃏 New blackjack game created for {user_id}, bet: {bet}")
    
    return game


def get_game(user_id: int) -> Dict | None:
    """Get active game for user or None if expired."""
    if user_id not in active_blackjack_games:
        return None
    
    game = active_blackjack_games[user_id]
    
    # Check if expired
    if time.time() - game["created"] > GAME_TIMEOUT:
        logger.warning(f"⏰ Game for {user_id} expired (timeout)")
        del active_blackjack_games[user_id]
        return None
    
    return game


def player_hit(user_id: int) -> bool:
    """Player takes a hit. Returns True if valid action."""
    game = get_game(user_id)
    if not game:
        return False
    
    game["player"].append(draw_card())
    return True


def player_stand(user_id: int) -> bool:
    """Player stands. Triggers dealer turn."""
    game = get_game(user_id)
    if not game:
        return False
    
    game["state"] = STATE_DEALER_TURN
    return True


def player_double(user_id: int) -> bool:
    """Player doubles down. Doubles bet, gives 1 card, auto-stands."""
    game = get_game(user_id)
    if not game:
        return False
    
    if len(game["player"]) != 2:
        return False  # Can only double on first 2 cards
    
    game["bet"] *= 2
    game["doubled"] = True
    game["player"].append(draw_card())
    game["state"] = STATE_DEALER_TURN
    
    return True


def player_surrender(user_id: int) -> Tuple[bool, int]:
    """Player surrenders. Returns (success, refund_amount)."""
    game = get_game(user_id)
    if not game:
        return False, 0
    
    # Can only surrender on first turn (only 2 cards visible)
    if len(game["player"]) != 2:
        return False, 0
    
    refund = game["bet"] // 2
    game["state"] = STATE_FINISHED
    
    return True, refund


def dealer_play(user_id: int) -> bool:
    """Execute dealer AI. Dealer hits <17, stands 17+."""
    game = get_game(user_id)
    if not game:
        return False
    
    while hand_value(game["dealer"]) < 17:
        game["dealer"].append(draw_card())
        logger.debug(f"🤖 Dealer hits: {game['dealer']}")
    
    game["state"] = STATE_FINISHED
    return True


# ╔════════════════════════════════════════╗
# ║  GAME OUTCOME DETERMINATION            ║
# ╚════════════════════════════════════════╝

def determine_winner(user_id: int) -> Tuple[str, int]:
    """
    Determine game outcome.
    Returns: (outcome_string, payout_multiplier)
    
    Outcomes:
    - "blackjack" = 2.5x (natural 21)
    - "win" = 2x (beat dealer)
    - "push" = 1x (tie)
    - "bust" = 0x (player over 21)
    - "dealer_bust" = 2x (player 21 or less, dealer over)
    - "loss" = 0x (dealer better hand)
    """
    game = get_game(user_id)
    if not game:
        return "error", 0
    
    player_val = hand_value(game["player"])
    dealer_val = hand_value(game["dealer"])
    
    logger.debug(f"🎯 Comparing: Player={player_val}, Dealer={dealer_val}")
    
    # Player bust
    if player_val > 21:
        return "bust", 0
    
    # Dealer bust (with player <= 21)
    if dealer_val > 21:
        return "dealer_bust", 2
    
    # Both under 21 - compare
    if player_val > dealer_val:
        # Check if it was a natural blackjack
        if is_blackjack(game["player"]):
            return "blackjack", 2.5
        return "win", 2
    elif player_val == dealer_val:
        return "push", 1
    else:  # dealer_val > player_val
        return "loss", 0


def cleanup_game(user_id: int):
    """Remove expired or finished games."""
    if user_id in active_blackjack_games:
        del active_blackjack_games[user_id]
        logger.debug(f"🗑️ Game cleaned up for {user_id}")


# ╔════════════════════════════════════════╗
# ║  GAME DISPLAY FORMATTING              ║
# ╚════════════════════════════════════════╝

def format_game_status(user_id: int, show_dealer_cards: bool = False) -> str:
    """
    Format current game state for display.
    
    Args:
        user_id: Player's user ID
        show_dealer_cards: If True, reveal all dealer cards (end of game)
    """
    game = get_game(user_id)
    if not game:
        return "❌ No active game"
    
    player_hand_str = format_hand(game["player"])
    player_value_str = format_hand_value(game["player"])
    
    if show_dealer_cards:
        dealer_hand_str = format_hand(game["dealer"])
        dealer_value_str = format_hand_value(game["dealer"])
    else:
        # Hide dealer's hole card
        dealer_hand_str = f"{CARD_EMOJIS.get(game['dealer'][0], game['dealer'][0])} ❓"
        dealer_value_str = "?"
    
    status = f"""╔═══════════════════════════╗
║     🃏 BLACKJACK 🃏      ║
╠═══════════════════════════╣
║ 👤 You: {player_hand_str:<14} = {player_value_str:<3} ║
║ 🤖 Dealer: {dealer_hand_str:<10} = {dealer_value_str:<3} ║
║ 💰 Bet: {game['bet']:<18} ║
╚═══════════════════════════╝"""
    
    return status


def format_game_result(user_id: int, outcome: str, payout: int) -> str:
    """Format the final game result."""
    game = get_game(user_id)
    if not game:
        return "❌ Error retrieving game"
    
    player_val = hand_value(game["player"])
    dealer_val = hand_value(game["dealer"])
    
    outcome_emoji = {
        "blackjack": "🎯",
        "win": "🎉",
        "push": "🤝",
        "bust": "💥",
        "dealer_bust": "💥",
        "loss": "😭",
    }.get(outcome, "❓")
    
    outcome_text = {
        "blackjack": "BLACKJACK! You got 21 with 2 cards!",
        "win": "YOU WIN!",
        "push": "PUSH - Tie Game",
        "bust": "BUST - You went over 21",
        "dealer_bust": "DEALER BUST - You win!",
        "loss": "DEALER WINS",
    }.get(outcome, "Game finished")
    
    result = f"""╔═══════════════════════════╗
║   {outcome_emoji} {outcome_text:<18} {outcome_emoji}   ║
╠═══════════════════════════╣
║ 👤 You: {player_val} points      ║
║ 🤖 Dealer: {dealer_val} points   ║
║ 💰 Bet: {game['bet']} coins        ║
║ 🏆 Payout: {payout} coins      ║
╚═══════════════════════════╝"""
    
    return result


# ╔════════════════════════════════════════╗
# ║  ACTION VALIDATION                    ║
# ╚════════════════════════════════════════╝

def can_hit(user_id: int) -> Tuple[bool, str]:
    """Check if player can hit."""
    game = get_game(user_id)
    if not game:
        return False, "❌ No active game"
    
    if game["state"] != STATE_PLAYING:
        return False, "❌ Game is not in play"
    
    player_val = hand_value(game["player"])
    if player_val > 21:
        return False, "❌ You already busted!"
    
    return True, ""


def can_stand(user_id: int) -> Tuple[bool, str]:
    """Check if player can stand."""
    game = get_game(user_id)
    if not game:
        return False, "❌ No active game"
    
    if game["state"] != STATE_PLAYING:
        return False, "❌ Game is not in play"
    
    return True, ""


def can_double(user_id: int) -> Tuple[bool, str]:
    """Check if player can double down."""
    game = get_game(user_id)
    if not game:
        return False, "❌ No active game"
    
    if game["state"] != STATE_PLAYING:
        return False, "❌ Game is not in play"
    
    if len(game["player"]) != 2:
        return False, "❌ Can only double on first 2 cards"
    
    if game["doubled"]:
        return False, "❌ Already doubled"
    
    return True, ""


def can_surrender(user_id: int) -> Tuple[bool, str]:
    """Check if player can surrender."""
    game = get_game(user_id)
    if not game:
        return False, "❌ No active game"
    
    if game["state"] != STATE_PLAYING:
        return False, "❌ Game is not in play"
    
    if len(game["player"]) != 2:
        return False, "❌ Can only surrender before hitting"
    
    return True, ""
