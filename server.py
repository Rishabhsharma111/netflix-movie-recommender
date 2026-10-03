"""
Netflix Movie Recommendation Backend Server
Built with FastAPI, serving personalized feeds, real-time ratings, explainability, and static UI.
"""
import copy
import json
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from engine import NetflixHybridRecommender

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
VIDEOS_DIR = BASE_DIR / "videos"
VIDEOS_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Netflix Movie Recommendation System",
    description="Full-stack hybrid recommender using Matrix Factorization SVD, Content TF-IDF, and Bayesian Popularity.",
    version="2.0.0"
)

app.mount("/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Initial Data
with open(DATA_DIR / "movies.json", "r", encoding="utf-8") as f:
    INITIAL_MOVIES = json.load(f)

with open(DATA_DIR / "user_ratings.json", "r", encoding="utf-8") as f:
    INITIAL_USERS = json.load(f)

# State
movies_db = INITIAL_MOVIES
user_profiles_db = copy.deepcopy(INITIAL_USERS)
hybrid_recommender = NetflixHybridRecommender(movies_db, user_profiles_db)


# Request Models
class RateRequest(BaseModel):
    user_id: str
    movie_id: int
    rating: float  # 1.0 to 5.0 (or thumbs up=5.0, thumbs down=1.0)


class WatchlistRequest(BaseModel):
    user_id: str
    movie_id: int


class WeightSettings(BaseModel):
    cf: float = 0.45
    content: float = 0.40
    pop: float = 0.15


@app.get("/api/profiles")
def get_profiles():
    """Returns all available user profiles."""
    profiles = []
    for uid, data in user_profiles_db.items():
        profiles.append({
            "id": uid,
            "name": data["name"],
            "avatar": data["avatar"],
            "tagline": data["tagline"],
            "ratings_count": len(data.get("ratings", {})),
            "watchlist_count": len(data.get("watchlist", [])),
            "top_genres": data.get("preferences", [])
        })
    return {"profiles": profiles}


@app.get("/api/feed")
def get_feed(
    user_id: str = Query("user_1", description="User ID"),
    cf: float = Query(0.45, ge=0.0, le=1.0, description="Collaborative weight"),
    content: float = Query(0.40, ge=0.0, le=1.0, description="Content weight"),
    pop: float = Query(0.15, ge=0.0, le=1.0, description="Popularity weight")
):
    """Generates personalized Netflix homepage rows for the requested user profile."""
    if user_id not in user_profiles_db:
        raise HTTPException(status_code=404, detail="User profile not found")

    feed = hybrid_recommender.get_personalized_feed(
        user_id=user_id,
        custom_ratings=user_profiles_db[user_id].get("ratings", {}),
        custom_watchlist=user_profiles_db[user_id].get("watchlist", []),
        weight_cf=cf,
        weight_content=content,
        weight_pop=pop
    )
    return feed


@app.get("/api/movies")
def get_movies(
    q: Optional[str] = Query(None, description="Search term for title, director, cast, or genre"),
    genre: Optional[str] = Query(None, description="Genre filter")
):
    """Searches and filters the catalog."""
    results = movies_db
    if genre:
        results = [m for m in results if genre.lower() in [g.lower() for g in m.get("genres", [])]]
    if q:
        query_norm = q.lower().strip()
        results = [
            m for m in results
            if query_norm in m["title"].lower()
            or query_norm in m.get("director", "").lower()
            or any(query_norm in c.lower() for c in m.get("cast", []))
            or any(query_norm in g.lower() for g in m.get("genres", []))
            or any(query_norm in k.lower() for k in m.get("keywords", []))
        ]
    return {"count": len(results), "movies": results}


@app.get("/api/movies/{movie_id}")
def get_movie_detail(movie_id: int, user_id: Optional[str] = "user_1"):
    """Returns detailed movie info + 'More Like This' recommendations."""
    movie = next((m for m in movies_db if m["id"] == movie_id), None)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Content-based similar
    similar_tuples = hybrid_recommender.content_engine.get_similar_to_movie(movie_id, top_n=6)
    more_like_this = []
    for sid, score, tags in similar_tuples:
        sm = next((m for m in movies_db if m["id"] == sid), None)
        if sm:
            sm_copy = dict(sm)
            sm_copy["similarity_score"] = round(score * 100, 1)
            sm_copy["shared_tags"] = tags
            more_like_this.append(sm_copy)

    # User context
    user_rating = None
    in_watchlist = False
    if user_id and user_id in user_profiles_db:
        user_rating = user_profiles_db[user_id].get("ratings", {}).get(movie_id)
        in_watchlist = movie_id in user_profiles_db[user_id].get("watchlist", [])

    return {
        "movie": movie,
        "user_context": {
            "rating": user_rating,
            "in_watchlist": in_watchlist
        },
        "more_like_this": more_like_this
    }


@app.get("/api/local-videos")
def get_local_videos():
    """Scans the videos/ directory for custom user movies (.mp4, .mkv, .webm)."""
    extensions = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
    local_files = []
    if VIDEOS_DIR.exists():
        for f in VIDEOS_DIR.iterdir():
            if f.suffix.lower() in extensions:
                title = f.stem.replace(".", " ").replace("_", " ").title()
                local_files.append({
                    "filename": f.name,
                    "title": title,
                    "stream_url": f"/videos/{f.name}",
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2)
                })
    return {"count": len(local_files), "videos": local_files}


@app.post("/api/rate")
def rate_movie(req: RateRequest):
    """
    Rates a movie (1.0 to 5.0 stars or thumbs up=5.0, thumbs down=1.0).
    Instantly updates user taste profile.
    """
    if req.user_id not in user_profiles_db:
        raise HTTPException(status_code=404, detail="User profile not found")

    user = user_profiles_db[req.user_id]
    if "ratings" not in user:
        user["ratings"] = {}

    user["ratings"][req.movie_id] = req.rating
    return {
        "status": "success",
        "user_id": req.user_id,
        "movie_id": req.movie_id,
        "rating": req.rating,
        "total_ratings": len(user["ratings"])
    }


@app.post("/api/watchlist")
def toggle_watchlist(req: WatchlistRequest):
    """Toggles movie presence in the user's watchlist."""
    if req.user_id not in user_profiles_db:
        raise HTTPException(status_code=404, detail="User profile not found")

    user = user_profiles_db[req.user_id]
    if "watchlist" not in user:
        user["watchlist"] = []

    if req.movie_id in user["watchlist"]:
        user["watchlist"].remove(req.movie_id)
        in_list = False
    else:
        user["watchlist"].append(req.movie_id)
        in_list = True

    return {
        "status": "success",
        "movie_id": req.movie_id,
        "in_watchlist": in_list,
        "total_watchlist": len(user["watchlist"])
    }


@app.post("/api/reset-profile")
def reset_profile(user_id: str = Query("user_1")):
    """Resets the user profile to default seeded ratings."""
    if user_id in INITIAL_USERS:
        user_profiles_db[user_id] = copy.deepcopy(INITIAL_USERS[user_id])
    return {"status": "reset", "user_id": user_id}


# Mount Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
