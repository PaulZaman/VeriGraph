#!/usr/bin/env python3
"""
Script pour télécharger les modèles GAN par stage en utilisant le run_id.

Ce script combine la recherche par stage (Production/Staging) et le téléchargement
d'artefacts qui fonctionne.

Usage:
  python download_gan_by_stage.py staging
  python download_gan_by_stage.py production
  python download_gan_by_stage.py both
"""

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
    dagshub_repo = "MarcoSrhl/NLP-Fact-checking"
    
    print(f"🔗 Connexion à DagsHub: {dagshub_repo}")
    dagshub.init(repo_name=dagshub_repo.split('/')[1], 
                 repo_owner=dagshub_repo.split('/')[0], 
                 mlflow=True)
    
    return MlflowClient()


def get_run_id_from_stage(client, model_name, stage):
    """
    Récupère le run_id d'un modèle selon son stage.
    
    Args:
        client: MlflowClient instance
        model_name: Nom du modèle (ex: 'fact-checker-gan')
        stage: Stage du modèle ('Production', 'Staging', 'Archived', 'None')
    
    Returns:
        Tuple (run_id, version_info) ou (None, None) si non trouvé
    """
    print(f"\n🔍 Recherche du modèle: {model_name} (Stage: {stage})")
    
    try:
        # Rechercher les versions du modèle pour ce stage
        versions = client.search_model_versions(f"name='{model_name}'")
        
        # Filtrer par stage
        target_versions = [v for v in versions if v.current_stage == stage]
        
        if not target_versions:
            print(f"❌ Aucune version trouvée pour le stage '{stage}'")
            return None, None
        
        # Prendre la version la plus récente
        version = sorted(target_versions, key=lambda v: int(v.version), reverse=True)[0]
        
        print(f"\n✅ Modèle trouvé:")
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
        except Exception as e:
            print(f"   ⚠️  Impossible de récupérer les métriques: {e}")
        
        return version.run_id, version
    
    except Exception as e:
        print(f"❌ Erreur lors de la recherche: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def download_artifacts_from_run(client, run_id, model_name, stage, version_num, output_base_dir="./models"):
    """
    Télécharge les artefacts d'un run MLflow.
    
    Args:
        client: MlflowClient instance
        run_id: ID du run MLflow
        model_name: Nom du modèle
        stage: Stage du modèle
        version_num: Numéro de version
        output_base_dir: Dossier de base pour sauvegarder les modèles
    
    Returns:
        Chemin local du modèle téléchargé, ou None en cas d'erreur
    """
    print("\n" + "=" * 80)
    print(f"📥 TÉLÉCHARGEMENT DES ARTEFACTS")
    print("=" * 80)
    
    try:
        # Vérifier si le run a un source_run_id (cas des runs de packaging)
        run = client.get_run(run_id)
        source_run_id = run.data.params.get('source_run_id')
        
        actual_run_id = run_id
        if source_run_id:
            print(f"\n🔗 Run de packaging détecté")
            print(f"   Run actuel: {run_id}")
            print(f"   Run source: {source_run_id}")
            print(f"   → Téléchargement depuis le run source\n")
            actual_run_id = source_run_id
        
        # Définir le dossier de destination
        output_dir = Path(output_base_dir) / f"{model_name}_{stage.lower()}_v{version_num}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📥 Téléchargement depuis le run: {actual_run_id}")
        print(f"   Destination: {output_dir.absolute()}")
        print(f"   (Cela peut prendre quelques minutes...)\n")
        
        # Télécharger les artefacts depuis le run approprié
        local_path = client.download_artifacts(actual_run_id, "", dst_path=str(output_dir))
        
        print(f"\n✅ Artefacts téléchargés dans: {local_path}")
        
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


def download_model_by_stage(client, model_name, stage, output_base_dir="./models"):
    """
    Télécharge un modèle en trouvant d'abord son run_id depuis le Model Registry.
    
    Args:
        client: MlflowClient instance
        model_name: Nom du modèle (ex: 'fact-checker-gan')
        stage: Stage du modèle ('Production', 'Staging', 'Archived', 'None')
        output_base_dir: Dossier de base pour sauvegarder les modèles
    
    Returns:
        Chemin local du modèle téléchargé, ou None en cas d'erreur
    """
    print("\n" + "=" * 80)
    print(f"📦 TÉLÉCHARGEMENT DU MODÈLE - Stage: {stage}")
    print("=" * 80)
    
    # Étape 1: Trouver le run_id
    run_id, version = get_run_id_from_stage(client, model_name, stage)
    
    if not run_id:
        return None
    
    # Étape 2: Télécharger les artefacts avec le run_id
    local_path = download_artifacts_from_run(
        client, 
        run_id, 
        model_name, 
        stage, 
        version.version, 
        output_base_dir
    )
    
    return local_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python download_gan_by_stage.py <staging|production|both>")
        print("\nExemples:")
        print("  python download_gan_by_stage.py staging")
        print("  python download_gan_by_stage.py production")
        print("  python download_gan_by_stage.py both")
        sys.exit(1)
    
    stage_choice = sys.argv[1].lower()
    
    print("=" * 80)
    print("📥 TÉLÉCHARGEMENT DE MODÈLE GAN PAR STAGE - VeriGraph")
    print("=" * 80)
    
    try:
        client = setup_mlflow()
        
        if stage_choice == "staging":
            result = download_model_by_stage(client, "fact-checker-gan", "Staging")
            if result:
                print(f"\n💡 Modèle Staging téléchargé dans: {result}")
                print(f"\n🚀 Utilisation:")
                # Trouver le chemin gan_model
                gan_model_path = Path(result) / "gan_model"
                if gan_model_path.exists():
                    print(f"   python -m factcheck.infer_gan --local {gan_model_path} \"Paris\" \"is capital of\" \"France\"")
                else:
                    print(f"   python -m factcheck.infer_gan --local {result} \"Paris\" \"is capital of\" \"France\"")
        
        elif stage_choice == "production":
            result = download_model_by_stage(client, "fact-checker-gan", "Production")
            if result:
                print(f"\n💡 Modèle Production téléchargé dans: {result}")
                print(f"\n🚀 Utilisation:")
                # Trouver le chemin gan_model
                gan_model_path = Path(result) / "gan_model"
                if gan_model_path.exists():
                    print(f"   python -m factcheck.infer_gan --local {gan_model_path} \"Paris\" \"is capital of\" \"France\"")
                else:
                    print(f"   python -m factcheck.infer_gan --local {result} \"Paris\" \"is capital of\" \"France\"")
        
        elif stage_choice == "both":
            print("\n📦 Téléchargement des deux modèles...")
            
            result_prod = download_model_by_stage(client, "fact-checker-gan", "Production")
            result_staging = download_model_by_stage(client, "fact-checker-gan", "Staging")
            
            if result_prod or result_staging:
                print("\n💡 Résumé des téléchargements:")
                if result_prod:
                    print(f"   ✅ Production: {result_prod}")
                if result_staging:
                    print(f"   ✅ Staging: {result_staging}")
        
        else:
            print(f"❌ Option invalide: {stage_choice}")
            print("Utilisez: staging, production ou both")
            sys.exit(1)
        
        print("\n" + "=" * 80)
        print("✅ Téléchargement terminé")
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
