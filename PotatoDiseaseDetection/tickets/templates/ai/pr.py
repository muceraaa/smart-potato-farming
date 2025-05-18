import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
filepath = os.path.join(BASE_DIR, "ai", "3.h5")
# Load the trained model
model = load_model(filepath)

# Define class labels
class_labels = ["Healthy", "Late Blight", "Other Disease"]  # Adjust to your setup

def predict_single_image(img_path, true_label=1):
    # Load and preprocess the image
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)  # Batch size = 1
    img_array = img_array / 255.0  # Normalize

    # Make prediction
    predictions = model.predict(img_array)
    predicted_index = np.argmax(predictions[0])
    predicted_class = class_labels[predicted_index]
    confidence = round(100 * np.max(predictions[0]), 2)

    # Display results
    print(f"Predicted Class: {predicted_class}")
    print(f"Confidence: {confidence}%")
    return predicted_class, confidence

    

# Example usage
# img_path = "C:\\Users\\HP\\Desktop\\PROJECT\\potato\\PlantVillage\\Potato___Late_blight\\8b0ef54c-6d28-47bb-a657-287afbb8a620___RS_LB 3298.JPG"
# predict_single_image(img_path, model, true_label=1)  # Replace true_label if known
