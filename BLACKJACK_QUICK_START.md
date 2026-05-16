# 🃏 BLACKJACK QUICK REFERENCE

## Start a Game
```
/bj 50
```

## During Game
| Command | What It Does |
|---------|--------------|
| `/hit` | Take another card |
| `/stand` | Finish hand, dealer plays |
| `/double` | Double bet, get 1 card, auto-stand |
| `/surrender` | Quit, get 50% of bet back |

## Card Values
- **2-10**: Face value
- **J, Q, K**: 10 points  
- **A**: 1 or 11 (auto-chosen)

## Win Conditions

| Outcome | Payout | When |
|---------|--------|------|
| 🎯 Blackjack | 2.5x | Natural 21 (2 cards) |
| 🎉 Win | 2x | Beat dealer ≤21 |
| 💥 Dealer Bust | 2x | Dealer >21, you ≤21 |
| 🤝 Push | 1x | Tie |
| 🏳️ Surrender | 0.5x | You quit (50% back) |
| 😭 Loss | 0x | Dealer beats you |
| 💥 Bust | 0x | You >21 |

## Example

```
User: /bj 100
Bot: Shows your 2 cards + dealer 1 visible card

User: /hit
Bot: You get 3rd card

User: /stand
Bot: Dealer plays, shows final result
```

## Rules
- You win if your hand > dealer AND ≤21
- Dealer hits on <17, stands on 17+
- You bust if >21 (instant loss)
- Double only on first 2 cards
- Surrender only on first 2 cards

That's it! Enjoy! 🎰
