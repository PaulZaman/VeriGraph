import mlflow
from mlflow.tracking import MlflowClient

DAGSHUB_REPO = "MarcoSrhl/NLP-Fact-checking"
mlflow.set_tracking_uri(f"https://dagshub.com/{DAGSHUB_REPO}.mlflow")

client = MlflowClient()
run_id = "83c07187e08644c590e3cd92358ac4a4"

print(f"Checking artifacts for run {run_id[:8]}...\n")
artifacts = client.list_artifacts(run_id)

if artifacts:
    print("Artifacts found:")
    for art in artifacts:
        print(f"  {'📂' if art.is_dir else '📄'} {art.path}")
else:
    print("❌ No artifacts found!")
