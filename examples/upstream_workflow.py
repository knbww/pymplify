"""A direct upstream workflow used as read-only analyzer input."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler


def text_features(documents):
    vectorizer = TfidfVectorizer(max_features=100)
    matrix = vectorizer.fit_transform(documents)
    return matrix, vectorizer


def numeric_features(data):
    scaler = StandardScaler()
    scaled = scaler.fit_transform(data)
    return scaled, scaler
