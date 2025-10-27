const socket = io();
const wordCounts = { all: {}, python: {}, java: {} };
const colorMap = {};
let filter = "";
let currentLang = "all";

function getColor(word) {
    if (!colorMap[word]) {
        const hue = Math.floor(Math.random() * 360);
        colorMap[word] = `hsl(${hue}, 70%, 75%)`;
    }
    return colorMap[word];
}

const ctx = document.getElementById("wordChart").getContext("2d");
const chart = new Chart(ctx, {
    type: "bar",
    data: { labels: [], datasets: [{ label: "Word Frequency", data: [], backgroundColor: [] }] },
    options: {
        responsive: true,
        animation: { duration: 600, easing: "easeOutQuart" },
        scales: { y: { beginAtZero: true, grace: "10%" } },
        plugins: { legend: { display: false } },
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
    chart.data.datasets[0].backgroundColor = filtered.map(([w]) => getColor(w));
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
