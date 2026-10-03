# 🎬 Netflix AI — Movie Recommendation System

A full-stack Netflix-inspired movie recommendation application built with **Python, FastAPI, Scikit-learn, HTML, CSS and JavaScript**.

The recommendation engine combines **Collaborative Filtering**, **Content-Based Filtering**, and **Bayesian Popularity Ranking** to generate personalized movie recommendations.

> **Note:** This is an educational/portfolio project inspired by the Netflix-style recommendation experience. It is not affiliated with Netflix.

## ✨ Features

- 🎯 Personalized movie recommendations
- 🧠 Hybrid recommendation engine
- 🤝 Collaborative Filtering with Truncated SVD
- 📝 Content-Based Filtering with TF-IDF + cosine similarity
- ⭐ Bayesian weighted movie ratings
- 🔥 Trending movie ranking with recency decay
- ❄️ Cold-start handling
- 💡 Explainable recommendations
- 🎚️ Interactive recommendation-weight tuning
- 👤 Multiple demo profiles
- ⭐ Movie ratings from 1–5
- 📋 Watchlist / My List
- 🔎 Search by title, director, cast, genre and keywords
- 🎞️ Movie detail modal with trailer support
- 📱 Responsive Netflix-inspired UI
- 📚 REST API with FastAPI
- 🧪 Automated unit tests
- 📖 Swagger API documentation

## 🧠 Recommendation Pipeline

The final recommendation score combines three signals:

```text
                    ┌─────────────────────┐
                    │   User Interaction  │
                    │      & Ratings      │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
      Collaborative      Content-Based      Popularity
       Filtering           Filtering          Ranking
       TruncatedSVD         TF-IDF             Bayesian
       Item-Item CF      Cosine Similarity    Trending
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Hybrid Ranker     │
                    │                     │
                    │ CF + Content + Pop  │
                    └──────────┬──────────┘
                               ▼
                    Personalized Feed
```

### 1. Collaborative Filtering

The project builds a user–movie rating matrix and uses **TruncatedSVD** to learn latent factors. It also uses item-to-item cosine similarity to capture relationships between movies based on user interactions.

### 2. Content-Based Filtering

Movie metadata is combined into a weighted metadata representation containing:

- Genres
- Director
- Cast
- Keywords
- Plot overview

TF-IDF vectors and cosine similarity are then used to identify movies with similar content.

### 3. Popularity Ranking

The popularity component uses a Bayesian weighted-rating formula so that movies with very few votes do not automatically dominate the ranking.

Trending scores additionally include a recency-decay component.

### 4. Hybrid Recommendation

The three recommendation signals are combined:

```text
Hybrid Score =
    CF Weight      × Collaborative Score
  + Content Weight × Content Similarity
  + Popularity Weight × Popularity Score
```

The application allows the weights to be adjusted interactively.

## 🏗️ Project Structure

```text
netflix-movie-recommender/
│
├── data/
│   ├── movies.json
│   ├── user_ratings.json
│   └── seed_data.py
│
├── engine/
│   ├── __init__.py
│   ├── collaborative.py
│   ├── content_based.py
│   ├── explainability.py
│   ├── hybrid.py
│   └── popularity.py
│
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── tests/
│   └── test_recommender.py
│
├── server.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## 🛠️ Tech Stack

### Backend
- Python
- FastAPI
- Uvicorn
- Pydantic

### Machine Learning
- Scikit-learn
- NumPy
- Pandas
- TruncatedSVD
- TF-IDF
- Cosine Similarity

### Frontend
- HTML5
- CSS3
- JavaScript

### Data
- JSON-based movie catalog
- JSON-based user-rating profiles

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd netflix-movie-recommender
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the FastAPI server

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Open the application

```text
http://127.0.0.1:8000/
```

### 6. Open API documentation

```text
http://127.0.0.1:8000/docs
```

## 🧪 Run Tests

```bash
python -m unittest tests/test_recommender.py
```

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/feed` | Generate personalized recommendation feed |
| GET | `/api/profiles` | Get available profiles |
| GET | `/api/movies` | Search/filter movies |
| GET | `/api/movies/{id}` | Get movie details and similar movies |
| POST | `/api/rate` | Add/update a movie rating |
| POST | `/api/watchlist` | Add/remove a movie from My List |
| POST | `/api/reset-profile` | Reset a profile |

## 👤 Demo Profiles

The project contains pre-seeded profiles representing different movie preferences, including:

- **Alex** — Sci-Fi & mind-bending movies
- **Priya** — Drama, Romance & cinephile picks
- **Marcus** — Crime, Thriller & classics
- **Maya** — Animation, Adventure & Fantasy
- **Guest** — Cold-start profile

## 📊 Dataset

The repository contains a curated movie catalog and pre-seeded user-rating profiles for demonstrating the recommendation algorithms.

The current catalog is intentionally small and is designed for a portfolio/demo application rather than production-scale recommendation training.

## 🔐 Security Note

This repository is intended as a portfolio/educational project.

- Do not commit API keys.
- Do not commit passwords or tokens.
- Keep secrets in environment variables.
- The included JSON data is demo data.

## 📌 Future Improvements

Possible extensions:

- Real database integration
- User authentication
- Larger movie/rating dataset
- Recommendation evaluation with Precision@K, Recall@K and NDCG
- User watch history
- Continue Watching
- Production deployment
- Docker support

## 👨‍💻 Author

**Rishabh Sharma**

B.Tech — Computer Science & Artificial Intelligence

## ⭐ If you find this project useful

Feel free to fork the repository, experiment with the recommendation weights, and extend the recommendation engine.
