"""
🃏 BLACKJACK SYSTEM - UNIT TESTS
Verify all game logic is working correctly before production
"""

import sys
sys.path.insert(0, '.')
from blackjack import *


def test_card_values():
    """Test card value calculations."""
    print("🧪 Test 1: Card Values")
    assert card_value('A') == 11
    assert card_value('2') == 2
    assert card_value('10') == 10
    assert card_value('J') == 10
    assert card_value('Q') == 10
    assert card_value('K') == 10
    print("   ✅ All card values correct")


def test_hand_value_basic():
    """Test basic hand value calculations."""
    print("\n🧪 Test 2: Hand Values (Basic)")
    assert hand_value(['5', '5']) == 10
    assert hand_value(['10', '10']) == 20
    assert hand_value(['K', '5']) == 15
    assert hand_value(['A', '9']) == 20  # 11 + 9
    print("   ✅ Basic hand values correct")


def test_hand_value_ace():
    """Test Ace handling in hand values."""
    print("\n🧪 Test 3: Hand Values (Ace Handling)")
    # Single Ace
    assert hand_value(['A']) == 11
    assert hand_value(['A', '5']) == 16  # 11 + 5
    # Two Aces
    assert hand_value(['A', 'A']) == 12  # 11 + 1
    # Ace preventing bust
    assert hand_value(['A', 'K', '5']) == 16  # 1 + 10 + 5
    assert hand_value(['A', '5', '5']) == 21  # 11 + 5 + 5
    # Multiple Aces
    assert hand_value(['A', 'A', 'A', '8']) == 21  # 1 + 1 + 1 + 8 + 11 = 22, reduce → 12
    print("   ✅ Ace handling correct")


def test_blackjack_detection():
    """Test blackjack detection."""
    print("\n🧪 Test 4: Blackjack Detection")
    assert is_blackjack(['K', 'A']) == True
    assert is_blackjack(['A', 'K']) == True
    assert is_blackjack(['Q', 'A']) == True
    assert is_blackjack(['10', '10']) == False  # Not 2 cards
    assert is_blackjack(['A', '5', '5']) == False  # 3 cards
    print("   ✅ Blackjack detection correct")


def test_hand_formatting():
    """Test hand display formatting."""
    print("\n🧪 Test 5: Hand Formatting")
    formatted = format_hand(['K', 'A'])
    # Should contain emoji or letter representation
    assert len(formatted) > 0  # Not empty
    assert '🂮' in formatted or 'K' in formatted  # King card
    print(f"   Formatted hand: {formatted}")
    print("   ✅ Hand formatting works")


def test_game_creation():
    """Test game creation."""
    print("\n🧪 Test 6: Game Creation")
    user_id = 123456
    game = create_game(user_id, 100)
    assert user_id in active_blackjack_games
    assert game["bet"] == 100
    assert len(game["player"]) == 2
    assert len(game["dealer"]) == 2
    assert game["state"] == STATE_PLAYING
    assert game["doubled"] == False
    print("   ✅ Game creation works")


def test_player_actions():
    """Test player actions."""
    print("\n🧪 Test 7: Player Actions")
    user_id = 789012
    create_game(user_id, 50)
    
    # Test hit
    assert player_hit(user_id) == True
    game = get_game(user_id)
    assert len(game["player"]) == 3
    print("   ✅ Hit works")
    
    # Test stand
    assert player_stand(user_id) == True
    game = get_game(user_id)
    assert game["state"] == STATE_DEALER_TURN
    print("   ✅ Stand works")


def test_player_double():
    """Test doubling down."""
    print("\n🧪 Test 8: Double Down")
    user_id = 345678
    create_game(user_id, 100)
    
    # Test double
    assert player_double(user_id) == True
    game = get_game(user_id)
    assert game["bet"] == 200  # Doubled
    assert game["doubled"] == True
    assert len(game["player"]) == 3  # 2 initial + 1 from double
    assert game["state"] == STATE_DEALER_TURN  # Auto-stand
    print("   ✅ Double down works")


def test_player_surrender():
    """Test surrender."""
    print("\n🧪 Test 9: Surrender")
    user_id = 234567
    create_game(user_id, 80)
    
    # Test surrender
    success, refund = player_surrender(user_id)
    assert success == True
    assert refund == 40  # 50% of 80
    game = get_game(user_id)
    assert game["state"] == STATE_FINISHED
    print("   ✅ Surrender works")


def test_dealer_ai():
    """Test dealer AI logic."""
    print("\n🧪 Test 10: Dealer AI")
    user_id = 901234
    game = create_game(user_id, 100)
    
    # Manually set dealer hand to test hitting logic
    game["dealer"] = ['5', '4']  # 9, should hit until 17+
    dealer_play(user_id)
    
    game = get_game(user_id)
    dealer_val = hand_value(game["dealer"])
    assert dealer_val >= 17  # Dealer should hit to 17+
    assert game["state"] == STATE_FINISHED
    print("   ✅ Dealer AI works")


def test_winner_determination():
    """Test winner determination."""
    print("\n🧪 Test 11: Winner Determination")
    
    # Test blackjack
    user_id = 555555
    game = create_game(user_id, 100)
    game["player"] = ['K', 'A']  # Blackjack
    game["dealer"] = ['10', '5']  # 15
    outcome, mult = determine_winner(user_id)
    assert outcome == "blackjack"
    assert mult == 2.5
    print("   ✅ Blackjack detection works")
    
    # Test win
    user_id = 666666
    game = create_game(user_id, 100)
    game["player"] = ['10', '10']  # 20
    game["dealer"] = ['9', '5']  # 14
    outcome, mult = determine_winner(user_id)
    assert outcome == "win"
    assert mult == 2
    print("   ✅ Win detection works")
    
    # Test push
    user_id = 777777
    game = create_game(user_id, 100)
    game["player"] = ['10', '8']  # 18
    game["dealer"] = ['10', '8']  # 18
    outcome, mult = determine_winner(user_id)
    assert outcome == "push"
    assert mult == 1
    print("   ✅ Push detection works")
    
    # Test bust
    user_id = 888888
    game = create_game(user_id, 100)
    game["player"] = ['10', '10', '5']  # 25
    outcome, mult = determine_winner(user_id)
    assert outcome == "bust"
    assert mult == 0
    print("   ✅ Bust detection works")


def test_game_cleanup():
    """Test game cleanup."""
    print("\n🧪 Test 12: Game Cleanup")
    user_id = 999999
    create_game(user_id, 100)
    assert user_id in active_blackjack_games
    
    cleanup_game(user_id)
    assert user_id not in active_blackjack_games
    print("   ✅ Game cleanup works")


def test_game_expiry():
    """Test game expiry timeout."""
    print("\n🧪 Test 13: Game Expiry")
    user_id = 111111
    create_game(user_id, 100)
    
    # Manually expire the game
    game = active_blackjack_games[user_id]
    game["created"] = 0  # Very old
    
    # get_game should return None and clean up
    result = get_game(user_id)
    assert result is None
    assert user_id not in active_blackjack_games
    print("   ✅ Game expiry works")


def test_action_validation():
    """Test action validation."""
    print("\n🧪 Test 14: Action Validation")
    user_id = 222222
    create_game(user_id, 100)
    
    # Test can hit
    can, msg = can_hit(user_id)
    assert can == True
    print("   ✅ Can hit validation works")
    
    # Test can stand
    can, msg = can_stand(user_id)
    assert can == True
    print("   ✅ Can stand validation works")
    
    # Test can double (should be true on first 2 cards)
    can, msg = can_double(user_id)
    assert can == True
    print("   ✅ Can double validation works")
    
    # Test can surrender
    can, msg = can_surrender(user_id)
    assert can == True
    print("   ✅ Can surrender validation works")


def run_all_tests():
    """Run all unit tests."""
    print("=" * 50)
    print("🃏 BLACKJACK SYSTEM - UNIT TESTS")
    print("=" * 50)
    
    try:
        test_card_values()
        test_hand_value_basic()
        test_hand_value_ace()
        test_blackjack_detection()
        test_hand_formatting()
        test_game_creation()
        test_player_actions()
        test_player_double()
        test_player_surrender()
        test_dealer_ai()
        test_winner_determination()
        test_game_cleanup()
        test_game_expiry()
        test_action_validation()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        print("\n🚀 Blackjack system is ready for production!")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
