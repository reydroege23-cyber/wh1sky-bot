"""
Gambling Games for Whisky_bot
Implements coinflip, slots, and dice games
⚠️ VIRTUAL CURRENCY ONLY - NO REAL MONEY VALUE
"""

import logging
import random
from config import (
    COINFLIP_ODDS,
    COINFLIP_MULTIPLIER,
    SLOTS_JACKPOT_CHANCE,
    SLOTS_JACKPOT_MULTIPLIER,
    SLOTS_WIN_CHANCE,
    SLOTS_WIN_MULTIPLIER,
    DICE_WIN_CHANCE,
    DICE_WIN_MULTIPLIER
)

logger = logging.getLogger(__name__)

class GamblingGames:
    """Handles all gambling game logic."""
    
    @staticmethod
    def coinflip(bet_amount: int) -> dict:
        """
        Coinflip game: 50/50 win or lose
        Returns: {'won': bool, 'result': str, 'coins_won': int, 'emoji': str}
        """
        won = random.randint(1, 100) <= COINFLIP_ODDS
        
        if won:
            coins_won = int(bet_amount * COINFLIP_MULTIPLIER)
            return {
                'won': True,
                'result': f"🪙 **HEADS!** You won {coins_won} coins!",
                'coins_won': coins_won,
                'emoji': '🪙'
            }
        else:
            return {
                'won': False,
                'result': f"🪙 **TAILS!** You lost {bet_amount} coins!",
                'coins_won': -bet_amount,
                'emoji': '💔'
            }
    
    @staticmethod
    def slots(bet_amount: int) -> dict:
        """
        Slot machine game with jackpot possibility
        Returns: {'won': bool, 'result': str, 'coins_won': int, 'display': str}
        """
        # Symbols for slots
        symbols = ['🍎', '🍊', '🍋', '🍌', '🍉', '💎', '🎰', '⭐']
        
        # Spin 3 reels
        reel1 = random.choice(symbols)
        reel2 = random.choice(symbols)
        reel3 = random.choice(symbols)
        
        display = f"🎰 [{reel1}] [{reel2}] [{reel3}]"
        
        # Check for jackpot (all 3 match)
        if reel1 == reel2 == reel3:
            if random.random() < SLOTS_JACKPOT_CHANCE:
                coins_won = int(bet_amount * SLOTS_JACKPOT_MULTIPLIER)
                return {
                    'won': True,
                    'result': f"🎰 **JACKPOT!!!** Triple {reel1}! Won {coins_won} coins!",
                    'coins_won': coins_won,
                    'display': display
                }
        
        # Check for regular win (2 matching symbols)
        if reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
            if random.random() < SLOTS_WIN_CHANCE:
                coins_won = int(bet_amount * SLOTS_WIN_MULTIPLIER)
                return {
                    'won': True,
                    'result': f"🎰 **WIN!** Matched symbols! Won {coins_won} coins!",
                    'coins_won': coins_won,
                    'display': display
                }
        
        # No win
        return {
            'won': False,
            'result': f"🎰 **NO MATCH!** Lost {bet_amount} coins!",
            'coins_won': -bet_amount,
            'display': display
        }
    
    @staticmethod
    def dice(bet_amount: int) -> dict:
        """
        Dice game: Roll vs bot
        Returns: {'won': bool, 'result': str, 'coins_won': int}
        """
        player_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        if player_roll > bot_roll:
            coins_won = int(bet_amount * DICE_WIN_MULTIPLIER)
            return {
                'won': True,
                'result': f"🎲 You rolled **{player_roll}**, bot rolled **{bot_roll}**\n✅ You won {coins_won} coins!",
                'coins_won': coins_won,
                'emoji': '✅'
            }
        elif player_roll < bot_roll:
            return {
                'won': False,
                'result': f"🎲 You rolled **{player_roll}**, bot rolled **{bot_roll}**\n❌ Bot wins! Lost {bet_amount} coins!",
                'coins_won': -bet_amount,
                'emoji': '❌'
            }
        else:
            return {
                'won': False,
                'result': f"🎲 You rolled **{player_roll}**, bot rolled **{bot_roll}**\n🤝 It's a tie! No coins lost or gained!",
                'coins_won': 0,
                'emoji': '🤝'
            }
    
    @staticmethod
    def scratch_card(bet_amount: int) -> dict:
        """
        Scratch card game: hidden prizes
        Returns: {'won': bool, 'result': str, 'coins_won': int}
        """
        prizes = [
            (0.05, 10, "🎟️ 10x Prize!"),
            (0.15, 3, "🎟️ 3x Prize!"),
            (0.25, 1.5, "🎟️ 1.5x Prize!"),
            (0.55, 0, "💸 Nothing!")
        ]
        
        roll = random.random()
        cumulative = 0
        
        for prob, multiplier, label in prizes:
            cumulative += prob
            if roll < cumulative:
                if multiplier > 0:
                    coins_won = int(bet_amount * multiplier)
                    return {
                        'won': True,
                        'result': f"🎟️ **SCRATCH!** {label} Won {coins_won} coins!",
                        'coins_won': coins_won,
                        'emoji': '🎟️'
                    }
                else:
                    return {
                        'won': False,
                        'result': f"🎟️ **SCRATCH!** {label} Lost {bet_amount} coins!",
                        'coins_won': -bet_amount,
                        'emoji': '😢'
                    }
        
        # Fallback (shouldn't reach)
        return {
            'won': False,
            'result': f"🎟️ Lost {bet_amount} coins!",
            'coins_won': -bet_amount,
            'emoji': '😢'
        }
