const API = "http://127.0.0.1:5000/api";

let selectedGenres = new Set();
let charts = {};
let dashboardLoaded = false;

async function fetchAPI(endpoint) {
    const response = await fetch(`${API}${endpoint}`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return response.json();
}

function showPage(page) {
    document.querySelectorAll(".page").forEach(element =>
        element.classList.remove("active")
    );

    document.querySelectorAll(".nav-link").forEach(element =>
        element.classList.remove("active")
    );

    document.getElementById(`${page}Page`).classList.add("active");
    document.getElementById(`${page}Nav`).classList.add("active");

    if (page === "analytics" && !dashboardLoaded) {
        loadDashboard();
    }
}

function formatNumber(value) {
    return Number(value).toLocaleString("en-IN");
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

async function loadGenres() {
    try {
        const genres = await fetchAPI("/analytics/genres");
        const container = document.getElementById("genreOptions");
        container.innerHTML = "";

        genres.forEach(item => {
            const button = document.createElement("button");
            button.className = "genre-chip";
            button.textContent = item.genre;

            button.addEventListener("click", () => {
                const genre = item.genre;

                if (selectedGenres.has(genre)) {
                    selectedGenres.delete(genre);
                    button.classList.remove("selected");
                } else {
                    selectedGenres.add(genre);
                    button.classList.add("selected");
                }
            });

            container.appendChild(button);
        });
    } catch (error) {
        document.getElementById("genreOptions").textContent =
            "Unable to load genres.";
        console.error(error);
    }
}

async function loadRecommendations() {
    const grid = document.getElementById("movieGrid");
    const count = document.getElementById("resultCount");

    grid.innerHTML = "<p class='muted'>Finding movies...</p>";

    const params = new URLSearchParams({
        genres: [...selectedGenres].join(","),
        min_rating: document.getElementById("minRating").value,
        sort_by: document.getElementById("sortBy").value,
        limit: document.getElementById("resultLimit").value
    });

    try {
        const data = await fetchAPI(`/recommendations?${params}`);
        count.textContent = `${formatNumber(data.total_results)} matching movies`;

        if (!data.recommendations.length) {
            grid.innerHTML = "<p class='muted'>No movies match these filters. Try changing your preferences.</p>";
            return;
        }

        grid.innerHTML = data.recommendations.map((movie, index) => `
            <article class="movie-card">
                <div>
                    <span class="movie-number">MOVIE #${index + 1}</span>
                    <h3>${escapeHTML(movie.title)}</h3>
                    <p class="movie-genres">${escapeHTML(movie.genres || "Unclassified")}</p>
                </div>
                <div class="movie-meta">
                    <span class="rating">★ ${Number(movie.average_rating).toFixed(2)} / 5</span>
                    <span class="muted">${formatNumber(movie.rating_count)} ratings</span>
                </div>
            </article>
        `).join("");

    } catch (error) {
        grid.innerHTML = "<p class='muted'>Unable to load recommendations. Check that Flask is running.</p>";
        console.error(error);
    }
}

function renderChart(id, type, labels, datasets, extraOptions = {}) {
    const canvas = document.getElementById(id);

    if (charts[id]) {
        charts[id].destroy();
    }

    charts[id] = new Chart(canvas, {
        type,
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: type === "doughnut",
                    labels: { color: "#c5ccda", padding: 18 }
                }
            },
            scales: type === "doughnut" ? {} : {
                x: {
                    ticks: { color: "#8993a5" },
                    grid: { color: "#252c39" }
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: "#8993a5" },
                    grid: { color: "#252c39" }
                }
            },
            ...extraOptions
        }
    });
}

function renderTable(elementId, rows, type) {
    const body = document.getElementById(elementId);

    if (!rows.length) {
        body.innerHTML = "<tr><td colspan='3'>No data available</td></tr>";
        return;
    }

    body.innerHTML = rows.map(row => {
        if (type === "users") {
            return `
                <tr>
                    <td>User ${row.user_id}</td>
                    <td>${formatNumber(row.ratings_given)}</td>
                    <td>${Number(row.average_rating).toFixed(2)}</td>
                </tr>`;
        }

        return `
            <tr>
                <td>${escapeHTML(row.title)}</td>
                <td>${formatNumber(row.rating_count)}</td>
                <td>${Number(row.average_rating).toFixed(2)}</td>
            </tr>`;
    }).join("");
}

async function loadDashboard() {
    try {
        const [
            overview,
            ratings,
            genres,
            demographics,
            occupations,
            topRated,
            mostRated,
            activeUsers
        ] = await Promise.all([
            fetchAPI("/analytics/overview"),
            fetchAPI("/analytics/ratings"),
            fetchAPI("/analytics/genres"),
            fetchAPI("/analytics/users"),
            fetchAPI("/analytics/occupations"),
            fetchAPI("/analytics/top-rated"),
            fetchAPI("/analytics/most-rated"),
            fetchAPI("/analytics/active-users")
        ]);

        document.getElementById("totalMovies").textContent =
            formatNumber(overview.total_movies);
        document.getElementById("totalRatings").textContent =
            formatNumber(overview.total_ratings);
        document.getElementById("totalUsers").textContent =
            formatNumber(overview.total_users);
        document.getElementById("totalGenres").textContent =
            formatNumber(overview.total_genres);

        renderChart(
            "ratingChart",
            "bar",
            ratings.map(r => `${r.rating} Stars`),
            [{
                label: "Number of ratings",
                data: ratings.map(r => r.total_ratings),
                backgroundColor: "#e8ad49",
                borderRadius: 6
            }]
        );

        renderChart(
            "genreChart",
            "bar",
            genres.map(g => g.genre),
            [{
                label: "Average rating",
                data: genres.map(g => g.average_rating),
                backgroundColor: "#68bda0",
                borderRadius: 5
            }],
            {
                indexAxis: "y",
                scales: {
                    x: {
                        min: 0,
                        max: 5,
                        ticks: { color: "#8993a5" },
                        grid: { color: "#252c39" }
                    },
                    y: {
                        ticks: { color: "#c5ccda" },
                        grid: { display: false }
                    }
                }
            }
        );

        renderChart(
            "demographicsChart",
            "doughnut",
            demographics.map(d => d.gender === "M" ? "Male" : "Female"),
            [{
                data: demographics.map(d => d.total_users),
                backgroundColor: ["#e8ad49", "#68bda0"],
                borderColor: "#131720",
                borderWidth: 4
            }]
        );

        renderChart(
            "occupationChart",
            "bar",
            occupations.map(o => o.occupation),
            [{
                label: "Number of users",
                data: occupations.map(o => o.total_users),
                backgroundColor: "#8b86d9",
                borderRadius: 5
            }],
            {
                indexAxis: "y",
                scales: {
                    x: {
                        ticks: { color: "#8993a5" },
                        grid: { color: "#252c39" }
                    },
                    y: {
                        ticks: { color: "#c5ccda" },
                        grid: { display: false }
                    }
                }
            }
        );

        renderTable("topRatedTable", topRated, "movies");
        renderTable("mostRatedTable", mostRated, "movies");
        renderTable("activeUsersTable", activeUsers, "users");

        dashboardLoaded = true;

    } catch (error) {
        console.error("Dashboard loading error:", error);
        alert("Unable to load dashboard data. Please check the Flask server.");
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    await loadGenres();
    await loadRecommendations();
});
