#!/usr/bin/env python3
"""
Test the leaderboard fix
"""

import sqlite3
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_leaderboard():
    """Test that leaderboard displays correctly."""
    print("\n" + "="*50)
    print("LEADERBOARD FIX TEST")
    print("="*50 + "\n")
    
    # Connect to database (use persistent data directory copy)
    db_file = "data/economy.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Get top 10 users
    cursor.execute("""
        SELECT user_id, balance
        FROM users
        ORDER BY balance DESC
        LIMIT 10
    """)
    
    top_users = cursor.fetchall()
    conn.close()
    
    # Import the formatting function
    from ui_animations import format_leaderboard
    
    # Format the leaderboard
    leaderboard = format_leaderboard(top_users)
    
    # Print it
    print(leaderboard)
    print("\n" + "-"*50)
    print("VERIFICATION")
    print("-"*50)
    
    # Verify expected users
    expected = [
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
    for idx, (expected_id, expected_balance) in enumerate(expected):
        if idx < len(top_users):
            actual_id, actual_balance = top_users[idx]
            match = actual_id == expected_id and actual_balance == expected_balance
            status = "✓" if match else "✗"
            print(f"{status} Position {idx+1}: {actual_id} ({actual_balance} coins)")
            if not match:
                print(f"  Expected: {expected_id} ({expected_balance} coins)")
                all_correct = False
        else:
            print(f"✗ Position {idx+1}: MISSING")
            all_correct = False
    
    print("\n" + "="*50)
    if all_correct:
        print("SUCCESS: Leaderboard is correct!")
    else:
        print("ERROR: Leaderboard has issues!")
    print("="*50 + "\n")
    
    return all_correct

if __name__ == "__main__":
    success = test_leaderboard()
    sys.exit(0 if success else 1)
