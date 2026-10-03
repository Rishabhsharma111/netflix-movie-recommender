"""
Unit Tests for Netflix Recommendation Engine
"""
import json
import unittest
from pathlib import Path
from engine import NetflixHybridRecommender

BASE_DIR = Path(__file__).resolve().parent.parent

class TestNetflixRecommender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(BASE_DIR / "data" / "movies.json", "r", encoding="utf-8") as f:
            cls.movies = json.load(f)
        with open(BASE_DIR / "data" / "user_ratings.json", "r", encoding="utf-8") as f:
            cls.users = json.load(f)
        cls.recommender = NetflixHybridRecommender(cls.movies, cls.users)

    def test_catalog_loaded(self):
        self.assertGreaterEqual(len(self.movies), 40)
        self.assertIn("user_1", self.users)

    def test_content_recommender(self):
        # Similar movies to Interstellar (id=1)
        similars = self.recommender.content_engine.get_similar_to_movie(1, top_n=5)
        self.assertEqual(len(similars), 5)
        # Verify scores are bounded between 0 and 1
        for sid, score, tags in similars:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_collaborative_recommender(self):
        ratings = {1: 5.0, 2: 5.0} # User likes Interstellar and Inception
        scores = self.recommender.collaborative_engine.score_movies_for_user(ratings)
        self.assertEqual(len(scores), len(self.movies))
        self.assertTrue(any(s > 0.0 for s in scores))

    def test_popularity_ranker(self):
        trending = self.recommender.popularity_engine.get_trending_movies(top_n=5)
        self.assertEqual(len(trending), 5)
        top_rated = self.recommender.popularity_engine.get_top_rated_movies(genre="Sci-Fi", top_n=3)
        self.assertGreaterEqual(len(top_rated), 1)

    def test_hybrid_feed_user1(self):
        feed = self.recommender.get_personalized_feed("user_1")
        self.assertEqual(feed["user"]["name"], "Alex")
        self.assertIsNotNone(feed["hero_movie"])
        self.assertGreaterEqual(len(feed["rows"]), 5)

        # First row is "Top Picks"
        top_picks = feed["rows"][0]["movies"]
        self.assertGreater(len(top_picks), 0)
        # Match percentage should be between 60 and 99
        for m in top_picks:
            self.assertGreaterEqual(m["match_percentage"], 60)
            self.assertLessEqual(m["match_percentage"], 99)

    def test_cold_start_guest(self):
        feed = self.recommender.get_personalized_feed("user_guest")
        self.assertEqual(feed["user"]["name"], "Guest (Cold Start)")
        self.assertIsNotNone(feed["hero_movie"])
        self.assertGreaterEqual(len(feed["rows"]), 4)

if __name__ == "__main__":
    unittest.main()
