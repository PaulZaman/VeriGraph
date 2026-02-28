"""
Data Service for VeriGraph
Handles DVC operations and RDF data querying
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
import subprocess
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDFS, RDF

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DBpedia namespaces
DBPEDIA = Namespace("http://dbpedia.org/resource/")
DBPEDIA_ONT = Namespace("http://dbpedia.org/ontology/")
DBPEDIA_PROP = Namespace("http://dbpedia.org/property/")


class DataService:
    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", "data_dvc")
        self.gcs_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.graph = None
        self.is_loaded = False
        
    def initialize_dvc(self) -> bool:
        """Initialize DVC and check if data is available"""
        try:
            # Check if DVC is initialized
            if not os.path.exists(".dvc"):
                logger.info("DVC not initialized. Run 'dvc init' first.")
                return False
            
            # Check if data directory exists
            if not os.path.exists(self.data_dir):
                logger.info(f"Data directory {self.data_dir} not found. Pulling from DVC...")
                # Try to pull data
                result = subprocess.run(
                    ["dvc", "pull"], 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    logger.error(f"DVC pull failed: {result.stderr}")
                    return False
                    
            logger.info(f"✅ DVC initialized. Data available at: {self.data_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing DVC: {str(e)}")
            return False
    
    def load_data(self, filename: str = None) -> bool:
        """Load RDF data into memory (or specific file)"""
        try:
            if not os.path.exists(self.data_dir):
                logger.warning("Data directory not found. Using mock mode.")
                return False
            
            self.graph = Graph()
            
            # If specific file requested
            if filename:
                file_path = os.path.join(self.data_dir, filename)
                if not os.path.exists(file_path):
                    logger.error(f"File not found: {file_path}")
                    return False
                    
                logger.info(f"Loading {filename}...")
                # Handle .bz2 files
                if filename.endswith('.bz2'):
                    import bz2
                    with bz2.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                        self.graph.parse(data=f.read(), format='turtle')
                else:
                    self.graph.parse(file_path, format='turtle')
                    
                logger.info(f"✅ Loaded {len(self.graph)} triples from {filename}")
            else:
                # Load all TTL files (limit for demo)
                logger.info("Loading sample RDF data...")
                files = list(Path(self.data_dir).glob("*.ttl"))[:2]  # Limit to 2 files for demo
                
                for file_path in files:
                    logger.info(f"Loading {file_path.name}...")
                    self.graph.parse(file_path, format='turtle')
                    
                logger.info(f"✅ Loaded {len(self.graph)} total triples")
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False
    
    def get_entity_info(self, entity_name: str) -> Optional[Dict]:
        """Get information about a DBpedia entity"""
        if not self.is_loaded or not self.graph:
            return None
            
        try:
            # Construct the DBpedia URI
            entity_uri = URIRef(f"http://dbpedia.org/resource/{entity_name}")
            
            # Get all triples where this entity is the subject
            info = {
                "uri": str(entity_uri),
                "label": None,
                "properties": [],
                "types": []
            }
            
            # Get label
            for s, p, o in self.graph.triples((entity_uri, RDFS.label, None)):
                if isinstance(o, Literal):
                    info["label"] = str(o)
                    break
            
            # Get types
            for s, p, o in self.graph.triples((entity_uri, RDF.type, None)):
                info["types"].append(str(o))
            
            # Get other properties (limit to avoid huge responses)
            count = 0
            for s, p, o in self.graph.triples((entity_uri, None, None)):
                if count >= 20:  # Limit properties
                    break
                if p not in [RDFS.label, RDF.type]:
                    info["properties"].append({
                        "predicate": str(p),
                        "object": str(o)
                    })
                    count += 1
            
            return info if (info["label"] or info["properties"]) else None
            
        except Exception as e:
            logger.error(f"Error getting entity info: {str(e)}")
            return None
    
    def search_entities(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for entities by label"""
        if not self.is_loaded or not self.graph:
            return []
            
        try:
            results = []
            query_lower = query.lower()
            
            # Search in labels
            for s, p, o in self.graph.triples((None, RDFS.label, None)):
                if isinstance(o, Literal):
                    label = str(o)
                    if query_lower in label.lower():
                        results.append({
                            "uri": str(s),
                            "label": label,
                            "match_score": 1.0 if label.lower() == query_lower else 0.5
                        })
                        
                        if len(results) >= limit:
                            break
            
            # Sort by match score
            results.sort(key=lambda x: x["match_score"], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Error searching entities: {str(e)}")
            return []
    
    def get_available_files(self) -> List[Dict]:
        """List available data files"""
        try:
            if not os.path.exists(self.data_dir):
                return []
            
            files = []
            for file_path in Path(self.data_dir).glob("*"):
                if file_path.is_file():
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    files.append({
                        "name": file_path.name,
                        "size_mb": round(size_mb, 2),
                        "type": file_path.suffix[1:] if file_path.suffix else "unknown"
                    })
            
            return sorted(files, key=lambda x: x["name"])
            
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []
    
    def get_stats(self) -> Dict:
        """Get statistics about loaded data"""
        if not self.is_loaded or not self.graph:
            return {
                "loaded": False,
                "triples": 0,
                "entities": 0,
                "message": "No data loaded"
            }
        
        try:
            # Count unique subjects (entities)
            subjects = set(s for s, p, o in self.graph.triples((None, None, None)))
            
            return {
                "loaded": True,
                "triples": len(self.graph),
                "entities": len(subjects),
                "data_dir": self.data_dir
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"loaded": False, "error": str(e)}


# Global data service instance
data_service: Optional[DataService] = None


def get_data_service() -> DataService:
    """Get or create the global data service instance"""
    global data_service
    if data_service is None:
        data_service = DataService()
    return data_service
