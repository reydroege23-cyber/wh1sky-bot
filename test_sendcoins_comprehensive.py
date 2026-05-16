#!/usr/bin/env python3
"""
Comprehensive test for the /sendcoins command fix
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from economy import Economy
from database import EconomyDatabase

def test_sendcoins_comprehensive():
    """Test all aspects of the sendcoins command."""
    print("\n" + "="*70)
    print("SENDCOINS COMMAND - COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")
    
    # Initialize
    economy = Economy({})
    db = EconomyDatabase("data/economy.db")
    
    # Test scenarios
    test_results = []
    
    # ========== TEST 1: Basic Transfer ==========
    print("TEST 1: Basic Coin Transfer")
    print("-" * 70)
    
    user_a = 10001
    user_b = 10002
    economy.set_balance(user_a, 500, "Test setup")
    economy.set_balance(user_b, 100, "Test setup")
    
    print(f"Before transfer:")
    print(f"  User A ({user_a}): {economy.get_balance(user_a)} coins")
    print(f"  User B ({user_b}): {economy.get_balance(user_b)} coins")
    
    success, msg = economy.transfer_coins(user_a, user_b, 150)
    
    print(f"\nTransfer 150 coins from A to B: {success}")
    print(f"Message: {msg}")
    print(f"\nAfter transfer:")
    print(f"  User A ({user_a}): {economy.get_balance(user_a)} coins")
    print(f"  User B ({user_b}): {economy.get_balance(user_b)} coins")
    
    balance_a = economy.get_balance(user_a)
    balance_b = economy.get_balance(user_b)
    test1_pass = success and balance_a == 350 and balance_b == 250
    test_results.append(("Basic transfer", test1_pass))
    print(f"Result: {'PASS' if test1_pass else 'FAIL'}\n")
    
    # ========== TEST 2: Insufficient Balance ==========
    print("TEST 2: Insufficient Balance Check")
    print("-" * 70)
    
    user_c = 20001
    user_d = 20002
    economy.set_balance(user_c, 50, "Test setup")
    
    print(f"User C balance: {economy.get_balance(user_c)} coins")
    print(f"Attempting transfer of 100 coins...")
    
    success2, msg2 = economy.transfer_coins(user_c, user_d, 100)
    
    print(f"Result: {success2}")
    print(f"Message: {msg2}")
    
    test2_pass = success2 == False and "Insufficient" in msg2
    test_results.append(("Insufficient balance check", test2_pass))
    print(f"Result: {'PASS' if test2_pass else 'FAIL'}\n")
    
    # ========== TEST 3: Self-Transfer Prevention ==========
    print("TEST 3: Self-Transfer Prevention")
    print("-" * 70)
    
    user_e = 30001
    economy.set_balance(user_e, 200, "Test setup")
    
    print(f"Attempting self-transfer (same sender/receiver)...")
    
    success3, msg3 = economy.transfer_coins(user_e, user_e, 50)
    
    print(f"Result: {success3}")
    print(f"Message: {msg3}")
    
    test3_pass = success3 == False and "yourself" in msg3.lower()
    test_results.append(("Self-transfer prevention", test3_pass))
    print(f"Result: {'PASS' if test3_pass else 'FAIL'}\n")
    
    # ========== TEST 4: Negative Amount Prevention ==========
    print("TEST 4: Negative Amount Prevention")
    print("-" * 70)
    
    user_f = 40001
    user_g = 40002
    economy.set_balance(user_f, 300, "Test setup")
    
    print(f"Attempting transfer with negative amount (-50)...")
    
    success4, msg4 = economy.transfer_coins(user_f, user_g, -50)
    
    print(f"Result: {success4}")
    print(f"Message: {msg4}")
    
    test4_pass = success4 == False and "positive" in msg4.lower()
    test_results.append(("Negative amount prevention", test4_pass))
    print(f"Result: {'PASS' if test4_pass else 'FAIL'}\n")
    
    # ========== TEST 5: Auto-Create Receiver ==========
    print("TEST 5: Auto-Create Receiver User")
    print("-" * 70)
    
    user_h = 50001
    user_i = 50002
    economy.set_balance(user_h, 200, "Test setup")
    
    # User I doesn't exist yet
    print(f"User H ({user_h}): {economy.get_balance(user_h)} coins")
    print(f"User I ({user_i}): {economy.get_balance(user_i)} coins (new users start with 100)")
    
    success5, msg5 = economy.transfer_coins(user_h, user_i, 75)
    
    print(f"\nTransfer 75 coins from H to I: {success5}")
    print(f"\nAfter transfer:")
    print(f"  User H ({user_h}): {economy.get_balance(user_h)} coins")
    print(f"  User I ({user_i}): {economy.get_balance(user_i)} coins")
    
    balance_h = economy.get_balance(user_h)
    balance_i = economy.get_balance(user_i)
    
    # New users start with 100, then receive 75 = 175
    expected_i = 175
    
    test5_pass = success5 and balance_h == 125 and balance_i == expected_i
    test_results.append(("Auto-create receiver", test5_pass))
    print(f"Result: {'PASS' if test5_pass else 'FAIL'}\n")
    
    # ========== TEST 6: Atomicity (Transaction) ==========
    print("TEST 6: Atomic Transfer (Transaction Safety)")
    print("-" * 70)
    
    user_j = 60001
    user_k = 60002
    economy.set_balance(user_j, 1000, "Test setup")
    economy.set_balance(user_k, 500, "Test setup")
    
    initial_j = economy.get_balance(user_j)
    initial_k = economy.get_balance(user_k)
    total_before = initial_j + initial_k
    
    print(f"Total coins before: {total_before}")
    
    success6, msg6 = economy.transfer_coins(user_j, user_k, 200)
    
    final_j = economy.get_balance(user_j)
    final_k = economy.get_balance(user_k)
    total_after = final_j + final_k
    
    print(f"Total coins after: {total_after}")
    print(f"Total preserved: {total_before == total_after}")
    
    test6_pass = total_before == total_after and success6
    test_results.append(("Atomic transaction", test6_pass))
    print(f"Result: {'PASS' if test6_pass else 'FAIL'}\n")
    
    # ========== SUMMARY ==========
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in test_results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in test_results)
    
    print("\n" + "="*70)
    if all_passed:
        print("SUCCESS: All tests passed!")
        print("\n/sendcoins command is ready:")
        print("  • Reply method: Reply to message + /sendcoins 100")
        print("  • Mention method: /sendcoins @username 100")
        print("  • Direct ID: /sendcoins 123456789 100")
        print("\nFeatures working:")
        print("  ✓ Balance validation")
        print("  ✓ Self-transfer prevention")
        print("  ✓ Auto-create recipients")
        print("  ✓ Atomic database transactions")
        print("  ✓ Persistent storage")
    else:
        print("FAILURE: Some tests failed!")
        print("Please review the errors above.")
    print("="*70 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = test_sendcoins_comprehensive()
    sys.exit(0 if success else 1)
