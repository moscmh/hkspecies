#!/usr/bin/env python3
"""
Test script to check prediction functionality
"""

import json
import sys
import os

def test_species_data():
    """Test if species data is available"""
    try:
        with open("processed/species_index.json") as f:
            species_index = json.load(f)
        
        print(f"✅ Species index loaded: {len(species_index)} species")
        
        # Get first few species for testing
        species_names = list(species_index.keys())[:5]
        print(f"📋 First 5 species: {species_names}")
        
        return species_names[0] if species_names else None
        
    except Exception as e:
        print(f"❌ Error loading species data: {e}")
        return None

def test_prediction_model():
    """Test if prediction model can be loaded"""
    try:
        from species_inference import Species
        
        print("✅ Species inference module imported")
        
        # Initialize predictor
        predictor = Species()
        print("✅ Species predictor initialized")
        
        # Prepare data
        predictor.prepare_data()
        print("✅ Data prepared")
        
        # Get species names
        predictor.get_species_names()
        print(f"✅ Species names loaded: {len(predictor.species_names)} species")
        
        # Create species layers
        predictor.species_layer(predictor.species_df)
        print("✅ Species layers created")
        
        return predictor
        
    except Exception as e:
        print(f"❌ Error with prediction model: {e}")
        return None

def test_single_prediction(predictor, species_name):
    """Test prediction for a single species"""
    try:
        if species_name not in predictor.species_names:
            print(f"❌ Species '{species_name}' not available for prediction")
            available = predictor.species_names[:5]
            print(f"📋 Available species (first 5): {available}")
            species_name = available[0] if available else None
            
        if not species_name:
            print("❌ No species available for testing")
            return False
            
        print(f"🔮 Testing prediction for: {species_name}")
        
        # Train model
        trained_model = predictor.train_model(species_name)
        print("✅ Model trained")
        
        # Get predictions
        predicted_centroids = predictor.inference_model(species_name, trained_model)
        print(f"✅ Predictions generated: {len(predicted_centroids)} locations")
        
        # Show first few predictions
        for i, (x, y) in enumerate(predicted_centroids[:3]):
            print(f"   Location {i+1}: ({x:.2f}, {y:.2f})")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        return False

def main():
    print("🧪 Hong Kong Species Prediction Test")
    print("=" * 40)
    
    # Test 1: Species data
    test_species = test_species_data()
    if not test_species:
        print("❌ Cannot proceed without species data")
        return
    
    print()
    
    # Test 2: Prediction model
    predictor = test_prediction_model()
    if not predictor:
        print("❌ Cannot proceed without prediction model")
        return
    
    print()
    
    # Test 3: Single prediction
    success = test_single_prediction(predictor, test_species)
    
    print()
    if success:
        print("🎉 All tests passed! Prediction system is working.")
    else:
        print("❌ Prediction test failed.")

if __name__ == "__main__":
    main()