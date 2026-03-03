#!/usr/bin/env python3
"""
Script pour télécharger les artefacts d'un run MLflow spécifique.

Usage:
  python download_mlflow_artifacts.py [RUN_ID] [--output OUTPUT_DIR]
  
Exemple:
  python download_mlflow_artifacts.py e0417a99aef747e7bf4be3f265c25b6b
  python download_mlflow_artifacts.py e0417a99aef747e7bf4be3f265c25b6b --output models/
"""

import os
import sys
import argparse
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


def get_run_info(client, run_id):
    """Récupère les informations d'un run."""
    try:
        run = client.get_run(run_id)
        return run
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du run: {e}")
        return None


def list_artifacts(client, run_id, path=""):
    """Liste tous les artefacts d'un run de manière récursive."""
    artifacts = []
    try:
        items = client.list_artifacts(run_id, path)
        for item in items:
            if item.is_dir:
                # Récursion pour les dossiers
                artifacts.extend(list_artifacts(client, run_id, item.path))
            else:
                artifacts.append(item)
    except Exception as e:
        print(f"⚠️  Erreur lors du listage de {path}: {e}")
    
    return artifacts


def download_artifacts(client, run_id, output_dir="./downloaded_artifacts"):
    """Télécharge tous les artefacts d'un run."""
    output_path = Path(output_dir)
    
    # Créer le dossier de destination s'il n'existe pas
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📥 Téléchargement des artefacts...")
    print(f"   Destination: {output_path.absolute()}")
    
    try:
        # Télécharger tous les artefacts
        local_path = client.download_artifacts(run_id, "", dst_path=str(output_path))
        print(f"✅ Artefacts téléchargés dans: {local_path}")
        
        # Lister les fichiers téléchargés
        downloaded_files = list(Path(local_path).rglob("*"))
        files_only = [f for f in downloaded_files if f.is_file()]
        
        if files_only:
            print(f"\n📦 {len(files_only)} fichier(s) téléchargé(s):")
            for file in sorted(files_only):
                rel_path = file.relative_to(Path(local_path).parent)
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"   • {rel_path} ({size_mb:.2f} MB)")
        
        return local_path
    
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Télécharge les artefacts d'un run MLflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s e0417a99aef747e7bf4be3f265c25b6b
  %(prog)s e0417a99aef747e7bf4be3f265c25b6b --output models/downloaded/
        """
    )
    
    parser.add_argument(
        'run_id',
        type=str,
        nargs='?',
        default='e0417a99aef747e7bf4be3f265c25b6b',
        help='ID du run MLflow (défaut: e0417a99aef747e7bf4be3f265c25b6b)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./downloaded_artifacts',
        help='Dossier de destination (défaut: ./downloaded_artifacts)'
    )
    
    parser.add_argument(
        '--list-only', '-l',
        action='store_true',
        help='Lister uniquement les artefacts sans les télécharger'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("📦 TÉLÉCHARGEMENT D'ARTEFACTS MLFLOW - VeriGraph")
    print("=" * 80)
    
    try:
        # Configuration
        client = setup_mlflow()
        
        # Récupérer les informations du run
        print(f"\n🔍 Recherche du run: {args.run_id}")
        run = get_run_info(client, args.run_id)
        
        if not run:
            print(f"❌ Run non trouvé: {args.run_id}")
            sys.exit(1)
        
        # Afficher les informations du run
        print("\n📊 Informations du run:")
        print(f"   Nom: {run.info.run_name or 'N/A'}")
        print(f"   ID: {run.info.run_id}")
        print(f"   Status: {run.info.status}")
        print(f"   Experiment ID: {run.info.experiment_id}")
        
        if run.data.params:
            print(f"\n   📝 Paramètres:")
            for key, value in sorted(run.data.params.items()):
                print(f"      • {key}: {value}")
        
        if run.data.metrics:
            print(f"\n   📈 Métriques:")
            for key, value in sorted(run.data.metrics.items()):
                print(f"      • {key}: {value:.4f}")
        
        # Lister les artefacts
        print(f"\n📋 Artefacts disponibles:")
        artifacts = list_artifacts(client, args.run_id)
        
        if not artifacts:
            print("   ⚠️  Aucun artefact trouvé")
            sys.exit(0)
        
        total_size = sum(a.file_size or 0 for a in artifacts)
        total_size_mb = total_size / (1024 * 1024)
        
        print(f"   Nombre: {len(artifacts)}")
        print(f"   Taille totale: {total_size_mb:.2f} MB")
        print()
        
        for artifact in artifacts:
            size_mb = (artifact.file_size or 0) / (1024 * 1024)
            print(f"   • {artifact.path} ({size_mb:.2f} MB)")
        
        # Télécharger ou non
        if args.list_only:
            print("\n✅ Listage terminé (mode --list-only)")
            sys.exit(0)
        
        # Demander confirmation
        print()
        confirm = input(f"Télécharger dans '{args.output}' ? (O/n): ").strip().lower()
        if confirm and confirm not in ['o', 'oui', 'y', 'yes', '']:
            print("❌ Téléchargement annulé")
            sys.exit(0)
        
        # Télécharger
        result = download_artifacts(client, args.run_id, args.output)
        
        if result:
            print("\n" + "=" * 80)
            print("✅ Téléchargement terminé avec succès")
            print("=" * 80)
            print(f"\n💡 Les artefacts sont dans: {Path(args.output).absolute()}")
        else:
            print("\n" + "=" * 80)
            print("❌ Échec du téléchargement")
            print("=" * 80)
            sys.exit(1)
        
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
