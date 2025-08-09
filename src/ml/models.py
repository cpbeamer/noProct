"""Machine Learning models for enhanced question detection"""
import numpy as np
import pickle
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import cv2
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass
import logging

@dataclass
class QuestionFeatures:
    """Features extracted from potential question region"""
    text_length: int
    word_count: int
    has_question_mark: bool
    has_question_word: bool
    option_count: int
    confidence_score: float
    region_area: float
    text_density: float
    capital_ratio: float
    numeric_ratio: float
    
    def to_vector(self) -> np.ndarray:
        """Convert features to numpy vector"""
        return np.array([
            self.text_length,
            self.word_count,
            float(self.has_question_mark),
            float(self.has_question_word),
            self.option_count,
            self.confidence_score,
            self.region_area,
            self.text_density,
            self.capital_ratio,
            self.numeric_ratio
        ])

class QuestionDetectorNN(nn.Module):
    """Neural network for question detection"""
    
    def __init__(self, input_size: int = 10, hidden_sizes: List[int] = [64, 32, 16]):
        super(QuestionDetectorNN, self).__init__()
        
        layers = []
        prev_size = input_size
        
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(prev_size, hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_size = hidden_size
        
        layers.append(nn.Linear(prev_size, 2))  # Binary classification
        
        self.model = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.model(x)

class ImageQuestionCNN(nn.Module):
    """CNN for question detection from images"""
    
    def __init__(self):
        super(ImageQuestionCNN, self).__init__()
        
        # Convolutional layers
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        
        # Pooling
        self.pool = nn.MaxPool2d(2, 2)
        
        # Fully connected layers
        self.fc1 = nn.Linear(128 * 28 * 28, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, 2)
        
        self.dropout = nn.Dropout(0.3)
    
    def forward(self, x):
        # Convolutional layers with pooling
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        
        # Flatten
        x = x.view(-1, 128 * 28 * 28)
        
        # Fully connected layers
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        
        return x

class MLQuestionDetector:
    """Machine Learning based question detector"""
    
    def __init__(self):
        self.logger = logging.getLogger("MLDetector")
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Feature extractor
        self.scaler = StandardScaler()
        
        # Traditional ML models
        self.rf_classifier = None
        self.gb_classifier = None
        self.mlp_classifier = None
        
        # Deep learning models
        self.nn_model = None
        self.cnn_model = None
        
        # Model weights
        self.ensemble_weights = {
            'rf': 0.2,
            'gb': 0.2,
            'mlp': 0.2,
            'nn': 0.25,
            'cnn': 0.15
        }
        
        # Load pre-trained models if available
        self.load_models()
    
    def extract_features(self, text: str, region: Dict, image: np.ndarray) -> QuestionFeatures:
        """Extract features from potential question"""
        # Text features
        text_length = len(text)
        words = text.split()
        word_count = len(words)
        
        # Question indicators
        has_question_mark = '?' in text
        question_words = ['what', 'when', 'where', 'who', 'which', 'how', 'why']
        has_question_word = any(word.lower() in text.lower() for word in question_words)
        
        # Count potential options
        option_patterns = ['A)', 'B)', 'C)', 'D)', '1.', '2.', '3.', '4.']
        option_count = sum(1 for pattern in option_patterns if pattern in text)
        
        # Region features
        region_area = region.get('width', 0) * region.get('height', 0)
        text_density = text_length / max(region_area, 1)
        
        # Character ratios
        capital_count = sum(1 for c in text if c.isupper())
        capital_ratio = capital_count / max(text_length, 1)
        
        numeric_count = sum(1 for c in text if c.isdigit())
        numeric_ratio = numeric_count / max(text_length, 1)
        
        # Initial confidence
        confidence = 0.5
        if has_question_mark:
            confidence += 0.2
        if has_question_word:
            confidence += 0.15
        if option_count >= 2:
            confidence += 0.15
        
        return QuestionFeatures(
            text_length=text_length,
            word_count=word_count,
            has_question_mark=has_question_mark,
            has_question_word=has_question_word,
            option_count=option_count,
            confidence_score=min(confidence, 1.0),
            region_area=region_area,
            text_density=text_density,
            capital_ratio=capital_ratio,
            numeric_ratio=numeric_ratio
        )
    
    def preprocess_image(self, image: np.ndarray, target_size: Tuple[int, int] = (224, 224)) -> torch.Tensor:
        """Preprocess image for CNN"""
        # Resize image
        resized = cv2.resize(image, target_size)
        
        # Convert to RGB if needed
        if len(resized.shape) == 2:
            resized = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)
        
        # Normalize
        normalized = resized.astype(np.float32) / 255.0
        
        # Convert to tensor
        tensor = torch.from_numpy(normalized).permute(2, 0, 1).unsqueeze(0)
        
        return tensor
    
    def predict_with_ml(self, features: QuestionFeatures) -> Dict[str, float]:
        """Predict using traditional ML models"""
        predictions = {}
        
        # Prepare feature vector
        feature_vector = features.to_vector().reshape(1, -1)
        
        # Scale features
        if hasattr(self.scaler, 'mean_'):
            feature_vector = self.scaler.transform(feature_vector)
        
        # Random Forest
        if self.rf_classifier:
            rf_proba = self.rf_classifier.predict_proba(feature_vector)[0, 1]
            predictions['rf'] = rf_proba
        
        # Gradient Boosting
        if self.gb_classifier:
            gb_proba = self.gb_classifier.predict_proba(feature_vector)[0, 1]
            predictions['gb'] = gb_proba
        
        # MLP
        if self.mlp_classifier:
            mlp_proba = self.mlp_classifier.predict_proba(feature_vector)[0, 1]
            predictions['mlp'] = mlp_proba
        
        return predictions
    
    def predict_with_nn(self, features: QuestionFeatures) -> float:
        """Predict using neural network"""
        if not self.nn_model:
            return 0.5
        
        # Prepare input
        feature_vector = features.to_vector()
        tensor = torch.FloatTensor(feature_vector).unsqueeze(0)
        
        # Predict
        self.nn_model.eval()
        with torch.no_grad():
            output = self.nn_model(tensor)
            proba = F.softmax(output, dim=1)[0, 1].item()
        
        return proba
    
    def predict_with_cnn(self, image: np.ndarray) -> float:
        """Predict using CNN"""
        if not self.cnn_model:
            return 0.5
        
        # Preprocess image
        image_tensor = self.preprocess_image(image)
        
        # Predict
        self.cnn_model.eval()
        with torch.no_grad():
            output = self.cnn_model(image_tensor)
            proba = F.softmax(output, dim=1)[0, 1].item()
        
        return proba
    
    def predict(self, text: str, region: Dict, image: np.ndarray) -> Dict[str, Any]:
        """Ensemble prediction combining all models"""
        # Extract features
        features = self.extract_features(text, region, image)
        
        # Get predictions from all models
        all_predictions = {}
        
        # Traditional ML predictions
        ml_predictions = self.predict_with_ml(features)
        all_predictions.update(ml_predictions)
        
        # Neural network prediction
        all_predictions['nn'] = self.predict_with_nn(features)
        
        # CNN prediction
        all_predictions['cnn'] = self.predict_with_cnn(image)
        
        # Calculate weighted ensemble
        ensemble_score = 0
        total_weight = 0
        
        for model_name, score in all_predictions.items():
            weight = self.ensemble_weights.get(model_name, 0.1)
            ensemble_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            ensemble_score /= total_weight
        
        # Determine if it's a question
        is_question = ensemble_score > 0.5
        
        return {
            'is_question': is_question,
            'confidence': ensemble_score,
            'model_scores': all_predictions,
            'features': {
                'text_length': features.text_length,
                'word_count': features.word_count,
                'has_question_mark': features.has_question_mark,
                'option_count': features.option_count
            }
        }
    
    def train_models(self, training_data: List[Tuple[QuestionFeatures, bool]]):
        """Train all models with collected data"""
        if len(training_data) < 100:
            self.logger.warning("Insufficient training data")
            return
        
        # Prepare data
        X = np.array([features.to_vector() for features, _ in training_data])
        y = np.array([int(label) for _, label in training_data])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.rf_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.rf_classifier.fit(X_train_scaled, y_train)
        rf_score = self.rf_classifier.score(X_test_scaled, y_test)
        self.logger.info(f"Random Forest accuracy: {rf_score:.3f}")
        
        # Train Gradient Boosting
        self.gb_classifier = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.gb_classifier.fit(X_train_scaled, y_train)
        gb_score = self.gb_classifier.score(X_test_scaled, y_test)
        self.logger.info(f"Gradient Boosting accuracy: {gb_score:.3f}")
        
        # Train MLP
        self.mlp_classifier = MLPClassifier(
            hidden_layer_sizes=(64, 32),
            max_iter=500,
            random_state=42
        )
        self.mlp_classifier.fit(X_train_scaled, y_train)
        mlp_score = self.mlp_classifier.score(X_test_scaled, y_test)
        self.logger.info(f"MLP accuracy: {mlp_score:.3f}")
        
        # Save models
        self.save_models()
    
    def train_neural_network(self, training_data: List[Tuple[QuestionFeatures, bool]], 
                           epochs: int = 50):
        """Train the neural network model"""
        if len(training_data) < 100:
            return
        
        # Prepare data
        X = torch.FloatTensor([f.to_vector() for f, _ in training_data])
        y = torch.LongTensor([int(label) for _, label in training_data])
        
        # Initialize model
        self.nn_model = QuestionDetectorNN()
        
        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.nn_model.parameters(), lr=0.001)
        
        # Training loop
        self.nn_model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = self.nn_model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()
            
            if epoch % 10 == 0:
                self.logger.info(f"NN Epoch {epoch}, Loss: {loss.item():.4f}")
    
    def save_models(self):
        """Save trained models to disk"""
        # Save traditional ML models
        if self.rf_classifier:
            with open(self.models_dir / "rf_classifier.pkl", 'wb') as f:
                pickle.dump(self.rf_classifier, f)
        
        if self.gb_classifier:
            with open(self.models_dir / "gb_classifier.pkl", 'wb') as f:
                pickle.dump(self.gb_classifier, f)
        
        if self.mlp_classifier:
            with open(self.models_dir / "mlp_classifier.pkl", 'wb') as f:
                pickle.dump(self.mlp_classifier, f)
        
        # Save scaler
        with open(self.models_dir / "scaler.pkl", 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save neural network
        if self.nn_model:
            torch.save(self.nn_model.state_dict(), self.models_dir / "nn_model.pth")
        
        if self.cnn_model:
            torch.save(self.cnn_model.state_dict(), self.models_dir / "cnn_model.pth")
        
        self.logger.info("Models saved successfully")
    
    def load_models(self):
        """Load pre-trained models from disk"""
        try:
            # Load traditional ML models
            rf_path = self.models_dir / "rf_classifier.pkl"
            if rf_path.exists():
                with open(rf_path, 'rb') as f:
                    self.rf_classifier = pickle.load(f)
            
            gb_path = self.models_dir / "gb_classifier.pkl"
            if gb_path.exists():
                with open(gb_path, 'rb') as f:
                    self.gb_classifier = pickle.load(f)
            
            mlp_path = self.models_dir / "mlp_classifier.pkl"
            if mlp_path.exists():
                with open(mlp_path, 'rb') as f:
                    self.mlp_classifier = pickle.load(f)
            
            # Load scaler
            scaler_path = self.models_dir / "scaler.pkl"
            if scaler_path.exists():
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            # Load neural network
            nn_path = self.models_dir / "nn_model.pth"
            if nn_path.exists():
                self.nn_model = QuestionDetectorNN()
                self.nn_model.load_state_dict(torch.load(nn_path))
                self.nn_model.eval()
            
            cnn_path = self.models_dir / "cnn_model.pth"
            if cnn_path.exists():
                self.cnn_model = ImageQuestionCNN()
                self.cnn_model.load_state_dict(torch.load(cnn_path))
                self.cnn_model.eval()
            
            self.logger.info("Models loaded successfully")
        
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")

class ActiveLearning:
    """Active learning system for continuous improvement"""
    
    def __init__(self, ml_detector: MLQuestionDetector):
        self.ml_detector = ml_detector
        self.training_data = []
        self.uncertainty_threshold = 0.3
        self.min_samples_for_retrain = 50
        
        self.data_file = Path("data/training_data.json")
        self.load_training_data()
    
    def should_request_label(self, confidence: float) -> bool:
        """Determine if we should request user feedback"""
        uncertainty = 1 - abs(confidence - 0.5) * 2
        return uncertainty > self.uncertainty_threshold
    
    def add_training_sample(self, features: QuestionFeatures, 
                           is_question: bool, confidence: float):
        """Add new training sample"""
        sample = {
            'features': features.__dict__,
            'label': is_question,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        self.training_data.append(sample)
        
        # Retrain if enough new samples
        if len(self.training_data) % self.min_samples_for_retrain == 0:
            self.retrain_models()
    
    def retrain_models(self):
        """Retrain models with new data"""
        # Convert stored data to training format
        training_samples = []
        
        for sample in self.training_data:
            features = QuestionFeatures(**sample['features'])
            label = sample['label']
            training_samples.append((features, label))
        
        # Retrain
        self.ml_detector.train_models(training_samples)
        
        # Save updated training data
        self.save_training_data()
    
    def save_training_data(self):
        """Save training data to disk"""
        self.data_file.parent.mkdir(exist_ok=True)
        
        with open(self.data_file, 'w') as f:
            json.dump(self.training_data, f, indent=2)
    
    def load_training_data(self):
        """Load training data from disk"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    self.training_data = json.load(f)
            except:
                self.training_data = []

# Global ML detector instance
from datetime import datetime
ml_detector = MLQuestionDetector()
active_learner = ActiveLearning(ml_detector)