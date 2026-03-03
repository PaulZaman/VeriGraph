#!/usr/bin/env python3
"""
Test model promotion locally

Run this to test the promotion workflow:
1. Lists all model versions and their stages
2. Shows Staging model metrics
3. Shows Production model (if exists)
4. Prompts for promotion
5. Archives old Production version if promotion proceeds
"""

import os
import sys
import mlflow
from mlflow.tracking import MlflowClient
from datetime import datetime

# Configuration
DAGSHUB_REPO = "MarcoSrhl/NLP-Fact-checking"
MODEL_NAME = "fact-checker-gan"  # Change to "fact-checker-bert" to test BERT model

def setup_mlflow_direct():
    """Setup MLflow without dagshub.init() for local testing"""
    print("\n" + "="*80)
    print("🔧 MLFLOW SETUP (Local Test)")
    print("="*80)
    
    # Get credentials
    dagshub_user = os.getenv("DAGSHUB_USER")
    dagshub_token = os.getenv("DAGSHUB_TOKEN")
    
    if not dagshub_user or not dagshub_token:
        print("Enter your DagHub credentials (get token from: https://dagshub.com/user/settings/tokens)")
        dagshub_user = input("DagHub username: ").strip()
        dagshub_token = input("DagHub token: ").strip()
        
        if not dagshub_user or not dagshub_token:
            print("❌ Error: Credentials required")
            sys.exit(1)
    
    # Setup MLflow directly
    tracking_uri = f"https://dagshub.com/{DAGSHUB_REPO}.mlflow"
    os.environ["MLFLOW_TRACKING_URI"] = tracking_uri
    os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_user
    os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token
    mlflow.set_tracking_uri(tracking_uri)
    
    print(f"✅ MLflow tracking configured")
    print(f"📍 Repository: {DAGSHUB_REPO}")
    print(f"🔗 URI: {tracking_uri}")
    print(f"📦 Model: {MODEL_NAME}")
    
    return MlflowClient()

def list_all_versions(client: MlflowClient):
    """List all model versions and their stages"""
    print("\n" + "="*80)
    print("📋 ALL MODEL VERSIONS")
    print("="*80)
    
    try:
        all_versions = client.search_model_versions(f"name='{MODEL_NAME}'")
        
        if not all_versions:
            print(f"❌ No versions found for model '{MODEL_NAME}'")
            return
        
        # Group by stage
        by_stage = {}
        for v in all_versions:
            stage = v.current_stage
            if stage not in by_stage:
                by_stage[stage] = []
            by_stage[stage].append(v)
        
        # Display by stage
        for stage in ["Production", "Staging", "Archived", "None"]:
            if stage in by_stage:
                print(f"\n{stage.upper()}:")
                for v in sorted(by_stage[stage], key=lambda x: x.version, reverse=True):
                    print(f"  • Version {v.version} | Run: {v.run_id[:8]}... | Created: {datetime.fromtimestamp(v.creation_timestamp/1000)}")
        
    except Exception as e:
        print(f"❌ Error listing versions: {e}")

def show_model_metrics(client: MlflowClient, version):
    """Display model metrics"""
    try:
        run = client.get_run(version.run_id)
        metrics = run.data.metrics
        
        if metrics:
            print(f"\n  📊 Metrics:")
            for key in ['test_accuracy', 'accuracy', 'test_f1', 'f1_score', 'test_precision', 'precision', 'test_recall', 'recall']:
                if key in metrics:
                    print(f"     • {key}: {metrics[key]:.4f}")
        else:
            print("  ⚠️  No metrics found")
            
        return metrics
    except Exception as e:
        print(f"  ⚠️  Could not fetch metrics: {e}")
        return {}

def promote_staging_to_production(client: MlflowClient):
    """Main promotion logic"""
    print("\n" + "="*80)
    print("🚀 PROMOTION WORKFLOW")
    print("="*80)
    
    # Get Staging model
    print("\n🔎 Checking Staging model...")
    staging_versions = client.get_latest_versions(MODEL_NAME, stages=["Staging"])
    
    if not staging_versions:
        print(f"❌ No model in Staging stage")
        return
    
    staging_version = staging_versions[0]
    print(f"\n✅ Found Staging model:")
    print(f"   Version: {staging_version.version}")
    print(f"   Run ID: {staging_version.run_id}")
    staging_metrics = show_model_metrics(client, staging_version)
    
    # Get Production model
    print("\n🔎 Checking Production model...")
    production_versions = client.get_latest_versions(MODEL_NAME, stages=["Production"])
    
    if production_versions:
        production_version = production_versions[0]
        print(f"\n📦 Current Production model:")
        print(f"   Version: {production_version.version}")
        print(f"   Run ID: {production_version.run_id}")
        production_metrics = show_model_metrics(client, production_version)
        
        # Check if same version
        if staging_version.version == production_version.version:
            print(f"\n✅ Staging version {staging_version.version} is already in Production")
            print("   No promotion needed")
            return
    else:
        print("\nℹ️  No Production model exists (first deployment)")
        production_version = None
    
    # Prompt for promotion
    print("\n" + "="*80)
    print("🎯 PROMOTION ACTION")
    print("="*80)
    print(f"Ready to promote version {staging_version.version} to Production")
    
    if production_version:
        print(f"⚠️  This will archive the current Production version {production_version.version}")
    
    response = input("\nProceed with promotion? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Promotion cancelled")
        return
    
    # Execute promotion
    print(f"\n📤 Promoting version {staging_version.version} to Production...")
    
    try:
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=staging_version.version,
            stage="Production",
            archive_existing_versions=True  # This archives old production versions
        )
        
        print("\n" + "="*80)
        print("✅ PROMOTION SUCCESSFUL")
        print("="*80)
        print(f"🎉 Version {staging_version.version} is now in Production!")
        
        if production_version:
            print(f"📁 Previous Production version {production_version.version} has been archived")
        
        print(f"\n🔗 View on DagHub: https://dagshub.com/{DAGSHUB_REPO}")
        
    except Exception as e:
        print(f"\n❌ Promotion failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main execution"""
    print("\n" + "="*80)
    print("🧪 LOCAL MODEL PROMOTION TEST")
    print("="*80)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        client = setup_mlflow_direct()
        list_all_versions(client)
        promote_staging_to_production(client)
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
