"""
Lightweight FastAPI backend - No predictions to save memory
"""

import os
import gc
import json
import logging

import pandas as pd
import geopandas as gpd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Hong Kong Species API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_species_index = None
_data_summary = None

def get_species_index():
    global _species_index
    if _species_index is None:
        try:
            with open("processed/species_index.json") as f:
                _species_index = json.load(f)
            logger.info(f"Loaded {len(_species_index)} species")
        except Exception as e:
            logger.error(f"Failed to load species: {e}")
            _species_index = {}
    return _species_index

def get_data_summary():
    global _data_summary
    if _data_summary is None:
        try:
            with open("processed/data_summary.json") as f:
                _data_summary = json.load(f)
        except Exception as e:
            _data_summary = {}
    return _data_summary

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hk-species-api-lite"}

@app.get("/api/summary")
async def get_summary():
    return get_data_summary()

@app.get("/api/species/list")
async def get_all_species(limit: int = Query(100, le=500)):
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
async def search_species(q: str = Query(None), limit: int = Query(50, le=100)):
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
    
    return {"results": matches, "total": len(matches)}

@app.get("/api/species/{species_name}")
async def get_species_details(species_name: str):
    species_index = get_species_index()
    
    if species_name not in species_index:
        raise HTTPException(status_code=404, detail="Species not found")
    
    species_data = species_index[species_name]
    
    return {
        "species": species_data,
        "total_occurrences": len(species_data.get("locations", [])),
        "districts_count": len(species_data.get("districts", []))
    }

@app.get("/api/species/{species_name}/predict-2025")
async def predict_species_2025(species_name: str):
    raise HTTPException(status_code=503, detail="Predictions disabled in lite version - upgrade instance for full features")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)