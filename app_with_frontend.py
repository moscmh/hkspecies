"""
Memory-optimized FastAPI backend with frontend serving
"""

import os
import gc
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import geopandas as gpd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hong Kong Species API", 
    version="1.0.0",
    description="Memory-optimized API for Hong Kong species data with web interface"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data storage - lazy loaded
_species_index = None
_data_summary = None
_districts_cache = None

def get_species_index():
    """Lazy load species index"""
    global _species_index
    if _species_index is None:
        try:
            with open("processed/species_index.json") as f:
                _species_index = json.load(f)
            logger.info(f"Loaded species index with {len(_species_index)} species")
        except Exception as e:
            logger.error(f"Failed to load species index: {e}")
            _species_index = {}
    return _species_index

def get_data_summary():
    """Lazy load data summary"""
    global _data_summary
    if _data_summary is None:
        try:
            with open("processed/data_summary.json") as f:
                _data_summary = json.load(f)
            logger.info("Loaded data summary")
        except Exception as e:
            logger.error(f"Failed to load data summary: {e}")
            _data_summary = {}
    return _data_summary

def load_species_locations(species_name: str):
    """Load specific species location data on demand"""
    try:
        df = gpd.read_parquet("processed/species_locations.parquet")
        species_data = df[df['scientific_name'] == species_name].copy()
        del df
        gc.collect()
        return species_data
    except Exception as e:
        logger.error(f"Failed to load species locations for {species_name}: {e}")
        return gpd.GeoDataFrame()

def get_districts():
    """Lazy load districts data"""
    global _districts_cache
    if _districts_cache is None:
        try:
            _districts_cache = gpd.read_parquet("processed/districts.parquet")
            logger.info("Loaded districts data")
        except Exception as e:
            logger.error(f"Failed to load districts: {e}")
            _districts_cache = gpd.GeoDataFrame()
    return _districts_cache

# Serve frontend
@app.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    return FileResponse("frontend.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "hk-species-api"}

@app.get("/api/summary")
async def get_summary():
    """Get dataset summary statistics"""
    return get_data_summary()

@app.get("/api/species/list")
async def get_all_species(limit: int = Query(100, le=500)):
    """Get list of all available species (with limit for memory optimization)"""
    species_index = get_species_index()
    
    species_list = []
    for name, data in list(species_index.items())[:limit]:
        species_list.append({
            "scientific_name": name,
            "family": data.get("family", "Unknown"),
            "occurrences_count": len(data.get("locations", []))
        })
    
    species_list.sort(key=lambda x: x["scientific_name"])
    
    return {
        "species": species_list, 
        "total": len(species_list),
        "total_available": len(species_index)
    }

@app.get("/api/species/search")
async def search_species(
    q: str = Query(None, description="Species name to search"),
    limit: int = Query(50, le=100)
):
    """Search for species by name"""
    species_index = get_species_index()
    matches = []
    
    if q:
        q_lower = q.lower()
        count = 0
        for name, data in species_index.items():
            if count >= limit:
                break
            if q_lower in name.lower():
                matches.append({
                    "scientific_name": name,
                    "family": data.get("family", "Unknown"),
                    "districts_count": len(data.get("districts", [])),
                    "occurrences_count": len(data.get("locations", [])),
                    "latest_date": data.get("latest_date", "Unknown")
                })
                count += 1
    
    if not matches and q:
        raise HTTPException(status_code=404, detail="No species found matching query")
    
    return {"results": matches, "total": len(matches)}

@app.get("/api/species/{species_name}")
async def get_species_details(species_name: str):
    """Get detailed information for a specific species"""
    species_index = get_species_index()
    
    if species_name not in species_index:
        raise HTTPException(status_code=404, detail="Species not found")
    
    species_data = species_index[species_name]
    
    return {
        "species": species_data,
        "total_occurrences": len(species_data.get("locations", [])),
        "districts_count": len(species_data.get("districts", []))
    }

@app.get("/api/species/{species_name}/map")
async def get_species_map_data(species_name: str):
    """Get GeoJSON map data for a specific species"""
    species_index = get_species_index()
    
    if species_name not in species_index:
        raise HTTPException(status_code=404, detail="Species not found")
    
    species_data = load_species_locations(species_name)
    
    if species_data.empty:
        raise HTTPException(status_code=404, detail="No location data found")
    
    try:
        if 'date' in species_data.columns:
            species_data['date'] = species_data['date'].dt.strftime('%Y-%m-%d')
        
        species_data_wgs84 = species_data.to_crs('EPSG:4326')
        geojson = json.loads(species_data_wgs84.to_json())
        
        del species_data, species_data_wgs84
        gc.collect()
        
        return {"type": "FeatureCollection", "features": geojson["features"]}
        
    except Exception as e:
        logger.error(f"Error processing map data for {species_name}: {e}")
        raise HTTPException(status_code=500, detail="Error processing map data")

@app.get("/api/species/{species_name}/predict-2025")
async def predict_species_2025(species_name: str):
    """Predict 2025 occurrence locations for a specific species"""
    species_index = get_species_index()
    
    if species_name not in species_index:
        raise HTTPException(status_code=404, detail="Species not found")
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("species_inference", "species_inference.py")
        species_inference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(species_inference)
        
        species_predictor = species_inference.Species()
        species_predictor.prepare_data()
        species_predictor.get_species_names()
        species_predictor.species_layer(species_predictor.species_df)
        
        if species_name not in species_predictor.species_names:
            raise HTTPException(status_code=404, detail="Species not available for prediction")
        
        trained_model = species_predictor.train_model(species_name)
        predicted_centroids = species_predictor.inference_model(species_name, trained_model)
        
        features = []
        for i, (x, y) in enumerate(predicted_centroids):
            lat = 22.3193 + (y - 820000) / 111000
            lng = 114.1694 + (x - 836000) / (111000 * 0.9135)
            
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
                    "confidence": "predicted"
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        workers=1,
        access_log=False
    )