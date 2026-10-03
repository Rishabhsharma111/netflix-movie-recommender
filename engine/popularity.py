"""
Popularity & Trending Engine
Calculates IMDb/Bayesian weighted rating priors and time-decayed trending scores.
"""
from typing import Dict, List
import numpy as np


class PopularityRanker:
    def __init__(self, movies: List[Dict], min_votes_quantile: float = 0.5):
        self.movies = movies
        self.movie_ids = [m["id"] for m in movies]
        self.movie_id_to_idx = {m["id"]: idx for idx, m in enumerate(movies)}

        # Extract ratings and votes
        ratings = [m.get("rating", 7.0) for m in movies]
        votes = [m.get("vote_count", 100000) for m in movies]

        self.C = float(np.mean(ratings))  # Mean rating across all movies
        self.m = float(np.quantile(votes, min_votes_quantile))  # Vote threshold

        self.weighted_ratings = np.zeros(len(movies))
        self.trending_scores = np.zeros(len(movies))
        self._calculate_scores()

    def _calculate_scores(self):
        current_year = 2024

        for idx, m in enumerate(self.movies):
            v = float(m.get("vote_count", 0))
            r = float(m.get("rating", self.C))
            year = int(m.get("year", 2010))

            # Bayesian weighted rating formula (IMDb formula)
            # WR = (v / (v + m)) * R + (m / (v + m)) * C
            wr = (v / (v + self.m)) * r + (self.m / (v + self.m)) * self.C
            self.weighted_ratings[idx] = wr

            # Trending score: balances high weighted rating with recent release recency
            # Movies released recently get a temporal boost
            age = max(0, current_year - year)
            recency_decay = np.exp(-0.06 * age)  # Smooth decay over time
            # Combine popularity, rating quality, and recency
            trending = (wr / 10.0) * 0.6 + recency_decay * 0.4
            self.trending_scores[idx] = trending

        # Normalize weighted ratings to [0, 1]
        min_wr, max_wr = np.min(self.weighted_ratings), np.max(self.weighted_ratings)
        if max_wr > min_wr:
            self.normalized_wr = (self.weighted_ratings - min_wr) / (max_wr - min_wr)
        else:
            self.normalized_wr = np.ones(len(self.movies)) * 0.5

        # Normalize trending scores to [0, 1]
        min_tr, max_tr = np.min(self.trending_scores), np.max(self.trending_scores)
        if max_tr > min_tr:
            self.normalized_trending = (self.trending_scores - min_tr) / (max_tr - min_tr)
        else:
            self.normalized_trending = np.ones(len(self.movies)) * 0.5

    def get_popularity_score_array(self) -> np.ndarray:
        return self.normalized_wr

    def get_trending_movies(self, top_n: int = 15) -> List[Dict]:
        """Returns top trending movies ordered by trending velocity."""
        ranked_indices = np.argsort(-self.normalized_trending)[:top_n]
        return [self.movies[i] for i in ranked_indices]

    def get_top_rated_movies(self, genre: str = None, top_n: int = 15) -> List[Dict]:
        """Returns critically acclaimed titles by weighted rating, optionally filtered by genre."""
        ranked_indices = np.argsort(-self.weighted_ratings)
        results = []
        for idx in ranked_indices:
            movie = self.movies[idx]
            if genre is None or genre.lower() in [g.lower() for g in movie.get("genres", [])]:
                results.append(movie)
                if len(results) >= top_n:
                    break
        return results
