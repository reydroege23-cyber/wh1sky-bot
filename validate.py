#!/usr/bin/env python3
"""
🥃 WHISKY_BOT ELITE - COMPLETE VALIDATION
Comprehensive system verification before deployment
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

class BotValidator:
    def __init__(self):
        self.results = []
        self.warnings = []
        self.errors = []
        
    def log(self, level, message):
        """Log validation message."""
        if level == "✅":
            print(f"{level} {message}")
            self.results.append((level, message))
        elif level == "⚠️":
            print(f"{level} {message}")
            self.warnings.append(message)
        elif level == "❌":
            print(f"{level} {message}")
            self.errors.append(message)
    
    def validate_files(self):
        """Validate required files exist."""
        print("\n📁 VALIDATING FILES")
        print("-" * 50)
        
        required = {
            "main.py": "Bot application",
            "config.py": "Configuration",
            "requirements.txt": "Dependencies",
            ".env.example": "Env template",
        }
        
        for file, desc in required.items():
            if Path(file).exists():
                size = Path(file).stat().st_size
                self.log("✅", f"{file} ({size} bytes) - {desc}")
            else:
                self.log("❌", f"{file} - MISSING: {desc}")
    
    def validate_python_syntax(self):
        """Validate Python syntax."""
        print("\n🐍 VALIDATING PYTHON SYNTAX")
        print("-" * 50)
        
        files = ["main.py", "config.py"]
        for filename in files:
            if Path(filename).exists():
                try:
                    with open(filename, 'r') as f:
                        compile(f.read(), filename, 'exec')
                    self.log("✅", f"{filename} - Syntax OK")
                except SyntaxError as e:
                    self.log("❌", f"{filename} - Syntax Error: {e}")
    
    def validate_config(self):
        """Validate configuration."""
        print("\n⚙️ VALIDATING CONFIGURATION")
        print("-" * 50)
        
        try:
            from config import (
                TELEGRAM_TOKEN, GEMINI_API_KEY, ADMIN_IDS,
                MAX_WARNINGS, MUTE_DURATION, BAD_WORDS,
                AI_MODEL, LOG_FILE, DATA_FILE
            )
            
            self.log("✅", f"Token configured: {'***' + TELEGRAM_TOKEN[-4:]}")
            self.log("✅", f"API Key configured: {'***' + GEMINI_API_KEY[-4:]}")
            self.log("✅", f"Admins: {len(ADMIN_IDS)} configured")
            self.log("✅", f"Max Warnings: {MAX_WARNINGS}")
            self.log("✅", f"Mute Duration: {MUTE_DURATION}m")
            self.log("✅", f"Bad Words: {len(BAD_WORDS)}")
            self.log("✅", f"AI Model: {AI_MODEL}")
            
        except Exception as e:
            self.log("❌", f"Config validation failed: {e}")
    
    def validate_imports(self):
        """Validate all imports work."""
        print("\n📦 VALIDATING IMPORTS")
        print("-" * 50)
        
        imports = {
            "telegram": "Telegram Bot API",
            "google.generativeai": "Google Gemini AI",
            "asyncio": "Async support",
            "logging": "Logging system",
            "json": "JSON support",
        }
        
        for module, desc in imports.items():
            try:
                __import__(module)
                self.log("✅", f"{module} - {desc}")
            except ImportError as e:
                self.log("❌", f"{module} - MISSING: {desc}")
    
    def validate_code_quality(self):
        """Validate code quality metrics."""
        print("\n✨ VALIDATING CODE QUALITY")
        print("-" * 50)
        
        with open("main.py", 'r') as f:
            code = f.read()
        
        lines = len(code.splitlines())
        commands = code.count("CommandHandler(")
        decorators = code.count("@")
        docstrings = code.count('"""') // 2
        error_handling = code.count("try:")
        logging = code.count("logger.")
        
        self.log("✅", f"Total Lines: {lines}")
        self.log("✅", f"Commands: {commands}")
        self.log("✅", f"Decorators: {decorators}")
        self.log("✅", f"Docstrings: {docstrings}")
        self.log("✅", f"Error Handlers: {error_handling}")
        self.log("✅", f"Log Statements: {logging}")
        
        if error_handling < 10:
            self.log("⚠️", "Limited error handling")
        if logging < 20:
            self.log("⚠️", "Limited logging")
    
    def validate_database(self):
        """Validate database setup."""
        print("\n💾 VALIDATING DATABASE")
        print("-" * 50)
        
        try:
            test_data = {
                "warnings": {},
                "stats": {},
                "mutes": {}
            }
            
            test_file = "test_validation.json"
            with open(test_file, 'w') as f:
                json.dump(test_data, f, indent=4)
            
            with open(test_file, 'r') as f:
                loaded = json.load(f)
            
            Path(test_file).unlink()
            
            self.log("✅", "Database save/load - OK")
            self.log("✅", "JSON serialization - OK")
        except Exception as e:
            self.log("❌", f"Database test failed: {e}")
    
    def validate_documentation(self):
        """Validate documentation."""
        print("\n📚 VALIDATING DOCUMENTATION")
        print("-" * 50)
        
        docs = {
            "README.md": "Full documentation",
            "QUICKSTART.md": "Quick start guide",
            "FEATURES.md": "Features list",
        }
        
        for doc, desc in docs.items():
            if Path(doc).exists():
                size = Path(doc).stat().st_size
                self.log("✅", f"{doc} ({size} bytes) - {desc}")
            else:
                self.log("⚠️", f"{doc} - Optional: {desc}")
    
    def validate_setup_scripts(self):
        """Validate setup scripts."""
        print("\n🔧 VALIDATING SETUP SCRIPTS")
        print("-" * 50)
        
        scripts = {
            "setup.bat": "Windows setup",
            "setup.sh": "Linux/Mac setup",
        }
        
        for script, desc in scripts.items():
            if Path(script).exists():
                size = Path(script).stat().st_size
                self.log("✅", f"{script} ({size} bytes) - {desc}")
            else:
                self.log("⚠️", f"{script} - Optional: {desc}")
    
    def validate_environment(self):
        """Validate environment setup."""
        print("\n🌍 VALIDATING ENVIRONMENT")
        print("-" * 50)
        
        if Path(".env").exists():
            self.log("✅", ".env file exists")
        else:
            if Path(".env.example").exists():
                self.log("⚠️", "Create .env from .env.example")
            else:
                self.log("❌", ".env and .env.example not found")
        
        # Check Python version
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self.log("✅", f"Python {version.major}.{version.minor}.{version.micro}")
        else:
            self.log("❌", f"Python 3.8+ required (found {version.major}.{version.minor})")
    
    def generate_report(self):
        """Generate validation report."""
        print("\n" + "=" * 50)
        print("📊 VALIDATION REPORT")
        print("=" * 50)
        
        passed = len(self.results)
        warnings = len(self.warnings)
        errors = len(self.errors)
        
        print(f"\n✅ Passed: {passed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"❌ Errors: {errors}")
        
        if errors == 0 and warnings <= 2:
            print("\n🎉 VALIDATION SUCCESSFUL!")
            print("Bot is ready for deployment.")
            return 0
        elif errors == 0:
            print("\n⚠️ Validation complete with warnings.")
            print("Bot should work but check warnings above.")
            return 0
        else:
            print(f"\n❌ Validation failed with {errors} error(s).")
            print("Please fix errors above before running bot.")
            return 1
    
    def run_all_validations(self):
        """Run all validation tests."""
        print("\n" + "=" * 50)
        print("🥃 WHISKY_BOT ELITE - VALIDATION")
        print("=" * 50)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.validate_files()
        self.validate_python_syntax()
        self.validate_config()
        self.validate_imports()
        self.validate_code_quality()
        self.validate_database()
        self.validate_documentation()
        self.validate_setup_scripts()
        self.validate_environment()
        
        return self.generate_report()

def main():
    """Main validation entry point."""
    validator = BotValidator()
    exit_code = validator.run_all_validations()
    
    print("\n" + "=" * 50)
    print("Next steps:")
    print("1. Review any warnings above")
    print("2. Create .env file with your tokens")
    print("3. Run: python main.py")
    print("=" * 50 + "\n")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
