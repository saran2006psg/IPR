#!/usr/bin/env python3
"""
Quick run script for Legal Contract Risk Analyzer

Usage:
    python run.py                           # Interactive mode
    python run.py analyze contract.pdf     # Analyze a contract
    python run.py test                      # Run system tests
    python run.py sample                    # Create sample contract
    python run.py setup                     # Run setup
"""

import sys
import subprocess
import os

def print_menu():
    """Display interactive menu."""
    print("\n" + "=" * 80)
    print("  🏛️  LEGAL CONTRACT RISK ANALYZER")
    print("=" * 80)
    print("\nChoose an option:")
    print("\n  1. 🧪 Run System Tests")
    print("  2. 📄 Create Sample Contract")
    print("  3. 🔍 Analyze Contract (PDF)")
    print("  4. 📊 Run Ingestion Pipeline")
    print("  5. ⚙️  Run Setup")
    print("  6. ❌ Exit")
    print("\n" + "=" * 80)
    
    choice = input("\nEnter option (1-6): ").strip()
    return choice

def run_command(cmd):
    """Run a command and return to menu."""
    print(f"\n▶ Running: {cmd}\n")
    result = subprocess.run(cmd, shell=True)
    
    input("\n\nPress Enter to continue...")
    return result.returncode

def main():
    """Main runner."""
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "analyze":
            if len(sys.argv) < 3:
                print("❌ Error: Please specify a PDF file")
                print("Usage: python run.py analyze contract.pdf")
                sys.exit(1)
            pdf_file = sys.argv[2]
            if not os.path.exists(pdf_file):
                print(f"❌ Error: File not found: {pdf_file}")
                sys.exit(1)
            
            verbose = "--verbose" if len(sys.argv) > 3 and sys.argv[3] == "-v" else ""
            sys.exit(subprocess.call(f"python -m retrieval_pipeline.main {verbose} {pdf_file}", shell=True))
        
        elif command == "test":
            sys.exit(subprocess.call("python test_system.py", shell=True))
        
        elif command == "sample":
            sys.exit(subprocess.call("python create_sample_contract.py", shell=True))
        
        elif command == "setup":
            sys.exit(subprocess.call("python setup.py", shell=True))
        
        elif command == "ingest":
            sys.exit(subprocess.call("python ingest_pipeline.py", shell=True))
        
        else:
            print(f"❌ Unknown command: {command}")
            print("\nAvailable commands:")
            print("  python run.py analyze <file.pdf>   # Analyze a contract")
            print("  python run.py test                  # Run tests")
            print("  python run.py sample                # Create sample PDF")
            print("  python run.py setup                 # Run setup")
            print("  python run.py ingest                # Run ingestion")
            sys.exit(1)
    
    # Interactive mode
    while True:
        choice = print_menu()
        
        if choice == "1":
            run_command("python test_system.py")
        
        elif choice == "2":
            run_command("python create_sample_contract.py")
        
        elif choice == "3":
            pdf_file = input("\nEnter PDF file path: ").strip()
            if os.path.exists(pdf_file):
                verbose = input("Verbose output? (y/n): ").strip().lower()
                v_flag = "--verbose" if verbose == "y" else ""
                run_command(f"python -m retrieval_pipeline.main {v_flag} {pdf_file}")
            else:
                print(f"\n❌ File not found: {pdf_file}")
                input("\nPress Enter to continue...")
        
        elif choice == "4":
            confirm = input("\nThis will upload 9,447 vectors to Pinecone (~5 min). Continue? (y/n): ").strip().lower()
            if confirm == "y":
                run_command("python ingest_pipeline.py")
        
        elif choice == "5":
            run_command("python setup.py")
        
        elif choice == "6":
            print("\n👋 Goodbye!\n")
            sys.exit(0)
        
        else:
            print("\n❌ Invalid option. Please choose 1-6.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
