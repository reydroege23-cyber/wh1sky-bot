"""
Test script to verify warns system works correctly
This simulates the warning process and checks data persistence
"""

import json
from pathlib import Path

DATA_FILE = "bot_data.json"

def load_data():
    """Load bot data."""
    if Path(DATA_FILE).exists():
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded data: {len(data.get('warnings', {}))} users with warnings")
                return data
        except Exception as e:
            print(f"❌ Error loading: {e}")
    return {"warnings": {}, "stats": {}, "mutes": {}, "metadata": {}}

def save_data(data):
    """Save bot data."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"💾 Data saved")
    except Exception as e:
        print(f"❌ Error saving: {e}")

def test_warns_system():
    """Test the warns system."""
    print("=" * 60)
    print("🧪 WARNS SYSTEM TEST")
    print("=" * 60)
    
    # Load initial data
    bot_data = load_data()
    print(f"\n📊 Initial state: {bot_data['warnings']}")
    
    # Simulate warning a test user
    test_user_id = "999888777"  # Test user
    MAX_WARNINGS = 3
    
    print(f"\n🔄 Simulating 3 warnings for user {test_user_id}...")
    
    for warn_num in range(1, MAX_WARNINGS + 1):
        print(f"\n--- Warning #{warn_num} ---")
        
        # Get current
        current_warns = bot_data["warnings"].get(test_user_id, 0)
        print(f"📍 Current: {current_warns}")
        
        # Increment
        new_count = current_warns + 1
        bot_data["warnings"][test_user_id] = new_count
        print(f"📍 Incremented to: {new_count}")
        
        # Save
        save_data(bot_data)
        
        # Verify
        verify_data = load_data()
        verify_count = verify_data["warnings"].get(test_user_id, 0)
        print(f"✅ Verified in file: {verify_count}/{MAX_WARNINGS}")
        
        if verify_count != new_count:
            print(f"❌ MISMATCH: Expected {new_count}, got {verify_count}")
            return False
        
        # Check ban condition
        if new_count >= MAX_WARNINGS:
            print(f"\n🚫 BAN CONDITION REACHED!")
            print(f"   User: {test_user_id}")
            print(f"   Warnings: {new_count}/{MAX_WARNINGS}")
            print(f"   Action: Would execute ban now")
            
            # Reset after ban
            bot_data["warnings"][test_user_id] = 0
            save_data(bot_data)
            print(f"✅ Warns reset to 0 after ban")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE - Warns system working correctly")
    print("=" * 60)
    
    # Show final state
    final_data = load_data()
    print(f"\n📊 Final state: {final_data['warnings']}")
    
    return True

if __name__ == "__main__":
    success = test_warns_system()
    if not success:
        print("\n❌ TEST FAILED - Warns system has issues")
        exit(1)
