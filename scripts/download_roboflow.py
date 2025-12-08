"""
Download Pre-configured Road Defect Dataset from Roboflow

This script uses Roboflow's public API to download a ready-to-use dataset.
You'll need a free Roboflow account and API key.

Usage:
    1. Sign up at https://roboflow.com (free)
    2. Get your API key from Account Settings
    3. Run: python download_roboflow.py --api-key YOUR_KEY
"""

import argparse
import os
import subprocess
from pathlib import Path

def setup_roboflow():
    """Install roboflow package if not available"""
    try:
        import roboflow
        print("✅ Roboflow package found")
        return True
    except ImportError:
        print("📦 Installing roboflow package...")
        try:
            subprocess.check_call([
                "pip", "install", "roboflow"
            ])
            print("✅ Roboflow installed successfully")
            return True
        except:
            print("❌ Failed to install roboflow")
            print("   Try manually: pip install roboflow")
            return False

def download_dataset_instructions():
    """Provide detailed instructions for dataset download"""
    print("\n" + "=" * 70)
    print("🎓 HOW TO GET A ROAD DEFECT DATASET FROM ROBOFLOW")
    print("=" * 70)
    
    print("\n📝 STEP 1: Create Free Roboflow Account")
    print("   → Visit: https://app.roboflow.com/signup")
    print("   → Sign up with email (takes 1 minute)")
    
    print("\n🔍 STEP 2: Find a Public Road Defect Dataset")
    print("   → Visit: https://universe.roboflow.com/")
    print("   → Search for: 'road defect' or 'pothole detection' or 'crack detection'")
    print("   → Look for datasets with 'Public' tag")
    print("   → Choose one with good quality images (500+ images recommended)")
    
    print("\n💡 RECOMMENDED DATASETS:")
    print("   1. 'Road Damage Detection' - Multiple damage types")
    print("   2. 'Pothole Detection' - Focused on potholes")
    print("   3. 'Crack Detection' - Pavement crack detection")
    
    print("\n⬇️  STEP 3: Download the Dataset")
    print("   → Click on the dataset")
    print("   → Click 'Download Dataset'")
    print("   → Select format: 'YOLOv8' ⭐")
    print("   → Choose 'show download code'")
    print("   → Copy the code snippet provided")
    
    print("\n🔑 STEP 4: Get Your API Key")
    print("   → Click your profile (top right)")
    print("   → Go to 'Account' → 'Roboflow API'")
    print("   → Copy your private API key")
    
    print("\n🚀 STEP 5: Run This Script")
    print("   → python download_roboflow.py --workspace YOUR_WORKSPACE --project YOUR_PROJECT --version 1")
    print("   → Or paste the download code snippet below")
    
    print("\n" + "=" * 70)
    print()

def download_with_code(api_key, workspace, project, version=1):
    """Download dataset using Roboflow API"""
    try:
        from roboflow import Roboflow
        
        print(f"\n🌐 Connecting to Roboflow...")
        rf = Roboflow(api_key=api_key)
        
        print(f"📂 Downloading project: {workspace}/{project}")
        project_obj = rf.workspace(workspace).project(project)
        dataset = project_obj.version(version).download("yolov8")
        
        print(f"\n✅ Dataset downloaded successfully!")
        print(f"📁 Location: {dataset.location}")
        print(f"📋 Data YAML: {dataset.location}/data.yaml")
        
        print("\n🎯 NEXT STEP: Start Training")
        print(f"   cd ../detection-fissures")
        print(f"   python train_yolo.py --data {dataset.location}/data.yaml")
        
        return dataset.location
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your API key is correct")
        print("  2. Verify workspace and project names")
        print("  3. Ensure you have access to the dataset")
        print("  4. Try downloading manually from Roboflow website")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Download road defect dataset from Roboflow",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--api-key", type=str, help="Your Roboflow API key")
    parser.add_argument("--workspace", type=str, help="Roboflow workspace name")
    parser.add_argument("--project", type=str, help="Project name")
    parser.add_argument("--version", type=int, default=1, help="Dataset version")
    parser.add_argument("--setup", action="store_true", help="Install roboflow package")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_roboflow()
        return
    
    if not args.api_key or not args.workspace or not args.project:
        download_dataset_instructions()
        
        print("\n📋 QUICK EXAMPLE:")
        print("   If the download code snippet says:")
        print('   rf.workspace("john-doe").project("road-damage").version(1).download("yolov8")')
        print("\n   Then run:")
        print('   python download_roboflow.py --api-key YOUR_KEY --workspace john-doe --project road-damage --version 1')
        print()
        return
    
    # Setup roboflow first
    if not setup_roboflow():
        return
    
    # Download dataset
    download_with_code(args.api_key, args.workspace, args.project, args.version)

if __name__ == "__main__":
    main()
