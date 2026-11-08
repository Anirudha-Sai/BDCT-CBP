from pathlib import Path
import csv

from flask import Flask, jsonify, request

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
ANALYTICS_DIR = BASE_DIR / "data" / "analytics"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def read_tsv(filename, columns, directory=ANALYTICS_DIR):
    """Read a TSV file without a header."""
    path = directory / filename

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter="\t")
        return [dict(zip(columns, row)) for row in reader if row]


def read_movie_analytics():
    """Read the enriched movie analytics file with its header."""
    path = PROCESSED_DIR / "movie_analytics.tsv"

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return list(csv.DictReader(file, delimiter="\t"))


def number(value, conversion=float, default=0):
    try:
        return conversion(value)
    except (ValueError, TypeError):
        return default


def analytics_data():
    return {
        "rating_distribution": read_tsv(
            "rating_distribution.tsv",
            ["rating", "total_ratings"]
        ),
        "top_rated_movies": read_tsv(
            "top_rated_movies.tsv",
            ["movie_id", "title", "rating_count", "average_rating"]
        ),
        "most_rated_movies": read_tsv(
            "most_rated_movies.tsv",
            ["movie_id", "title", "rating_count", "average_rating"]
        ),
        "genre_analytics": read_tsv(
            "genre_analytics.tsv",
            ["genre", "average_rating", "total_ratings"]
        ),
        "user_demographics": read_tsv(
            "user_demographics.tsv",
            ["gender", "total_users", "average_age"]
        ),
        "occupation_distribution": read_tsv(
            "occupation_distribution.tsv",
            ["occupation", "total_users"]
        ),
        "most_active_users": read_tsv(
            "most_active_users.tsv",
            ["user_id", "ratings_given", "average_rating"]
        )
    }


def count_lines(path):
    if not path.exists():
        return 0

    with path.open("r", encoding="utf-8") as file:
        return sum(1 for _ in file)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response


@app.get("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "message": "MovieLens API is running"
    })


@app.get("/api/analytics/overview")
def overview():
    movies = read_movie_analytics()

    genres = set()
    for movie in movies:
        for genre in movie["genres"].split(","):
            if genre.strip():
                genres.add(genre.strip())

    return jsonify({
        "total_movies": len(movies),
        "total_ratings": count_lines(PROCESSED_DIR / "ratings.tsv"),
        "total_users": count_lines(PROCESSED_DIR / "users.tsv"),
        "total_genres": len(genres)
    })


@app.get("/api/analytics/ratings")
def ratings():
    rows = analytics_data()["rating_distribution"]
    return jsonify([
        {
            "rating": number(row["rating"], int),
            "total_ratings": number(row["total_ratings"], int)
        }
        for row in rows
    ])


@app.get("/api/analytics/genres")
def genres():
    rows = analytics_data()["genre_analytics"]
    return jsonify([
        {
            "genre": row["genre"],
            "average_rating": number(row["average_rating"]),
            "total_ratings": number(row["total_ratings"], int)
        }
        for row in rows
    ])


@app.get("/api/analytics/top-rated")
def top_rated():
    rows = analytics_data()["top_rated_movies"]
    return jsonify([
        {
            "movie_id": number(r["movie_id"], int),
            "title": r["title"],
            "rating_count": number(r["rating_count"], int),
            "average_rating": number(r["average_rating"])
        }
        for r in rows
    ])


@app.get("/api/analytics/most-rated")
def most_rated():
    rows = analytics_data()["most_rated_movies"]
    return jsonify([
        {
            "movie_id": number(r["movie_id"], int),
            "title": r["title"],
            "rating_count": number(r["rating_count"], int),
            "average_rating": number(r["average_rating"])
        }
        for r in rows
    ])


@app.get("/api/analytics/users")
def users():
    rows = analytics_data()["user_demographics"]
    return jsonify([
        {
            "gender": r["gender"],
            "total_users": number(r["total_users"], int),
            "average_age": number(r["average_age"])
        }
        for r in rows
    ])


@app.get("/api/analytics/occupations")
def occupations():
    rows = analytics_data()["occupation_distribution"]
    return jsonify([
        {
            "occupation": r["occupation"],
            "total_users": number(r["total_users"], int)
        }
        for r in rows
    ])


@app.get("/api/analytics/active-users")
def active_users():
    rows = analytics_data()["most_active_users"]
    return jsonify([
        {
            "user_id": number(r["user_id"], int),
            "ratings_given": number(r["ratings_given"], int),
            "average_rating": number(r["average_rating"])
        }
        for r in rows
    ])


@app.get("/api/recommendations")
def recommendations():
    selected_genres = {
        genre.strip().lower()
        for genre in request.args.get("genres", "").split(",")
        if genre.strip()
    }

    min_rating = number(request.args.get("min_rating", 0))
    sort_by = request.args.get("sort_by", "rating").lower()
    limit = min(max(number(request.args.get("limit", 20), int), 1), 100)

    if sort_by not in ("rating", "popularity"):
        return jsonify({
            "error": "sort_by must be 'rating' or 'popularity'"
        }), 400

    movies = read_movie_analytics()
    results = []

    for movie in movies:
        movie_genres = {
            genre.strip().lower()
            for genre in movie["genres"].split(",")
            if genre.strip()
        }

        average_rating = number(movie["average_rating"])

        if average_rating < min_rating:
            continue

        # A movie matches if it belongs to at least one selected genre.
        if selected_genres and not selected_genres.intersection(movie_genres):
            continue

        results.append({
            "movie_id": number(movie["movie_id"], int),
            "title": movie["title"],
            "genres": movie["genres"],
            "rating_count": number(movie["rating_count"], int),
            "average_rating": average_rating
        })

    if sort_by == "popularity":
        results.sort(
            key=lambda x: (x["rating_count"], x["average_rating"]),
            reverse=True
        )
    else:
        results.sort(
            key=lambda x: (x["average_rating"], x["rating_count"]),
            reverse=True
        )

    return jsonify({
        "filters": {
            "genres": sorted(selected_genres),
            "min_rating": min_rating,
            "sort_by": sort_by
        },
        "total_results": len(results),
        "recommendations": results[:limit]
    })


@app.errorhandler(FileNotFoundError)
def handle_missing_file(error):
    return jsonify({"error": str(error)}), 500


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception("Unexpected API error")
    return jsonify({"error": "An internal server error occurred"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
