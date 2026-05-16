"""
🔍 TEST: Database Persistence - Verify /top doesn't reset after bot updates
This test ensures economy.db is persisted correctly and survives restarts
"""

import sqlite3
import os
import json
from pathlib import Path
import sys

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

from database import EconomyDatabase
from economy import Economy
from config import STARTING_BALANCE

def test_persistence():
    """Test that economy data persists after restart."""
    
    print("\n" + "="*60)
    print("🔍 PERSISTENCE TEST: Database Survives Restarts")
    print("="*60)
    
    # Step 1: Check database location
    print("\n[1️⃣] Checking database location...")
    
    db_path = Path("economy.db").resolve()
    print(f"   📍 Database path: {db_path}")
    print(f"   ✅ Absolute path: {db_path.exists()}")
    
    # Step 2: Initialize economy and add test users
    print("\n[2️⃣] Adding test users to economy...")
    
    economy = Economy()
    test_users = [
        (6228240, 3000, "User A"),
        (37521522, 2387, "User B"),
        (93704808, 367, "User C"),
        (52547401, 250, "User D"),
        (77797097, 150, "User E"),
    ]
    
    # Add test data
    for user_id, balance, name in test_users:
        economy.set_balance(user_id, balance, f"Test user: {name}")
        print(f"   ✅ Added {name}: ID={user_id}, Balance={balance}")
    
    # Step 3: Get top users before "restart"
    print("\n[3️⃣] Reading top users (BEFORE restart)...")
    top_before = economy.get_top_users(10)
    print(f"   📊 Top users count: {len(top_before)}")
    for i, (uid, balance) in enumerate(top_before, 1):
        print(f"      {i}. User {uid}: {balance} coins")
    
    # Step 4: Verify database file exists
    print("\n[4️⃣] Verifying database file...")
    if db_path.exists():
        size = db_path.stat().st_size
        print(f"   ✅ Database file exists: {db_path}")
        print(f"   📦 File size: {size} bytes")
    else:
        print(f"   ❌ DATABASE FILE NOT FOUND: {db_path}")
        return False
    
    # Step 5: Simulate restart by creating new Economy instance
    print("\n[5️⃣] Simulating bot restart (creating new Economy instance)...")
    
    # Create NEW instance (simulates bot restart)
    economy_new = Economy()
    print("   ✅ New Economy instance created")
    
    # Step 6: Read top users after "restart"
    print("\n[6️⃣] Reading top users (AFTER restart)...")
    top_after = economy_new.get_top_users(10)
    print(f"   📊 Top users count: {len(top_after)}")
    for i, (uid, balance) in enumerate(top_after, 1):
        print(f"      {i}. User {uid}: {balance} coins")
    
    # Step 7: Compare results
    print("\n[7️⃣] Comparing BEFORE vs AFTER restart...")
    
    if len(top_before) != len(top_after):
        print(f"   ❌ USER COUNT MISMATCH!")
        print(f"      Before: {len(top_before)}, After: {len(top_after)}")
        return False
    
    all_match = True
    for (uid_before, bal_before), (uid_after, bal_after) in zip(top_before, top_after):
        if uid_before != uid_after or bal_before != bal_after:
            print(f"   ❌ DATA MISMATCH!")
            print(f"      Before: User {uid_before} = {bal_before}")
            print(f"      After:  User {uid_after} = {bal_after}")
            all_match = False
    
    if all_match:
        print(f"   ✅ ALL DATA MATCHES! Persistence is working correctly.")
    
    # Step 8: Direct database query check
    print("\n[8️⃣] Direct database verification...")
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Check table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """)
            if not cursor.fetchone():
                print(f"   ❌ USERS TABLE NOT FOUND!")
                return False
            
            print(f"   ✅ Users table exists")
            
            # Check user count
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            print(f"   ✅ Total users in database: {count}")
            
            # Check specific users
            cursor.execute("""
                SELECT user_id, balance FROM users 
                ORDER BY balance DESC LIMIT 5
            """)
            print(f"   ✅ Top 5 users in database:")
            for uid, bal in cursor.fetchall():
                print(f"      User {uid}: {bal} coins")
    
    except Exception as e:
        print(f"   ❌ Database query error: {e}")
        return False
    
    # Final verdict
    print("\n" + "="*60)
    if all_match and len(top_after) > 0:
        print("✅ PERSISTENCE TEST PASSED!")
        print("   Database DOES survive bot restarts")
        print("   Data is NOT being reset")
        return True
    else:
        print("❌ PERSISTENCE TEST FAILED!")
        print("   Database is being reset on restart")
        print("   Data is NOT persisting")
        return False

def check_database_structure():
    """Check if database is properly structured."""
    print("\n" + "="*60)
    print("🔍 DATABASE STRUCTURE CHECK")
    print("="*60)
    
    db_path = Path("economy.db").resolve()
    
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='users'
            """)
            result = cursor.fetchone()
            
            if result:
                print("\n✅ Users table schema:")
                print(f"   {result[0]}")
            else:
                print("\n❌ Users table not found!")
                return False
            
            # Check indexes
            cursor.execute("""
                SELECT name, sql FROM sqlite_master 
                WHERE type='index' AND tbl_name='users'
            """)
            indexes = cursor.fetchall()
            
            if indexes:
                print("\n✅ Indexes found:")
                for name, sql in indexes:
                    print(f"   - {name}")
            else:
                print("\n⚠️  No indexes found (performance may be slow)")
            
            return True
    
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 Starting database persistence tests...\n")
    
    # Check structure first
    check_database_structure()
    
    # Run persistence test
    success = test_persistence()
    
    print("\n" + "="*60)
    if success:
        print("✅ ALL CHECKS PASSED - Your economy system is persistent!")
    else:
        print("❌ SOME CHECKS FAILED - Your economy needs fixing!")
    print("="*60 + "\n")
    
    sys.exit(0 if success else 1)
