
import csv
from pathlib import Path
from collections import Counter

DATA_DIR = Path.home() / "BigData/MovieLens/data/raw/ml-100k"

# Read ratings
with open(DATA_DIR / "u.data", encoding="utf-8") as f:
    ratings = list(csv.reader(f, delimiter="\t"))

# Read movies
with open(DATA_DIR / "u.item", encoding="latin-1") as f:
    movies = list(csv.reader(f, delimiter="|"))

# Read users
with open(DATA_DIR / "u.user", encoding="latin-1") as f:
    users = list(csv.reader(f, delimiter="|"))

# Read genres
with open(DATA_DIR / "u.genre", encoding="latin-1") as f:
    genre_rows = [
        row for row in csv.reader(f, delimiter="|") if row
    ]

genres = {int(row[1]): row[0] for row in genre_rows}

# Create ID sets
movie_ids = {row[0] for row in movies}
user_ids = {row[0] for row in users}

# Rating statistics
rating_distribution = Counter()
movie_rating_counts = Counter()
user_rating_counts = Counter()

invalid_ratings = []
missing_movies = []
missing_users = []

for row in ratings:
    if len(row) != 4:
        invalid_ratings.append(row)
        continue

    user_id, movie_id, rating, timestamp = row

    if movie_id not in movie_ids:
        missing_movies.append(movie_id)

    if user_id not in user_ids:
        missing_users.append(user_id)

    rating_value = int(rating)

    if rating_value < 1 or rating_value > 5:
        invalid_ratings.append(row)

    rating_distribution[rating_value] += 1
    movie_rating_counts[movie_id] += 1
    user_rating_counts[user_id] += 1

# Genre statistics
genre_movie_counts = Counter()
movies_without_genre = 0

for movie in movies:
    if len(movie) != 24:
        continue

    flags = movie[5:24]
    assigned = False

    for index, flag in enumerate(flags):
        if flag == "1" and index > 0:
            genre_movie_counts[genres[index]] += 1
            assigned = True

    if not assigned:
        movies_without_genre += 1

# Duplicate checks
movie_id_count = Counter(row[0] for row in movies)
user_id_count = Counter(row[0] for row in users)

print("=" * 55)
print("             MOVIELENS DATASET ANALYSIS")
print("=" * 55)

print("\nDATASET COUNTS")
print(f"Ratings records : {len(ratings)}")
print(f"Movies          : {len(movies)}")
print(f"Users           : {len(users)}")
print(f"Genre entries   : {len(genres)}")
print(f"Named genres    : {len(genres) - 1}")

print("\nDATA VALIDATION")
print(f"Invalid ratings/rows : {len(invalid_ratings)}")
print(f"Missing movie IDs    : {len(missing_movies)}")
print(f"Missing user IDs     : {len(missing_users)}")
print(f"Duplicate movie IDs  : {sum(v - 1 for v in movie_id_count.values() if v > 1)}")
print(f"Duplicate user IDs   : {sum(v - 1 for v in user_id_count.values() if v > 1)}")

print("\nRATING DISTRIBUTION")
for rating in sorted(rating_distribution):
    print(f"{rating} stars: {rating_distribution[rating]}")

print("\nMOVIES PER GENRE")
for genre, count in genre_movie_counts.most_common():
    print(f"{genre:15s}: {count}")

print(f"\nMovies without assigned genre: {movies_without_genre}")

print("\nUSER ACTIVITY")
print(f"Users with ratings : {len(user_rating_counts)}")
print(f"Most active user   : {user_rating_counts.most_common(1)[0]}")
print(f"Least active user  : {user_rating_counts.most_common()[-1]}")

print("\nMOVIE ACTIVITY")
print(f"Movies with ratings: {len(movie_rating_counts)}")
print(f"Most rated movie ID: {movie_rating_counts.most_common(1)[0]}")

print("\n" + "=" * 55)
print("             ANALYSIS COMPLETED")
print("=" * 55)
