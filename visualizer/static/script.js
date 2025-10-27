const socket = io();
const wordCounts = { all: {}, python: {}, java: {} };
const colorMap = {};
let filter = "";
let currentLang = "all";

function getColor(word) {
    if (!colorMap[word]) {
        const hue = Math.floor(Math.random() * 360);
        colorMap[word] = `hsl(${hue}, 70%, 65%)`;
    }
    return colorMap[word];
}

const ctx = document.getElementById("wordChart").getContext("2d");

function createGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, color.replace("65%", "75%"));
    gradient.addColorStop(1, color.replace("65%", "55%"));
    return gradient;
}

const chart = new Chart(ctx, {
    type: "bar",
    data: {
        labels: [],
        datasets: [
            {
                label: "Word Frequency",
                data: [],
                backgroundColor: [],
                borderRadius: 8,
                borderSkipped: false, 
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 700,
            easing: "easeOutQuart",
        },
        scales: {
            x: {
                grid: {
                    display: false,
                },
                ticks: {
                    color: "#555",
                    font: { size: 13 },
                },
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: "rgba(0,0,0,0.05)",
                },
                ticks: {
                    color: "#777",
                    font: { size: 12 },
                },
            },
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: "rgba(0,0,0,0.7)",
                titleFont: { size: 14, weight: "600" },
                bodyFont: { size: 13 },
                padding: 10,
                cornerRadius: 8,
            },
        },
    },
});

function updateChart() {
    const data = wordCounts[currentLang] || {};
    const filtered = Object.entries(data)
        .filter(([word]) => word.includes(filter))
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    chart.data.labels = filtered.map(([w]) => w);
    chart.data.datasets[0].data = filtered.map(([_, c]) => c);

    chart.data.datasets[0].backgroundColor = filtered.map(([w]) => {
        const base = getColor(w);
        return createGradient(ctx, base);
    });

    chart.update();

    const total = Object.values(data).reduce((a, b) => a + b, 0);
    document.getElementById("total").textContent = `Total: ${total}`;
}

socket.on("new_word", (data) => {
    const { word, lang, repo } = data;

    wordCounts["all"][word] = (wordCounts["all"][word] || 0) + 1;
    wordCounts[lang] = wordCounts[lang] || {};
    wordCounts[lang][word] = (wordCounts[lang][word] || 0) + 1;

    document.getElementById("repoLabel").textContent = `Last repo: ${repo}`;
    updateChart();
});

document.getElementById("filter").addEventListener("input", (e) => {
    filter = e.target.value.trim().toLowerCase();
    updateChart();
});

document.getElementById("langSelect").addEventListener("change", (e) => {
    currentLang = e.target.value;
    updateChart();
});

["all", "python", "java"].forEach((lang) => {
    fetch(`/api/words?lang=${lang}`)
        .then((res) => res.json())
        .then((data) => {
            for (const [word, count] of Object.entries(data)) {
                wordCounts[lang][word] = parseInt(count);
            }
            updateChart();
        });
});
