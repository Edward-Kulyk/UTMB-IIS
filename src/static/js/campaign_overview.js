$(document).ready(function() {
    var currentFilter = 'all';
    var sortOrder = { column: 'clicks_total', order: 'desc' };
    var chart;
    var currentPage = 1;
    var rowsPerPage = 10;
    var totalRows = 0;
    var filteredData = [];
    var chartData;

    function getCurrentQuarterDates() {
        var now = new Date();
        var quarter = Math.floor((now.getMonth() / 3));
        var startDate = new Date(now.getFullYear(), quarter * 3, 1);
        var endDate = new Date(startDate.getFullYear(), startDate.getMonth() + 3, 0);

        return {
            start: startDate.toISOString().split('T')[0],
            end: endDate.toISOString().split('T')[0]
        };
    }

    // Set initial dates to current quarter
    var currentQuarterDates = getCurrentQuarterDates();
    $('#start-date').val(currentQuarterDates.start);
    $('#end-date').val(currentQuarterDates.end);

    // Campaign tab click handler
    $('.campaign-tab').on('click', function() {
        $('.campaign-tab').removeClass('selected');
        $(this).addClass('selected');
        var campaignId = $(this).data('campaign-id');
        console.log("Campaign changed to:", campaignId);

        // Reset dates to current quarter
        var currentQuarterDates = getCurrentQuarterDates();
        $('#start-date').val(currentQuarterDates.start);
        $('#end-date').val(currentQuarterDates.end);

        fetchCampaignData(campaignId);
        fetchCampaignGraphData(campaignId);
    });

    $('#apply-date-filter').on('click', function() {
        var campaignId = $('.campaign-tab.selected').data('campaign-id');
        if (!campaignId) {
            alert("Please select a campaign first.");
            return;
        }
        console.log("Applying date filters for campaign ID:", campaignId);
        fetchCampaignData(campaignId);
    });

    function fetchCampaignData(campaignId) {
        var startDate = $('#start-date').val();
        var endDate = $('#end-date').val();

        var tableUrl = `/campaigns/api/table/${campaignId}`;
        var graphUrl = `/campaigns/api/graph/${campaignId}`;
        var queryParams = [];
        if (startDate) queryParams.push(`start_date=${startDate}`);
        if (endDate) queryParams.push(`end_date=${endDate}`);
        var queryString = queryParams.length ? '?' + queryParams.join('&') : '';

        console.log("Fetching table data from:", tableUrl + queryString);
        console.log("Fetching graph data from:", graphUrl + queryString);

        $.when(
            $.ajax({
                url: tableUrl + queryString,
                method: 'GET'
            }),
            $.ajax({
                url: graphUrl + queryString,
                method: 'GET'
            })
        ).done(function(tableData, graphData) {
            updateCampaignContent(tableData[0]);
            updateGraph(graphData[0]);
        }).fail(function(error) {
            console.error('Error fetching campaign data:', error);
        });
    }

    function updateCampaignContent(data) {
        filteredData = data;
        currentPage = 1;
        applyDefaultSort();
        applyFilterAndSort();
    }

    function applyDefaultSort() {
        switch (currentFilter) {
            case 'all':
                sortOrder = { column: 'clicks_total', order: 'desc' };
                break;
            case 'ga4':
                sortOrder = { column: 'ga_sessions', order: 'desc' };
                break;
            case 'clicks':
                sortOrder = { column: 'clicks_total', order: 'desc' };
                break;
        }
    }

    function applyFilterAndSort() {
        var filteredRows = filteredData.filter(function(row) {
            var shortUrl = row.short_secure_url || '-';
            if (currentFilter === 'clicks' && shortUrl !== '-') {
                return true;
            } else if (currentFilter === 'ga4' && shortUrl === '-') {
                return true;
            } else if (currentFilter === 'all') {
                return true;
            }
            return false;
        });

        filteredRows.sort(function(a, b) {
            var A = a[sortOrder.column];
            var B = b[sortOrder.column];

            if (A === '-') A = 0;
            if (B === '-') B = 0;

            if ($.isNumeric(A) && $.isNumeric(B)) {
                A = parseFloat(A);
                B = parseFloat(B);
            }

            if (sortOrder.order === 'asc') {
                return (A < B) ? -1 : (A > B) ? 1 : 0;
            } else {
                return (A > B) ? -1 : (A < B) ? 1 : 0;
            }
        });

        totalRows = filteredRows.length;
        displayTable(filteredRows);
        updatePaginationControls();
    }

    function displayTable(rows) {
        var startIndex = (currentPage - 1) * rowsPerPage;
        var endIndex = startIndex + rowsPerPage;
        var pageData = rows.slice(startIndex, endIndex);

        var contentHtml = '<div class="filter-buttons">';
        contentHtml += '<button id="filter-clicks" class="filter-btn">Clicks</button>';
        contentHtml += '<button id="filter-ga4" class="filter-btn">GA4</button>';
        contentHtml += '<button id="filter-all" class="filter-btn">All</button>';
        contentHtml += '</div>';
        contentHtml += '<h2>' + filteredData[0].campaign_name + ' - [Launch Date: ' + filteredData[0].start_date + ']</h2>';
        contentHtml += '<table>';
        contentHtml += '<thead><tr>';
        contentHtml += '<th>Short Secure URL</th>';
        contentHtml += '<th>Campaign Content</th>';
        contentHtml += '<th>Campaign Source</th>';
        contentHtml += '<th>Campaign Medium</th>';
        contentHtml += '<th class="sortable" data-sort="clicks_total">Clicks</th>';
        contentHtml += '<th class="sortable" data-sort="ga_active_users">Users</th>';
        contentHtml += '<th class="sortable" data-sort="ga_sessions">Sessions</th>';
        contentHtml += '<th class="sortable" data-sort="ga_average_session_duration">Avg session duration</th>';
        contentHtml += '<th class="sortable" data-sort="bounce_rate">Bounce rate</th>';
        contentHtml += '</tr></thead>';
        contentHtml += '<tbody>';

        pageData.forEach(function(link) {
            contentHtml += '<tr>';
            contentHtml += '<td class="short-url">' + (link.short_secure_url || '-') + '</td>';
            contentHtml += '<td>' + (link.campaign_content || '-') + '</td>';
            contentHtml += '<td>' + (link.campaign_source || '-') + '</td>';
            contentHtml += '<td>' + (link.campaign_medium || '-') + '</td>';
            contentHtml += '<td class="clicks_total">' + (link.clicks_total !== undefined ? link.clicks_total : '-') + '</td>';
            contentHtml += '<td class="ga_active_users">' + (link.ga_active_users !== undefined ? link.ga_active_users : '-') + '</td>';
            contentHtml += '<td class="ga_sessions">' + (link.ga_sessions !== undefined ? link.ga_sessions : '-') + '</td>';
            contentHtml += '<td class="ga_average_session_duration">' + (link.ga_average_session_duration !== undefined ? link.ga_average_session_duration : '-') + '</td>';
            contentHtml += '<td class="bounce_rate">' + (link.bounce_rate !== undefined ? link.bounce_rate : '-') + '</td>';
            contentHtml += '</tr>';
        });

        contentHtml += '</tbody></table>';
        $('#campaign-content').html(contentHtml);

        // Добавляем индикатор сортировки к заголовку таблицы
        $('th.sortable').each(function() {
            var column = $(this).data('sort');
            if (column === sortOrder.column) {
                $(this).append(sortOrder.order === 'asc' ? ' ▲' : ' ▼');
            }
        });

        addFilterHandlers();
        addSortHandlers();
    }

    function updatePaginationControls() {
        var totalPages = Math.ceil(totalRows / rowsPerPage);
        var paginationHtml = '';

        // Добавляем кнопку "Предыдущая"
        paginationHtml += `<button class="page-btn prev-btn" ${currentPage === 1 ? 'disabled' : ''}>&laquo; Prev</button>`;

        // Добавляем номера страниц
        var startPage = Math.max(1, currentPage - 2);
        var endPage = Math.min(totalPages, startPage + 4);

        if (startPage > 1) {
            paginationHtml += `<button class="page-btn" data-page="1">1</button>`;
            if (startPage > 2) {
                paginationHtml += `<span class="page-ellipsis">...</span>`;
            }
        }

        for (var i = startPage; i <= endPage; i++) {
            paginationHtml += `<button class="page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHtml += `<span class="page-ellipsis">...</span>`;
            }
            paginationHtml += `<button class="page-btn" data-page="${totalPages}">${totalPages}</button>`;
        }

        // Добавляем кнопку "Следующая"
        paginationHtml += `<button class="page-btn next-btn" ${currentPage === totalPages ? 'disabled' : ''}>Next &raquo;</button>`;

        $('#pagination-controls').html(paginationHtml);

        $('.page-btn').on('click', function() {
            if ($(this).hasClass('prev-btn')) {
                currentPage = Math.max(1, currentPage - 1);
            } else if ($(this).hasClass('next-btn')) {
                currentPage = Math.min(totalPages, currentPage + 1);
            } else {
                currentPage = parseInt($(this).data('page'));
            }
            applyFilterAndSort();
        });
    }

    function updateGraph(data) {
        // Find min and max dates
        var dates = [];
        for (var sourceMedium in data) {
            dates = dates.concat(Object.keys(data[sourceMedium]));
        }
        var minDate = new Date(Math.min(...dates.map(date => new Date(date))));
        var maxDate = new Date(Math.max(...dates.map(date => new Date(date))));

        // Fill missing dates with zeros
        for (var sourceMedium in data) {
            var currentData = data[sourceMedium];
            var filledData = {};
            var currentDate = new Date(minDate);
            while (currentDate <= maxDate) {
                var dateString = currentDate.toISOString().split('T')[0];
                if (!currentData[dateString]) {
                    filledData[dateString] = { clicks: 0, sessions: 0 };
                } else {
                    filledData[dateString] = currentData[dateString];
                }
                currentDate.setDate(currentDate.getDate() + 1);
            }
            data[sourceMedium] = filledData;
        }

        chartData = data;
        renderGraph();
    }

    function renderGraph() {
        if (chart) {
            chart.destroy();
        }

        var ctx = document.getElementById('graph-container').getContext('2d');
        var datasets = [];
        var colorIndex = 0;
        var colors = ['rgb(75, 192, 192)', 'rgb(255, 99, 132)', 'rgb(255, 205, 86)', 'rgb(54, 162, 235)', 'rgb(153, 102, 255)'];

        for (var sourceMedium in chartData) {
            var color = colors[colorIndex % colors.length];
            if (currentFilter === 'all' || currentFilter === 'clicks') {
                datasets.push({
                    label: sourceMedium + ' (Clicks)',
                    data: Object.entries(chartData[sourceMedium]).map(([date, values]) => ({x: date, y: values.clicks})),
                    borderColor: color,
                    backgroundColor: color,
                    fill: false,
                    tension: 0.1
                });
            }
            if (currentFilter === 'all' || currentFilter === 'ga4') {
                datasets.push({
                    label: sourceMedium + ' (Sessions)',
                    data: Object.entries(chartData[sourceMedium]).map(([date, values]) => ({x: date, y: values.sessions})),
                    borderColor: color,
                    backgroundColor: color,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.1
                });
            }
            colorIndex++;
        }

        chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        }
                    },
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    function addFilterHandlers() {
        $('#filter-clicks, #filter-ga4, #filter-all').on('click', function() {
            currentFilter = $(this).attr('id').replace('filter-', '');
            currentPage = 1;
            applyDefaultSort();
            applyFilterAndSort();
            renderGraph();
        });
    }

    function addSortHandlers() {
        $('.sortable').on('click', function() {
            var column = $(this).data('sort');
            var order = column === sortOrder.column && sortOrder.order === 'desc' ? 'asc' : 'desc';
            sortOrder = { column: column, order: order };
            currentPage = 1;
            applyFilterAndSort();
        });
    }

    // Вызываем applyDefaultSort при инициализации
    applyDefaultSort();
});