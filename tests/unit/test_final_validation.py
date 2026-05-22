"""Final validation test before sale."""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_all_components():
    """Test all components for final validation."""
    print("=" * 70)
    print("FINAL VALIDATION TEST - SALE READINESS")
    print("=" * 70)
    
    results = []
    
    # Test 1: Dashboard Buttons
    print("\n[1/6] Testing Dashboard Buttons...")
    try:
        from test_dashboard_buttons import test_database_operations, test_button_functionality, test_external_dependencies
        db_ok = test_database_operations()
        btn_ok = test_button_functionality()
        ext_ok = test_external_dependencies()
        dashboard_ok = db_ok and btn_ok and ext_ok
        results.append(("Dashboard Buttons", dashboard_ok))
        print(f"{'✅' if dashboard_ok else '❌'} Dashboard Buttons: {'PASS' if dashboard_ok else 'FAIL'}")
    except Exception as e:
        print(f"❌ Dashboard Buttons: FAIL - {e}")
        results.append(("Dashboard Buttons", False))
    
    # Test 2: Monitoring
    print("\n[2/6] Testing Monitoring System...")
    try:
        from test_monitoring import test_health_checks, test_metrics_collection, test_monitoring_dashboard_views, test_prometheus_endpoint
        health_ok = test_health_checks()
        metrics_ok = test_metrics_collection()
        views_ok = test_monitoring_dashboard_views()
        prom_ok = test_prometheus_endpoint()
        monitoring_ok = health_ok and metrics_ok and views_ok and prom_ok
        results.append(("Monitoring System", monitoring_ok))
        print(f"{'✅' if monitoring_ok else '❌'} Monitoring System: {'PASS' if monitoring_ok else 'FAIL'}")
    except Exception as e:
        print(f"❌ Monitoring System: FAIL - {e}")
        results.append(("Monitoring System", False))
    
    # Test 3: API Endpoints
    print("\n[3/6] Testing API Endpoints...")
    try:
        import requests
        # Test health
        resp = requests.get("http://localhost:8000/api/v1/health/", timeout=5)
        health_ok = resp.status_code == 200
        # Test valuation
        payload = {"preco_pedido": 250000, "area_util_m2": 80, "quartos": 2, "casas_banho": 1, "concelho": "Porto"}
        resp = requests.post("http://localhost:8000/api/v1/valuation/", json=payload, timeout=5)
        val_ok = resp.status_code == 200
        # Test scoring
        resp = requests.post("http://localhost:8000/api/v1/scoring/", json=payload, timeout=5)
        score_ok = resp.status_code == 200
        api_ok = health_ok and val_ok and score_ok
        results.append(("API Endpoints", api_ok))
        print(f"{'✅' if api_ok else '❌'} API Endpoints: {'PASS' if api_ok else 'FAIL'}")
    except Exception as e:
        print(f"❌ API Endpoints: FAIL - {e}")
        results.append(("API Endpoints", False))
    
    # Test 4: Database Operations
    print("\n[4/6] Testing Database Operations...")
    try:
        from realestate_engine.database.repository import DatabaseRepository
        repo = DatabaseRepository()
        listings = repo.get_clean_listings(limit=1)
        config = repo.get_config("test_key")
        db_ok = True
        results.append(("Database Operations", db_ok))
        print(f"✅ Database Operations: PASS")
    except Exception as e:
        print(f"❌ Database Operations: FAIL - {e}")
        results.append(("Database Operations", False))
    
    # Test 5: Documentation Files
    print("\n[5/6] Checking Documentation Files...")
    required_docs = [
        os.path.join("docs", "reports", "SALE_DOCUMENTATION.md"),
        os.path.join("docs", "reports", "QUICK_START.md"),
        os.path.join("docs", "reports", "CLOUDFLARE_TUNNEL_SETUP.md"),
        os.path.join("docs", "reports", "PRODUCTION_READINESS.md"),
        os.path.join("docs", "reports", "DEPLOYMENT_SUMMARY.md"),
        os.path.join("scripts", "start_services.bat"),
        os.path.join("scripts", "start_https.bat"),
    ]
    docs_ok = all(os.path.exists(os.path.join(project_root, doc)) for doc in required_docs)
    results.append(("Documentation Files", docs_ok))
    print(f"{'✅' if docs_ok else '❌'} Documentation Files: {'PASS' if docs_ok else 'FAIL'}")
    if not docs_ok:
        missing = [doc for doc in required_docs if not os.path.exists(os.path.join(project_root, doc))]
        print(f"  Missing: {missing}")
    
    # Test 6: Configuration Files
    print("\n[6/6] Checking Configuration Files...")
    required_configs = [
        ".env",
        ".env.example",
        os.path.join("scripts", "start_services.bat"),
        os.path.join("scripts", "start_https.bat")
    ]
    configs_ok = all(os.path.exists(os.path.join(project_root, config)) for config in required_configs)
    results.append(("Configuration Files", configs_ok))
    print(f"{'✅' if configs_ok else '❌'} Configuration Files: {'PASS' if configs_ok else 'FAIL'}")
    if not configs_ok:
        missing = [config for config in required_configs if not os.path.exists(os.path.join(project_root, config))]
        print(f"  Missing: {missing}")
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED - SYSTEM READY FOR SALE")
    else:
        print("❌ SOME VALIDATIONS FAILED - FIX BEFORE SALE")
    print("=" * 70)
    
    # Recommendations
    if all_passed:
        print("\n📋 READY FOR SALE:")
        print("  • All components tested and working")
        print("  • Documentation complete")
        print("  • Configuration files ready")
        print("  • Monitoring operational")
        print("  • API endpoints functional")
        print("\n🚀 Next Steps:")
        print("  1. Create demo video (see VIDEO_GUIDE.md)")
        print("  2. Set up HTTPS with Cloudflare Tunnel (see CLOUDFLARE_TUNNEL_SETUP.md)")
        print("  3. Prepare sales materials")
        print("  4. Define pricing and support model")
    else:
        print("\n📋 ITEMS TO FIX:")
        for name, result in results:
            if not result:
                print(f"  • {name}")
    
    return all_passed

if __name__ == "__main__":
    success = test_all_components()
    sys.exit(0 if success else 1)
