#!/usr/bin/env python3
"""
VeriGraph MacMini Main Service

Vérifie que les modèles staging et production sont téléchargés,
puis tourne en boucle pour traiter les tâches de fact-checking depuis la base de données.
"""

import os
import sys
import time
import logging
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import dagshub
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  MLflow/DagsHub non disponible - la surveillance des modèles sera désactivée")
    MLFLOW_AVAILABLE = False

# Configuration de la base de données
Base = declarative_base()

class Verification(Base):
    """Modèle de tâche de vérification"""
    __tablename__ = 'verifications'
    
    id = Column(String, primary_key=True)
    claim = Column(String, nullable=False)
    environment = Column(String, nullable=False)  # 'staging' ou 'production'
    status = Column(String, nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class VeriGraphService:
    """Service principal de VeriGraph pour le MacMini"""
    
    def __init__(self):
        # Configuration
        self.models_dir = Path("./models")
        self.poll_interval = 1  # 1 seconde
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.model_check_interval = 5  # Vérifier les modèles toutes les 5 itérations
        
        # Tracking des versions de modèles actuellement utilisées
        self.current_staging_version = None
        self.current_production_version = None
        self.mlflow_client = None
        
        # Chemins dynamiques des modèles (mis à jour selon les versions)
        self.staging_model_path = None
        self.production_model_path = None
        
        # Configuration de la base de données
        self.db_url = os.getenv("NEON_DB_URL")
        if not self.db_url:
            logger.error("❌ NEON_DB_URL non définie dans les variables d'environnement")
            sys.exit(1)
        
        # Initialiser la base de données
        logger.info("🔗 Connexion à la base de données...")
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info("✅ Base de données connectée")
        
    def check_model_downloaded(self, model_path: Path) -> bool:
        """Vérifie si un modèle est téléchargé et contient les fichiers nécessaires."""
        if not model_path.exists():
            return False
        
        required_files = ['discriminator.pt', 'generator.pt', 'gan_meta.pt']
        for file in required_files:
            if not (model_path / file).exists():
                logger.warning(f"⚠️  Fichier manquant: {file}")
                return False
        
        return True
    
    def download_model(self, stage: str) -> bool:
        """Télécharge un modèle via le script download_gan_by_stage.py."""
        logger.info(f"📥 Téléchargement du modèle {stage}...")
        
        try:
            result = subprocess.run(
                ["python", "download_gan_by_stage.py", stage.lower()],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Modèle {stage} téléchargé avec succès")
                return True
            else:
                logger.error(f"❌ Erreur lors du téléchargement: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout lors du téléchargement du modèle {stage}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return False
    
    def ensure_models_downloaded(self):
        """S'assure que les modèles staging et production sont téléchargés."""
        logger.info("=" * 80)
        logger.info("🔍 VÉRIFICATION DES MODÈLES")
        logger.info("=" * 80)
        
        # Initialiser MLflow et récupérer les versions actuelles en premier
        # Ceci définit les chemins des modèles basés sur les versions MLflow
        if MLFLOW_AVAILABLE:
            self.initialize_mlflow_tracking()
        else:
            logger.warning("⚠️  MLflow non disponible - impossible de déterminer les versions des modèles")
            sys.exit(1)
        
        # Vérifier Staging
        logger.info("\n📦 Vérification du modèle Staging...")
        if self.check_model_downloaded(self.staging_model_path):
            logger.info(f"✅ Modèle Staging trouvé: {self.staging_model_path}")
        else:
            logger.warning(f"⚠️  Modèle Staging non trouvé: {self.staging_model_path}")
            if not self.download_model("staging"):
                logger.error("❌ Impossible de télécharger le modèle Staging")
                sys.exit(1)
        
        # Vérifier Production
        logger.info("\n📦 Vérification du modèle Production...")
        if self.check_model_downloaded(self.production_model_path):
            logger.info(f"✅ Modèle Production trouvé: {self.production_model_path}")
        else:
            logger.warning(f"⚠️  Modèle Production non trouvé: {self.production_model_path}")
            if not self.download_model("production"):
                logger.error("❌ Impossible de télécharger le modèle Production")
                sys.exit(1)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ TOUS LES MODÈLES SONT PRÊTS")
        logger.info("=" * 80)
    
    def initialize_mlflow_tracking(self):
        """Initialise la connexion MLflow et récupère les versions actuelles des modèles."""
        try:
            logger.info("\n🔗 Initialisation de la surveillance MLflow...")
            dagshub_repo = "MarcoSrhl/NLP-Fact-checking"
            dagshub.init(
                repo_name=dagshub_repo.split('/')[1],
                repo_owner=dagshub_repo.split('/')[0],
                mlflow=True
            )
            self.mlflow_client = MlflowClient()
            
            # Récupérer les versions actuelles
            self.current_staging_version = self.get_model_version("Staging")
            self.current_production_version = self.get_model_version("Production")
            
            # Mettre à jour les chemins avec les versions actuelles
            self.update_model_path("staging", self.current_staging_version)
            self.update_model_path("production", self.current_production_version)
            
            logger.info(f"✅ Surveillance MLflow activée")
            logger.info(f"   Staging: Version {self.current_staging_version}")
            logger.info(f"   Production: Version {self.current_production_version}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation MLflow: {e}")
            self.mlflow_client = None
    
    def get_model_version(self, stage: str) -> str:
        """Récupère la version actuelle d'un modèle depuis MLflow Registry."""
        if not self.mlflow_client:
            return None
        
        try:
            versions = self.mlflow_client.search_model_versions(f"name='fact-checker-gan'")
            target_versions = [v for v in versions if v.current_stage == stage]
            
            if target_versions:
                version = sorted(target_versions, key=lambda v: int(v.version), reverse=True)[0]
                return version.version
            
            return None
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération de la version {stage}: {e}")
            return None
    
    def get_model_path(self, environment: str) -> Path:
        """Retourne le chemin du modèle pour l'environnement spécifié."""
        if environment.lower() == "staging":
            return self.staging_model_path
        elif environment.lower() == "production":
            return self.production_model_path
        else:
            raise ValueError(f"Environment invalide: {environment}")
    
    def update_model_path(self, environment: str, version: str):
        """Met à jour le chemin du modèle après un téléchargement ou une détection de version."""
        if not version:
            return
        
        environment_lower = environment.lower()
        model_path = self.models_dir / f"fact-checker-gan_{environment_lower}_v{version}" / "gan_model"
        
        if environment_lower == "staging":
            self.staging_model_path = model_path
            logger.info(f"🔄 Chemin Staging mis à jour: {model_path}")
        elif environment_lower == "production":
            self.production_model_path = model_path
            logger.info(f"🔄 Chemin Production mis à jour: {model_path}")
    
    def check_model_updates(self):
        """Vérifie si les modèles ont été mis à jour dans MLflow et les re-télécharge si nécessaire."""
        if not self.mlflow_client:
            return
        
        logger.info("\n🔍 Vérification des mises à jour des modèles sur MLflow...")
        
        try:
            # Vérifier Staging
            new_staging_version = self.get_model_version("Staging")
            if new_staging_version and new_staging_version != self.current_staging_version:
                logger.info(f"🔄 Nouveau modèle Staging détecté: v{self.current_staging_version} -> v{new_staging_version}")
                if self.download_model("staging"):
                    self.current_staging_version = new_staging_version
                    self.update_model_path("staging", new_staging_version)
                    logger.info(f"✅ Modèle Staging mis à jour vers v{new_staging_version}")
            else:
                logger.info(f"✓ Modèle Staging inchangé (v{self.current_staging_version})")
            
            # Vérifier Production
            new_production_version = self.get_model_version("Production")
            if new_production_version and new_production_version != self.current_production_version:
                logger.info(f"🔄 Nouveau modèle Production détecté: v{self.current_production_version} -> v{new_production_version}")
                if self.download_model("production"):
                    self.current_production_version = new_production_version
                    self.update_model_path("production", new_production_version)
                    logger.info(f"✅ Modèle Production mis à jour vers v{new_production_version}")
            else:
                logger.info(f"✓ Modèle Production inchangé (v{self.current_production_version})")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification des mises à jour: {e}")
    
    def run_inference(self, claim: str, model_path: Path, environment: str) -> dict:
        """
        Exécute l'inférence sur un claim avec le modèle GAN spécifié.
        
        Args:
            claim: Le texte à vérifier
            model_path: Chemin vers le modèle GAN
            environment: 'staging' ou 'production'
        
        Returns:
            Dict avec label, confidence, et probabilities
        """
        logger.info(f"🔮 Inférence avec modèle {environment}: {claim[:100]}...")
        
        try:
            # Utiliser le mode phrase pour les claims complets
            cmd = [
                "python", "-m", "factcheck.infer_gan",
                "--local", str(model_path),
                "--phrase", claim
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Erreur d'inférence: {result.stderr}")
            
            # Parser la sortie pour extraire le résultat
            # Format attendu: "  Score: 0.8701 -> REAL"
            output = result.stdout.strip()
            logger.info(f"   Sortie brute: {output[:200]}...")
            
            # Extraire le triplet extrait
            # Format: "Extracted triplet: (subject, relation, object)"
            triplet = None
            triplet_lines = [line for line in output.split('\n') if 'Extracted triplet:' in line]
            if triplet_lines:
                triplet_line = triplet_lines[0]
                # Parser "(subject, relation, object)"
                if '(' in triplet_line and ')' in triplet_line:
                    triplet_str = triplet_line.split('(')[1].split(')')[0]
                    triplet_parts = [part.strip() for part in triplet_str.split(',')]
                    if len(triplet_parts) == 3:
                        triplet = {
                            "subject": triplet_parts[0],
                            "relation": triplet_parts[1],
                            "object": triplet_parts[2]
                        }
                        logger.info(f"   Triplet extrait: ({triplet['subject']}, {triplet['relation']}, {triplet['object']})")
            
            # Extraire la prédiction et le score
            # Chercher la ligne avec "Score: X.XXXX -> VERDICT"
            score_lines = [line for line in output.split('\n') if 'Score:' in line and '->' in line]
            
            if score_lines:
                score_line = score_lines[0].strip()
                # Parser "  Score: 0.8701 -> REAL"
                parts = score_line.split('->')
                score_part = parts[0].split('Score:')[1].strip()
                score = float(score_part)
                label = parts[1].strip()
                
                # Déterminer le nom du modèle et la version
                model_name = f"fact-checker-gan_{environment}"
                model_version = "v1" if environment == "staging" else "v2"
                
                result_data = {
                    "label": label,
                    "confidence": score,
                    "probabilities": {
                        "REAL": score if label == "REAL" else 1 - score,
                        "FAKE": 1 - score if label == "REAL" else score
                    },
                    "model": environment,
                    "model_name": model_name,
                    "model_version": model_version,
                    "raw_output": output
                }
                
                # Ajouter le triplet s'il a été extrait
                if triplet:
                    result_data["triplet"] = triplet
                
                return result_data
            else:
                raise Exception(f"Format de sortie invalide: {output}")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout lors de l'inférence")
            raise Exception("Timeout lors de l'inférence")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'inférence: {e}")
            raise
    
    def process_task(self, task: Verification):
        """Traite une tâche de vérification."""
        session = self.Session()
        try:
            # Re-fetch du task dans cette session
            task = session.query(Verification).filter(Verification.id == task.id).first()
            if not task:
                logger.error(f"❌ Tâche non trouvée")
                return
            
            logger.info(f"🔄 Traitement de la tâche {task.id}")
            logger.info(f"   Claim: {task.claim[:100]}...")
            logger.info(f"   Environment: {task.environment}")
            
            # Mise à jour du statut à 'processing'
            task.status = 'processing'
            task.updated_at = datetime.now(timezone.utc)
            session.commit()
            
            # Sélectionner le modèle approprié
            try:
                model_path = self.get_model_path(task.environment)
            except ValueError as e:
                raise ValueError(f"Environment invalide: {task.environment}")
            
            # Exécuter l'inférence
            result = self.run_inference(task.claim, model_path, task.environment)
            
            # Mise à jour avec les résultats
            task.status = 'completed'
            task.result = result
            task.updated_at = datetime.now(timezone.utc)
            session.commit()
            
            logger.info(f"✅ Tâche {task.id} terminée: {result.get('label')} ({result.get('confidence'):.2%})")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de la tâche {task.id}: {e}")
            
            # Incrémenter les retries
            task.retries += 1
            
            if task.retries >= self.max_retries:
                task.status = 'failed'
                task.error = str(e)
                logger.error(f"   Tâche {task.id} échouée après {self.max_retries} tentatives")
            else:
                task.status = 'pending'  # Réessayer plus tard
                logger.warning(f"   Tâche {task.id} repassée en pending (tentative {task.retries}/{self.max_retries})")
            
            task.updated_at = datetime.now(timezone.utc)
            session.commit()
            
        finally:
            session.close()
    
    def poll_and_process(self):
        """Interroge la base de données pour les tâches en attente et les traite."""
        session = self.Session()
        try:
            # Récupérer TOUTES les tâches pending (staging et production)
            tasks = session.query(Verification).filter(
                Verification.status == 'pending',
                Verification.retries < self.max_retries
            ).limit(10).all()
            
            if tasks:
                logger.info(f"📋 {len(tasks)} tâche(s) en attente")
                for task in tasks:
                    self.process_task(task)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'interrogation de la base de données: {e}")
        finally:
            session.close()
    
    def run(self):
        """Boucle principale du service."""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 DÉMARRAGE DU SERVICE VERIGRAPH")
        logger.info("=" * 80)
        logger.info(f"📦 Modèle Staging: {self.staging_model_path}")
        logger.info(f"📦 Modèle Production: {self.production_model_path}")
        logger.info(f"⏱️  Intervalle de polling: {self.poll_interval}s")
        logger.info(f"🔄 Max retries: {self.max_retries}")
        if MLFLOW_AVAILABLE:
            logger.info(f"🔍 Vérification des modèles MLflow: toutes les {self.model_check_interval} itérations")
        logger.info("=" * 80 + "\n")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                logger.info(f"🔄 Iteration #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Vérifier les mises à jour de modèles toutes les N itérations
                if MLFLOW_AVAILABLE and iteration % self.model_check_interval == 0:
                    self.check_model_updates()
                
                self.poll_and_process()
                
                # Sleep 1 seconde
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 80)
            logger.info("⏹️  ARRÊT GRACIEUX DU SERVICE")
            logger.info("=" * 80)
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            raise


def main():
    """Point d'entrée principal."""
    try:
        # Initialiser le service
        service = VeriGraphService()
        
        # S'assurer que les modèles sont téléchargés
        service.ensure_models_downloaded()
        
        # Lancer la boucle de traitement
        service.run()
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
