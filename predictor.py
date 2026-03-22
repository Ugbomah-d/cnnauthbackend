import torch
import torch.nn as nn
import joblib
import json
import numpy as np
from torchvision import transforms, models
from PIL import Image
import os

IMG_SIZE = 224

val_transforms = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

class RiceFeatureExtractor(nn.Module):
    def __init__(self, num_classes):
        super(RiceFeatureExtractor, self).__init__()
        resnet = models.resnet18(weights=None)
        self.features = nn.Sequential(*list(resnet.children())[:-1])
        self.feature_dim = resnet.fc.in_features
        self.classifier = nn.Linear(self.feature_dim, num_classes)

    def forward(self, x):
        features = self.features(x)
        features = torch.flatten(features, 1)
        logits = self.classifier(features)
        return logits, features


def load_model():
    base = os.path.join(os.path.dirname(__file__), "Model")

    with open(os.path.join(base, "class_names.json")) as f:
        class_names = json.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    cnn = RiceFeatureExtractor(len(class_names))
    cnn.load_state_dict(torch.load(os.path.join(base, "rice_cnn.pth"), map_location=device))
    cnn.to(device)
    cnn.eval()

    svm = joblib.load(os.path.join(base, "rice_svm.pkl"))

    return cnn, svm, class_names, device


def predict(image_path, cnn, svm, class_names, device):
    img = Image.open(image_path).convert("RGB")
    img_t = val_transforms(img).unsqueeze(0).to(device)

    with torch.no_grad():
        _, features = cnn(img_t)
        features = features.cpu().numpy()

    prediction = svm.predict(features)[0]
    probabilities = svm.predict_proba(features)[0]
    confidence = float(max(probabilities))
    predicted_class = class_names[prediction]

    return predicted_class, confidence