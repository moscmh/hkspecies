#!/usr/bin/env python3
"""
Quick script to run the data processing pipeline and start the API
"""

import subprocess
import sys
from pathlib import Path

def run_data_processing():
    """Run the data processing pipeline"""
    print("🔄 Running data processing pipeline...")
    
    try:
        from data_processor import HKSpeciesDataProcessor
        processor = HKSpeciesDataProcessor()
        stats = processor.process_all()
        
        print("✅ Data processing completed!")
        print(f"   - {stats['total_species']} species processed")
        print(f"   - {stats['total_occurrences']} occurrence records")
        print(f"   - {stats['total_districts']} districts")
        
        return True
    except Exception as e:
        print(f"❌ Data processing failed: {e}")
        return False

def start_api():
    """Start the FastAPI server"""
    print("🚀 Starting API server...")
    print("   API will be available at: http://localhost:8000")
    print("   API docs at: http://localhost:8000/docs")
    
    try:
        subprocess.run([sys.executable, "species_api.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 API server stopped")
    except Exception as e:
        print(f"❌ Failed to start API: {e}")

def main():
    """Main execution flow"""
    print("🌿 Hong Kong Species Data Pipeline")
    print("=" * 40)
    
    # Check if processed data exists
    processed_dir = Path("processed")
    if not processed_dir.exists() or not (processed_dir / "species_index.json").exists():
        print("📊 No processed data found. Running pipeline...")
        if not run_data_processing():
            return
    else:
        print("📊 Processed data found. Skipping pipeline.")
        print("   (Delete 'processed' folder to rerun pipeline)")
    
    print("\n" + "=" * 40)
    start_api()

if __name__ == "__main__":
    main()