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
                    layer[row['year'] - 2001, int(row['x_bin']), int(row['y_bin'])] += 1
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
        X = torch.tensor(species_layer[:23, :, :]).to(torch.float32)
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

    def inference_model(self, a_species, model):
        # model.eval()
        # with torch.no_grad():
        #     for i in range(23):
        #         test_data = torch.tensor(abisara_echerius_layer[i, :, :]).unsqueeze(0).to(torch.float32).to(device)
        #         test_output = model(test_data)
        #         predicted_grid = test_output.cpu().numpy().reshape(20, 20)

        model = self.model
        # Inference on the last layer (2024)
        species_layer = self.species_layers[a_species]
        # Define device
        device = torch.device('mpu' if torch.cuda.is_available() else 'cpu')
        model.eval()
        with torch.no_grad():
            test_data = torch.tensor(species_layer[-1, :, :]).unsqueeze(0).to(torch.float32).to(device)
            test_output = model(test_data)
            predicted_grid = test_output.cpu().numpy().reshape(20, 20)
            predicted_grid = np.round(predicted_grid)

        # Get the grid_id of each cell with value >= 1
        grid_ids = []
        for i in range(20):
            for j in range(20):
                if predicted_grid[i, j] >= 1:
                    grid_ids.append((i, j))

        # Convert grid_ids to centroids
        centroids = []
        for grid in grid_ids:
            x_bin, y_bin = grid
            x_center = (self.x_bins[x_bin] + self.x_bins[x_bin + 1]) / 2
            y_center = (self.y_bins[y_bin] + self.y_bins[y_bin + 1]) / 2
            centroids.append((x_center, y_center))

        return centroids
    
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

# Neural Network Model
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        # First fully connected layer: from 400 (20x20) to 512 neurons
        self.fc1 = nn.Linear(20 * 20, 512)
        # Second fully connected layer: from 512 to (20x20: 400) neurons
        self.fc2 = nn.Linear(512, 400)

    def forward(self, x):
        # Flatten the image input
        x = x.view(-1, 20 * 20)
        # Apply the first FC layer and sigmoid activation
        x = self.fc1(x)
        x = torch.sigmoid(x)
        # Apply the second FC layer (output layer)
        x = self.fc2(x)
        
        return x
    
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

def predict_species_locations_2025(species_name):
    """Predict 2025 locations for a specific species"""
    try:
        # Initialize Species class
        species_instance = Species()
        
        # Prepare data
        species_instance.prepare_data()
        
        # Create grid
        species_instance.create_grid()
        
        # Get species names
        species_instance.get_species_names()
        
        # Check if species exists
        if species_name not in species_instance.species_names:
            return None
        
        # Create species layers
        species_instance.species_layer(species_instance.species_df)
        
        # Train model for the specific species
        trained_model = species_instance.train_model(species_name)
        
        # Get predictions
        centroids = species_instance.inference_model(species_name, trained_model)
        
        if not centroids:
            return None
        
        # Convert to GeoJSON format
        features = []
        for i, (x, y) in enumerate(centroids):
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [x, y]
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

if __name__ == "__main__":
    main()