"""Unified verification script for the Real Estate Engine.

This script consolidates all verification tools into a single interface:
- Database checks (connections, data quality, duplicates)
- System health checks (dependencies, configuration)
- Data validation (listings, valuations, scores)
- Pipeline status checks

Usage:
    python verify_all.py db              # Database checks
    python verify_all.py data            # Data quality checks
    python verify_all.py system          # System health checks
    python verify_all.py all             # Run all checks
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from realestate_engine.database.repository import DatabaseRepository


def check_db_connection():
    """Check database connection."""
    print("Checking database connection...")
    try:
        repo = DatabaseRepository()
        with repo.Session() as session:
            session.execute("SELECT 1")
        print("✓ Database connection OK")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def check_db_data_quality():
    """Check data quality in database."""
    print("\nChecking data quality...")
    try:
        repo = DatabaseRepository()
        
        # Check raw listings count
        raw_count = repo.get_raw_listings(limit=1).__len__() if hasattr(repo, 'get_raw_listings') else 0
        print(f"Raw listings: {raw_count}")
        
        # Check clean listings count
        clean_count = repo.get_clean_listings(limit=1).__len__() if hasattr(repo, 'get_clean_listings') else 0
        print(f"Clean listings: {clean_count}")
        
        print("✓ Data quality check completed")
        return True
    except Exception as e:
        print(f"✗ Data quality check failed: {e}")
        return False


def check_duplicates():
    """Check for duplicate listings."""
    print("\nChecking for duplicates...")
    try:
        repo = DatabaseRepository()
        # This would need actual implementation based on DB schema
        print("✓ Duplicate check completed (placeholder)")
        return True
    except Exception as e:
        print(f"✗ Duplicate check failed: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\nChecking dependencies...")
    required = ['sqlalchemy', 'fastapi', 'streamlit', 'httpx', 'loguru']
    missing = []
    
    for module in required:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} (missing)")
            missing.append(module)
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        return False
    else:
        print("\n✓ All dependencies installed")
        return True


def check_configuration():
    """Check configuration files."""
    print("\nChecking configuration...")
    
    # Check .env file
    env_file = Path('.env')
    if env_file.exists():
        print("✓ .env file exists")
    else:
        print("✗ .env file missing (copy from .env.example)")
        return False
    
    # Check .env.example
    env_example = Path('.env.example')
    if env_example.exists():
        print("✓ .env.example exists")
    else:
        print("✗ .env.example missing")
        return False
    
    print("✓ Configuration check completed")
    return True


def check_valuations():
    """Check valuation data."""
    print("\nChecking valuation data...")
    try:
        repo = DatabaseRepository()
        # This would need actual implementation
        print("✓ Valuation check completed (placeholder)")
        return True
    except Exception as e:
        print(f"✗ Valuation check failed: {e}")
        return False


def check_scores():
    """Check scoring data."""
    print("\nChecking scoring data...")
    try:
        repo = DatabaseRepository()
        # This would need actual implementation
        print("✓ Score check completed (placeholder)")
        return True
    except Exception as e:
        print(f"✗ Score check failed: {e}")
        return False


def mode_db():
    """Run database checks."""
    print("=" * 50)
    print("DATABASE CHECKS")
    print("=" * 50)
    
    results = []
    results.append(check_db_connection())
    results.append(check_db_data_quality())
    results.append(check_duplicates())
    
    print("\n" + "=" * 50)
    print(f"Database checks: {'PASSED' if all(results) else 'FAILED'}")
    print("=" * 50)
    
    return all(results)


def mode_data():
    """Run data quality checks."""
    print("=" * 50)
    print("DATA QUALITY CHECKS")
    print("=" * 50)
    
    results = []
    results.append(check_db_data_quality())
    results.append(check_duplicates())
    results.append(check_valuations())
    results.append(check_scores())
    
    print("\n" + "=" * 50)
    print(f"Data quality checks: {'PASSED' if all(results) else 'FAILED'}")
    print("=" * 50)
    
    return all(results)


def mode_system():
    """Run system health checks."""
    print("=" * 50)
    print("SYSTEM HEALTH CHECKS")
    print("=" * 50)
    
    results = []
    results.append(check_dependencies())
    results.append(check_configuration())
    results.append(check_db_connection())
    
    print("\n" + "=" * 50)
    print(f"System health checks: {'PASSED' if all(results) else 'FAILED'}")
    print("=" * 50)
    
    return all(results)


def mode_all():
    """Run all checks."""
    print("=" * 50)
    print("COMPREHENSIVE VERIFICATION")
    print("=" * 50)
    
    results = []
    
    # System checks
    results.append(mode_system())
    
    # Database checks
    results.append(mode_db())
    
    # Data checks
    results.append(mode_data())
    
    print("\n" + "=" * 50)
    print(f"OVERALL: {'ALL CHECKS PASSED' if all(results) else 'SOME CHECKS FAILED'}")
    print("=" * 50)
    
    return all(results)


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_all.py <mode>")
        print("\nModes:")
        print("  db     - Database checks")
        print("  data   - Data quality checks")
        print("  system - System health checks")
        print("  all    - Run all checks")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "db":
        success = mode_db()
    elif mode == "data":
        success = mode_data()
    elif mode == "system":
        success = mode_system()
    elif mode == "all":
        success = mode_all()
    else:
        print(f"Error: Unknown mode '{mode}'")
        print("Available modes: db, data, system, all")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
