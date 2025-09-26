"""
FastAPI backend for Hong Kong Species Search
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import geopandas as gpd
from pathlib import Path
from typing import List, Optional
import uvicorn
import pandas as pd
import sys
import importlib.util

from api_models import SpeciesSearchResponse, DistrictSpecies, MapData, DataSummary

app = FastAPI(title="Hong Kong Species API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data storage
species_index = {}
species_locations = None
districts = None
data_summary = {}
species_predictor = None

@app.on_event("startup")
async def load_data():
    """Load processed data on startup"""
    global species_index, species_locations, districts, data_summary, species_predictor
    
    data_dir = Path("processed")
    
    # Load species index
    with open(data_dir / "species_index.json") as f:
        species_index = json.load(f)
    
    # Load geospatial data
    species_locations = gpd.read_parquet(data_dir / "species_locations.parquet")
    districts = gpd.read_parquet(data_dir / "districts.parquet")
    
    # Load summary
    with open(data_dir / "data_summary.json") as f:
        data_summary = json.load(f)
    
    # Initialize species predictor (lazy loading for memory optimization)
    species_predictor = None
    print("Species predictor will be loaded on first prediction request")

@app.get("/")
async def root():
    return {"message": "Hong Kong Species API", "version": "1.0.0"}

@app.get("/api/summary", response_model=DataSummary)
async def get_summary():
    """Get dataset summary statistics"""
    return data_summary

@app.get("/api/species/list")
async def get_all_species():
    """Get list of all available species for dropdown"""
    species_list = []
    for name, data in species_index.items():
        species_list.append({
            "scientific_name": name,
            "family": data["family"],
            "occurrences_count": len(data["locations"])
        })
    
    # Sort by scientific name
    species_list.sort(key=lambda x: x["scientific_name"])
    
    return {"species": species_list, "total": len(species_list)}

@app.get("/api/species/search")
async def search_species(q: str = Query(None, description="Species name to search")):
    """Search for species by name (partial matching) or return all if no query"""
    matches = []
    
    if q:
        q_lower = q.lower()
        for name, data in species_index.items():
            if q_lower in name.lower():
                matches.append({
                    "scientific_name": name,
                    "family": data["family"],
                    "districts_count": len(data["districts"]),
                    "occurrences_count": len(data["locations"]),
                    "latest_date": data["latest_date"]
                })
    else:
        # Return all species if no query
        for name, data in species_index.items():
            matches.append({
                "scientific_name": name,
                "family": data["family"],
                "districts_count": len(data["districts"]),
                "occurrences_count": len(data["locations"]),
                "latest_date": data["latest_date"]
            })
    
    if not matches:
        raise HTTPException(status_code=404, detail="No species found matching query")
    
    return {"results": matches, "total": len(matches)}

@app.get("/api/species/{species_name}")
async def get_species_details(species_name: str):
    """Get detailed information for a specific species"""
    if species_name not in species_index:
        raise HTTPException(status_code=404, detail="Species not found")
    
    species_data = species_index[species_name]
    
    return SpeciesSearchResponse(
        species=species_data,
        total_occurrences=len(species_data["locations"]),
        districts_count=len(species_data["districts"])
    )

@app.get("/api/species/{species_name}/map")
async def get_species_map_data(species_name: str):
    """Get GeoJSON map data for a specific species"""
    if species_name not in species_index:
        raise HTTPException(status_code=404, detail="Species not found")
    
    # Filter species locations
    species_data = species_locations[
        species_locations['scientific_name'] == species_name
    ].copy()
    
    if species_data.empty:
        raise HTTPException(status_code=404, detail="No location data found")
    
    # Convert date column to string to avoid JSON serialization issues
    if 'date' in species_data.columns:
        species_data['date'] = species_data['date'].dt.strftime('%Y-%m-%d')
    
    # Convert to WGS84 for web mapping
    species_data_wgs84 = species_data.to_crs('EPSG:4326')
    
    # Convert to GeoJSON
    geojson = json.loads(species_data_wgs84.to_json())
    
    return MapData(features=geojson["features"])

@app.get("/api/districts")
async def get_districts():
    """Get list of all districts"""
    district_list = []
    for _, district in districts.iterrows():
        district_list.append({
            "name_en": district["name_en"],
            "name_tc": district["name_tc"],
            "area_code": district["area_code"]
        })
    
    return {"districts": district_list}

@app.get("/api/districts/map")
async def get_districts_map():
    """Get GeoJSON map data for Hong Kong districts"""
    # Make a copy to avoid modifying original data
    districts_copy = districts.copy()
    
    # Convert any datetime columns to strings
    for col in districts_copy.columns:
        if districts_copy[col].dtype == 'datetime64[ns]':
            districts_copy[col] = districts_copy[col].dt.strftime('%Y-%m-%d')
    
    # Convert to WGS84 for web mapping
    districts_wgs84 = districts_copy.to_crs('EPSG:4326')
    
    # Convert to GeoJSON
    geojson = json.loads(districts_wgs84.to_json())
    
    return MapData(features=geojson["features"])

@app.get("/api/districts/{district_name}/species")
async def get_district_species(district_name: str):
    """Get all species found in a specific district"""
    district_species = []
    
    for name, data in species_index.items():
        if district_name in data["districts"]:
            district_species.append({
                "scientific_name": name,
                "family": data["family"],
                "occurrences": len([loc for loc in data["locations"] 
                                 if loc["district"] == district_name])
            })
    
    if not district_species:
        raise HTTPException(status_code=404, detail="District not found or no species data")
    
    return DistrictSpecies(
        district_name=district_name,
        species_count=len(district_species),
        species_list=[s["scientific_name"] for s in district_species]
    )

@app.get("/api/families")
async def get_families():
    """Get list of all species families"""
    return {"families": data_summary["families"]}

@app.get("/api/families/{family_name}/species")
async def get_family_species(family_name: str):
    """Get all species in a specific family"""
    family_species = []
    
    for name, data in species_index.items():
        if data["family"].lower() == family_name.lower():
            family_species.append({
                "scientific_name": name,
                "districts_count": len(data["districts"]),
                "occurrences_count": len(data["locations"])
            })
    
    if not family_species:
        raise HTTPException(status_code=404, detail="Family not found")
    
    return {"family": family_name, "species": family_species, "count": len(family_species)}

@app.get("/api/map/bounds")
async def get_map_bounds():
    """Get Hong Kong map bounds for initial map view"""
    # Hong Kong approximate bounds in WGS84
    return {
        "bounds": {
            "north": 22.58,
            "south": 22.15,
            "east": 114.45,
            "west": 113.83
        },
        "center": {
            "lat": 22.3193,
            "lng": 114.1694
        },
        "zoom": 10
    }

@app.get("/api/species/{species_name}/predict-2025")
async def predict_species_2025(species_name: str):
    """Predict 2025 occurrence locations for a specific species"""
    global species_predictor
    
    if species_name not in species_index:
        raise HTTPException(status_code=404, detail="Species not found")
    
    # Lazy load species predictor
    if species_predictor is None:
        try:
            spec = importlib.util.spec_from_file_location("species_inference", "species_inference.py")
            species_inference = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(species_inference)
            species_predictor = species_inference.Species()
            species_predictor.prepare_data()
            species_predictor.get_species_names()
            species_predictor.species_layer(species_predictor.species_df)
            print("Species predictor loaded successfully")
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Prediction model not available: {str(e)}")
    
    try:
        # Check if species exists in predictor data
        if species_name not in species_predictor.species_names:
            raise HTTPException(status_code=404, detail="Species not available for prediction")
        
        # Train model and get predictions
        trained_model = species_predictor.train_model(species_name)
        predicted_centroids = species_predictor.inference_model(species_name, trained_model)
        
        # Convert centroids to GeoJSON format
        features = []
        for i, (x, y) in enumerate(predicted_centroids):
            # Convert to WGS84 coordinates (approximate conversion)
            lat = 22.3193 + (y - 820000) / 111000
            lng = 114.1694 + (x - 836000) / (111000 * 0.9135)  # cos(22.3193°)
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "properties": {
                    "species_name": species_name,
                    "prediction_id": i,
                    "year": 2025,
                    "confidence": "predicted",
                    "x_coord": x,
                    "y_coord": y
                }
            })
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "prediction_info": {
                "species_name": species_name,
                "predicted_locations": len(predicted_centroids),
                "prediction_year": 2025,
                "model_type": "neural_network"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/api/debug/species/{species_name}")
async def debug_species_data(species_name: str):
    """Debug endpoint to check species data structure"""
    if species_name not in species_index:
        raise HTTPException(status_code=404, detail="Species not found")
    
    # Get original data info
    species_data = species_locations[
        species_locations['scientific_name'] == species_name
    ]
    
    return {
        "species_name": species_name,
        "total_records": len(species_data),
        "columns": list(species_data.columns),
        "crs": str(species_data.crs),
        "sample_record": species_data.iloc[0].to_dict() if len(species_data) > 0 else None,
        "geometry_types": species_data.geometry.geom_type.unique().tolist() if len(species_data) > 0 else [],
        "prediction_available": species_predictor is not None and species_name in (species_predictor.species_names if species_predictor else [])
    }

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)