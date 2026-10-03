"""
Content-Based Recommendation Engine
Uses TF-IDF Vectorization and Cosine Similarity over rich movie metadata
(genres, director, top cast, keywords, and storyline overview).
"""
import re
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ContentRecommender:
    def __init__(self, movies: List[Dict]):
        self.movies = movies
        self.df = pd.DataFrame(movies)
        self.id_to_idx = {movie["id"]: idx for idx, movie in enumerate(movies)}
        self.idx_to_id = {idx: movie["id"] for idx, movie in enumerate(movies)}
        self._build_content_matrix()

    def _clean_str(self, text: str) -> str:
        return re.sub(r"[^\w\s]", "", str(text)).lower().replace(" ", "")

    def _build_content_matrix(self):
        # Create metadata soup:
        # Heavily weight genres (x3) and director (x2) and keywords (x2) to match real cinematic affinity
        soups = []
        for _, row in self.df.iterrows():
            genres = " ".join([self._clean_str(g) for g in row.get("genres", [])] * 3)
            director = f"dir_{self._clean_str(row.get('director', ''))} " * 2
            cast = " ".join([f"actor_{self._clean_str(c)}" for c in row.get("cast", [])[:3]])
            keywords = " ".join([self._clean_str(k) for k in row.get("keywords", [])] * 2)
            overview = str(row.get("overview", ""))

            soup = f"{genres} {director} {cast} {keywords} {overview}"
            soups.append(soup)

        self.df["soup"] = soups
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df["soup"])
        self.similarity_matrix = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)

    def get_similar_to_movie(self, movie_id: int, top_n: int = 10) -> List[Tuple[int, float, List[str]]]:
        """
        Returns top_n similar movies for a given movie_id with similarity score and shared tags.
        """
        if movie_id not in self.id_to_idx:
            return []

        idx = self.id_to_idx[movie_id]
        sim_scores = list(enumerate(self.similarity_matrix[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

        results = []
        source_movie = self.movies[idx]
        source_genres = set(source_movie.get("genres", []))
        source_dir = source_movie.get("director")

        for other_idx, score in sim_scores[1 : top_n + 1]:
            other_id = self.idx_to_id[other_idx]
            other_movie = self.movies[other_idx]

            # Compute shared attributes for explainability
            shared_tags = []
            common_genres = source_genres.intersection(set(other_movie.get("genres", [])))
            if common_genres:
                shared_tags.append(f"Genres: {', '.join(common_genres)}")
            if source_dir and source_dir == other_movie.get("director"):
                shared_tags.append(f"Director: {source_dir}")

            results.append((other_id, float(score), shared_tags))

        return results

    def score_movies_for_user(self, user_ratings: Dict[int, float]) -> np.ndarray:
        """
        Calculates content similarity scores [0, 1] for all movies against user rating profile.
        Positive ratings (> 3.5) pull towards movie vectors; low ratings (< 3.0) penalize.
        """
        num_movies = len(self.movies)
        if not user_ratings:
            return np.zeros(num_movies)

        user_vector = np.zeros(self.tfidf_matrix.shape[1])
        weight_sum = 0.0

        for movie_id, rating in user_ratings.items():
            if movie_id in self.id_to_idx:
                idx = self.id_to_idx[movie_id]
                # Center around neutral rating (3.0): 5 -> +2.0, 4 -> +1.0, 2 -> -1.0, 1 -> -2.0
                weight = float(rating) - 3.0
                if weight != 0:
                    movie_vec = self.tfidf_matrix[idx].toarray()[0]
                    user_vector += weight * movie_vec
                    weight_sum += abs(weight)

        if weight_sum > 0:
            user_vector /= weight_sum
            # Normalize vector
            norm = np.linalg.norm(user_vector)
            if norm > 0:
                user_vector /= norm
                user_vector = user_vector.reshape(1, -1)
                scores = cosine_similarity(user_vector, self.tfidf_matrix)[0]
                # Scale from [-1, 1] to [0, 1]
                scores = np.clip(scores, 0, 1)
                return scores

        return np.zeros(num_movies)
