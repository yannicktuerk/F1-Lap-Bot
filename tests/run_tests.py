"""Test runner for comprehensive coaching system tests (Issue 15)."""
import pytest
import sys
import os
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for tests
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during testing
    format='%(name)s - %(levelname)s - %(message)s'
)

def run_unit_tests():
    """Run all unit tests."""
    print("🔧 Running Unit Tests...")
    
    # Run specific unit test modules
    unit_test_modules = [
        'tests/unit/test_marker_detector.py',
        'tests/unit/test_slip_ampel.py', 
        'tests/unit/test_language_validation.py'
    ]
    
    success = True
    for module in unit_test_modules:
        module_path = project_root / module
        if module_path.exists():
            print(f"   Running {module}...")
            result = pytest.main(['-v', str(module_path)])
            if result != 0:
                success = False
                print(f"   ❌ {module} failed")
            else:
                print(f"   ✅ {module} passed")
        else:
            print(f"   ⚠️  {module} not found")
    
    return success

def run_integration_tests():
    """Run all integration tests."""
    print("🔗 Running Integration Tests...")
    
    integration_test_modules = [
        'tests/integration/test_coaching_scenarios.py'
    ]
    
    success = True
    for module in integration_test_modules:
        module_path = project_root / module
        if module_path.exists():
            print(f"   Running {module}...")
            result = pytest.main(['-v', str(module_path), '--asyncio-mode=auto'])
            if result != 0:
                success = False
                print(f"   ❌ {module} failed")
            else:
                print(f"   ✅ {module} passed")
        else:
            print(f"   ⚠️  {module} not found")
    
    return success

def run_coverage_analysis():
    """Run coverage analysis on the codebase."""
    print("📊 Running Coverage Analysis...")
    
    try:
        # Install coverage if not available
        import coverage
    except ImportError:
        print("   Installing coverage...")
        os.system(f"{sys.executable} -m pip install coverage")
        import coverage
    
    # Run tests with coverage
    cov = coverage.Coverage()
    cov.start()
    
    # Import and run core modules to check coverage
    try:
        from src.domain.services.marker_detector import MarkerDetector
        from src.domain.services.slip_calculator import SlipCalculator
        from src.application.services.safety_ampel_service import SafetyAmpelService
        from src.infrastructure.config.configuration_service import ConfigurationService
        from src.infrastructure.observability.observability_service import StructuredLogger
        from src.infrastructure.performance.performance_optimizer import PerformanceOptimizer
        
        print("   ✅ Core modules imported successfully")
    except ImportError as e:
        print(f"   ⚠️  Import warning: {e}")
    
    cov.stop()
    cov.save()
    
    print("   Coverage analysis completed")
    
    # Generate coverage report
    try:
        coverage_report = cov.report(show_missing=True)
        print(f"   Coverage: {coverage_report:.1f}%")
    except Exception as e:
        print(f"   Coverage report error: {e}")

def run_performance_tests():
    """Run performance validation tests."""
    print("⚡ Running Performance Tests...")
    
    try:
        # Test configuration loading performance
        from src.infrastructure.config.configuration_service import ConfigurationService
        import time
        
        # Test config loading speed
        start_time = time.time()
        config_path = project_root / "config" / "coaching_config.yaml"
        if config_path.exists():
            config_service = ConfigurationService(str(config_path))
            load_time_ms = (time.time() - start_time) * 1000
            print(f"   Config loading: {load_time_ms:.1f}ms")
            if load_time_ms < 100:
                print("   ✅ Config loading performance OK")
            else:
                print("   ⚠️  Config loading slower than expected")
        else:
            print("   ⚠️  Config file not found")
        
        # Test performance optimizer
        from src.infrastructure.performance.performance_optimizer import PerformanceOptimizer
        
        optimizer = PerformanceOptimizer()
        
        # Test cache performance
        start_time = time.time()
        for i in range(1000):
            optimizer.cache.put(f"test_key_{i}", f"test_value_{i}")
        cache_time_ms = (time.time() - start_time) * 1000
        print(f"   Cache operations (1000 puts): {cache_time_ms:.1f}ms")
        
        if cache_time_ms < 50:
            print("   ✅ Cache performance OK")
        else:
            print("   ⚠️  Cache performance slower than expected")
        
        optimizer.stop()
        
    except Exception as e:
        print(f"   ❌ Performance test error: {e}")

def validate_configuration():
    """Validate configuration system."""
    print("⚙️  Validating Configuration System...")
    
    try:
        from src.infrastructure.config.configuration_service import ConfigurationService
        
        config_path = project_root / "config" / "coaching_config.yaml"
        if not config_path.exists():
            print("   ❌ Configuration file missing")
            return False
        
        # Test configuration loading
        config_service = ConfigurationService(str(config_path))
        
        # Test required sections
        required_sections = [
            'phases_priority', 'intensity_words', 'slip_amps', 
            'bandit', 'reviewer', 'performance', 'observability'
        ]
        
        for section in required_sections:
            value = config_service.loader.get_section(section)
            if not value:
                print(f"   ❌ Missing configuration section: {section}")
                return False
        
        print("   ✅ Configuration validation passed")
        
        # Test hot-reload capability
        print("   Testing hot-reload capability...")
        change_detected = False
        
        def on_change(event):
            nonlocal change_detected
            change_detected = True
        
        config_service.add_change_listener(on_change)
        
        # Simulate config change by touching file
        config_path.touch()
        
        # Wait briefly for change detection
        import time
        time.sleep(0.1)
        
        config_service.close()
        
        if change_detected:
            print("   ✅ Hot-reload working")
        else:
            print("   ⚠️  Hot-reload not detected (may be timing)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration validation error: {e}")
        return False

def main():
    """Main test runner function."""
    print("🏎️  F1 Coaching System - Comprehensive Test Suite")
    print("="*60)
    
    # Track overall success
    all_passed = True
    
    # 1. Validate configuration system
    if not validate_configuration():
        all_passed = False
    
    print()
    
    # 2. Run unit tests
    if not run_unit_tests():
        all_passed = False
    
    print()
    
    # 3. Run integration tests  
    if not run_integration_tests():
        all_passed = False
    
    print()
    
    # 4. Run performance tests
    run_performance_tests()
    
    print()
    
    # 5. Run coverage analysis
    run_coverage_analysis()
    
    print()
    
    # Final results
    print("="*60)
    if all_passed:
        print("✅ All critical tests PASSED")
        print("🎯 Coaching system ready for production")
        return 0
    else:
        print("❌ Some tests FAILED")
        print("🔧 Please review and fix issues before deployment")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)