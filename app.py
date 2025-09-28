"""
Clean FastAPI backend for Hong Kong Species data
"""

import os
import gc
import json
import logging
from typing import Optional

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
    description="API for Hong Kong species data"
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
_global_predictor = None

# Prediction model - initialize on demand to save memory
_global_predictor = None
logger.info("⚠️ Prediction model will initialize on first use to save memory")

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

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hk-species-api"}

@app.get("/api/summary")
async def get_summary():
    """Get dataset summary statistics"""
    return get_data_summary()

@app.get("/api/species/list")
async def get_all_species(limit: int = Query(100, le=500)):
    """Get list of all available species"""
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
    """Get pre-computed 2025 predictions for a specific species"""
    species_index = get_species_index()
    
    if species_name not in species_index:
        raise HTTPException(status_code=404, detail="Species not found")
    
    try:
        from precompute_predictions import get_cached_prediction
        
        logger.info(f"📂 Getting cached prediction for {species_name}")
        
        # Get pre-computed prediction
        prediction = get_cached_prediction(species_name)
        
        if prediction is None:
            raise HTTPException(
                status_code=404, 
                detail=f"No 2025 predictions available for {species_name}. This species may have insufficient historical data for prediction modeling."
            )
        
        logger.info(f"✅ Returned cached prediction for {species_name}: {prediction['prediction_info']['predicted_locations']} locations")
        return prediction
        
    except Exception as e:
        logger.error(f"❌ Prediction error for {species_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Prediction service temporarily unavailable"
        )

@app.get("/api/districts")
async def get_districts_list():
    """Get list of all districts"""
    districts = get_districts()
    
    district_list = []
    for _, district in districts.iterrows():
        district_list.append({
            "name_en": district.get("name_en", "Unknown"),
            "name_tc": district.get("name_tc", "Unknown"),
            "area_code": district.get("area_code", "Unknown")
        })
    
    return {"districts": district_list}

@app.get("/api/districts/map")
async def get_districts_map():
    """Get GeoJSON map data for Hong Kong districts"""
    districts = get_districts()
    
    if districts.empty:
        raise HTTPException(status_code=404, detail="Districts data not available")
    
    try:
        districts_copy = districts.copy()
        
        for col in districts_copy.columns:
            if districts_copy[col].dtype == 'datetime64[ns]':
                districts_copy[col] = districts_copy[col].dt.strftime('%Y-%m-%d')
        
        districts_wgs84 = districts_copy.to_crs('EPSG:4326')
        geojson = json.loads(districts_wgs84.to_json())
        
        del districts_copy, districts_wgs84
        gc.collect()
        
        return {"type": "FeatureCollection", "features": geojson["features"]}
        
    except Exception as e:
        logger.error(f"Error processing districts map data: {e}")
        raise HTTPException(status_code=500, detail="Error processing districts map data")

@app.get("/api/map/bounds")
async def get_map_bounds():
    """Get Hong Kong map bounds for initial map view"""
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

@app.get("/api/families")
async def get_families():
    """Get list of all species families"""
    data_summary = get_data_summary()
    return {"families": data_summary.get("families", [])}

@app.get("/api/cache/info")
async def get_cache_info():
    """Get prediction model cache information"""
    try:
        from species_inference import get_cache_info
        return get_cache_info()
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/cache/clear")
async def clear_cache():
    """Clear prediction model cache to free memory"""
    try:
        from species_inference import clear_model_cache
        clear_model_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/status")
async def get_status():
    """Get API status and memory info"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    # Get cache info
    try:
        from species_inference import get_cache_info
        cache_info = get_cache_info()
    except:
        cache_info = {"cached_models": 0}
    
    return {
        "status": "running",
        "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
        "species_loaded": len(get_species_index()),
        "data_summary_loaded": bool(_data_summary),
        "districts_loaded": bool(_districts_cache),
        "prediction_model_ready": _global_predictor is not None,
        "cached_models": cache_info.get("cached_models", 0)
    }

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