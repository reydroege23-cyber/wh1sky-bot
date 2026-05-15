"""
🎰 GAMBLING GAMES MODULE
Simple fun games for virtual coins

GAMES:
- coinflip() → 50/50 double or lose
- slots() → Spin the machine
- dice() → Roll vs bot
- scratch_card() → Hidden prize card

⚠️ VIRTUAL COINS ONLY - Entertainment!
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
    """
    Fun gambling games for entertainment.
    
    All games return dicts with:
    - won: True/False
    - result: Message to show
    - coins_won: +/- coins
    """
    
    @staticmethod
    def coinflip(bet_amount: int) -> dict:
        """
        Simple coin flip: 50/50 chance to win.
        
        Win: Double your coins (2x multiplier)
        Lose: Lose your bet
        
        Returns: {'won': bool, 'result': str, 'coins_won': int}
        """
        won = random.randint(1, 100) <= COINFLIP_ODDS
        
        if won:
            # Calculate winnings
            coins_won = int(bet_amount * COINFLIP_MULTIPLIER)
            
            return {
                'won': True,
                'result': f"🪙 **HEADS!** You won {coins_won} coins!",
                'coins_won': coins_won,
                'emoji': '🎉'
            }
        else:
            # You lose
            return {
                'won': False,
                'result': f"🪙 **TAILS!** You lost {bet_amount} coins!",
                'coins_won': -bet_amount,
                'emoji': '😢'
            }
    
    @staticmethod
    def slots(bet_amount: int) -> dict:
        """
        Slot machine: Spin 3 reels.
        
        Jackpot (2%): All 3 match → 10x multiplier
        Win (30%): 2 match → 1.5x multiplier
        Loss: No match → lose bet
        
        Returns: {'won': bool, 'result': str, 'coins_won': int, 'display': str}
        """
        # Slot symbols
        symbols = ['🍎', '🍊', '🍋', '🍌', '🍉', '💎', '🎰', '⭐']
        
        # Spin 3 reels
        reel1 = random.choice(symbols)
        reel2 = random.choice(symbols)
        reel3 = random.choice(symbols)
        
        # Show reels
        display = f"🎰 [{reel1}] [{reel2}] [{reel3}]"
        
        # Check for JACKPOT (all 3 same)
        if reel1 == reel2 == reel3:
            if random.random() < SLOTS_JACKPOT_CHANCE:
                coins_won = int(bet_amount * SLOTS_JACKPOT_MULTIPLIER)
                return {
                    'won': True,
                    'result': f"🎰 **JACKPOT!!!** 🏆 Triple {reel1}!\nWon **{coins_won}** coins!",
                    'coins_won': coins_won,
                    'display': display
                }
        
        # Check for WIN (any 2 match)
        if (reel1 == reel2) or (reel2 == reel3) or (reel1 == reel3):
            if random.random() < SLOTS_WIN_CHANCE:
                coins_won = int(bet_amount * SLOTS_WIN_MULTIPLIER)
                return {
                    'won': True,
                    'result': f"🎰 **WIN!** Matched symbols!\nWon **{coins_won}** coins!",
                    'coins_won': coins_won,
                    'display': display
                }
        
        # NO MATCH - You lose
        return {
            'won': False,
            'result': f"🎰 **NO MATCH!** Better luck next time.\nLost **{bet_amount}** coins!",
            'coins_won': -bet_amount,
            'display': display
        }
    
    @staticmethod
    def dice(bet_amount: int) -> dict:
        """
        Dice duel: Your roll vs bot roll.
        
        Your roll > Bot roll: Win (1.8x multiplier)
        Your roll < Bot roll: Lose
        Tie: No change
        
        Returns: {'won': bool, 'result': str, 'coins_won': int}
        """
        your_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        if your_roll > bot_roll:
            # You win!
            coins_won = int(bet_amount * DICE_WIN_MULTIPLIER)
            return {
                'won': True,
                'result': f"🎲 You: **{your_roll}** | Bot: **{bot_roll}**\n✅ You won **{coins_won}** coins!",
                'coins_won': coins_won,
                'emoji': '🎉'
            }
        
        elif your_roll < bot_roll:
            # Bot wins
            return {
                'won': False,
                'result': f"�️ **SCRATCH CARD!**\n{label}\nLost **{bet_amount}** coins!",
                'coins_won': -bet_amount,
                'emoji': '😢'
            }
        
        # Fallback (shouldn't reach)
        return {
            'won': False,
            'result': f"🎟️ Lost **{bet_amount}** coins!",
            'coins_won': -bet_amount,
            'emoji': '😢'
        }
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
                        'result': f"🎟️ **SCRATCH CARD!**\n{label}\nWon **{coins_won}** coins!",
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
