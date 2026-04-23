"""
Verification script to test backend setup
Run with: python verify_setup.py
"""
import sys
import importlib


def verify_imports():
    """Verify all required imports work"""
    print("Verifying imports...")
    
    required_modules = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "pydantic_settings",
        "echr_extractor",
        "pandas",
        "dotenv",
    ]
    
    missing = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module} - {e}")
            missing.append(module)
    
    return len(missing) == 0


def verify_local_modules():
    """Verify local module imports"""
    print("\nVerifying local modules...")
    
    modules_to_check = [
        ("config", "Settings configuration"),
        ("models", "Pydantic models"),
        ("database", "Database models"),
        ("echr_service", "ECHR service"),
        ("main", "FastAPI app"),
    ]
    
    failed = []
    
    for module_name, description in modules_to_check:
        try:
            importlib.import_module(module_name)
            print(f"  ✓ {module_name}: {description}")
        except Exception as e:
            print(f"  ✗ {module_name}: {description} - {e}")
            failed.append((module_name, str(e)))
    
    return len(failed) == 0, failed


def verify_routers():
    """Verify router modules"""
    print("\nVerifying routers...")
    
    routers = ["extraction", "cases", "statistics", "health"]
    failed = []
    
    for router_name in routers:
        try:
            importlib.import_module(f"routers.{router_name}")
            print(f"  ✓ routers.{router_name}")
        except Exception as e:
            print(f"  ✗ routers.{router_name} - {e}")
            failed.append((router_name, str(e)))
    
    return len(failed) == 0, failed


def main():
    """Run all verifications"""
    print("=" * 60)
    print("ECHR Dashboard Backend - Setup Verification")
    print("=" * 60)
    
    # Check imports
    imports_ok = verify_imports()
    
    # Check local modules
    local_ok, local_errors = verify_local_modules()
    
    # Check routers
    routers_ok, router_errors = verify_routers()
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_ok = imports_ok and local_ok and routers_ok
    
    print(f"External Dependencies: {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"Local Modules:        {'✓ PASS' if local_ok else '✗ FAIL'}")
    print(f"Router Modules:       {'✓ PASS' if routers_ok else '✗ FAIL'}")
    
    if all_ok:
        print("\n✓ All verifications passed!")
        print("\nTo start the API, run:")
        print("  python main.py")
        print("\nAPI Documentation will be available at:")
        print("  http://localhost:8000/docs")
        return 0
    else:
        print("\n✗ Some verifications failed.")
        if local_errors:
            print("\nLocal module errors:")
            for module, error in local_errors:
                print(f"  - {module}: {error}")
        if router_errors:
            print("\nRouter errors:")
            for router, error in router_errors:
                print(f"  - {router}: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
