#!/usr/bin/env python3
"""
Script per eseguire tutti i test del progetto SR_backend

Uso:
    python run_tests.py [--verbose] [--coverage]
    
Opzioni:
    --verbose   : Output verboso dei test
    --coverage  : Genera report di coverage (richiede coverage.py)
"""

import sys
import unittest
import argparse
import os

def run_tests(verbose=False, coverage=False):
    """Esegue tutti i test del progetto"""
    
    # Configurazione path (directory parent del progetto)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # Configurazione logging per i test
    import logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s - %(name)s - %(message)s'
    )
    
    # Lista dei moduli di test
    test_modules = [
        'test_unit_simplified',
        # 'test_unit_embedding_database',  # Commentato perché richiede dipendenze ML
    ]
    
    if coverage:
        try:
            import coverage
            cov = coverage.Coverage()
            cov.start()
        except ImportError:
            print("ATTENZIONE: coverage.py non è installato, proseguo senza coverage")
            coverage = False
    
    # Suite di test
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    print("🧪 Caricamento test...")
    for module_name in test_modules:
        try:
            module = __import__(module_name)
            module_suite = loader.loadTestsFromModule(module)
            suite.addTest(module_suite)
            print(f"✅ Caricato: {module_name}")
        except ImportError as e:
            print(f"⚠️  Saltato {module_name}: {e}")
        except Exception as e:
            print(f"❌ Errore caricamento {module_name}: {e}")
    
    # Esecuzione test
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
    
    print("\n" + "="*60)
    print("🚀 ESECUZIONE TEST")
    print("="*60)
    
    result = runner.run(suite)
    
    if coverage:
        cov.stop()
        cov.save()
        
        print("\n" + "="*60)
        print("📊 COVERAGE REPORT")
        print("="*60)
        
        # Report sulla console
        cov.report(show_missing=True)
        
        # Genera report HTML se richiesto
        html_dir = os.path.join(project_root, 'htmlcov')
        cov.html_report(directory=html_dir)
        print(f"\n📄 Report HTML generato in: {html_dir}/index.html")
    
    # Riassunto finale
    print("\n" + "="*60)
    print("📋 RIASSUNTO ESECUZIONE")
    print("="*60)
    
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    
    print(f"Test eseguiti: {tests_run}")
    print(f"Successi: {tests_run - failures - errors}")
    print(f"Fallimenti: {failures}")
    print(f"Errori: {errors}")
    print(f"Saltati: {skipped}")
    
    if result.wasSuccessful():
        print("🎉 TUTTI I TEST SONO PASSATI!")
        return 0
    else:
        print("❌ ALCUNI TEST SONO FALLITI!")
        return 1


def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(
        description="Esegue i test del progetto SR_backend"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Output verboso dei test'
    )
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Genera report di coverage'
    )
    
    args = parser.parse_args()
    
    print("🔬 Test Suite SR_backend")
    print(f"Python: {sys.version}")
    print(f"Path: {os.getcwd()}")
    print()
    
    exit_code = run_tests(
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
