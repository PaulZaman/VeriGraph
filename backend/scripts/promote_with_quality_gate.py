#!/usr/bin/env python3
"""
Promote MLflow model from Staging to Production with Quality Gates

This script:
1. Validates model exists in Staging
2. Runs quality checks (metrics validation)
3. Compares Staging vs current Production metrics
4. Promotes if quality gates pass
5. Logs detailed promotion information
"""

import os
import sys
import json
from datetime import datetime
import mlflow
from mlflow.tracking import MlflowClient
import dagshub

# Configuration
DAGSHUB_REPO = os.getenv("DAGSHUB_REPO", "MarcoSrhl/NLP-Fact-checking")
MODEL_NAME = os.getenv("MODEL_NAME", "fact-checker-gan")  # or fact-checker-bert
DAGSHUB_USER = os.getenv("DAGSHUB_USER")
DAGSHUB_TOKEN = os.getenv("DAGSHUB_TOKEN")

# Quality gate thresholds
MIN_ACCURACY = float(os.getenv("MIN_ACCURACY", "0.75"))  # Minimum 75% accuracy
MIN_F1_SCORE = float(os.getenv("MIN_F1_SCORE", "0.70"))  # Minimum 70% F1

# Initialize DagHub
def setup_mlflow():
    """Setup MLflow tracking with DagHub authentication"""
    print("\n" + "=" * 80)
    print("🔧 MLFLOW SETUP")
    print("=" * 80)
    
    if not DAGSHUB_USER or not DAGSHUB_TOKEN:
        print("❌ Error: DAGSHUB_USER and DAGSHUB_TOKEN must be set")
        sys.exit(1)
    
    print(f"📍 Repository: {DAGSHUB_REPO}")
    print(f"👤 User: {DAGSHUB_USER}")
    
    # Initialize DagHub
    repo_owner, repo_name = DAGSHUB_REPO.split('/')
    dagshub.init(repo_name=repo_name, repo_owner=repo_owner, mlflow=True)
    
    # Set authentication
    tracking_uri = f"https://dagshub.com/{DAGSHUB_REPO}.mlflow"
    os.environ["MLFLOW_TRACKING_URI"] = tracking_uri
    os.environ["MLFLOW_TRACKING_USERNAME"] = DAGSHUB_USER
    os.environ["MLFLOW_TRACKING_PASSWORD"] = DAGSHUB_TOKEN
    mlflow.set_tracking_uri(tracking_uri)
    
    print(f"✅ MLflow tracking configured")
    print(f"🔗 URI: {tracking_uri}")
    
    return MlflowClient()

def get_model_metrics(client: MlflowClient, model_version) -> dict:
    """Extract metrics from a model version's run"""
    try:
        run_id = model_version.run_id
        run = client.get_run(run_id)
        metrics = run.data.metrics
        
        print(f"\n📊 Metrics for version {model_version.version}:")
        for key, value in sorted(metrics.items()):
            print(f"   • {key}: {value:.4f}")
        
        return metrics
    except Exception as e:
        print(f"⚠️  Warning: Could not fetch metrics: {e}")
        return {}

def validate_quality_gates(metrics: dict, version_number: str) -> tuple[bool, list]:
    """Check if model meets quality gate requirements"""
    print("\n" + "=" * 80)
    print("🚦 QUALITY GATE VALIDATION")
    print("=" * 80)
    
    passed = True
    failures = []
    
    # Check accuracy
    accuracy = metrics.get('test_accuracy', metrics.get('accuracy', None))
    if accuracy is not None:
        if accuracy >= MIN_ACCURACY:
            print(f"✅ Accuracy: {accuracy:.4f} (>= {MIN_ACCURACY})")
        else:
            print(f"❌ Accuracy: {accuracy:.4f} (< {MIN_ACCURACY})")
            passed = False
            failures.append(f"Accuracy {accuracy:.4f} below threshold {MIN_ACCURACY}")
    else:
        print(f"⚠️  Warning: Accuracy metric not found")
    
    # Check F1 score
    f1_score = metrics.get('test_f1', metrics.get('f1_score', metrics.get('f1', None)))
    if f1_score is not None:
        if f1_score >= MIN_F1_SCORE:
            print(f"✅ F1 Score: {f1_score:.4f} (>= {MIN_F1_SCORE})")
        else:
            print(f"❌ F1 Score: {f1_score:.4f} (< {MIN_F1_SCORE})")
            passed = False
            failures.append(f"F1 Score {f1_score:.4f} below threshold {MIN_F1_SCORE}")
    else:
        print(f"⚠️  Warning: F1 score metric not found")
    
    # Additional metrics info
    precision = metrics.get('test_precision', metrics.get('precision', None))
    recall = metrics.get('test_recall', metrics.get('recall', None))
    
    if precision is not None:
        print(f"ℹ️  Precision: {precision:.4f}")
    if recall is not None:
        print(f"ℹ️  Recall: {recall:.4f}")
    
    return passed, failures

def compare_models(staging_metrics: dict, production_metrics: dict) -> str:
    """Compare Staging vs Production metrics and provide recommendation"""
    print("\n" + "=" * 80)
    print("⚖️  MODEL COMPARISON")
    print("=" * 80)
    
    if not production_metrics:
        print("ℹ️  No Production model to compare against")
        return "No comparison (first production deployment)"
    
    improvements = []
    regressions = []
    
    # Compare key metrics
    metric_keys = ['test_accuracy', 'accuracy', 'test_f1', 'f1_score', 'f1']
    
    for key in metric_keys:
        staging_val = staging_metrics.get(key)
        prod_val = production_metrics.get(key)
        
        if staging_val is not None and prod_val is not None:
            diff = staging_val - prod_val
            diff_pct = (diff / prod_val * 100) if prod_val != 0 else 0
            
            metric_display = key.replace('test_', '').replace('_', ' ').title()
            
            if diff > 0:
                print(f"📈 {metric_display}: {staging_val:.4f} vs {prod_val:.4f} (+{diff_pct:+.2f}%)")
                improvements.append(metric_display)
            elif diff < 0:
                print(f"📉 {metric_display}: {staging_val:.4f} vs {prod_val:.4f} ({diff_pct:+.2f}%)")
                regressions.append(metric_display)
            else:
                print(f"➡️  {metric_display}: {staging_val:.4f} (unchanged)")
    
    if improvements and not regressions:
        return f"🎯 Recommended: Model shows improvements in {', '.join(improvements)}"
    elif regressions:
        return f"⚠️  Warning: Model has regressions in {', '.join(regressions)}"
    else:
        return "➡️  Model metrics unchanged"

def promote_model(client: MlflowClient):
    """Execute model promotion with quality gates"""
    print("\n" + "=" * 80)
    print("🔍 MODEL DISCOVERY")
    print("=" * 80)
    print(f"📦 Model name: {MODEL_NAME}")
    
    # Get Staging model
    print("\n🔎 Searching for Staging model...")
    staging_versions = client.get_latest_versions(MODEL_NAME, stages=["Staging"])
    
    if not staging_versions:
        print(f"❌ No model found in Staging stage for '{MODEL_NAME}'")
        print("   Cannot promote - no candidate model available")
        sys.exit(1)
    
    staging_version = staging_versions[0]
    print(f"✅ Found Staging model:")
    print(f"   • Version: {staging_version.version}")
    print(f"   • Run ID: {staging_version.run_id}")
    print(f"   • Created: {staging_version.creation_timestamp}")
    
    # Get Production model (if exists)
    production_versions = client.get_latest_versions(MODEL_NAME, stages=["Production"])
    production_version = production_versions[0] if production_versions else None
    
    if production_version:
        print(f"\n📦 Current Production model:")
        print(f"   • Version: {production_version.version}")
        print(f"   • Run ID: {production_version.run_id}")
    else:
        print("\nℹ️  No existing Production model found (first deployment)")
    
    # Check if Staging is already in Production
    if production_version and staging_version.version == production_version.version:
        print(f"\n✅ Version {staging_version.version} is already in Production")
        print("   No promotion needed - exiting successfully")
        return
    
    # Get metrics
    staging_metrics = get_model_metrics(client, staging_version)
    production_metrics = get_model_metrics(client, production_version) if production_version else {}
    
    # Quality gates
    passed, failures = validate_quality_gates(staging_metrics, staging_version.version)
    
    if not passed:
        print("\n" + "=" * 80)
        print("🚫 QUALITY GATE FAILED")
        print("=" * 80)
        for failure in failures:
            print(f"   ❌ {failure}")
        print("\n⛔ Promotion blocked - quality requirements not met")
        sys.exit(1)
    
    print(f"\n✅ Quality gates passed for version {staging_version.version}")
    
    # Model comparison
    comparison = compare_models(staging_metrics, production_metrics)
    print(f"\n{comparison}")
    
    # Promote to Production
    print("\n" + "=" * 80)
    print("🚀 PROMOTING TO PRODUCTION")
    print("=" * 80)
    
    try:
        print(f"📤 Promoting version {staging_version.version} to Production stage...")
        
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=staging_version.version,
            stage="Production",
            archive_existing_versions=True  # Archive old production versions
        )
        
        print("\n" + "=" * 80)
        print("✅ PROMOTION SUCCESSFUL")
        print("=" * 80)
        print(f"🎉 Model version {staging_version.version} is now in Production!")
        print(f"📦 Model: {MODEL_NAME}")
        print(f"🔖 Version: {staging_version.version}")
        print(f"🆔 Run ID: {staging_version.run_id}")
        print(f"📅 Promoted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"🔗 DagHub: https://dagshub.com/{DAGSHUB_REPO}")
        
        if production_version:
            print(f"\n📁 Previous Production version {production_version.version} archived")
        
        # Create summary for CI
        summary = {
            "status": "success",
            "model_name": MODEL_NAME,
            "promoted_version": staging_version.version,
            "run_id": staging_version.run_id,
            "previous_version": production_version.version if production_version else None,
            "quality_gates_passed": True,
            "metrics": {
                "accuracy": staging_metrics.get('test_accuracy', staging_metrics.get('accuracy')),
                "f1_score": staging_metrics.get('test_f1', staging_metrics.get('f1_score')),
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Write summary to file for CI consumption
        summary_file = os.getenv("GITHUB_STEP_SUMMARY", None)
        if summary_file:
            with open(summary_file, 'a') as f:
                f.write("\n### 🎯 Model Promotion\n\n")
                f.write(f"- **Model:** {MODEL_NAME}\n")
                f.write(f"- **Version:** {staging_version.version}\n")
                f.write(f"- **Status:** ✅ Promoted to Production\n")
                f.write(f"- **Quality Gates:** ✅ Passed\n")
                if staging_metrics.get('test_accuracy') or staging_metrics.get('accuracy'):
                    acc = staging_metrics.get('test_accuracy', staging_metrics.get('accuracy'))
                    f.write(f"- **Accuracy:** {acc:.4f}\n")
                if staging_metrics.get('test_f1') or staging_metrics.get('f1_score'):
                    f1 = staging_metrics.get('test_f1', staging_metrics.get('f1_score'))
                    f.write(f"- **F1 Score:** {f1:.4f}\n")
        
        # Print JSON summary for CI/CD parsing
        print("\n📋 JSON Summary:")
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ PROMOTION FAILED")
        print("=" * 80)
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("🎯 MODEL PROMOTION WITH QUALITY GATES")
    print("=" * 80)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"📦 Model: {MODEL_NAME}")
    print(f"🚦 Quality Thresholds:")
    print(f"   • Min Accuracy: {MIN_ACCURACY}")
    print(f"   • Min F1 Score: {MIN_F1_SCORE}")
    
    try:
        client = setup_mlflow()
        promote_model(client)
        
        print("\n" + "=" * 80)
        print("✅ PROCESS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
