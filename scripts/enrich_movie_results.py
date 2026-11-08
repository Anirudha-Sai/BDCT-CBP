import csv
from pathlib import Path

BASE_DIR = Path.home() / "BigData/MovieLens"
DATA_DIR = BASE_DIR / "data/processed"

movies_file = DATA_DIR / "movies.tsv"
ratings_file = DATA_DIR / "movie_rating_average.tsv"
output_file = DATA_DIR / "movie_analytics.tsv"

# Load movie metadata
movies = {}

with open(movies_file, encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")

    for row in reader:
        if len(row) == 3:
            movie_id, title, genres = row
            movies[movie_id] = {
                "title": title,
                "genres": genres
            }

# Join MapReduce results with movie metadata
joined_count = 0
missing_count = 0

with open(ratings_file, encoding="utf-8") as source, \
     open(output_file, "w", encoding="utf-8", newline="") as target:

    reader = csv.reader(source, delimiter="\t")
    writer = csv.writer(target, delimiter="\t")

    writer.writerow([
        "movie_id",
        "title",
        "genres",
        "rating_count",
        "average_rating"
    ])

    for row in reader:
        if len(row) != 3:
            continue

        movie_id, rating_count, average_rating = row

        if movie_id not in movies:
            missing_count += 1
            continue

        movie = movies[movie_id]

        writer.writerow([
            movie_id,
            movie["title"],
            movie["genres"],
            rating_count,
            average_rating
        ])

        joined_count += 1

print("=" * 45)
print("       MOVIE ANALYTICS ENRICHMENT")
print("=" * 45)
print(f"Movies enriched : {joined_count}")
print(f"Missing movies  : {missing_count}")
print(f"Output file     : {output_file}")

