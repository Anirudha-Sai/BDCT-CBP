import csv
from pathlib import Path

BASE_DIR = Path.home() / "BigData/MovieLens"

RAW_DIR = BASE_DIR / "data/raw/ml-100k"
PROCESSED_DIR = BASE_DIR / "data/processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Load genre mapping
with open(RAW_DIR / "u.genre", encoding="latin-1") as f:
    genre_rows = [
        row for row in csv.reader(f, delimiter="|") if row
    ]

genres = {int(row[1]): row[0] for row in genre_rows}

# Process ratings
ratings_count = 0

with open(RAW_DIR / "u.data", encoding="utf-8") as source, \
     open(PROCESSED_DIR / "ratings.tsv", "w", encoding="utf-8") as target:

    reader = csv.reader(source, delimiter="\t")

    for row in reader:
        if len(row) != 4:
            continue

        target.write("\t".join(row) + "\n")
        ratings_count += 1


# Process movies
movies_count = 0

with open(RAW_DIR / "u.item", encoding="latin-1") as source, \
     open(PROCESSED_DIR / "movies.tsv", "w", encoding="utf-8") as target:

    reader = csv.reader(source, delimiter="|")

    for row in reader:
        if len(row) != 24:
            continue

        movie_id = row[0]
        title = row[1]

        movie_genres = [
            genres[index]
            for index, flag in enumerate(row[5:24])
            if flag == "1" and index > 0
        ]

        genre_string = ",".join(movie_genres) if movie_genres else "Unknown"

        target.write(
            f"{movie_id}\t{title}\t{genre_string}\n"
        )

        movies_count += 1


# Process users
users_count = 0

with open(RAW_DIR / "u.user", encoding="latin-1") as source, \
     open(PROCESSED_DIR / "users.tsv", "w", encoding="utf-8") as target:

    reader = csv.reader(source, delimiter="|")

    for row in reader:
        if len(row) != 5:
            continue

        target.write("\t".join(row) + "\n")
        users_count += 1


# Print summary
print("=" * 45)
print("       DATA PREPROCESSING COMPLETED")
print("=" * 45)

print(f"Ratings processed : {ratings_count}")
print(f"Movies processed  : {movies_count}")
print(f"Users processed   : {users_count}")

print("\nGenerated files:")
for file in sorted(PROCESSED_DIR.iterdir()):
    print(f"{file.name:15s} {file.stat().st_size:,} bytes")

print("\nAll files are stored in data/processed/")
