import os
import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.metrics.pairwise import cosine_similarity
import joblib

# Download stopwords
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
filepath = os.path.join(BASE_DIR, "ai", "Potato_LateBlight_Dataset.xlsx")

# Load dataset
df = pd.read_excel(filepath)

# Preprocessing Function
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    words = text.split()
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

# Apply text preprocessing - USING ONLY DESCRIPTION NOW
df['Processed_Text'] = df['Issue Description'].apply(preprocess_text)

# Feature Extraction with TF-IDF
vectorizer = TfidfVectorizer(max_features=5000)
X = vectorizer.fit_transform(df['Processed_Text']).toarray()

# Encode categorical labels
def encode_labels(column):
    return {label: idx for idx, label in enumerate(column.unique())}

category_mapping = encode_labels(df['Category'])
subcategory_mapping = encode_labels(df['Sub-category'])
urgency_mapping = encode_labels(df['Urgency Level'])

df['Category_Label'] = df['Category'].map(category_mapping)
df['Urgency_Label'] = df['Urgency Level'].map(urgency_mapping)

y_category = df['Category_Label']
y_urgency = df['Urgency_Label']
y_resolution_time = df['Predicted Resolution Time (mins)']

# Split data
X_train, X_test, y_train_cat, y_test_cat = train_test_split(X, y_category, test_size=0.2, random_state=42)
X_train, X_test, y_train_urg, y_test_urg = train_test_split(X, y_urgency, test_size=0.2, random_state=42)
X_train, X_test, y_train_time, y_test_time = train_test_split(X, y_resolution_time, test_size=0.2, random_state=42)

# Train Category Classifier
category_model = RandomForestClassifier(n_estimators=100, random_state=42)
category_model.fit(X_train, y_train_cat)
cat_preds = category_model.predict(X_test)
print("Category Classification Accuracy:", accuracy_score(y_test_cat, cat_preds))

# Train Urgency Classifier
urgency_model = RandomForestClassifier(n_estimators=100, random_state=42)
urgency_model.fit(X_train, y_train_urg)
urg_preds = urgency_model.predict(X_test)
print("Urgency Classification Accuracy:", accuracy_score(y_test_urg, urg_preds))

# Train Resolution Time Predictor
resolution_model = RandomForestRegressor(n_estimators=100, random_state=42)
resolution_model.fit(X_train, y_train_time)
time_preds = resolution_model.predict(X_test)
print("Resolution Time Prediction MAE:", mean_absolute_error(y_test_time, time_preds))

# Save the models and vectorizer
joblib.dump(vectorizer, 'tfidf_vectorizer.pkl')
joblib.dump(category_model, 'category_model.pkl')
joblib.dump(urgency_model, 'urgency_model.pkl')
joblib.dump(resolution_model, 'resolution_model.pkl')
joblib.dump({
    'category_mapping': category_mapping,
    'urgency_mapping': urgency_mapping
}, 'label_mappings.pkl')

# Load the models and vectorizer
vectorizer = joblib.load('tfidf_vectorizer.pkl')
category_model = joblib.load('category_model.pkl')
urgency_model = joblib.load('urgency_model.pkl')
resolution_model = joblib.load('resolution_model.pkl')
label_mappings = joblib.load('label_mappings.pkl')
category_mapping = label_mappings['category_mapping']
urgency_mapping = label_mappings['urgency_mapping']

# Function to Suggest Solution - NOW TAKES ONLY DESCRIPTION
def suggest_solution(description):
    text = preprocess_text(description)
    features = vectorizer.transform([text]).toarray()
    similarities = cosine_similarity(features, X)
    most_similar_idx = np.argmax(similarities)
    return df.iloc[most_similar_idx]['Suggested Solution']

# Function to Predict New Issues - NOW TAKES ONLY DESCRIPTION
def predict_issue(description):
    text = preprocess_text(description)
    features = vectorizer.transform([text]).toarray()
    category_pred = list(category_mapping.keys())[category_model.predict(features)[0]]
    urgency_pred = list(urgency_mapping.keys())[urgency_model.predict(features)[0]]
    resolution_time_pred = resolution_model.predict(features)[0]
    suggested_solution = suggest_solution(description)
    return category_pred, urgency_pred, resolution_time_pred, suggested_solution