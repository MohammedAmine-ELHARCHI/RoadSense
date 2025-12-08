"""
Download the Road Defect CV Model from Roboflow

This script downloads the specific dataset shown in the screenshot.
"""

from roboflow import Roboflow

def download_road_defect_dataset():
    """Download the Road Defect Computer Vision Model dataset"""
    print("🌐 Downloading Road Defect Dataset from Roboflow...")
    print("=" * 60)
    
    # You'll need to get your API key from Roboflow
    print("\n⚠️  API KEY REQUIRED")
    print("Please enter your Roboflow API key:")
    print("(Get it from: https://app.roboflow.com/settings/api)")
    print()
    
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided!")
        return
    
    try:
        rf = Roboflow(api_key=api_key)
        
        # Note: You'll need to get the exact workspace/project from the dataset page
        # The URL format is: universe.roboflow.com/WORKSPACE/PROJECT
        print("\n📋 Enter the dataset details from the URL:")
        print("   Example URL: universe.roboflow.com/my-workspace/road-defect")
        print()
        
        workspace = input("Workspace name: ").strip()
        project = input("Project name: ").strip()
        version = input("Version (default: 1): ").strip() or "1"
        
        print(f"\n📥 Downloading {workspace}/{project} version {version}...")
        
        project_obj = rf.workspace(workspace).project(project)
        dataset = project_obj.version(int(version)).download("yolov8")
        
        print(f"\n✅ Dataset downloaded successfully!")
        print(f"📁 Location: {dataset.location}")
        print(f"📋 Data config: {dataset.location}/data.yaml")
        
        print("\n🎯 READY TO TRAIN!")
        print("\nOption 1 - Quick training (50 epochs, ~30-60 min):")
        print(f"   cd ..")
        print(f"   python scripts/quick_train.py --mode full --data {dataset.location}/data.yaml --epochs 50")
        
        print("\nOption 2 - Full training (100 epochs, production-ready):")
        print(f"   cd ../detection-fissures")
        print(f"   python train_yolo.py --data {dataset.location}/data.yaml --epochs 100")
        
        return dataset.location
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify your API key is correct")
        print("  2. Check workspace and project names from the dataset URL")
        print("  3. Make sure you have access to the dataset")
        print("\nAlternative: Download manually from Roboflow website")
        print("  1. Go to the dataset page")
        print("  2. Click 'Download'")
        print("  3. Select 'YOLOv8' format")
        print("  4. Download and extract to: ../data/road_defect_dataset")

if __name__ == "__main__":
    download_road_defect_dataset()
