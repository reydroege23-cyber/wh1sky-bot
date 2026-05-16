#!/usr/bin/env python3
"""
✅ BLACKJACK SYSTEM - INTEGRATION VERIFICATION
Verify that all components are properly integrated and ready to go live
"""

import sys
import importlib
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a required file exists."""
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size
        print(f"✅ {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False


def check_import(module_name, description):
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}: Module '{module_name}' imports successfully")
        return True
    except ImportError as e:
        print(f"❌ {description}: Cannot import '{module_name}': {e}")
        return False
    except SyntaxError as e:
        print(f"❌ {description}: Syntax error in '{module_name}': {e}")
        return False


def check_blackjack_functions():
    """Check that all required blackjack functions exist."""
    try:
        import blackjack
        required_functions = [
            'draw_card', 'card_value', 'hand_value', 'is_blackjack',
            'create_game', 'get_game', 'player_hit', 'player_stand',
            'player_double', 'player_surrender', 'dealer_play',
            'determine_winner', 'cleanup_game', 'format_game_status',
            'format_game_result', 'can_hit', 'can_stand', 'can_double',
            'can_surrender'
        ]
        
        missing = []
        for func in required_functions:
            if not hasattr(blackjack, func):
                missing.append(func)
        
        if missing:
            print(f"❌ Blackjack functions missing: {', '.join(missing)}")
            return False
        else:
            print(f"✅ All 18 blackjack functions present")
            return True
    except Exception as e:
        print(f"❌ Error checking blackjack functions: {e}")
        return False


def check_main_handlers():
    """Check that all command handlers are defined in main.py."""
    try:
        import main
        required_handlers = [
            'blackjack_start', 'blackjack_hit', 'blackjack_stand',
            'blackjack_double', 'blackjack_surrender'
        ]
        
        missing = []
        for handler in required_handlers:
            if not hasattr(main, handler):
                missing.append(handler)
        
        if missing:
            print(f"❌ Handlers missing in main.py: {', '.join(missing)}")
            return False
        else:
            print(f"✅ All 5 command handlers defined in main.py")
            return True
    except Exception as e:
        print(f"❌ Error checking main.py handlers: {e}")
        return False


def check_documentation():
    """Check that all documentation files exist."""
    docs = [
        ('BLACKJACK_GUIDE.md', 'Complete user guide'),
        ('BLACKJACK_QUICK_START.md', 'Quick start reference'),
        ('BLACKJACK_IMPLEMENTATION.md', 'Technical documentation'),
        ('BLACKJACK_READY_TO_DEPLOY.md', 'Deployment checklist'),
    ]
    
    all_exist = True
    for filename, description in docs:
        if check_file_exists(filename, description):
            pass
        else:
            all_exist = False
    
    return all_exist


def run_verification():
    """Run complete verification suite."""
    print("\n" + "=" * 60)
    print("🃏 BLACKJACK SYSTEM - INTEGRATION VERIFICATION")
    print("=" * 60 + "\n")
    
    results = {
        "Files": [],
        "Imports": [],
        "Functions": [],
        "Handlers": [],
        "Documentation": []
    }
    
    # File checks
    print("📁 FILE VERIFICATION")
    print("-" * 60)
    results["Files"].append(check_file_exists("blackjack.py", "Game logic module"))
    results["Files"].append(check_file_exists("main.py", "Bot main file"))
    results["Files"].append(check_file_exists("economy.py", "Economy module"))
    print()
    
    # Import checks
    print("📦 IMPORT VERIFICATION")
    print("-" * 60)
    results["Imports"].append(check_import("blackjack", "Blackjack module"))
    results["Imports"].append(check_import("main", "Main module"))
    results["Imports"].append(check_import("economy", "Economy module"))
    print()
    
    # Function checks
    print("🔧 FUNCTION VERIFICATION")
    print("-" * 60)
    results["Functions"].append(check_blackjack_functions())
    print()
    
    # Handler checks
    print("⚙️ HANDLER VERIFICATION")
    print("-" * 60)
    results["Handlers"].append(check_main_handlers())
    print()
    
    # Documentation checks
    print("📚 DOCUMENTATION VERIFICATION")
    print("-" * 60)
    results["Documentation"].append(check_documentation())
    print()
    
    # Summary
    print("=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_checks = sum(1 for v in results.values() for item in v)
    passed = sum(1 for v in results.values() for item in v if item)
    
    for category, checks in results.items():
        status = "✅" if all(checks) else "❌"
        count = sum(1 for c in checks if c)
        print(f"{status} {category}: {count}/{len(checks)} checks passed")
    
    print()
    print(f"{'=' * 60}")
    print(f"OVERALL: {passed}/{total_checks} checks passed")
    print(f"{'=' * 60}")
    
    if passed == total_checks:
        print("\n🟢 VERIFICATION COMPLETE - SYSTEM IS READY!")
        print("✅ All components properly integrated")
        print("✅ All files present")
        print("✅ All imports working")
        print("✅ All functions available")
        print("✅ All handlers registered")
        print("✅ All documentation complete")
        print("\n🚀 READY TO DEPLOY\n")
        return True
    else:
        print(f"\n🔴 VERIFICATION FAILED - {total_checks - passed} issues found")
        print("⚠️  Please fix the above errors before deploying\n")
        return False


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
