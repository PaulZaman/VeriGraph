#!/usr/bin/env python3
"""
Standalone script to test the data retrieval workflow for GAN models.

This script implements the manual workflow:
1. Connect to MLflow and find the model (staging or production)
2. Get the source run ID (mlflow_run_id)
3. Query Neon DB training_runs table where mlflow_run_id matches
4. Get the run_id from training_runs
5. Query training_data table where run_id matches

Usage:
  python test_data_workflow.py staging
  python test_data_workflow.py production
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import mlflow
    from mlflow.tracking import MlflowClient
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Install dependencies with: pip install mlflow sqlalchemy psycopg2-binary python-dotenv")
    sys.exit(1)


def setup_mlflow():
    """Configure MLflow connection to DagsHub."""
    dagshub_repo = os.getenv("DAGSHUB_REPO", "MarcoSrhl/NLP-Fact-checking")
    dagshub_user = os.getenv("DAGSHUB_USER", "MarcoSrhl")
    dagshub_token = os.getenv("DAGSHUB_TOKEN")
    
    if not dagshub_token:
        print("❌ DAGSHUB_TOKEN not set in .env file")
        sys.exit(1)
    
    # Set up authentication
    os.environ['MLFLOW_TRACKING_USERNAME'] = dagshub_user
    os.environ['MLFLOW_TRACKING_PASSWORD'] = dagshub_token
    
    # Set tracking URI
    tracking_uri = f"https://dagshub.com/{dagshub_repo}.mlflow"
    mlflow.set_tracking_uri(tracking_uri)
    
    print(f"🔗 Connected to MLflow: {tracking_uri}")
    return MlflowClient()


def get_mlflow_run_id_from_stage(client, model_name, stage):
    """
    Get the MLflow run_id for a model in a specific stage.
    
    Args:
        client: MlflowClient instance
        model_name: Name of the model (e.g., 'fact-checker-gan')
        stage: Stage of the model ('Production' or 'Staging')
    
    Returns:
        Tuple (source_run_id, version_info) or (None, None) if not found
    """
    print(f"\n🔍 Step 1: Searching for model: {model_name} (Stage: {stage})")
    
    try:
        # Search for model versions
        versions = client.search_model_versions(f"name='{model_name}'")
        
        # Filter by stage
        target_versions = [v for v in versions if v.current_stage == stage]
        
        if not target_versions:
            print(f"❌ No versions found for stage '{stage}'")
            return None, None
        
        # Get the most recent version
        version = sorted(target_versions, key=lambda v: int(v.version), reverse=True)[0]
        
        print(f"\n✅ Model found:")
        print(f"   Name: {model_name}")
        print(f"   Version: {version.version}")
        print(f"   Stage: {version.current_stage}")
        print(f"   Status: {version.status}")
        print(f"   Model Version Run ID: {version.run_id}")
        
        # Get the run to check for source_run_id
        print(f"\n🔍 Step 1b: Checking for source_run_id parameter...")
        run = client.get_run(version.run_id)
        
        # Check params for source_run_id
        source_run_id = None
        if 'source_run_id' in run.data.params:
            source_run_id = run.data.params['source_run_id']
            print(f"✅ Found source_run_id in params: {source_run_id}")
        # Also check tags
        elif 'source_run_id' in run.data.tags:
            source_run_id = run.data.tags['source_run_id']
            print(f"✅ Found source_run_id in tags: {source_run_id}")
        else:
            print(f"⚠️  No source_run_id found, using model version run_id")
            source_run_id = version.run_id
        
        print(f"   Training Run ID: {source_run_id}")
        
        return source_run_id, version
        
    except Exception as e:
        print(f"❌ Error searching MLflow: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def query_training_run(db_url, mlflow_run_id):
    """
    Query the training_runs table to find the run_id for a given mlflow_run_id.
    
    Args:
        db_url: Database connection URL
        mlflow_run_id: The MLflow run ID to search for
    
    Returns:
        run_id or None if not found
    """
    print(f"\n🔍 Step 2: Querying training_runs table for mlflow_run_id: {mlflow_run_id}")
    
    try:
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            query = text("""
                SELECT run_id, model_name, model_type, status, 
                       num_training_examples, num_validation_examples,
                       training_started_at, training_completed_at
                FROM training_runs
                WHERE mlflow_run_id = :mlflow_run_id
            """)
            
            result = conn.execute(query, {"mlflow_run_id": mlflow_run_id})
            row = result.fetchone()
            
            if row:
                print(f"\n✅ Training run found:")
                print(f"   Run ID: {row[0]}")
                print(f"   Model Name: {row[1]}")
                print(f"   Model Type: {row[2]}")
                print(f"   Status: {row[3]}")
                print(f"   Training Examples: {row[4]}")
                print(f"   Validation Examples: {row[5]}")
                print(f"   Started: {row[6]}")
                print(f"   Completed: {row[7]}")
                return row[0]
            else:
                print(f"❌ No training run found with mlflow_run_id: {mlflow_run_id}")
                return None
                
    except Exception as e:
        print(f"❌ Error querying training_runs: {e}")
        return None


def query_training_data(db_url, run_id, limit=10):
    """
    Query the training_data table for a given run_id.
    
    Args:
        db_url: Database connection URL
        run_id: The run_id to search for
        limit: Maximum number of rows to return
    
    Returns:
        List of training data rows
    """
    print(f"\n🔍 Step 3: Querying training_data table for run_id: {run_id}")
    
    try:
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # First get the count
            count_query = text("""
                SELECT COUNT(*) FROM training_data WHERE run_id = :run_id
            """)
            count_result = conn.execute(count_query, {"run_id": run_id})
            total_count = count_result.fetchone()[0]
            
            print(f"\n💾 Total training data rows: {total_count}")
            
            # Get sample data
            query = text("""
                SELECT data_id, run_id, claim, label, evidence, data_type, created_at
                FROM training_data
                WHERE run_id = :run_id
                LIMIT :limit
            """)
            
            result = conn.execute(query, {"run_id": run_id, "limit": limit})
            rows = result.fetchall()
            
            if rows:
                print(f"\n✅ Sample training data (first {len(rows)} rows):")
                print("\n" + "=" * 100)
                
                for i, row in enumerate(rows, 1):
                    print(f"\n📝 Row {i}:")
                    print(f"   Data ID: {row[0]}")
                    print(f"   Run ID: {row[1]}")
                    print(f"   Claim: {row[2][:100]}..." if len(row[2]) > 100 else f"   Claim: {row[2]}")
                    print(f"   Label: {row[3]}")
                    if row[4]:
                        evidence_preview = row[4][:100] + "..." if len(row[4]) > 100 else row[4]
                        print(f"   Evidence: {evidence_preview}")
                    print(f"   Data Type: {row[5]}")
                    print(f"   Created At: {row[6]}")
                    
                    if i < len(rows):
                        print("   " + "-" * 90)
                
                print("\n" + "=" * 100)
                
                # Get label distribution
                dist_query = text("""
                    SELECT label, COUNT(*) as count
                    FROM training_data
                    WHERE run_id = :run_id
                    GROUP BY label
                    ORDER BY count DESC
                """)
                
                dist_result = conn.execute(dist_query, {"run_id": run_id})
                dist_rows = dist_result.fetchall()
                
                print(f"\n📊 Label Distribution:")
                for label, count in dist_rows:
                    percentage = (count / total_count) * 100
                    print(f"   {label}: {count} ({percentage:.1f}%)")
                
                return rows
            else:
                print(f"❌ No training data found for run_id: {run_id}")
                return []
                
    except Exception as e:
        print(f"❌ Error querying training_data: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    """Main function to test the data workflow."""
    
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python test_data_workflow.py [staging|production]")
        sys.exit(1)
    
    stage_arg = sys.argv[1].lower()
    
    if stage_arg == "staging":
        stage = "Staging"
    elif stage_arg == "production":
        stage = "Production"
    else:
        print(f"❌ Invalid stage: {stage_arg}. Use 'staging' or 'production'")
        sys.exit(1)
    
    # Model name for GANs
    model_name = "fact-checker-gan"
    
    print("=" * 100)
    print(f"🧪 Testing Data Retrieval Workflow for {model_name} ({stage})")
    print("=" * 100)
    
    # Step 1: Get MLflow run ID
    client = setup_mlflow()
    mlflow_run_id, version = get_mlflow_run_id_from_stage(client, model_name, stage)
    
    if not mlflow_run_id:
        print("\n❌ Failed to get MLflow run ID. Exiting.")
        sys.exit(1)
    
    # Step 2: Get database URL
    db_url = os.getenv("NEON_DB_URL")
    if not db_url:
        print("\n❌ NEON_DB_URL not set in .env file")
        sys.exit(1)
    
    # Step 3: Query training_runs table
    run_id = query_training_run(db_url, mlflow_run_id)
    
    if not run_id:
        print("\n❌ Failed to find training run in database. Exiting.")
        print("\n💡 This might mean:")
        print("   1. The model was trained without logging to the Neon DB")
        print("   2. The mlflow_run_id doesn't match any records in training_runs table")
        print("   3. The database connection is incorrect")
        sys.exit(1)
    
    # Step 4: Query training_data table
    rows = query_training_data(db_url, run_id, limit=5)
    
    if rows:
        print("\n" + "=" * 100)
        print("✅ WORKFLOW SUCCESSFUL!")
        print(f"   MLflow Run ID: {mlflow_run_id}")
        print(f"   Database Run ID: {run_id}")
        print(f"   Training data retrieved successfully")
        print("=" * 100)
    else:
        print("\n❌ Workflow failed at training_data retrieval")
        sys.exit(1)


if __name__ == "__main__":
    main()
