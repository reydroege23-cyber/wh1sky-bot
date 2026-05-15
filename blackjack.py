"""
🎴 BLACKJACK GAME MODULE
Professional blackjack game for virtual coins

Features:
- Full 52-card deck
- Hit, Stand, Double Down, Surrender options
- Interactive button controls
- Dealer AI (hits to 17)
- Anti-abuse protection
- Game tracking (wins, losses, streaks, blackjack count)
- Animated gameplay

⚠️ VIRTUAL COINS ONLY - Entertainment purposes ONLY
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import MIN_BET, MAX_BET, STARTING_BALANCE

logger = logging.getLogger(__name__)

# ==========================================
# BLACKJACK GAME ENGINE
# ==========================================

class BlackjackGame:
    """
    Professional blackjack game engine.
    Handles cards, deck, hand values, dealer logic, etc.
    """
    
    # Card values
    CARD_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
        '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 10, 'Q': 10, 'K': 10, 'A': 11
    }
    
    # Card suits and symbols
    SUITS = {'♠': '♠', '♥': '♥', '♦': '♦', '♣': '♣'}
    SUIT_SYMBOLS = {'spades': '♠', 'hearts': '♥', 'diamonds': '♦', 'clubs': '♣'}
    
    def __init__(self):
        """Initialize game engine."""
        self.deck = []
        self.player_hand = []
        self.dealer_hand = []
        self.shuffle_deck()
    
    def shuffle_deck(self):
        """Create and shuffle a standard 52-card deck."""
        suits = ['♠', '♥', '♦', '♣']
        values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        self.deck = [f"{value}{suit}" for suit in suits for value in values]
        random.shuffle(self.deck)
    
    def draw_card(self) -> str:
        """Draw a card from deck. Reshuffle if needed."""
        if len(self.deck) < 10:  # Reshuffle when deck is running low
            self.shuffle_deck()
        
        return self.deck.pop()
    
    def calculate_hand_value(self, hand: List[str]) -> Tuple[int, bool]:
        """
        Calculate best hand value considering aces.
        Optimized to avoid recalculation.
        Returns: (value, is_blackjack)
        """
        if not hand:
            return 0, False
        
        hand_len = len(hand)
        value = 0
        aces = 0
        
        # Count card values and aces - single pass
        for card in hand:
            card_value = card[:-1]  # Remove suit symbol
            
            if card_value == 'A':
                aces += 1
                value += 11
            else:
                # Use direct lookup
                value += self.CARD_VALUES.get(card_value, 10)
        
        # Adjust for aces if busting - optimized
        while value > 21 and aces:
            value -= 10  # Convert ace from 11 to 1
            aces -= 1
        
        # Check for blackjack (21 with 2 cards)
        is_blackjack = (hand_len == 2 and value == 21 and aces > 0)
        
        return value, is_blackjack
    
    def start_game(self) -> Tuple[int, int]:
        """
        Deal initial hands.
        Returns: (player_value, dealer_visible_value)
        """
        self.player_hand = [self.draw_card(), self.draw_card()]
        self.dealer_hand = [self.draw_card(), self.draw_card()]
        
        player_value, _ = self.calculate_hand_value(self.player_hand)
        # Only show first dealer card
        dealer_visible, _ = self.calculate_hand_value([self.dealer_hand[0]])
        
        return player_value, dealer_visible
    
    def hit(self, is_player: bool = True) -> Tuple[int, bool]:
        """
        Draw a card for player or dealer.
        Returns: (hand_value, is_bust)
        """
        if is_player:
            self.player_hand.append(self.draw_card())
            value, _ = self.calculate_hand_value(self.player_hand)
        else:
            self.dealer_hand.append(self.draw_card())
            value, _ = self.calculate_hand_value(self.dealer_hand)
        
        is_bust = value > 21
        return value, is_bust
    
    def double_down(self) -> Tuple[int, bool]:
        """Double bet and receive one more card."""
        self.player_hand.append(self.draw_card())
        value, _ = self.calculate_hand_value(self.player_hand)
        return value, value > 21
    
    def get_game_result(self, player_value: int, dealer_value: int, 
                       player_hand_size: int, dealer_hand_size: int) -> str:
        """
        Determine game result.
        Returns: 'WIN', 'LOSE', 'PUSH', 'BLACKJACK'
        """
        # Check for player blackjack (21 with 2 cards)
        player_blackjack = (player_hand_size == 2 and player_value == 21)
        dealer_blackjack = (dealer_hand_size == 2 and dealer_value == 21)
        
        # Player blackjack vs dealer blackjack = push
        if player_blackjack and dealer_blackjack:
            return 'PUSH'
        
        # Player blackjack = win with 2.5x multiplier
        if player_blackjack:
            return 'BLACKJACK'
        
        # Player bust = automatic loss
        if player_value > 21:
            return 'LOSE'
        
        # Dealer bust = player win
        if dealer_value > 21:
            return 'WIN'
        
        # Compare values
        if player_value > dealer_value:
            return 'WIN'
        elif player_value < dealer_value:
            return 'LOSE'
        else:
            return 'PUSH'
    
    def dealer_play(self) -> int:
        """Dealer must hit until 17+. Returns final dealer value."""
        while True:
            dealer_value, _ = self.calculate_hand_value(self.dealer_hand)
            
            if dealer_value >= 17:
                return dealer_value
            
            # Dealer hits
            self.hit(is_player=False)
    
    def format_card(self, card: str) -> str:
        """Format card for display (e.g., K♠)."""
        return card if len(card) <= 3 else f"{card[:-1]}{''.join(c for c in card[-1:] if c in self.SUIT_SYMBOLS.values())}"
    
    def format_hand(self, hand: List[str], hide_first: bool = False) -> str:
        """Format hand for display."""
        if hide_first and len(hand) > 0:
            # Show first card hidden, rest visible
            cards = ["❓"] + [self.format_card(card) for card in hand[1:]]
        else:
            cards = [self.format_card(card) for card in hand]
        
        return " ".join(cards)


class BlackjackTracker:
    """Track blackjack game statistics for users."""
    
    def __init__(self, bot_data: dict):
        """Initialize tracker with bot data."""
        self.bot_data = bot_data
        self._ensure_structure()
    
    def _ensure_structure(self):
        """Create blackjack tracking structure if missing."""
        if "blackjack_stats" not in self.bot_data:
            self.bot_data["blackjack_stats"] = {}
        if "blackjack_games" not in self.bot_data:
            self.bot_data["blackjack_games"] = {}
    
    def init_user(self, user_id: int):
        """Initialize stats for new user."""
        user_str = str(user_id)
        
        if user_str not in self.bot_data["blackjack_stats"]:
            self.bot_data["blackjack_stats"][user_str] = {
                "wins": 0,
                "losses": 0,
                "blackjacks": 0,
                "pushes": 0,
                "total_bet": 0,
                "total_won": 0,
                "current_streak": 0,
                "best_streak": 0,
                "games_played": 0
            }
    
    def add_game_result(self, user_id: int, result: str, bet: int, payout: int):
        """Record game result."""
        user_str = str(user_id)
        self.init_user(user_id)
        
        stats = self.bot_data["blackjack_stats"][user_str]
        
        # Update result counts
        if result == 'BLACKJACK':
            stats["blackjacks"] += 1
            stats["wins"] += 1
            current_won = True
        elif result == 'WIN':
            stats["wins"] += 1
            current_won = True
        elif result == 'PUSH':
            stats["pushes"] += 1
            current_won = None  # Neutral
        else:
            stats["losses"] += 1
            current_won = False
        
        # Update streak
        if current_won is True:
            stats["current_streak"] += 1
            stats["best_streak"] = max(stats["best_streak"], stats["current_streak"])
        elif current_won is False:
            stats["current_streak"] = 0
        # Pushes don't break streak
        
        # Update totals
        stats["total_bet"] += bet
        stats["total_won"] += payout
        stats["games_played"] += 1
    
    def get_stats(self, user_id: int) -> dict:
        """Get user statistics."""
        user_str = str(user_id)
        self.init_user(user_id)
        return self.bot_data["blackjack_stats"][user_str]


# ==========================================
# GAME STATE MANAGEMENT (OPTIMIZED)
# ==========================================

# Track active games with timestamps for cleanup
ACTIVE_GAMES: Dict[int, dict] = {}

# Track game cooldowns: {user_id: timestamp}
GAME_COOLDOWNS: Dict[int, datetime] = {}

# Prevent multiple simultaneous games per user
PLAYER_IN_GAME = set()

# Game cleanup timeout (5 minutes)
GAME_TIMEOUT = 300


def is_player_playing(user_id: int) -> bool:
    """Check if player already has an active game."""
    return user_id in PLAYER_IN_GAME


def cleanup_old_games():
    """Remove inactive games (older than 5 minutes)."""
    current_time = datetime.now()
    expired_users = []
    
    for user_id, game_data in list(ACTIVE_GAMES.items()):
        if 'started_at' in game_data:
            elapsed = (current_time - game_data['started_at']).total_seconds()
            if elapsed > GAME_TIMEOUT:
                expired_users.append(user_id)
    
    for user_id in expired_users:
        end_game(user_id)
        logger.info(f"🧹 Cleaned up expired blackjack game for {user_id}")


def start_new_game(user_id: int, bet: int):
    """Start a new blackjack game for user."""
    # Cleanup expired games periodically
    if len(ACTIVE_GAMES) > 10:
        cleanup_old_games()
    
    if user_id in PLAYER_IN_GAME:
        return False
    
    PLAYER_IN_GAME.add(user_id)
    
    game = BlackjackGame()
    player_val, dealer_visible = game.start_game()
    
    ACTIVE_GAMES[user_id] = {
        'game': game,
        'bet': bet,
        'state': 'playing',
        'doubled': False,
        'player_value': player_val,
        'dealer_visible': dealer_visible,
        'result': None,
        'started_at': datetime.now()
    }
    
    return True


def end_game(user_id: int):
    """End game and clean up."""
    if user_id in ACTIVE_GAMES:
        del ACTIVE_GAMES[user_id]
    
    PLAYER_IN_GAME.discard(user_id)


def has_cooldown(user_id: int, cooldown_seconds: int = 3) -> bool:
    """Check if user is in cooldown period."""
    if user_id not in GAME_COOLDOWNS:
        return False
    
    elapsed = (datetime.now() - GAME_COOLDOWNS[user_id]).total_seconds()
    return elapsed < cooldown_seconds


def set_cooldown(user_id: int):
    """Set cooldown for user."""
    GAME_COOLDOWNS[user_id] = datetime.now()


# ==========================================
# FLAVOR MESSAGES
# ==========================================

WIN_MESSAGES = [
    "🔥 INSANE WIN!",
    "🍀 Lucky pull!",
    "👑 BLACKJACK!",
    "💎 Big money!",
    "🎉 YES YES YES!",
    "🏆 You're on fire!",
    "✨ Sweet victory!",
    "💰 Money maker!",
]

LOSE_MESSAGES = [
    "💀 Dealer destroyed you.",
    "😢 Tough luck.",
    "🔥 Ouch! Better luck next time.",
    "😭 That hurts.",
    "☠️ Brutal loss.",
    "💔 Game over.",
    "🎭 Not your day.",
]

PUSH_MESSAGES = [
    "🤝 It's a tie!",
    "⚖️ Split the pot.",
    "🔄 One more time!",
    "🤷 No winner today.",
]

DEALER_MESSAGES = [
    "🤖 Dealer shows...",
    "🎰 House reveals...",
    "🃏 Let's see...",
    "🤐 Opening the cards...",
]


def get_flavor_message(msg_type: str) -> str:
    """Get random flavor message."""
    if msg_type == 'win':
        return random.choice(WIN_MESSAGES)
    elif msg_type == 'lose':
        return random.choice(LOSE_MESSAGES)
    elif msg_type == 'push':
        return random.choice(PUSH_MESSAGES)
    elif msg_type == 'dealer':
        return random.choice(DEALER_MESSAGES)
    return ""


# ==========================================
# UI FORMATTING
# ==========================================

# Cache BlackjackGame instance to avoid recreating
_game_cache = BlackjackGame()

def format_blackjack_board(player_hand: List[str], player_val: int, 
                           dealer_hand: List[str], dealer_val: int,
                           bet: int, show_dealer: bool = False) -> str:
    """Format beautiful blackjack game board. Optimized."""
    # Reuse cached instance
    player_display = _game_cache.format_hand(player_hand)
    dealer_display = (_game_cache.format_hand(dealer_hand) if show_dealer 
                     else _game_cache.format_hand(dealer_hand, hide_first=True))
    
    dealer_val_str = str(dealer_val) if show_dealer else '?'
    
    return (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🃏 **BLACKJACK**\n\n"
        f"👤 **You:**\n{player_display} = **{player_val}**\n\n"
        f"🤖 **Dealer:**\n{dealer_display} = **{dealer_val_str}**\n\n"
        f"💰 **Bet:** {bet} coins\n"
        f"━━━━━━━━━━━━━━━━━━"
    )


def format_result_message(result: str, player_val: int, dealer_val: int,
                         bet: int, payout: int, old_balance: int, 
                         new_balance: int) -> str:
    """Format final game result message."""
    
    if result == 'BLACKJACK':
        flavor = "👑 BLACKJACK! 👑"
        emoji = "🎉"
        msg = f"You got 21 with 2 cards! Amazing!"
    elif result == 'WIN':
        flavor = get_flavor_message('win')
        emoji = "🎉"
        msg = f"You ({player_val}) beat Dealer ({dealer_val})!"
    elif result == 'PUSH':
        flavor = get_flavor_message('push')
        emoji = "🤝"
        msg = f"Both have {player_val}. It's a tie."
    else:  # LOSE
        flavor = get_flavor_message('lose')
        emoji = "😢"
        if player_val > 21:
            msg = f"You busted with {player_val}!"
        else:
            msg = f"Dealer ({dealer_val}) beat you ({player_val})."
    
    output = f"""
━━━━━━━━━━━━━━━━━━
{emoji} **{flavor}**

{msg}

💰 **Payout:** {payout} coins
💵 **Balance:** {old_balance} → {new_balance}
━━━━━━━━━━━━━━━━━━
    """.strip()
    
    return output


# ==========================================
# BUTTON KEYBOARDS
# ==========================================

def get_blackjack_buttons() -> InlineKeyboardMarkup:
    """Get interactive game buttons."""
    buttons = [
        [
            InlineKeyboardButton("🃏 Hit", callback_data="bj_hit"),
            InlineKeyboardButton("✋ Stand", callback_data="bj_stand")
        ],
        [
            InlineKeyboardButton("💰 Double", callback_data="bj_double"),
            InlineKeyboardButton("🏳️ Surrender", callback_data="bj_surrender")
        ]
    ]
    
    return InlineKeyboardMarkup(buttons)
