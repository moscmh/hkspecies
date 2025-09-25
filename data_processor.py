#!/usr/bin/env python3
"""
Hong Kong Species Data Processing Pipeline
Cleans and optimizes geospatial datasets for API consumption
"""

import geopandas as gpd
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HKSpeciesDataProcessor:
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.output_dir = self.data_dir / "processed"
        self.output_dir.mkdir(exist_ok=True)
        
    def load_raw_data(self) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """Load and validate raw shapefiles"""
        logger.info("Loading raw datasets...")
        
        # Load districts
        districts = gpd.read_file(self.data_dir / 'boundaries/Hong_Kong_District_Boundary.shp')
        logger.info(f"Loaded {len(districts)} districts")
        
        # Load all species data from 2001-2024
        species_list = []
        for year in range(2001, 2025):
            file_path = self.data_dir / f'species/O{year}.shp'
            if file_path.exists():
                year_data = gpd.read_file(file_path)
                year_data['year'] = year
                species_list.append(year_data)
                logger.info(f"Loaded {len(year_data)} records from {year}")
            else:
                logger.warning(f"File not found: {file_path}")
        
        # Combine all years
        species = pd.concat(species_list, ignore_index=True)
        logger.info(f"Total loaded: {len(species)} species records from all years")
        
        return districts, species
    
    def clean_districts(self, districts: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Clean and standardize district data"""
        logger.info("Cleaning district data...")
        
        # Keep only essential columns
        districts_clean = districts[['NAME_EN', 'NAME_TC', 'AREA_CODE', 'geometry']].copy()
        
        # Standardize column names
        districts_clean.columns = ['name_en', 'name_tc', 'area_code', 'geometry']
        
        # Ensure consistent CRS (Hong Kong 1980 Grid System)
        if districts_clean.crs != 'EPSG:2326':
            districts_clean = districts_clean.to_crs('EPSG:2326')
            
        return districts_clean
    
    def clean_species(self, species: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Clean and standardize species data"""
        logger.info("Cleaning species data...")
        
        # Keep essential columns
        species_clean = species[['scientific', 'family', 'date', 'geometry']].copy()
        
        # Standardize column names
        species_clean.columns = ['scientific_name', 'family', 'date', 'geometry']
        
        # Convert date to datetime
        species_clean['date'] = pd.to_datetime(species_clean['date'])
        
        # Ensure consistent CRS
        if species_clean.crs != 'EPSG:2326':
            species_clean = species_clean.to_crs('EPSG:2326')
            
        # Remove duplicates
        species_clean = species_clean.drop_duplicates()
        
        return species_clean
    
    def create_species_district_mapping(self, species: gpd.GeoDataFrame, 
                                      districts: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Create spatial overlay mapping species to districts"""
        logger.info("Creating species-district spatial mapping...")
        
        # Spatial overlay
        species_districts = gpd.overlay(species, districts, how='intersection')
        
        # Add centroid coordinates for map display
        centroids = species_districts.geometry.centroid
        species_districts['lat'] = centroids.y
        species_districts['lon'] = centroids.x
        
        return species_districts
    
    def generate_species_index(self, species_districts: gpd.GeoDataFrame) -> Dict:
        """Generate searchable species index"""
        logger.info("Generating species search index...")
        
        species_index = {}
        
        for _, row in species_districts.iterrows():
            name = row['scientific_name']
            if name not in species_index:
                species_index[name] = {
                    'scientific_name': name,
                    'family': row['family'],
                    'districts': set(),
                    'locations': [],
                    'latest_date': row['date']
                }
            
            # Add district
            species_index[name]['districts'].add(row['name_en'])
            
            # Add location
            species_index[name]['locations'].append({
                'lat': float(row['lat']),
                'lon': float(row['lon']),
                'district': row['name_en'],
                'date': row['date'].isoformat()
            })
            
            # Update latest date
            if row['date'] > species_index[name]['latest_date']:
                species_index[name]['latest_date'] = row['date']
        
        # Convert sets to lists for JSON serialization
        for species_data in species_index.values():
            species_data['districts'] = list(species_data['districts'])
            species_data['latest_date'] = species_data['latest_date'].isoformat()
        
        return species_index
    
    def save_processed_data(self, districts: gpd.GeoDataFrame, 
                          species_districts: gpd.GeoDataFrame,
                          species_index: Dict):
        """Save processed data in multiple formats"""
        logger.info("Saving processed data...")
        
        # Save as GeoJSON for web use
        districts.to_file(self.output_dir / 'districts.geojson', driver='GeoJSON')
        species_districts.to_file(self.output_dir / 'species_locations.geojson', driver='GeoJSON')
        
        # Save as Parquet for fast loading
        districts.to_parquet(self.output_dir / 'districts.parquet')
        species_districts.to_parquet(self.output_dir / 'species_locations.parquet')
        
        # Save species index as JSON
        with open(self.output_dir / 'species_index.json', 'w') as f:
            json.dump(species_index, f, indent=2)
        
        # Generate summary statistics
        stats = {
            'total_species': len(species_index),
            'total_districts': len(districts),
            'total_occurrences': len(species_districts),
            'families': list(set(species_districts['family'].unique())),
            'date_range': {
                'start': species_districts['date'].min().isoformat(),
                'end': species_districts['date'].max().isoformat()
            }
        }
        
        with open(self.output_dir / 'data_summary.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Processed data saved to {self.output_dir}")
        return stats
    
    def process_all(self) -> Dict:
        """Run complete data processing pipeline"""
        logger.info("Starting data processing pipeline...")
        
        # Load raw data
        districts_raw, species_raw = self.load_raw_data()
        
        # Clean data
        districts_clean = self.clean_districts(districts_raw)
        species_clean = self.clean_species(species_raw)
        
        # Create spatial mapping
        species_districts = self.create_species_district_mapping(species_clean, districts_clean)
        
        # Generate search index
        species_index = self.generate_species_index(species_districts)
        
        # Save processed data
        stats = self.save_processed_data(districts_clean, species_districts, species_index)
        
        logger.info("Data processing pipeline completed!")
        return stats

if __name__ == "__main__":
    processor = HKSpeciesDataProcessor()
    stats = processor.process_all()
    print(f"\nProcessing Summary:")
    print(f"- {stats['total_species']} unique species")
    print(f"- {stats['total_districts']} districts")
    print(f"- {stats['total_occurrences']} occurrence records")
    print(f"- Date range: {stats['date_range']['start']} to {stats['date_range']['end']}")