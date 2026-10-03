"""
Collaborative Filtering Engine
Implements:
1. Matrix Factorization via TruncatedSVD (Latent Factor Model, inspired by the Netflix Prize)
2. Item-Item Collaborative Filtering (User-affinity co-occurrence)
3. Dynamic fold-in for real-time user ratings
"""
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity


class CollaborativeRecommender:
    def __init__(self, movies: List[Dict], user_profiles: Dict[str, Dict], n_factors: int = 6):
        self.movies = movies
        self.user_profiles = user_profiles
        self.n_factors = n_factors

        self.movie_ids = [m["id"] for m in movies]
        self.movie_id_to_idx = {mid: idx for idx, mid in enumerate(self.movie_ids)}
        self.idx_to_movie_id = {idx: mid for idx, mid in enumerate(self.movie_ids)}

        self.user_ids = list(user_profiles.keys())
        self.user_id_to_idx = {uid: idx for idx, uid in enumerate(self.user_ids)}

        self._fit_model()

    def _fit_model(self):
        n_users = len(self.user_ids)
        n_movies = len(self.movie_ids)

        # Build User-Item Rating Matrix (users x movies)
        self.rating_matrix = np.full((n_users, n_movies), np.nan)

        for u_idx, uid in enumerate(self.user_ids):
            ratings = self.user_profiles[uid].get("ratings", {})
            for m_id, r in ratings.items():
                m_id = int(m_id)
                if m_id in self.movie_id_to_idx:
                    self.rating_matrix[u_idx, self.movie_id_to_idx[m_id]] = float(r)

        # Global average rating
        valid_ratings = self.rating_matrix[~np.isnan(self.rating_matrix)]
        self.global_mean = float(np.mean(valid_ratings)) if len(valid_ratings) > 0 else 4.0

        # Compute User Biases and Movie Biases
        self.user_biases = np.zeros(n_users)
        for u in range(n_users):
            user_ratings = self.rating_matrix[u, ~np.isnan(self.rating_matrix[u])]
            if len(user_ratings) > 0:
                self.user_biases[u] = np.mean(user_ratings) - self.global_mean

        self.movie_biases = np.zeros(n_movies)
        for m in range(n_movies):
            movie_ratings = self.rating_matrix[~np.isnan(self.rating_matrix[:, m]), m]
            if len(movie_ratings) > 0:
                self.movie_biases[m] = np.mean(movie_ratings) - self.global_mean

        # Fill NaNs with baseline estimates: global_mean + user_bias + movie_bias
        filled_matrix = self.rating_matrix.copy()
        for u in range(n_users):
            for m in range(n_movies):
                if np.isnan(filled_matrix[u, m]):
                    filled_matrix[u, m] = np.clip(
                        self.global_mean + self.user_biases[u] + self.movie_biases[m], 1.0, 5.0
                    )

        # Latent factor decomposition via SVD
        n_components = min(self.n_factors, n_users - 1, n_movies - 1)
        if n_components >= 2:
            self.svd = TruncatedSVD(n_components=n_components, random_state=42)
            # Item latent factors: Q (n_movies x k)
            self.item_factors = self.svd.fit_transform(filled_matrix.T)
            # Normalize item factors
            norms = np.linalg.norm(self.item_factors, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.item_factors = self.item_factors / norms

            # Item-Item similarity matrix based on collaborative interactions
            self.item_item_sim = cosine_similarity(self.item_factors)
        else:
            self.svd = None
            self.item_factors = np.zeros((n_movies, 2))
            self.item_item_sim = np.eye(n_movies)

    def score_movies_for_user(self, user_ratings: Dict[int, float]) -> np.ndarray:
        """
        Predicts collaborative affinity score [0, 1] for all movies given a user's ratings.
        Uses item latent factors projection or item-item collaborative averaging.
        """
        n_movies = len(self.movie_ids)
        if not user_ratings:
            return np.zeros(n_movies)

        # Method 1: Item-Item Collaborative filtering projection
        # Predicted score for movie j = sum(sim(j, i) * rating_i) / sum(sim(j, i))
        cf_scores = np.zeros(n_movies)
        sim_weights = np.zeros(n_movies)

        for rated_id, rating in user_ratings.items():
            rated_id = int(rated_id)
            if rated_id in self.movie_id_to_idx:
                rated_idx = self.movie_id_to_idx[rated_id]
                sims = self.item_item_sim[rated_idx]  # similarities to all other movies

                # Normalized rating (0 to 1 scale): (rating - 1.0) / 4.0
                norm_rating = (float(rating) - 1.0) / 4.0

                for m_idx in range(n_movies):
                    s = max(0.0, sims[m_idx])
                    cf_scores[m_idx] += s * norm_rating
                    sim_weights[m_idx] += s

        mask = sim_weights > 0
        cf_scores[mask] /= sim_weights[mask]

        # Method 2: If SVD item_factors exist, fold in user vector
        if self.svd is not None and len(user_ratings) >= 2:
            # Build user rating residual vector
            user_vec = np.zeros(n_movies)
            valid_count = 0
            for rated_id, rating in user_ratings.items():
                rated_id = int(rated_id)
                if rated_id in self.movie_id_to_idx:
                    idx = self.movie_id_to_idx[rated_id]
                    user_vec[idx] = float(rating) - self.global_mean - self.movie_biases[idx]
                    valid_count += 1

            if valid_count > 0:
                # Project user into latent factor space
                user_factors = np.dot(user_vec, self.item_factors)
                u_norm = np.linalg.norm(user_factors)
                if u_norm > 0:
                    user_factors /= u_norm
                    latent_preds = np.dot(self.item_factors, user_factors)
                    latent_preds = (latent_preds + 1.0) / 2.0  # scale [-1, 1] to [0, 1]
                    # Blend item-item and latent factors
                    cf_scores = 0.5 * cf_scores + 0.5 * latent_preds

        return np.clip(cf_scores, 0.0, 1.0)

    def get_collaborative_similar_movies(self, movie_id: int, top_n: int = 10) -> List[Tuple[int, float]]:
        """
        Returns movies frequently enjoyed together by users (Item-Item CF).
        """
        if movie_id not in self.movie_id_to_idx:
            return []
        idx = self.movie_id_to_idx[movie_id]
        sims = self.item_item_sim[idx]
        sorted_indices = np.argsort(-sims)

        results = []
        for other_idx in sorted_indices:
            if other_idx == idx:
                continue
            other_id = self.idx_to_movie_id[other_idx]
            results.append((other_id, float(sims[other_idx])))
            if len(results) >= top_n:
                break
        return results
