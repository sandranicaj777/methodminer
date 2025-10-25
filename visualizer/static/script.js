const socket = io('http://localhost:5050');
const wordCounts = {};

const ctx = document.getElementById('wordChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: [],
        datasets: [{
            label: 'Word Frequency',
            data: [],
        }]
    },
    options: {
        scales: {
            y: { beginAtZero: true }
        }
    }
});

socket.on('new_word', data => {
    const word = data.word;
    wordCounts[word] = (wordCounts[word] || 0) + 1;

    const sorted = Object.entries(wordCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);

    chart.data.labels = sorted.map(e => e[0]);
    chart.data.datasets[0].data = sorted.map(e => e[1]);
    chart.update();
});
