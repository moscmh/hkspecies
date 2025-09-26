# Railway Deployment Guide for Hong Kong Species API

## Overview
This guide helps you deploy your Hong Kong Species API to Railway with memory optimizations to avoid out-of-memory errors.

## Files Created for Railway Deployment

### Core Files
- `app.py` - Memory-optimized FastAPI application
- `requirements.txt` - Updated with CPU-only PyTorch and all dependencies
- `Procfile` - Tells Railway how to start your app
- `railway.json` - Railway-specific configuration
- `.gitignore` - Excludes large files from deployment

## Memory Optimizations Applied

1. **Lazy Loading**: Data is loaded only when needed
2. **Garbage Collection**: Explicit memory cleanup after operations
3. **CPU-only PyTorch**: Smaller memory footprint
4. **Single Worker**: Reduces memory usage
5. **Limited Query Results**: Prevents loading too much data at once
6. **On-demand Species Data**: Loads specific species data only when requested

## Deployment Steps

### 1. Prepare Your Repository
```bash
cd /Users/moswai/Documents/Mos_DataScience/project/Hackathon/AWS_AI_HK/hkspecies

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit for Railway deployment"

# Push to GitHub (create repo first)
git remote add origin https://github.com/yourusername/hk-species-api.git
git push -u origin main
```

### 2. Deploy to Railway

1. Go to [Railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway will automatically detect the Python app and deploy

### 3. Monitor Deployment

- Check the deployment logs in Railway dashboard
- Visit the provided URL to test your API
- Use `/health` endpoint to check if the service is running
- Use `/api/status` endpoint to monitor memory usage

## API Endpoints

### Health & Status
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/status` - Memory and status info

### Species Data
- `GET /api/species/list?limit=100` - List species (with limit)
- `GET /api/species/search?q=species_name&limit=50` - Search species
- `GET /api/species/{species_name}` - Species details
- `GET /api/species/{species_name}/map` - Species map data

### Geographic Data
- `GET /api/districts` - List districts
- `GET /api/districts/map` - Districts map data
- `GET /api/map/bounds` - Hong Kong map bounds

### Other
- `GET /api/summary` - Dataset summary
- `GET /api/families` - List families

## Memory Management Features

1. **Lazy Loading**: Data loaded only when requested
2. **Automatic Cleanup**: Memory freed after each request
3. **Query Limits**: Prevents loading too much data
4. **Status Monitoring**: `/api/status` shows memory usage

## Troubleshooting

### If deployment fails:
1. Check Railway logs for specific errors
2. Ensure all required files are in the repository
3. Verify `processed/` directory contains the required data files

### If memory issues persist:
1. Reduce query limits in the API
2. Consider upgrading Railway plan for more memory
3. Monitor memory usage via `/api/status` endpoint

### If data loading fails:
1. Ensure `processed/` directory is included in deployment
2. Check file paths are correct
3. Verify data files are not corrupted

## Railway Plans

- **Hobby Plan**: 512MB RAM (may be tight for your data)
- **Pro Plan**: 8GB RAM (recommended for your use case)

## Next Steps

1. Test the deployment locally first:
   ```bash
   python app.py
   ```

2. Push to GitHub and deploy to Railway

3. Monitor memory usage and performance

4. Consider upgrading Railway plan if needed