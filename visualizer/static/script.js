const socket = io();
const wordCounts = {};
const colorMap = {};
let totalCount = 0;
let filter = "";

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
        plugins: {
            legend: { display: false },
        },
    },
});

function updateChart() {
    const filtered = Object.entries(wordCounts)
        .filter(([word]) => word.includes(filter))
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    chart.data.labels = filtered.map(([w]) => w);
    chart.data.datasets[0].data = filtered.map(([_, c]) => c);
    chart.data.datasets[0].backgroundColor = filtered.map(([w]) => getColor(w));
    chart.update();

    document.getElementById("total").textContent = `Total: ${totalCount}`;
}

socket.on("new_word", (data) => {
    const word = data.word;
    wordCounts[word] = (wordCounts[word] || 0) + 1;
    totalCount++;
    updateChart();
});

document.getElementById("filter").addEventListener("input", (e) => {
    filter = e.target.value.trim().toLowerCase();
    updateChart();
});

fetch("/api/words")
    .then((res) => res.json())
    .then((data) => {
        for (const [word, count] of Object.entries(data)) {
            wordCounts[word] = parseInt(count);
            totalCount += parseInt(count);
        }
        updateChart();
    });
