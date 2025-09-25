"""
Data models for the Hong Kong Species API
"""

from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class Location(BaseModel):
    lat: float
    lon: float
    district: str
    date: str

class SpeciesInfo(BaseModel):
    scientific_name: str
    family: str
    districts: List[str]
    locations: List[Location]
    latest_date: str

class SpeciesSearchResponse(BaseModel):
    species: SpeciesInfo
    total_occurrences: int
    districts_count: int

class DistrictSpecies(BaseModel):
    district_name: str
    species_count: int
    species_list: List[str]

class MapData(BaseModel):
    type: str = "FeatureCollection"
    features: List[Dict]

class DataSummary(BaseModel):
    total_species: int
    total_districts: int
    total_occurrences: int
    families: List[str]
    date_range: Dict[str, str]