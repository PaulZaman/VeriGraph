"""
Test script to validate model promotion quality gates

This script tests the promotion logic without actually promoting,
useful for PR validation and testing.
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Mock environment for testing
os.environ.setdefault("DAGSHUB_REPO", "MarcoSrhl/NLP-Fact-checking")
os.environ.setdefault("DAGSHUB_USER", "test")
os.environ.setdefault("DAGSHUB_TOKEN", "test")
os.environ.setdefault("MODEL_NAME", "fact-checker-gan")

def test_quality_gate_validation():
    """Test quality gate validation logic"""
    from scripts.promote_with_quality_gate import validate_quality_gates
    
    print("Testing quality gate validation...")
    
    # Test case 1: Metrics pass quality gates
    good_metrics = {
        'test_accuracy': 0.85,
        'test_f1': 0.80,
        'test_precision': 0.82,
        'test_recall': 0.78
    }
    
    passed, failures = validate_quality_gates(good_metrics, "1")
    assert passed, f"Expected pass but got failures: {failures}"
    print("✅ Test 1 passed: Good metrics pass quality gates")
    
    # Test case 2: Low accuracy fails
    low_accuracy_metrics = {
        'test_accuracy': 0.60,  # Below 0.75 threshold
        'test_f1': 0.80
    }
    
    passed, failures = validate_quality_gates(low_accuracy_metrics, "2")
    assert not passed, "Expected failure but quality gates passed"
    assert any("Accuracy" in f for f in failures), "Expected accuracy failure"
    print("✅ Test 2 passed: Low accuracy correctly fails quality gate")
    
    # Test case 3: Low F1 fails
    low_f1_metrics = {
        'test_accuracy': 0.85,
        'test_f1': 0.50  # Below 0.70 threshold
    }
    
    passed, failures = validate_quality_gates(low_f1_metrics, "3")
    assert not passed, "Expected failure but quality gates passed"
    assert any("F1" in f for f in failures), "Expected F1 failure"
    print("✅ Test 3 passed: Low F1 correctly fails quality gate")
    
    print("\n✅ All quality gate tests passed!")

def test_model_comparison():
    """Test model comparison logic"""
    from scripts.promote_with_quality_gate import compare_models
    
    print("\nTesting model comparison...")
    
    # Test case 1: Improvements
    staging_metrics = {'test_accuracy': 0.85, 'test_f1': 0.82}
    production_metrics = {'test_accuracy': 0.80, 'test_f1': 0.78}
    
    result = compare_models(staging_metrics, production_metrics)
    assert "improvements" in result.lower() or "recommended" in result.lower()
    print("✅ Test 1 passed: Improvements detected")
    
    # Test case 2: No production model
    result = compare_models(staging_metrics, {})
    assert "no comparison" in result.lower() or "first" in result.lower()
    print("✅ Test 2 passed: First deployment handled")
    
    print("\n✅ All comparison tests passed!")

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 TESTING MODEL PROMOTION QUALITY GATES")
    print("=" * 80)
    
    try:
        test_quality_gate_validation()
        test_model_comparison()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
