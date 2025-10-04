import numpy as np

def calculate_likelihood_from_predictions(predictions):
    """
    Calculate likelihood from model predictions.
    Replace negative values with 0, keep positive values unchanged.
    
    Args:
        predictions: Array of prediction values from the model
    
    Returns:
        likelihood: Array with negative values replaced by 0
    """
    likelihood = np.where(predictions < 0, 0, predictions)
    return likelihood

# Example usage:
if __name__ == "__main__":
    # Example predictions with some negative values
    sample_predictions = np.array([-0.5, 0.3, -1.2, 0.8, 2.1, -0.1, 1.5])
    
    # Calculate likelihood
    likelihood = calculate_likelihood_from_predictions(sample_predictions)
    
    print("Original predictions:", sample_predictions)
    print("Updated likelihood:  ", likelihood)
    
    # Verify: negative values become 0, positive values unchanged
    print("\nVerification:")
    for i, (pred, like) in enumerate(zip(sample_predictions, likelihood)):
        print(f"Index {i}: {pred:5.1f} -> {like:5.1f}")