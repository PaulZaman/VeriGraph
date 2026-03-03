#!/usr/bin/env python3
"""
Script de test pour l'inférence du modèle GAN avec le package factcheck.

Usage:
  # Triplet direct
  python test_inference.py triplet "Paris" "is capital of" "France"
  
  # Phrase libre (extraction automatique du triplet)
  python test_inference.py phrase "Einstein was born in Berlin"
  
  # Utilisation directe du module factcheck.infer_gan
  python -m factcheck.infer_gan "Paris" "is capital of" "France"
  python -m factcheck.infer_gan --phrase "Einstein was born in Berlin"
"""

import sys
import argparse
import subprocess
from pathlib import Path


def run_inference_triplet(subject, relation, obj):
    """
    Execute l'inférence avec un triplet direct en utilisant le module factcheck.infer_gan.
    
    Args:
        subject: Le sujet du triplet
        relation: La relation du triplet
        obj: L'objet du triplet
    """
    cmd = ["python", "-m", "factcheck.infer_gan", subject, relation, obj]
    
    print(f"🔍 Exécution: {' '.join(cmd)}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("⚠️  Warnings:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution:")
        print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_inference_phrase(phrase):
    """
    Execute l'inférence avec une phrase libre en utilisant le module factcheck.infer_gan.
    
    Args:
        phrase: La phrase à analyser
    """
    cmd = ["python", "-m", "factcheck.infer_gan", "--phrase", phrase]
    
    print(f"🔍 Exécution: {' '.join(cmd)}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("⚠️  Warnings:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution:")
        print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test d'inférence avec le modèle GAN factcheck",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  %(prog)s triplet "Paris" "is capital of" "France"
  %(prog)s phrase "Einstein was born in Berlin"
  
Ou directement avec le module:
  python -m factcheck.infer_gan "Paris" "is capital of" "France"
  python -m factcheck.infer_gan --phrase "Einstein was born in Berlin"
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='Mode d\'inférence', required=True)
    
    # Sous-commande pour triplet
    triplet_parser = subparsers.add_parser('triplet', help='Inférence avec un triplet direct')
    triplet_parser.add_argument('subject', type=str, help='Sujet du triplet')
    triplet_parser.add_argument('relation', type=str, help='Relation du triplet')
    triplet_parser.add_argument('object', type=str, help='Objet du triplet')
    
    # Sous-commande pour phrase
    phrase_parser = subparsers.add_parser('phrase', help='Inférence avec une phrase libre')
    phrase_parser.add_argument('phrase', type=str, help='Phrase à analyser')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🧪 Test d'inférence du modèle GAN - VeriGraph")
    print("=" * 80)
    print()
    
    if args.mode == 'triplet':
        print(f"📝 Mode: Triplet direct")
        print(f"   Sujet: {args.subject}")
        print(f"   Relation: {args.relation}")
        print(f"   Objet: {args.object}")
        print()
        
        success = run_inference_triplet(args.subject, args.relation, args.object)
    
    elif args.mode == 'phrase':
        print(f"📝 Mode: Phrase libre")
        print(f"   Phrase: {args.phrase}")
        print()
        
        success = run_inference_phrase(args.phrase)
    
    print()
    print("=" * 80)
    if success:
        print("✅ Test terminé avec succès")
    else:
        print("❌ Test échoué")
    print("=" * 80)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
