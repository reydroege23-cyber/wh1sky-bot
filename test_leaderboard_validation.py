"""
🧪 Test Leaderboard Validation System

Tests the new fake user detection and removal system.
Verifies that the `/top` command only shows valid Telegram users.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database import is_valid_telegram_id, EconomyDatabase
from economy import Economy
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================================
# TEST USER IDs
# ========================================

VALID_IDS = [
    123456789,      # Normal valid ID
    987654321,      # Another valid ID
    100000000,      # Minimum valid ID
    999999999,      # Large valid ID
    1234567890,     # 10 digits
]

FAKE_IDS = [
    10,             # Too small
    1000,           # Too small
    100,            # Too small
    10000,          # Too small
    100000,         # Still too small
    1000000,        # Still too small
    10000000,       # Still too small
    "00000010",     # Leading zeros pattern
    "00010000",     # Leading zeros pattern
    "00060001",     # Leading zeros pattern
    "00001000",     # Leading zeros pattern
    99999999,       # Just below minimum (99999999 < 100000000)
    10000000000,    # Too large (> 9999999999)
]

# ========================================
# TEST FUNCTIONS
# ========================================

def test_id_validation():
    """Test the is_valid_telegram_id function."""
    print("\n" + "="*60)
    print("🧪 TESTING ID VALIDATION")
    print("="*60)
    
    # Test valid IDs
    print("\n✅ Testing VALID Telegram IDs:")
    for user_id in VALID_IDS:
        result = is_valid_telegram_id(user_id)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {user_id} -> {result}")
        assert result, f"Valid ID {user_id} failed validation"
    
    # Test fake IDs
    print("\n❌ Testing FAKE/INVALID IDs:")
    for user_id in FAKE_IDS:
        result = is_valid_telegram_id(user_id)
        status = "✅ PASS" if not result else "❌ FAIL"
        print(f"  {status}: {user_id} -> {result}")
        assert not result, f"Fake ID {user_id} passed validation (should fail)"
    
    print("\n✅ All ID validation tests passed!")

def test_database_cleanup():
    """Test database cleanup functionality."""
    print("\n" + "="*60)
    print("🧪 TESTING DATABASE CLEANUP")
    print("="*60)
    
    # Clean up old test database file first
    import os
    # The EconomyDatabase stores DB files in the data/ directory
    test_db_file = "data/test_economy_cleanup.db"
    if os.path.exists(test_db_file):
        os.remove(test_db_file)
        print("🧹 Removed old test database")
    
    # Create fresh test database
    # Pass just the filename; EconomyDatabase will place it under data/
    db = EconomyDatabase('test_economy_cleanup.db')
    
    # Add some valid users (add_balance calls register_user internally)
    print("\n➕ Adding valid test users...")
    valid_test_ids = [123456789, 987654321, 555666777]
    for user_id in valid_test_ids:
        # Just add balance - register_user is called automatically with starting_balance=100
        db.add_balance(user_id, 900)  # So total will be 100 + 900 = 1000
    
    # Add some fake users
    print("➕ Adding fake test users...")
    fake_test_ids = [100, 1000, 10000, 99999999]
    for user_id in fake_test_ids:
        try:
            db.register_user(user_id, f"fake_{user_id}", f"FakeUser{user_id}")
            db.add_balance(user_id, 400)  # So total will be 100 + 400 = 500
        except Exception as e:
            logger.warning(f"Could not add fake user {user_id}: {e}")
    
    # Check for fake users
    print("\n🔍 Checking for fake users...")
    fake_users = db.get_fake_users()
    print(f"Found {len(fake_users)} fake users: {fake_users}")
    
    # Cleanup
    print("\n🗑️ Cleaning up fake users...")
    removed_count, removed_ids = db.cleanup_fake_users()
    print(f"Removed {removed_count} fake users: {removed_ids}")
    
    # Verify cleanup
    print("\n✅ Verifying cleanup...")
    remaining_fake = db.get_fake_users()
    print(f"Remaining fake users: {remaining_fake}")
    assert len(remaining_fake) == 0, f"Cleanup failed - still have {remaining_fake}"
    
    # Verify valid users still exist with correct balances
    print("\n✅ Verifying valid users still exist with correct balances...")
    for user_id in valid_test_ids:
        balance = db.get_balance(user_id)
        print(f"  User {user_id}: {balance} coins (expected: 1000)")
        assert balance == 1000, f"Valid user {user_id} balance changed to {balance}, expected 1000"
    
    print("\n✅ All database cleanup tests passed!")
    
    # Cleanup test database
    try:
        os.remove(test_db_file)
        print("🧹 Cleaned up test database")
    except:
        pass

def test_economy_wrapper():
    """Test the Economy class wrapper methods."""
    print("\n" + "="*60)
    print("🧪 TESTING ECONOMY CLASS WRAPPER")
    print("="*60)
    
    economy = Economy({})
    
    # Test cleanup method
    print("\nTesting economy.cleanup_fake_users()...")
    result = economy.cleanup_fake_users()
    print(f"Result: {result}")
    assert isinstance(result, dict), "cleanup_fake_users should return dict"
    assert 'success' in result, "Result should have 'success' key"
    assert 'removed_count' in result, "Result should have 'removed_count' key"
    
    # Test get_fake_users_list method
    print("\nTesting economy.get_fake_users_list()...")
    fake_list = economy.get_fake_users_list()
    print(f"Fake users: {fake_list}")
    assert isinstance(fake_list, list), "get_fake_users_list should return list"
    
    print("\n✅ All Economy wrapper tests passed!")

def test_leaderboard_format():
    """Test the updated leaderboard format with usernames."""
    print("\n" + "="*60)
    print("🧪 TESTING LEADERBOARD FORMAT")
    print("="*60)
    
    from ui_animations import format_leaderboard
    
    # Test with new format (user_id, username, first_name, balance)
    print("\nTesting with new format (4-tuple)...")
    new_format_users = [
        (123456789, "john_doe", "John", 5000),
        (987654321, "jane_smith", "Jane", 4000),
        (555666777, "bob_test", "Bob", 3000),
    ]
    
    leaderboard = format_leaderboard(new_format_users)
    print("\nFormatted Leaderboard:")
    print(leaderboard)
    
    assert "@john_doe" in leaderboard, "Username should be displayed"
    assert "5000" in leaderboard, "Balance should be displayed"
    
    # Test with old format (user_id, balance) for backward compatibility
    print("\n\nTesting with old format (2-tuple) for backward compatibility...")
    old_format_users = [
        (123456789, 5000),
        (987654321, 4000),
    ]
    
    leaderboard = format_leaderboard(old_format_users)
    print("\nFormatted Leaderboard (backward compat):")
    print(leaderboard)
    
    assert "5000" in leaderboard, "Balance should be displayed"
    
    print("\n✅ All leaderboard format tests passed!")

# ========================================
# MAIN TEST RUNNER
# ========================================

def main():
    """Run all tests."""
    print("\n")
    print("█" * 60)
    print("█  🧪 LEADERBOARD VALIDATION SYSTEM TEST SUITE 🧪")
    print("█" * 60)
    
    try:
        test_id_validation()
        test_database_cleanup()
        test_economy_wrapper()
        test_leaderboard_format()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED! 🎉")
        print("="*60)
        print("\n✔️ ID validation system working correctly")
        print("✔️ Database cleanup system working correctly")
        print("✔️ Economy wrapper methods working correctly")
        print("✔️ Leaderboard formatting working correctly")
        print("\n💯 Leaderboard validation system is READY FOR DEPLOYMENT!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
