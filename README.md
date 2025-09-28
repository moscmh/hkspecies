# Hong Kong Species Prediction API

Interactive web application for exploring Hong Kong's biodiversity with AI-powered 2025 species occurrence predictions.

## 🌟 Features

- **Species Search & Exploration** - Browse 1000+ Hong Kong species
- **Interactive Maps** - Visualize species occurrences with Leaflet maps
- **AI Predictions** - Neural network predictions for 2025 species locations
- **Real-time Data** - Species occurrence data from 2001-2024
- **Responsive Design** - Works on desktop and mobile devices

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- 2GB+ RAM recommended

### Installation
```bash
# Clone repository
git clone <your-repo-url>
cd hkspecies

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Locally
```bash
# For local development and showcasing
python species_api.py

# Access application
open http://localhost:8000
```

### Features Available Locally
- ✅ Full species database
- ✅ Interactive maps
- ✅ AI predictions (lazy-loaded)
- ✅ Auto-reload for development
- ✅ Detailed logging

## 🌐 Production Deployment (AWS Lightsail)

### Prerequisites
- AWS CLI configured
- AWS Lightsail access

### Deploy to Cloud
```bash
# Use the production version
python app.py
```

### Production Features
- ✅ Memory optimization
- ✅ Prediction model caching
- ✅ Production logging
- ✅ CORS configuration
- ✅ Health monitoring

## 📊 API Endpoints

### Core Endpoints
- `GET /` - Web interface
- `GET /health` - Health check
- `GET /api/summary` - Dataset statistics
- `GET /api/species/list` - List all species
- `GET /api/species/search?q=<query>` - Search species

### Species Details
- `GET /api/species/{name}` - Species information
- `GET /api/species/{name}/map` - Species occurrence map
- `GET /api/species/{name}/predict-2025` - AI predictions

### Utility
- `GET /api/status` - System status
- `GET /api/cache/info` - Cache information
- `POST /api/cache/clear` - Clear prediction cache

## 🧠 AI Prediction Model

### Neural Network Architecture
- **Input**: 20x20 grid of historical occurrences (2001-2024)
- **Hidden Layer**: 512 neurons with sigmoid activation
- **Output**: 400 neurons (20x20 grid) for 2025 predictions
- **Training**: Adam optimizer, MSE loss, 3 epochs

### Performance Optimizations
- **Model Caching**: Trained models cached for instant reuse
- **Lazy Loading**: Prediction model loads on first use
- **Memory Management**: Automatic garbage collection
- **Fast Training**: Optimized hyperparameters

## 📁 Project Structure

```
hkspecies/
├── species_api.py          # Local development server
├── app.py                  # Production server
├── frontend.html           # Web interface
├── species_inference.py    # AI prediction model
├── requirements.txt        # Python dependencies
├── processed/              # Processed data files
├── boundaries/             # Hong Kong district boundaries
├── species/                # Raw species data (2001-2024)
└── hk.tif                 # Hong Kong map raster
```

## 🔧 Development vs Production

| Feature | Local (`species_api.py`) | Production (`app.py`) |
|---------|-------------------------|----------------------|
| **Host** | 127.0.0.1 (local only) | 0.0.0.0 (public) |
| **Auto-reload** | ✅ Enabled | ❌ Disabled |
| **Prediction Loading** | Lazy (on-demand) | Startup (pre-loaded) |
| **Logging** | Verbose | Optimized |
| **Memory Usage** | Higher (dev features) | Lower (optimized) |

## 💡 Usage Examples

### Local Development
```bash
# Start development server
python species_api.py

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/api/species/search?q=bird
```

### Production Deployment
```bash
# Start production server
python app.py

# Monitor status
curl http://your-server:8000/api/status
```

## 🐛 Troubleshooting

### Memory Issues
```bash
# Check memory usage
curl http://localhost:8000/api/status

# Clear prediction cache
curl -X POST http://localhost:8000/api/cache/clear
```

### Missing Dependencies
```bash
# Install geospatial libraries (Ubuntu/Debian)
sudo apt install gdal-bin libgdal-dev libproj-dev libgeos-dev

# Reinstall Python packages
pip install --force-reinstall -r requirements.txt
```

## 📈 Performance

- **Startup Time**: ~30-60 seconds (data loading)
- **First Prediction**: ~3-5 seconds (model training)
- **Cached Predictions**: ~0.5-1 second
- **Memory Usage**: ~200-500MB (depending on cache)

## 🎯 Use Cases

1. **Research & Education** - Explore Hong Kong biodiversity
2. **Conservation Planning** - Predict future species distributions
3. **Environmental Monitoring** - Track species occurrence trends
4. **Public Engagement** - Interactive species exploration

## 📄 License

This project is for educational and research purposes.

## 🤝 Contributing

1. Use `species_api.py` for local development
2. Test changes thoroughly
3. Ensure compatibility with production `app.py`
4. Update documentation as needed