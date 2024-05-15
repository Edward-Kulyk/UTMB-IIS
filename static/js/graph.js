function buildGraph(campaign, graphID, startDate) {
    const datesSet = new Set(campaign.data.map(entry => entry.date));
    const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'];
    const shapes = ['linear', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot'];

    const clicks = {};
    const sessions = {};

    // Fill data
    campaign.data.forEach(entry => {
        const { date, session_source_medium, clicks: clicksCount, sessions: sessionsCount } = entry;
        if (!clicks[date]) clicks[date] = {};
        if (!sessions[date]) sessions[date] = {};
        clicks[date][session_source_medium] = clicksCount;
        sessions[date][session_source_medium] = sessionsCount;
    });

    const dates = Array.from(datesSet);
    const datasets = createDatasets();

    const chartData = {
        labels: dates,
        datasets: datasets
    };

    const chartOptions = createChartOptions();

    const canvasId = 'graph-canvas-' + graphID.split('-')[1];
    const ctx = document.getElementById(canvasId).getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: chartOptions
    });

    // Checkbox state
    let clicksCheckboxChecked = true;
    let sessionsCheckboxChecked = true;

    document.getElementById('clicks-checkbox-' + graphID.split('-')[1]).addEventListener('change', function() {
        clicksCheckboxChecked = this.checked;
        updateChartVisibility();
    });

    document.getElementById('sessions-checkbox-' + graphID.split('-')[1]).addEventListener('change', function() {
        sessionsCheckboxChecked = this.checked;
        updateChartVisibility();
    });

    function createDatasets() {
        return Object.keys(clicks[dates[0]]).map((sourceMedium, index) => {
            const color = colors[index];
            const shape = shapes[index % shapes.length];
            const clickData = dates.map(date => clicks[date][sourceMedium] || 0);
            const sessionData = dates.map(date => sessions[date][sourceMedium] || 0);

            return [
                createDataset(sourceMedium + ' (clicks)', clickData, color, 'dot'),
                createDataset(sourceMedium + ' (sessions)', sessionData, color, 'dot', [5, 5])
            ];
        }).flat();
    }

    function createDataset(label, data, borderColor, pointStyle, borderDash) {
        return {
            label,
            data,
            borderColor,
            borderWidth: 1,
            pointStyle,
            borderDash
        };
    }

    function createChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            title: {
                display: true,
                text: `График кликов и сессий для ${campaign.campaign_name}`
            },
            scales: {
                xAxes: [{
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'YYYY-MM-DD'
                        },
                        scaleLabel: {
                            display: true,
                            labelString: 'Дата'
                        }
                    }
                }],
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: 'Клики/Сессии'
                    }
                }]
            }
        };
    }

    function updateChartVisibility() {
        const clicksDatasets = chart.data.datasets.filter(dataset => dataset.label.includes('(clicks)'));
        const sessionsDatasets = chart.data.datasets.filter(dataset => dataset.label.includes('(sessions)'));

        clicksDatasets.forEach(dataset => dataset.hidden = !clicksCheckboxChecked);
        sessionsDatasets.forEach(dataset => dataset.hidden = !sessionsCheckboxChecked);

        chart.update();
    }
}
