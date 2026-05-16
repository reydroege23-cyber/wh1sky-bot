#!/usr/bin/env python3
"""
Final verification test - Simulates /top command
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_top_command():
    """Simulate the /top command."""
    print("\n" + "="*60)
    print("FINAL VERIFICATION - SIMULATING /top COMMAND")
    print("="*60 + "\n")
    
    # Import the economy system
    from economy import Economy
    from ui_animations import format_leaderboard
    
    # Initialize economy
    economy = Economy({})
    
    # Get top 10 users (same as /top command)
    top_users = economy.get_top_users(10)
    
    if not top_users:
        print("ERROR: No users found!")
        return False
    
    # Format the leaderboard (same as /top command)
    leaderboard = format_leaderboard(top_users)
    
    # Add the message (same as /top command)
    leaderboard += "\n\n💰 **Play to climb the ranks!**"
    
    # Display it
    print("LEADERBOARD OUTPUT:")
    print(leaderboard)
    
    print("\n" + "-"*60)
    print("VERIFICATION")
    print("-"*60)
    
    # Expected order
    expected_order = [
        (7676185, 7460),
        (37521522, 4587),
        (93704808, 3910),
        (52547401, 250),
        (77797097, 150),
        (21139323, 50),
        (6228240, 0),
        (71828873, 0),
    ]
    
    all_correct = True
    
    # Check order
    print("\nOrder verification:")
    for idx, (expected_id, expected_bal) in enumerate(expected_order):
        if idx < len(top_users):
            actual_id, actual_bal = top_users[idx]
            position = idx + 1
            if actual_id == expected_id and actual_bal == expected_bal:
                print(f"  Position {position}: OK - {actual_id} ({actual_bal} coins)")
            else:
                print(f"  Position {position}: FAIL")
                print(f"    Expected: {expected_id} ({expected_bal} coins)")
                print(f"    Got:      {actual_id} ({actual_bal} coins)")
                all_correct = False
        else:
            print(f"  Position {idx+1}: MISSING")
            all_correct = False
    
    print("\n" + "="*60)
    if all_correct:
        print("SUCCESS: /top command will work 100%!")
        print("All users are in the correct order with correct balances.")
    else:
        print("ERROR: Some issues detected!")
    print("="*60 + "\n")
    
    return all_correct

if __name__ == "__main__":
    success = test_top_command()
    sys.exit(0 if success else 1)
