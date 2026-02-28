"""
Script to explore available models and experiments in DagHub
"""

import mlflow
import dagshub
from mlflow.tracking import MlflowClient  

# Initialize DagHub
dagshub.init(
    repo_owner="MarcoSrhl",
    repo_name="NLP-Fact-checking",
    mlflow=True
)

# Set MLflow tracking URI
mlflow.set_tracking_uri("https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow")

print("=" * 60)
print("DagHub MLflow Registry Explorer")
print("=" * 60)

# Initialize MLflow client
client = MlflowClient()

# List all registered models
print("\n📦 Registered Models:")
print("-" * 60)
try:
    models = client.search_registered_models()
    if models:
        for model in models:
            print(f"\nModel Name: {model.name}")
            print(f"Description: {model.description}")
            print(f"Tags: {model.tags}")
            
            # Get latest versions
            try:
                versions = client.search_model_versions(f"name='{model.name}'")
                if versions:
                    print(f"Available Versions:")
                    for version in versions[:5]:  # Show first 5 versions
                        print(f"  - Version {version.version}: Stage={version.current_stage}")
            except Exception as e:
                print(f"  Could not fetch versions: {e}")
    else:
        print("No registered models found.")
        print("\n💡 Tip: Models need to be registered in MLflow first.")
        print("   Check your experiments and runs below.")
except Exception as e:
    print(f"Error listing models: {e}")

# List experiments
print("\n\n🧪 Experiments:")
print("-" * 60)
try:
    experiments = client.search_experiments()
    for exp in experiments[:10]:  # Show first 10 experiments
        print(f"\nExperiment: {exp.name} (ID: {exp.experiment_id})")
        print(f"Lifecycle Stage: {exp.lifecycle_stage}")
        
        # Get some runs from this experiment
        try:
            runs = client.search_runs(
                experiment_ids=[exp.experiment_id],
                max_results=3
            )
            if runs:
                print(f"Recent Runs ({len(runs)} shown):")
                for run in runs:
                    print(f"  - Run ID: {run.info.run_id}")
                    print(f"    Status: {run.info.status}")
                    if run.data.metrics:
                        print(f"    Metrics: {list(run.data.metrics.keys())}")
        except Exception as e:
            print(f"  Could not fetch runs: {e}")
            
except Exception as e:
    print(f"Error listing experiments: {e}")

print("\n" + "=" * 60)
print("\n💡 Next Steps:")
print("-" * 60)
print("1. If no models are registered:")
print("   - Train a model and log it with mlflow.log_model()")
print("   - Register it with mlflow.register_model()")
print("\n2. If models exist:")
print("   - Update MODEL_NAME in your .env file")
print("   - Use the exact model name from above")
print("\n3. Visit the DagHub UI:")
print("   https://dagshub.com/MarcoSrhl/NLP-Fact-checking/experiments")
print("=" * 60)
