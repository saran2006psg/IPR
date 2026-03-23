#!/usr/bin/env python3
"""
Quick setup script for Legal Contract Risk Analyzer

This script automates the installation and verification process.
"""

import os
import sys
import subprocess

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n▶ {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.8+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_env_file():
    """Check if .env file exists."""
    if not os.path.exists(".env"):
        print("\n⚠️  .env file not found!")
        print("\nCreating .env template...")
        with open(".env", "w") as f:
            f.write("# Pinecone API Key\n")
            f.write("PINECONE_API_KEY=your-api-key-here\n")
        print("✅ Created .env template")
        print("\n⚠️  IMPORTANT: Edit .env and add your Pinecone API key!")
        return False
    
    # Check if API key is set
    with open(".env", "r") as f:
        content = f.read()
        if "your-api-key-here" in content or "PINECONE_API_KEY=" not in content:
            print("\n⚠️  Pinecone API key not configured in .env!")
            print("   Please update .env with your actual API key")
            return False
    
    print("✅ .env file configured")
    return True

def main():
    """Main setup process."""
    print_header("🏛️  LEGAL CONTRACT RISK ANALYZER - SETUP")
    
    print("\n[Step 1] Checking Python version...")
    if not check_python_version():
        sys.exit(1)
    
    print("\n[Step 2] Checking environment configuration...")
    env_ok = check_env_file()
    
    print("\n[Step 3] Installing dependencies...")
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python packages"
    ):
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    print("\n[Step 4] Verifying installation...")
    if not run_command(
        f"{sys.executable} -c \"from backend.retrieval_pipeline import analyze_contract\"",
        "Testing package imports"
    ):
        print("\n❌ Installation verification failed")
        sys.exit(1)
    
    if env_ok:
        print("\n[Step 5] Running system tests...")
        run_command(
            f"{sys.executable} test_system.py",
            "Running comprehensive system tests"
        )
    
    print_header("✅ SETUP COMPLETE")
    
    if not env_ok:
        print("\n⚠️  NEXT STEP: Configure your .env file with Pinecone API key")
        print("   Then run: python test_system.py")
    else:
        print("\n🚀 Your system is ready!")
        print("\nNext steps:")
        print("  1. Run ingestion (if not done): python ingest_pipeline.py")
        print("  2. Create sample contract: python create_sample_contract.py")
        print("  3. Analyze contract: python -m retrieval_pipeline.main sample_employment_contract.pdf")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()
