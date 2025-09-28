#!/usr/bin/env python3
"""
Pre-compute all species predictions at startup
"""
import json
import os
from pathlib import Path
import time
from species_inference import get_global_predictor, fast_predict_with_global_predictor

def precompute_all_predictions():
    """Pre-compute predictions for all species and save to disk"""
    print("🚀 Starting prediction pre-computation...")
    
    # Initialize predictor
    predictor = get_global_predictor()
    
    # Create predictions directory
    predictions_dir = Path("predictions_cache")
    predictions_dir.mkdir(exist_ok=True)
    
    # Track progress
    total_species = len(predictor.species_names)
    predictions_cache = {}
    
    print(f"📊 Pre-computing predictions for {total_species} species...")
    
    for i, species_name in enumerate(predictor.species_names):
        try:
            print(f"🔮 [{i+1}/{total_species}] Processing {species_name}...")
            
            # Generate prediction
            prediction = fast_predict_with_global_predictor(predictor, species_name)
            
            if prediction:
                # Save individual prediction file
                species_file = predictions_dir / f"{species_name.replace(' ', '_')}.json"
                with open(species_file, 'w') as f:
                    json.dump(prediction, f, indent=2)
                
                # Add to cache
                predictions_cache[species_name] = prediction
                print(f"✅ Cached {len(prediction['features'])} predictions for {species_name}")
            else:
                print(f"⚠️ No predictions generated for {species_name}")
                
        except Exception as e:
            print(f"❌ Error processing {species_name}: {e}")
            continue
    
    # Save master cache file
    cache_file = predictions_dir / "all_predictions.json"
    with open(cache_file, 'w') as f:
        json.dump(predictions_cache, f, indent=2)
    
    # Save metadata
    metadata = {
        "total_species": total_species,
        "successful_predictions": len(predictions_cache),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "species_list": list(predictions_cache.keys())
    }
    
    metadata_file = predictions_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"🎉 Pre-computation complete!")
    print(f"📈 Generated predictions for {len(predictions_cache)}/{total_species} species")
    print(f"💾 Cache saved to {predictions_dir}")
    
    return predictions_cache

def load_predictions_cache():
    """Load pre-computed predictions from disk"""
    cache_file = Path("predictions_cache/all_predictions.json")
    
    if cache_file.exists():
        print("📂 Loading pre-computed predictions...")
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        print(f"✅ Loaded {len(cache)} pre-computed predictions")
        return cache
    else:
        print("⚠️ No prediction cache found, generating...")
        return precompute_all_predictions()

def get_cached_prediction(species_name):
    """Get prediction from cache"""
    global _predictions_cache
    
    if '_predictions_cache' not in globals():
        _predictions_cache = load_predictions_cache()
    
    return _predictions_cache.get(species_name)

if __name__ == "__main__":
    # Run pre-computation
    precompute_all_predictions()