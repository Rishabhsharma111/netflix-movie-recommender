"""
Recommendation Explainability Engine
Generates human-readable, transparent insights into why each movie is recommended,
mirroring Netflix's personalized badge and reason generation.
"""
from typing import Dict, List, Optional


class ExplainabilityEngine:
    def __init__(self, movies: List[Dict]):
        self.movies = movies
        self.movie_by_id = {m["id"]: m for m in movies}

    def explain_recommendation(
        self,
        movie_id: int,
        user_ratings: Dict[int, float],
        content_score: float,
        cf_score: float,
        pop_score: float,
        top_seed_movie: Optional[Dict] = None
    ) -> Dict:
        """
        Generates structured explanation breakdown for a recommended movie.
        """
        target = self.movie_by_id.get(movie_id, {})
        reasons = []
        tags = []

        # Check director overlap with user's top-rated movies
        target_dir = target.get("director", "")
        favorite_movies = [
            self.movie_by_id[int(mid)]
            for mid, r in user_ratings.items()
            if float(r) >= 4.5 and int(mid) in self.movie_by_id
        ]

        same_dir_movies = [m["title"] for m in favorite_movies if m.get("director") == target_dir]
        if same_dir_movies:
            reasons.append(f"Directed by {target_dir} ({', '.join(same_dir_movies[:2])})")
            tags.append(f"Director: {target_dir}")

        # Check seed movie comparison
        if top_seed_movie and top_seed_movie["id"] != movie_id:
            common_genres = set(target.get("genres", [])).intersection(
                set(top_seed_movie.get("genres", []))
            )
            if common_genres:
                reasons.append(
                    f"Similar cinematic vibe to '{top_seed_movie['title']}' ({', '.join(list(common_genres)[:2])})"
                )
                tags.append(f"Like {top_seed_movie['title']}")

        # Collaborative signals
        if cf_score > 0.65:
            reasons.append("Highly rated by viewers with taste profiles matching yours")
            tags.append("Community Favorite")

        # Genre affinity
        target_genres = target.get("genres", [])
        if target_genres:
            tags.append(target_genres[0])

        # Fallback if few ratings
        if not reasons:
            if target.get("rating", 0) >= 8.5:
                reasons.append(f"Critically acclaimed masterpiece ({target.get('rating')} IMDb score)")
                tags.append("Critically Acclaimed")
            else:
                reasons.append("Trending among top-streamed titles this week")
                tags.append("Trending")

        return {
            "movie_id": movie_id,
            "primary_reason": reasons[0] if reasons else "Recommended for you",
            "all_reasons": reasons,
            "badges": tags[:3],
            "metrics": {
                "content_similarity": round(float(content_score) * 100, 1),
                "collaborative_affinity": round(float(cf_score) * 100, 1),
                "popularity_factor": round(float(pop_score) * 100, 1),
            }
        }
