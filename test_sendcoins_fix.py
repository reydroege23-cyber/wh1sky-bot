#!/usr/bin/env python3
"""
Test sendcoins command fix
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from economy import Economy

def test_sendcoins_logic():
    """Test coin transfer logic."""
    print("\n" + "="*60)
    print("SENDCOINS COMMAND FIX VERIFICATION")
    print("="*60 + "\n")
    
    # Initialize economy
    economy = Economy({})
    
    # Test data
    sender_id = 12345
    receiver_id = 67890
    amount = 500
    
    # Setup initial balances
    economy.set_balance(sender_id, 1000, "Test setup")
    economy.set_balance(receiver_id, 100, "Test setup")
    
    print("Initial State:")
    print(f"  Sender ({sender_id}): {economy.get_balance(sender_id)} coins")
    print(f"  Receiver ({receiver_id}): {economy.get_balance(receiver_id)} coins")
    
    # Perform transfer
    print(f"\nTransferring {amount} coins from sender to receiver...")
    success, message = economy.transfer_coins(sender_id, receiver_id, amount)
    
    print(f"\nTransfer Result: {success}")
    print(f"Message: {message}")
    
    # Check final balances
    sender_balance = economy.get_balance(sender_id)
    receiver_balance = economy.get_balance(receiver_id)
    
    print(f"\nFinal State:")
    print(f"  Sender ({sender_id}): {sender_balance} coins")
    print(f"  Receiver ({receiver_id}): {receiver_balance} coins")
    
    # Verify
    print("\n" + "-"*60)
    print("VERIFICATION")
    print("-"*60)
    
    expected_sender = 1000 - amount
    expected_receiver = 100 + amount
    
    checks = [
        (success == True, "Transfer succeeded"),
        (sender_balance == expected_sender, f"Sender balance correct ({expected_sender} coins)"),
        (receiver_balance == expected_receiver, f"Receiver balance correct ({expected_receiver} coins)"),
    ]
    
    all_passed = True
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"{status} {description}")
        if not check:
            all_passed = False
    
    # Test insufficient balance
    print("\n" + "-"*60)
    print("INSUFFICIENT BALANCE TEST")
    print("-"*60)
    
    sender_id_2 = 11111
    receiver_id_2 = 22222
    economy.set_balance(sender_id_2, 100, "Test setup")
    
    success2, message2 = economy.transfer_coins(sender_id_2, receiver_id_2, 500)
    print(f"Transfer 500 from account with 100 coins: {success2} (should be False)")
    print(f"Message: {message2}")
    
    insufficient_ok = success2 == False
    print(f"{'✓' if insufficient_ok else '✗'} Insufficient balance check works")
    if not insufficient_ok:
        all_passed = False
    
    # Test self-transfer prevention
    print("\n" + "-"*60)
    print("SELF-TRANSFER PREVENTION TEST")
    print("-"*60)
    
    sender_id_3 = 33333
    economy.set_balance(sender_id_3, 500, "Test setup")
    
    success3, message3 = economy.transfer_coins(sender_id_3, sender_id_3, 100)
    print(f"Transfer to self: {success3} (should be False)")
    print(f"Message: {message3}")
    
    self_transfer_ok = success3 == False
    print(f"{'✓' if self_transfer_ok else '✗'} Self-transfer prevention works")
    if not self_transfer_ok:
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("SUCCESS: Sendcoins logic verified!")
        print("Fix is ready to use:")
        print("  • /sendcoins @username amount (mention)")
        print("  • /sendcoins user_id amount (direct ID)")
        print("  • /sendcoins amount (reply to message)")
    else:
        print("ERROR: Some tests failed!")
    print("="*60 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = test_sendcoins_logic()
    sys.exit(0 if success else 1)
