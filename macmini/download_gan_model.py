#!/usr/bin/env python3
"""
Script simple pour télécharger les modèles fact-checker-gan par stage.

Usage:
  python download_gan_model.py staging
  python download_gan_model.py production
  python download_gan_model.py both
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
        except Exception as e:
            print(f"   ⚠️  Impossible de récupérer les métriques: {e}")
        
        # Définir le dossier de destination
        output_dir = Path(output_base_dir) / f"{model_name}_{stage.lower()}_v{version.version}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📥 Téléchargement des artefacts...")
        print(f"   Destination: {output_dir.absolute()}")
        print(f"   (Cela peut prendre quelques minutes...)")
        
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
    if len(sys.argv) < 2:
        print("Usage: python download_gan_model.py <staging|production|both>")
        sys.exit(1)
    
    stage_choice = sys.argv[1].lower()
    
    print("=" * 80)
    print("📥 TÉLÉCHARGEMENT DE MODÈLE GAN - VeriGraph")
    print("=" * 80)
    
    try:
        client = setup_mlflow()
        
        if stage_choice == "staging":
            result = download_model_by_stage(client, "fact-checker-gan", "Staging")
            if result:
                print(f"\n💡 Modèle Staging téléchargé dans: {result}")
                print(f"\n🚀 Utilisation:")
                print(f"   python -m factcheck.infer_gan --local {result}/gan_model \"Paris\" \"is capital of\" \"France\"")
        
        elif stage_choice == "production":
            result = download_model_by_stage(client, "fact-checker-gan", "Production")
            if result:
                print(f"\n💡 Modèle Production téléchargé dans: {result}")
                print(f"\n🚀 Utilisation:")
                print(f"   python -m factcheck.infer_gan --local {result}/gan_model \"Paris\" \"is capital of\" \"France\"")
        
        elif stage_choice == "both":
            print("\n📦 Téléchargement des deux modèles...")
            result_prod = download_model_by_stage(client, "fact-checker-gan", "Production")
            result_staging = download_model_by_stage(client, "fact-checker-gan", "Staging")
            
            if result_prod and result_staging:
                print("\n💡 Les deux modèles ont été téléchargés:")
                print(f"   Production: {result_prod}")
                print(f"   Staging: {result_staging}")
        
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
