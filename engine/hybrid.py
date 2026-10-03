"""
Master Netflix-Style Hybrid Recommendation Engine
Blends Content-Based Filtering, Collaborative Matrix Factorization, and Bayesian Popularity.
Generates full personalized Netflix home feeds, rows, and match percentages.
"""
from typing import Dict, List, Optional
import numpy as np

from .content_based import ContentRecommender
from .collaborative import CollaborativeRecommender
from .popularity import PopularityRanker
from .explainability import ExplainabilityEngine


class NetflixHybridRecommender:
    def __init__(self, movies: List[Dict], user_profiles: Dict[str, Dict]):
        self.movies = movies
        self.movies_by_id = {m["id"]: m for m in movies}
        self.user_profiles = user_profiles

        # Initialize sub-engines
        self.content_engine = ContentRecommender(movies)
        self.collaborative_engine = CollaborativeRecommender(movies, user_profiles)
        self.popularity_engine = PopularityRanker(movies)
        self.explainability_engine = ExplainabilityEngine(movies)

    def calculate_hybrid_scores(
        self,
        user_ratings: Dict[int, float],
        weight_cf: float = 0.45,
        weight_content: float = 0.40,
        weight_pop: float = 0.15,
    ) -> np.ndarray:
        """
        Calculates hybrid score for every movie in catalog for a user rating profile.
        """
        # If user has no ratings (cold start), lean heavily on popularity and curated quality
        if not user_ratings:
            pop = self.popularity_engine.get_popularity_score_array()
            zeros = np.zeros(len(self.movies))
            return pop, zeros, zeros, pop

        content_scores = self.content_engine.score_movies_for_user(user_ratings)
        cf_scores = self.collaborative_engine.score_movies_for_user(user_ratings)
        pop_scores = self.popularity_engine.get_popularity_score_array()

        # Dynamic weight adjustment based on user interaction density:
        # If user has only 1 rating, give content similarity slightly more weight than CF
        n_ratings = len(user_ratings)
        if n_ratings < 2:
            effective_cf = 0.20
            effective_content = 0.65
            effective_pop = 0.15
        else:
            total_w = weight_cf + weight_content + weight_pop
            effective_cf = weight_cf / total_w
            effective_content = weight_content / total_w
            effective_pop = weight_pop / total_w

        hybrid_scores = (
            effective_cf * cf_scores
            + effective_content * content_scores
            + effective_pop * pop_scores
        )
        return hybrid_scores, content_scores, cf_scores, pop_scores

    def score_to_match_percentage(self, score: float, user_ratings_count: int) -> int:
        """
        Maps a 0.0 - 1.0 hybrid score to a Netflix-style match percentage (e.g., 65% - 99%).
        """
        if user_ratings_count == 0:
            # Baseline popular match
            match = 70 + int(score * 25)
        else:
            match = 62 + int(score * 37)
        return int(np.clip(match, 60, 99))

    def get_seed_movie(self, user_ratings: Dict[int, float]) -> Optional[Dict]:
        """Finds user's top-rated movie to power the 'Because You Watched...' row."""
        if not user_ratings:
            return None
        # Sort by rating desc, then movie id desc
        sorted_ratings = sorted(user_ratings.items(), key=lambda x: (x[1], x[0]), reverse=True)
        top_id = int(sorted_ratings[0][0])
        return self.movies_by_id.get(top_id)

    def get_personalized_feed(
        self,
        user_id: str,
        custom_ratings: Optional[Dict[int, float]] = None,
        custom_watchlist: Optional[List[int]] = None,
        weight_cf: float = 0.45,
        weight_content: float = 0.40,
        weight_pop: float = 0.15,
    ) -> Dict:
        """
        Assembles a comprehensive, personalized Netflix page feed with carousels and hero billboard.
        """
        profile = self.user_profiles.get(user_id, {})
        ratings = (
            custom_ratings
            if custom_ratings is not None
            else profile.get("ratings", {})
        )
        # Ensure keys are ints
        ratings = {int(k): float(v) for k, v in ratings.items()}

        watchlist_ids = (
            custom_watchlist
            if custom_watchlist is not None
            else profile.get("watchlist", [])
        )
        watchlist_ids = [int(x) for x in watchlist_ids]

        hybrid_scores, content_scores, cf_scores, pop_scores = self.calculate_hybrid_scores(
            ratings, weight_cf, weight_content, weight_pop
        )

        rated_ids = set(ratings.keys())

        # Build annotated movie list with scores, match %, and explainability
        annotated_movies = []
        seed_movie = self.get_seed_movie(ratings)

        for idx, movie in enumerate(self.movies):
            mid = movie["id"]
            h_score = float(hybrid_scores[idx])
            c_score = float(content_scores[idx]) if len(content_scores) > idx else 0.0
            f_score = float(cf_scores[idx]) if len(cf_scores) > idx else 0.0
            p_score = float(pop_scores[idx]) if len(pop_scores) > idx else 0.0

            match_pct = self.score_to_match_percentage(h_score, len(ratings))
            explanation = self.explainability_engine.explain_recommendation(
                mid, ratings, c_score, f_score, p_score, seed_movie
            )

            movie_copy = dict(movie)
            movie_copy["hybrid_score"] = round(h_score, 4)
            movie_copy["match_percentage"] = match_pct
            movie_copy["explanation"] = explanation
            movie_copy["user_rating"] = ratings.get(mid)
            movie_copy["in_watchlist"] = mid in watchlist_ids

            annotated_movies.append(movie_copy)

        # Sort candidate movies (unrated) for "Top Picks"
        unrated_candidates = [m for m in annotated_movies if m["id"] not in rated_ids]
        top_picks = sorted(unrated_candidates, key=lambda x: x["hybrid_score"], reverse=True)[:14]

        # Hero Movie selection: Highest scored unrated movie with high visual backdrop
        hero_movie = top_picks[0] if top_picks else annotated_movies[0]

        # Row 1: "Trending Now"
        trending_raw = self.popularity_engine.get_trending_movies(top_n=14)
        trending_row = [
            next((m for m in annotated_movies if m["id"] == raw["id"]), raw)
            for raw in trending_raw
        ]

        # Row 2: "Because You Watched [Title]" (if user has rated something)
        because_you_watched_row = []
        because_title = ""
        if seed_movie:
            because_title = f"Because you watched {seed_movie['title']}"
            similar_tuples = self.content_engine.get_similar_to_movie(seed_movie["id"], top_n=14)
            similar_ids = [t[0] for t in similar_tuples]
            because_you_watched_row = [
                next((m for m in annotated_movies if m["id"] == sid), None)
                for sid in similar_ids
            ]
            because_you_watched_row = [m for m in because_you_watched_row if m is not None]

        # Genre Rows (filtered from annotated movies, sorted by hybrid score for personalization)
        def get_genre_row(genre_name: str, limit: int = 12):
            matches = [
                m for m in annotated_movies
                if genre_name.lower() in [g.lower() for g in m.get("genres", [])]
            ]
            # Order within genre by hybrid score
            return sorted(matches, key=lambda x: x["hybrid_score"], reverse=True)[:limit]

        scifi_row = get_genre_row("Sci-Fi")
        action_row = get_genre_row("Action")
        drama_row = get_genre_row("Drama")
        thriller_row = get_genre_row("Thriller")
        animation_row = get_genre_row("Animation")

        # Watchlist row
        watchlist_row = [m for m in annotated_movies if m["id"] in watchlist_ids]

        # Rated / History row
        rated_row = [
            m for m in annotated_movies
            if m["id"] in rated_ids
        ]
        rated_row.sort(key=lambda x: ratings.get(x["id"], 0), reverse=True)

        rows = []
        rows.append({
            "id": "top_picks",
            "title": f"Top Picks for {profile.get('name', 'You')}",
            "subtitle": "Personalized Hybrid Algorithm (Collaborative + Content-Based)",
            "movies": top_picks
        })

        rows.append({
            "id": "trending",
            "title": "Trending Now",
            "subtitle": "High Momentum & Bayesian IMDb Weighted Popularity",
            "movies": trending_row
        })

        full_movies_row = [m for m in annotated_movies if m.get("is_full_movie")]
        if full_movies_row:
            rows.append({
                "id": "full_movies",
                "title": "Complete Full-Length Feature Films (100% Free to Stream)",
                "subtitle": "Watch entire feature films from beginning to end with full video controls",
                "movies": full_movies_row
            })

        if because_you_watched_row:
            rows.append({
                "id": "because_watched",
                "title": because_title,
                "subtitle": f"Similar thematic soup, keywords & director style to {seed_movie['title']}",
                "movies": because_you_watched_row
            })

        if watchlist_row:
            rows.append({
                "id": "watchlist",
                "title": "My List",
                "subtitle": "Saved titles ready to stream",
                "movies": watchlist_row
            })

        rows.append({
            "id": "scifi",
            "title": "Mind-Bending Sci-Fi & Speculative Realities",
            "subtitle": "Space exploration, artificial intelligence & parallel realities",
            "movies": scifi_row
        })

        rows.append({
            "id": "action",
            "title": "High-Octane Action & Thrills",
            "subtitle": "Blockbusters, intense sequences & adrenaline rushes",
            "movies": action_row
        })

        rows.append({
            "id": "drama",
            "title": "Award-Winning Dramas & Human Stories",
            "subtitle": "Deep character journeys, emotional resonance & masterclass cinema",
            "movies": drama_row
        })

        rows.append({
            "id": "thriller",
            "title": "Dark Mysteries & Psychological Thrillers",
            "subtitle": "Edge-of-your-seat suspense, twist endings & serial investigators",
            "movies": thriller_row
        })

        if animation_row:
            rows.append({
                "id": "animation",
                "title": "Visionary Animation & Adventures",
                "subtitle": "Groundbreaking art styles, multiverse odysseys & family epics",
                "movies": animation_row
            })

        if rated_row:
            rows.append({
                "id": "history",
                "title": "Your Rated Movies & Watch History",
                "subtitle": "These titles train your personalized recommendation neural profile",
                "movies": rated_row
            })

        return {
            "user": {
                "id": user_id,
                "name": profile.get("name", "User"),
                "avatar": profile.get("avatar", ""),
                "tagline": profile.get("tagline", ""),
                "ratings_count": len(ratings),
                "watchlist_count": len(watchlist_ids)
            },
            "hero_movie": hero_movie,
            "rows": rows,
            "weights_used": {
                "collaborative": weight_cf,
                "content": weight_content,
                "popularity": weight_pop
            }
        }
