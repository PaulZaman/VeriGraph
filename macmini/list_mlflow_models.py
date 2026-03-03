#!/usr/bin/env python3
"""
Script simple pour lister les modèles et runs disponibles sur MLflow.

Usage:
  python list_mlflow_models.py
"""

import os
import sys
from pathlib import Path

try:
    import dagshub
    import mlflow
    from mlflow.tracking import MlflowClient
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Installez les dépendances avec: pip install mlflow dagshub")
    sys.exit(1)


def setup_mlflow():
    """Configure la connexion à MLflow via DagsHub."""
    # Configuration DagsHub
    dagshub_repo = "MarcoSrhl/NLP-Fact-checking"
    
    print(f"🔗 Connexion à DagsHub: {dagshub_repo}")
    dagshub.init(repo_name=dagshub_repo.split('/')[1], 
                 repo_owner=dagshub_repo.split('/')[0], 
                 mlflow=True)
    
    return MlflowClient()


def list_experiments(client):
    """Liste tous les experiments disponibles."""
    print("\n" + "=" * 80)
    print("📊 EXPERIMENTS DISPONIBLES")
    print("=" * 80)
    
    experiments = client.search_experiments()
    
    for exp in experiments:
        print(f"\n🔬 Experiment: {exp.name}")
        print(f"   ID: {exp.experiment_id}")
        print(f"   Lifecycle: {exp.lifecycle_stage}")
        if exp.tags:
            print(f"   Tags: {exp.tags}")


def list_runs(client, experiment_id=None, max_results=10):
    """Liste les runs disponibles."""
    print("\n" + "=" * 80)
    print("🏃 RUNS MLFLOW")
    print("=" * 80)
    
    # Rechercher tous les runs ou ceux d'un experiment spécifique
    if experiment_id:
        runs = client.search_runs(
            experiment_ids=[experiment_id],
            max_results=max_results,
            order_by=["start_time DESC"]
        )
    else:
        # Obtenir tous les experiments
        experiments = client.search_experiments()
        exp_ids = [exp.experiment_id for exp in experiments if exp.lifecycle_stage == "active"]
        runs = client.search_runs(
            experiment_ids=exp_ids,
            max_results=max_results,
            order_by=["start_time DESC"]
        )
    
    if not runs:
        print("⚠️  Aucun run trouvé")
        return
    
    for i, run in enumerate(runs, 1):
        print(f"\n{'─' * 80}")
        print(f"Run #{i}: {run.info.run_name or run.info.run_id}")
        print(f"  ID: {run.info.run_id}")
        print(f"  Status: {run.info.status}")
        print(f"  Experiment ID: {run.info.experiment_id}")
        
        # Afficher les paramètres
        if run.data.params:
            print(f"  📝 Paramètres:")
            for key, value in sorted(run.data.params.items()):
                print(f"     • {key}: {value}")
        
        # Afficher les métriques
        if run.data.metrics:
            print(f"  📈 Métriques:")
            for key, value in sorted(run.data.metrics.items()):
                print(f"     • {key}: {value:.4f}")
        
        # Afficher les artefacts
        artifacts = client.list_artifacts(run.info.run_id)
        if artifacts:
            print(f"  📦 Artefacts:")
            for artifact in artifacts:
                print(f"     • {artifact.path} ({artifact.file_size} bytes)")


def list_registered_models(client, filter_name=None):
    """Liste les modèles enregistrés dans le Model Registry."""
    print("\n" + "=" * 80)
    if filter_name:
        print(f"📚 MODÈLE: {filter_name}")
    else:
        print("📚 MODÈLES ENREGISTRÉS (MODEL REGISTRY)")
    print("=" * 80)
    
    try:
        if filter_name:
            # Filtrer sur un modèle spécifique
            models = [client.get_registered_model(filter_name)]
        else:
            models = client.search_registered_models()
        
        if not models:
            print("⚠️  Aucun modèle enregistré trouvé")
            return
        
        for model in models:
            print(f"\n🤖 Modèle: {model.name}")
            print(f"   Description: {model.description or 'N/A'}")
            
            # Lister les versions du modèle
            versions = client.search_model_versions(f"name='{model.name}'")
            if versions:
                print(f"\n   📌 Versions ({len(versions)}):")
                
                # Organiser par stage
                stages = {}
                for version in versions:
                    stage = version.current_stage or "None"
                    if stage not in stages:
                        stages[stage] = []
                    stages[stage].append(version)
                
                # Afficher par stage (Production, Staging, Archived, None)
                stage_order = ["Production", "Staging", "Archived", "None"]
                for stage in stage_order:
                    if stage in stages:
                        print(f"\n      🏷️  Stage: {stage}")
                        for version in sorted(stages[stage], key=lambda v: int(v.version), reverse=True):
                            print(f"         • Version {version.version}")
                            print(f"           Status: {version.status}")
                            if version.run_id:
                                print(f"           Run ID: {version.run_id}")
                                # Récupérer les métriques du run
                                try:
                                    run = client.get_run(version.run_id)
                                    if run.data.metrics:
                                        metrics_str = ", ".join([f"{k}={v:.4f}" for k, v in sorted(run.data.metrics.items())])
                                        print(f"           Métriques: {metrics_str}")
                                except:
                                    pass
                            if version.description:
                                print(f"           Description: {version.description}")
    except Exception as e:
        print(f"⚠️  Erreur lors de la récupération des modèles: {e}")
        print("   (Le Model Registry n'est peut-être pas activé)")


def search_gan_models(client):
    """Recherche spécifiquement les modèles GAN."""
    print("\n" + "=" * 80)
    print("🎯 RECHERCHE DES MODÈLES GAN")
    print("=" * 80)
    
    # Rechercher les runs avec "gan" dans le nom
    experiments = client.search_experiments()
    exp_ids = [exp.experiment_id for exp in experiments if exp.lifecycle_stage == "active"]
    
    runs = client.search_runs(
        experiment_ids=exp_ids,
        filter_string="",
        max_results=50,
        order_by=["start_time DESC"]
    )
    
    gan_runs = [run for run in runs if run.info.run_name and 'gan' in run.info.run_name.lower()]
    
    if not gan_runs:
        print("⚠️  Aucun run GAN trouvé")
        return
    
    print(f"\n✅ {len(gan_runs)} run(s) GAN trouvé(s):\n")
    
    for i, run in enumerate(gan_runs, 1):
        print(f"{i}. {run.info.run_name}")
        print(f"   ID: {run.info.run_id}")
        print(f"   Status: {run.info.status}")
        
        # Vérifier les artefacts
        artifacts = client.list_artifacts(run.info.run_id)
        model_artifacts = [a for a in artifacts if 'model' in a.path.lower() or 'gan' in a.path.lower()]
        if model_artifacts:
            print(f"   📦 Artefacts modèle:")
            for artifact in model_artifacts:
                print(f"      • {artifact.path}")
        print()


def download_model_by_stage(client, model_name, stage, output_base_dir="./models"):
    """
    Télécharge un modèle depuis le Model Registry selon son stage.
    
    Args:
        client: MlflowClient instance
        model_name: Nom du modèle (ex: 'fact-checker-gan')
        stage: Stage du modèle ('Production', 'Staging', 'Archived', 'None')
        output_base_dir: Dossier de base pour sauvegarder les modèles
    
    Returns:
        Chemin local du modèle téléchargé, ou None en cas d'erreur
    """
    print("\n" + "=" * 80)
    print(f"📥 TÉLÉCHARGEMENT DU MODÈLE - Stage: {stage}")
    print("=" * 80)
    
    try:
        # Rechercher les versions du modèle pour ce stage
        versions = client.search_model_versions(f"name='{model_name}'")
        
        # Filtrer par stage
        target_versions = [v for v in versions if v.current_stage == stage]
        
        if not target_versions:
            print(f"❌ Aucune version trouvée pour le stage '{stage}'")
            return None
        
        # Prendre la version la plus récente
        version = sorted(target_versions, key=lambda v: int(v.version), reverse=True)[0]
        
        print(f"\n📌 Modèle trouvé:")
        print(f"   Nom: {model_name}")
        print(f"   Version: {version.version}")
        print(f"   Stage: {version.current_stage}")
        print(f"   Status: {version.status}")
        print(f"   Run ID: {version.run_id}")
        
        # Récupérer les métriques du run
        try:
            run = client.get_run(version.run_id)
            if run.data.metrics:
                print(f"\n   📈 Métriques:")
                for key, value in sorted(run.data.metrics.items()):
                    print(f"      • {key}: {value:.4f}")
        except:
            pass
        
        # Définir le dossier de destination
        output_dir = Path(output_base_dir) / f"{model_name}_{stage.lower()}_v{version.version}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📥 Téléchargement des artefacts...")
        print(f"   Destination: {output_dir.absolute()}")
        
        # Télécharger les artefacts
        local_path = client.download_artifacts(version.run_id, "", dst_path=str(output_dir))
        
        print(f"✅ Artefacts téléchargés dans: {local_path}")
        
        # Lister les fichiers téléchargés
        downloaded_files = list(Path(local_path).rglob("*"))
        files_only = [f for f in downloaded_files if f.is_file()]
        
        if files_only:
            total_size_mb = sum(f.stat().st_size for f in files_only) / (1024 * 1024)
            print(f"\n📦 {len(files_only)} fichier(s) téléchargé(s) ({total_size_mb:.2f} MB):")
            for file in sorted(files_only):
                rel_path = file.relative_to(Path(local_path).parent)
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"   • {rel_path} ({size_mb:.2f} MB)")
        
        return str(local_path)
    
    except Exception as e:
        print(f"\n❌ Erreur lors du téléchargement: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("🔍 EXPLORATEUR DE MODÈLES MLFLOW - VeriGraph")
    print("=" * 80)
    
    try:
        # Configuration
        client = setup_mlflow()
        
        # Afficher le modèle fact-checker-gan par défaut
        print("\n📋 Affichage du modèle: fact-checker-gan")
        
        list_registered_models(client, filter_name="fact-checker-gan")
        
        # Option pour voir les runs GAN associés
        print("\n" + "=" * 80)
        show_runs = input("Voir aussi les runs GAN ? (O/n): ").strip().lower()
        if not show_runs or show_runs in ['o', 'oui', 'y', 'yes']:
            search_gan_models(client)
        
        # Option pour télécharger un modèle
        print("\n" + "=" * 80)
        download = input("Télécharger un modèle ? (O/n): ").strip().lower()
        if not download or download in ['o', 'oui', 'y', 'yes']:
            print("\n📋 Stages disponibles:")
            print("  1. Production")
            print("  2. Staging")
            print("  3. Les deux")
            
            choice = input("\nVotre choix (1-3): ").strip()
            
            if choice == "1":
                download_model_by_stage(client, "fact-checker-gan", "Production")
            elif choice == "2":
                download_model_by_stage(client, "fact-checker-gan", "Staging")
            elif choice == "3":
                download_model_by_stage(client, "fact-checker-gan", "Production")
                download_model_by_stage(client, "fact-checker-gan", "Staging")
            else:
                print(f"❌ Choix invalide: {choice}")
        
        print("\n" + "=" * 80)
        print("✅ Exploration terminée")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
