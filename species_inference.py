# Output inferenced centroids for a specific species

# Library
import numpy as np
import geopandas as gpd, pandas as pd
import shapely
import matplotlib.pyplot as plt
import rasterio, rasterstats
import contextily
import os

import torch
import torch.nn as nn
import random


# Species class for model training, inference, and visualisation
class Species:
    def __init__(self, 
                 species_years=np.arange(2001, 2025),
                 species_directory='species'):
        self.hkmap = rasterio.open('hk.tif', mode='r+')
        self.hkmap_array = self.hkmap.read(1)
        self.districts = gpd.read_file('boundaries/Hong_Kong_District_Boundary.shp')
        self.districts.to_crs(self.hkmap.crs, inplace=True)
        self.bound_left = self.hkmap.bounds.left
        self.bound_right = self.hkmap.bounds.right
        self.bound_top = self.hkmap.bounds.top
        self.bound_bottom = self.hkmap.bounds.bottom
        self.extent = (self.bound_left, self.bound_right, self.bound_bottom, self.bound_top)
        self.species_years = species_years
        self.species_directory = species_directory

        self.species_df = gpd.GeoDataFrame()
        for year in self.species_years:
            try:
                year_data = gpd.read_file(f'{self.species_directory}/O{year}.shp', engine='pyogrio')
                year_data['year'] = year
                self.species_df = pd.concat([self.species_df, year_data], ignore_index=True)
            except Exception as e:
                print(f"Error processing {year}: {e}")
        self.species_df.to_crs(self.hkmap.crs, inplace=True)

    def prepare_data(self, x_bins=20, y_bins=20):
        self.species_df['date'] = pd.to_datetime(self.species_df['date'])
        self.species_df['month'] = self.species_df['date'].dt.month
        self.species_df.drop(columns=['OBJECTID', 'OBJECTID_1'], inplace=True)
        self.species_df = self.species_df.astype({'year': 'int32'})
        self.species_df.drop(columns=['Shape__Are', 'Shape__Len', 'date'], inplace=True)
        self.species_df['centroid'] = self.species_df['geometry'].centroid
        self.species_df['x'] = self.species_df['centroid'].x
        self.species_df['y'] = self.species_df['centroid'].y

        self.x_bins = np.linspace(self.extent[0], self.extent[1], x_bins + 1)
        self.y_bins = np.linspace(self.extent[2], self.extent[3], y_bins + 1)
        self.species_df['x_bin'] = pd.cut(self.species_df['x'], bins=self.x_bins, labels=False)
        self.species_df['y_bin'] = pd.cut(self.species_df['y'], bins=self.y_bins, labels=False)

        self.grid_cells = self.create_grid()
        self.species_df['grid_id'] = self.species_df.apply(lambda row: self.griding(self.grid_cells, row['x_bin'], row['y_bin']), axis=1)

    def create_grid(self, x_bins=20, y_bins=20):
        self.grid_cells = []
        for i in range(y_bins):
            for j in range(x_bins):
                cell = {
                    'y_bin': i,
                    'x_bin': j,
                    'id': i * x_bins + j
                }
                self.grid_cells.append(cell)
        return self.grid_cells
    
    def griding(self, grid_cells, x_bin=20, y_bin=20):
        for grid in grid_cells:
            if grid['x_bin'] == x_bin and grid['y_bin'] == y_bin:
                return grid['id']
        return None

    def species_layer(self, species_df):
        self.species_layers = {}
        for s in self.species_names:
            layer = np.zeros((len(self.species_years), 20, 20), dtype=int)
            species_data = species_df[species_df['scientific'] == s]
            for _, row in species_data.iterrows():
                if pd.notnull(row['x_bin']) and pd.notnull(row['y_bin']):
                    layer[row['year'] - 2001, 19 - int(row['y_bin']), int(row['x_bin'])] += 1
            self.species_layers[s] = layer
        return None

    def get_species_names(self):
        try:
            self.species_names = sorted(self.species_df['scientific'].unique().tolist())
        except Exception as e:
            print(f"Error getting species names: {e}")
        return None

    def train_model(self, a_species):
        # Initialize the network and print its architecture
        self.model = Net()

        # Specify loss function and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.SGD(self.model.parameters(), lr=0.01)

        # Define device
        device = torch.device('mpu' if torch.cuda.is_available() else 'cpu')

        # Specify species for training and inference
        species_layer = self.species_layers[a_species]
        X = torch.tensor(species_layer[:23, :, :]).reshape(23, -1).to(torch.float32)  # Flatten X like Y
        y = torch.tensor(species_layer[1:, :, :]).reshape(23, -1).to(torch.float32)

        # Number of epochs for training
        n_epochs = 5  # For a faster demo; consider using between 20-50 epochs for real training
        self.model.train()  # Set the model to training mode
        for epoch in range(n_epochs):
            train_loss = 0.0
            
            # Train the model on each batch
            data, target = X.to(device), y.to(device)  # Move data to GPU if available
            optimizer.zero_grad()         # Clear gradients
            output = self.model(data)            # Forward pass
            loss = criterion(output, target)  # Calculate loss
            loss.backward()                 # Backward pass
            optimizer.step()                # Update parameters
            train_loss += loss.item()# * data.size(0)  # Accumulate loss
            
            # Calculate average loss over the epoch
            # train_loss = train_loss / len(train_loader.dataset)
            # print('Epoch: {} \tTraining Loss: {:.6f}'.format(epoch+1, train_loss))

        return self.model

    def train_model_fast(self, a_species):
        """CNN-LSTM training with optimized parameters"""
        # Set deterministic seed
        set_seed(48)
        
        # Initialize CNN-LSTM model
        self.model = ConvLSTM(input_dim=1, hidden_dim=1, kernel_size=(3, 3),
                              num_layers=1, batch_first=True, bias=True, return_all_layers=False)
        
        # Device setup
        device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        self.model.to(device)
        
        # Loss and optimizer
        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        # Prepare data in CNN-LSTM format
        species_layer = self.species_layers[a_species]
        X_train = torch.tensor(species_layer[:22, :, :]).to(torch.float32).reshape(1, 22, 1, 20, 20)
        y_train = torch.tensor(species_layer[22, :, :]).to(torch.float32).reshape(1, 1, 20, 20)
        
        # Training loop
        n_epochs = 20  # Reduced for faster training
        self.model.train()
        best_loss = float('inf')
        early_stopping_counter = 0
        
        for epoch in range(n_epochs):
            data = X_train.to(device)
            target = y_train.to(device)
            
            optimizer.zero_grad()
            output = self.model(data)[1][-1][0]  # Get last hidden state
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            # Early stopping
            if loss.item() < best_loss:
                best_loss = loss.item()
                early_stopping_counter = 0
            else:
                early_stopping_counter += 1
            
            if early_stopping_counter >= 5:
                break
        
        return self.model

    def inference_model(self, a_species, model):
        """CNN-LSTM inference for 2025 prediction"""
        model = self.model
        species_layer = self.species_layers[a_species]
        
        # Device setup
        device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        
        model.eval()
        with torch.no_grad():
            # Use all available years for 2025 prediction
            test_data = torch.tensor(species_layer[-species_layer.shape[0]+2:, :, :]).unsqueeze(0).unsqueeze(2).to(torch.float32).to(device)
            test_output = model(test_data)[1][-1][0]  # Get last hidden state
            predicted_grid = test_output[:, -1, :, :].cpu().numpy().reshape(20, 20)

        # Process predictions with likelihood values
        grid_ids = []
        likelihood_values = []
        for i in range(20):  # y-axis (rows)
            for j in range(20):  # x-axis (columns)
                likelihood_val = predicted_grid[predicted_grid.shape[0]-1-i, j]
                if likelihood_val > 0:  # Include positive predictions
                    grid_ids.append((j, 19-i))  # Fix: j=x_bin, 19-i=y_bin (flip y-axis)
                    likelihood_values.append(max(0, likelihood_val))  # Ensure non-negative

        # Convert grid_ids to centroids and grid bounds
        centroids = []
        grid_bounds = []
        for idx, grid in enumerate(grid_ids):
            x_bin, y_bin = grid
            x_center = (self.x_bins[x_bin] + self.x_bins[x_bin + 1]) / 2
            y_center = (self.y_bins[y_bin] + self.y_bins[y_bin + 1]) / 2
            centroids.append((x_center, y_center))
            
            # Store actual grid cell bounds with likelihood
            grid_bounds.append({
                'x_min': self.x_bins[x_bin],
                'x_max': self.x_bins[x_bin + 1],
                'y_min': self.y_bins[y_bin],
                'y_max': self.y_bins[y_bin + 1],
                'likelihood': likelihood_values[idx]
            })

        return centroids, grid_bounds
    
    def visualise(self, species, centroids):
        # Visualise the centroids on the map
        fig, ax = plt.subplots(figsize=(15, 15))
        ax.imshow(self.hkmap_array, extent=self.extent, origin='upper', vmin=self.hkmap_array.min(), vmax=self.hkmap_array.max())
        self.districts.boundary.plot(ax=ax, color='red', linewidth=0.5)
        for centroid in centroids:
            ax.plot(centroid[0], centroid[1], 'ro')  # Plot centroids as red dots
        ax.set_axis_off()
        ax.set(xlim=(self.bound_left, self.bound_right), ylim=(self.bound_bottom, self.bound_top))
        plt.title(f"{species} Predicted Locations in 2025", fontsize=20)
        plt.show()

        return None

# CNN-LSTM Model Classes
class ConvLSTMCell(nn.Module):
    def __init__(self, input_dim, hidden_dim, kernel_size, bias):
        super(ConvLSTMCell, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.padding = kernel_size[0] // 2, kernel_size[1] // 2
        self.bias = bias
        self.conv = nn.Conv2d(in_channels=self.input_dim + self.hidden_dim,
                              out_channels=4 * self.hidden_dim,
                              kernel_size=self.kernel_size,
                              padding=self.padding,
                              bias=self.bias)

    def forward(self, input_tensor, cur_state):
        h_cur, c_cur = cur_state
        combined = torch.cat([input_tensor, h_cur], dim=1)
        combined_conv = self.conv(combined)
        cc_i, cc_f, cc_o, cc_g = torch.split(combined_conv, self.hidden_dim, dim=1)
        i = torch.sigmoid(cc_i)
        f = torch.sigmoid(cc_f)
        o = torch.sigmoid(cc_o)
        g = torch.tanh(cc_g)
        c_next = f * c_cur + i * g
        h_next = o * torch.tanh(c_next)
        return h_next, c_next

    def init_hidden(self, batch_size, image_size):
        height, width = image_size
        return (torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device),
                torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device))

class ConvLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, kernel_size, num_layers,
                 batch_first=False, bias=True, return_all_layers=False):
        super(ConvLSTM, self).__init__()
        self._check_kernel_size_consistency(kernel_size)
        kernel_size = self._extend_for_multilayer(kernel_size, num_layers)
        hidden_dim = self._extend_for_multilayer(hidden_dim, num_layers)
        if not len(kernel_size) == len(hidden_dim) == num_layers:
            raise ValueError('Inconsistent list length.')
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.num_layers = num_layers
        self.batch_first = batch_first
        self.bias = bias
        self.return_all_layers = return_all_layers
        cell_list = []
        for i in range(0, self.num_layers):
            cur_input_dim = self.input_dim if i == 0 else self.hidden_dim[i - 1]
            cell_list.append(ConvLSTMCell(input_dim=cur_input_dim,
                                          hidden_dim=self.hidden_dim[i],
                                          kernel_size=self.kernel_size[i],
                                          bias=self.bias))
        self.cell_list = nn.ModuleList(cell_list)

    def forward(self, input_tensor, hidden_state=None):
        if not self.batch_first:
            input_tensor = input_tensor.permute(1, 0, 2, 3, 4)
        b, _, _, h, w = input_tensor.size()
        if hidden_state is not None:
            raise NotImplementedError()
        else:
            hidden_state = self._init_hidden(batch_size=b, image_size=(h, w))
        layer_output_list = []
        last_state_list = []
        seq_len = input_tensor.size(1)
        cur_layer_input = input_tensor
        for layer_idx in range(self.num_layers):
            h, c = hidden_state[layer_idx]
            output_inner = []
            for t in range(seq_len):
                h, c = self.cell_list[layer_idx](input_tensor=cur_layer_input[:, t, :, :, :],
                                                 cur_state=[h, c])
                output_inner.append(h)
            layer_output = torch.stack(output_inner, dim=1)
            cur_layer_input = layer_output
            layer_output_list.append(layer_output)
            last_state_list.append([h, c])
        if not self.return_all_layers:
            layer_output_list = layer_output_list[-1:]
            last_state_list = last_state_list[-1:]
        return layer_output_list, last_state_list

    def _init_hidden(self, batch_size, image_size):
        init_states = []
        for i in range(self.num_layers):
            init_states.append(self.cell_list[i].init_hidden(batch_size, image_size))
        return init_states

    @staticmethod
    def _check_kernel_size_consistency(kernel_size):
        if not (isinstance(kernel_size, tuple) or
                (isinstance(kernel_size, list) and all([isinstance(elem, tuple) for elem in kernel_size]))):
            raise ValueError('`kernel_size` must be tuple or list of tuples')

    @staticmethod
    def _extend_for_multilayer(param, num_layers):
        if not isinstance(param, list):
            param = [param] * num_layers
        return param

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":16:8"
    torch.use_deterministic_algorithms(True)
    
def main():
    # Initialize Species class
    species_instance = Species()
    
    # Prepare data
    species_instance.prepare_data()
    
    # Create grid
    species_instance.create_grid()
    
    # Get species names
    species_instance.get_species_names()
    
    # Create species layers
    species_instance.species_layer(species_instance.species_df)
    
    # Train and infer for a sample species
    a_species = species_instance.species_names[0]  # Example: first species in the list
    trained_model = species_instance.train_model(a_species)
    centroids = species_instance.inference_model(a_species, trained_model)
    species_instance.visualise(a_species, centroids)

# Global predictor instance - loaded once at startup
_global_predictor = None
_trained_models_cache = {}

def get_global_predictor():
    """Get or initialize the global predictor instance"""
    global _global_predictor
    if _global_predictor is None:
        print("🔮 Initializing prediction model...")
        _global_predictor = Species()
        _global_predictor.prepare_data()
        _global_predictor.create_grid()
        _global_predictor.get_species_names()
        _global_predictor.species_layer(_global_predictor.species_df)
        print(f"✅ Prediction model ready with {len(_global_predictor.species_names)} species")
    return _global_predictor

def fast_predict_with_global_predictor(predictor, species_name):
    """Fast prediction using pre-loaded predictor with model caching"""
    global _trained_models_cache
    
    try:
        # Import memory utilities
        from memory_optimizer import MemoryMonitor, clear_memory
        monitor = MemoryMonitor()
        
        # Check memory before prediction
        monitor.check_memory()
        
        # Check if species exists
        if species_name not in predictor.species_names:
            return None
        
        # Check if model is already trained and cached
        if species_name not in _trained_models_cache:
            print(f"🎨 Training model for {species_name}...")
            trained_model = predictor.train_model_fast(species_name)
            _trained_models_cache[species_name] = trained_model
            print(f"✅ Model cached for {species_name}")
            
            # Clear memory after training
            clear_memory()
        else:
            print(f"💾 Using cached model for {species_name}")
            trained_model = _trained_models_cache[species_name]
        
        # Get predictions using cached model
        result = predictor.inference_model(species_name, trained_model)
        
        if not result:
            return None
            
        centroids, grid_bounds = result
        
        # Convert coordinates to WGS84 for web display
        import geopandas as gpd
        from shapely.geometry import Point
        
        # Create GeoDataFrame with predictions
        points = [Point(x, y) for x, y in centroids]
        gdf = gpd.GeoDataFrame(geometry=points, crs=predictor.hkmap.crs)
        gdf_wgs84 = gdf.to_crs('EPSG:4326')
        
        # Convert to GeoJSON format with grid boxes only
        features = []
        for i, point in enumerate(gdf_wgs84.geometry):
            # Get actual grid bounds from model
            bounds = grid_bounds[i]
            
            # Convert grid bounds to WGS84
            from shapely.geometry import box
            grid_box = box(bounds['x_min'], bounds['y_min'], bounds['x_max'], bounds['y_max'])
            grid_gdf = gpd.GeoDataFrame([1], geometry=[grid_box], crs=predictor.hkmap.crs)
            grid_wgs84 = grid_gdf.to_crs('EPSG:4326')
            
            # Get polygon coordinates
            poly_coords = list(grid_wgs84.geometry.iloc[0].exterior.coords)
            min_x, min_y = poly_coords[0]
            max_x, max_y = poly_coords[2]
            
            # Add grid box feature with likelihood
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [min_x, min_y],
                        [max_x, min_y],
                        [max_x, max_y],
                        [min_x, max_y],
                        [min_x, min_y]
                    ]]
                },
                "properties": {
                    "species_name": species_name,
                    "prediction_year": 2025,
                    "prediction_id": i + 1,
                    "feature_type": "grid_box",
                    "likelihood": float(bounds.get('likelihood', 1.0)) if bounds.get('likelihood', 1.0) > 0 else 0.0
                }
            })
        
        # Final memory check
        monitor.check_memory()
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "prediction_info": {
                "species_name": species_name,
                "predicted_locations": len(centroids),
                "model_type": "Neural Network (Cached)",
                "prediction_year": 2025
            }
        }
        
    except Exception as e:
        print(f"Prediction error for {species_name}: {e}")
        # Clear memory on error
        clear_memory()
        return None

def predict_species_locations_2025(species_name):
    """Neural network prediction using pre-loaded data"""
    try:
        # Use global predictor instance
        predictor = get_global_predictor()
        
        # Check if species exists
        if species_name not in predictor.species_names:
            return None
        
        # Train model for the specific species (fast with pre-loaded data)
        trained_model = predictor.train_model(species_name)
        
        # Get predictions using neural network
        centroids = predictor.inference_model(species_name, trained_model)
        
        if not centroids:
            return None
        
        # Convert coordinates to WGS84 for web display
        import geopandas as gpd
        from shapely.geometry import Point
        
        # Create GeoDataFrame with predictions
        points = [Point(x, y) for x, y in centroids]
        gdf = gpd.GeoDataFrame(geometry=points, crs=predictor.hkmap.crs)
        gdf_wgs84 = gdf.to_crs('EPSG:4326')
        
        # Convert to GeoJSON format
        features = []
        for i, point in enumerate(gdf_wgs84.geometry):
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point.x, point.y]
                },
                "properties": {
                    "species_name": species_name,
                    "prediction_year": 2025,
                    "prediction_id": i + 1
                }
            })
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "prediction_info": {
                "species_name": species_name,
                "predicted_locations": len(centroids),
                "model_type": "Neural Network",
                "prediction_year": 2025
            }
        }
        
    except Exception as e:
        print(f"Prediction error for {species_name}: {e}")
        return None

def clear_model_cache():
    """Clear cached models to free memory"""
    global _trained_models_cache
    _trained_models_cache.clear()
    print("🗑️ Model cache cleared")

def get_cache_info():
    """Get information about cached models"""
    global _trained_models_cache
    return {
        "cached_models": len(_trained_models_cache),
        "species_list": list(_trained_models_cache.keys())
    }

if __name__ == "__main__":
    main()