# Import necessary libraries
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sn
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torchvision import datasets, transforms, models

# Device configuration (use GPU if available)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Paths to your test dataset and saved model
test_dir = r"C:\Users\bluch\Desktop\floradex\Skin cancer dataset\test"
saved_model_path = 'custom-classifier_resnet_18_final.pth'

# Define the transformation for the test dataset (same as during training)
transforms_test = transforms.Compose([
    transforms.Resize((224, 224)),   # Resize to match the input size of ResNet
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # Normalize with mean and std
])

# Load the test dataset
test_dataset = datasets.ImageFolder(test_dir, transforms_test)
test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=12, shuffle=False)

# Load the trained model
model = models.resnet18(pretrained=False)  # No need to load pre-trained weights, we're loading your trained model
num_features = model.fc.in_features
model.fc = nn.Linear(num_features, 2)  # Adjust for binary classification (2 classes: benign, malignant)
model.load_state_dict(torch.load(saved_model_path))  # Load saved model weights
model = model.to(device)

# Ensure model is in evaluation mode
model.eval()

# Initialize lists to store predictions and true labels
y_pred = []
y_true = []

# Disable gradient calculation (faster inference)
with torch.no_grad():
    for inputs, labels in test_dataloader:
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)  # Forward pass
        _, preds = torch.max(outputs, 1)  # Get the predicted class
        y_pred.extend(preds.cpu().numpy())  # Convert predictions to numpy and store
        y_true.extend(labels.cpu().numpy())  # Store the true labels

# Convert lists to NumPy arrays
y_pred = np.array(y_pred)
y_true = np.array(y_true)

# Calculate accuracy
accuracy = accuracy_score(y_true, y_pred)
print(f"Accuracy on Test dataset: {accuracy:.4f}")

# Generate the confusion matrix
cf_matrix = confusion_matrix(y_true, y_pred)
print('Confusion Matrix:\n', cf_matrix)

# Generate a classification report
print('Classification Report:\n', classification_report(y_true, y_pred, target_names=test_dataset.classes))

# Plot the confusion matrix
df_cm = pd.DataFrame(cf_matrix, index=test_dataset.classes, columns=test_dataset.classes)
plt.figure(figsize=(7, 7))
sn.heatmap(df_cm, annot=True, fmt='d', cmap='Blues')
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.show()
