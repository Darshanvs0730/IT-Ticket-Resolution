from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple
from .models import HistoricalTicket
from .utils.error_handler import NLPEngineError

class NLPEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),  # unigrams and bigrams
            min_df=1,
            max_df=0.8
        )
        self.historical_vectors = None
        self.historical_tickets = []
    
    def train(self, historical_tickets: List[HistoricalTicket]):
        """Train TF-IDF model on historical ticket descriptions"""
        if not historical_tickets:
            self.historical_vectors = None
            self.historical_tickets = []
            return
            
        # Combine title + description for better matching
        corpus = [f"{t.title} {t.description}" for t in historical_tickets]
        self.historical_vectors = self.vectorizer.fit_transform(corpus)
        self.historical_tickets = historical_tickets
    
    def find_similar_tickets(self, query: str, top_k: int = 5) -> List[Tuple[HistoricalTicket, float]]:
        """Find top K most similar historical tickets using cosine similarity"""
        if self.historical_vectors is None or not self.historical_tickets:
            raise NLPEngineError("NLP engine not trained. Run train() first.")
        
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.historical_vectors).flatten()
        
        # Get top K indices
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                results.append((self.historical_tickets[idx], float(similarities[idx])))
        
        return results
