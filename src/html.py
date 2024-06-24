from datetime import datetime
from fastapi.responses import HTMLResponse
from src.data import DeviceHistory


def get_todays_data(data: DeviceHistory):
    today_date = datetime.today().strftime("%Y-%m-%d")

    timestamps = []
    temperatures = []
    humidities = []
    dust_levels = []

    for feed_type, records in data.feeds.items():
        for record in records.values():
            record_time = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if today_date in record_time:
                timestamps.append(record_time)
                temperatures.append(record.s_t0)
                humidities.append(record.s_h0)
                dust_levels.append(record.s_d0)

    recent_data = {
        "timestamps": timestamps,
        "temperatures": temperatures,
        "humidities": humidities,
        "dust_levels": dust_levels,
    }

    return recent_data


def generate_html(data: DeviceHistory) -> HTMLResponse:
    recent_data = get_todays_data(data)

    feeds_html = ""
    for feed_type, records in data.feeds.items():
        feeds_html += f"<h3>{feed_type}</h3>"
        feeds_html += f"""
        <table class="data-table">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Device ID</th>
                    <th>Temperature (s_t0)</th>
                    <th>Humidity (s_h0)</th>
                    <th>Dust (s_d0)</th>
                    <th>Latitude</th>
                    <th>Longitude</th>
                </tr>
            </thead>
            <tbody>
        """
        for record in records.values():
            feeds_html += f"""
            <tr>
                <td>{record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                <td>{record.device_id}</td>
                <td>{record.s_t0}</td>
                <td>{record.s_h0}</td>
                <td>{record.s_d0}</td>
                <td>{record.gps_lat}</td>
                <td>{record.gps_lon}</td>
            </tr>
            """
        feeds_html += """
            </tbody>
        </table>
        """

    danger_counts = {}
    for instance in data.danger_threshold_instances:
        date = instance.strftime("%Y-%m-%d")
        if date in danger_counts:
            danger_counts[date] += 1
        else:
            danger_counts[date] = 1

    danger_thresholds = {
        "dates": list(danger_counts.keys()),
        "counts": list(danger_counts.values()),
    }

    metrics_html = ""
    for metric_date, metrics in data.daily_metrics.items():
        metrics_html += f"""
        <tr>
            <td>{metric_date}</td>
            <td>{metrics.max}</td>
            <td>{metrics.min}</td>
            <td>{metrics.avg}</td>
            <td>{metrics.count}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PM Analyzer</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #121212;
                color: #e0e0e0;
            }}
            h1, h2, h3 {{
                color: #ffffff;
            }}
            .section {{
                margin-bottom: 40px;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            .data-table th, .data-table td {{
                border: 1px solid #444;
                padding: 10px;
                text-align: left;
            }}
            .data-table th {{
                background-color: #333;
                color: #ffffff;
            }}
            .data-table tr:nth-child(even) {{
                background-color: #2a2a2a;
            }}
            .danger-list, .metrics-table {{
                margin-top: 20px;
            }}
            .danger-list li {{
                margin-bottom: 5px;
            }}
            .tab {{
                display: none;
            }}
            .tab.active {{
                display: block;
            }}
            .tab-buttons {{
                display: flex;
                border-bottom: 1px solid #444;
                margin-bottom: 20px;
            }}
            .tab-buttons button {{
                background-color: #333;
                border: none;
                padding: 10px 20px;
                cursor: pointer;
                outline: none;
                color: #ffffff;
            }}
            .tab-buttons button.active {{
                background-color: #555;
            }}
            .chart-container {{
                width: 100%;
                height: 80vh;
                margin-top: 20px;
            }}
            .chart-container canvas {{
                width: 100% !important;
                height: 100% !important;
            }}
            .source-info {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
            }}
            .source-info .card {{
                background-color: #1e1e1e;
                padding: 5px 10px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
                flex: 1;
                min-width: 150px;
                display: flex;
                align-items: center;
            }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            function showTab(tabId) {{
                var tabs = document.getElementsByClassName('tab');
                var buttons = document.getElementsByClassName('tab-button');
                for (var i = 0; i < tabs.length; i++) {{
                    tabs[i].classList.remove('active');
                    buttons[i].classList.remove('active');
                }}
                document.getElementById(tabId).classList.add('active');
                document.querySelector('[data-tab="' + tabId + '"]').classList.add('active');
            }}

            document.addEventListener('DOMContentLoaded', (event) => {{
                var ctx = document.getElementById('dataChart').getContext('2d');
                var dataChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: {recent_data['timestamps']}, 
                        datasets: [{{
                            label: 'Temperature',
                            data: {recent_data['temperatures']}, 
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Humidity',
                            data: {recent_data['humidities']}, 
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Dust',
                            data: {recent_data['dust_levels']}, 
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            x: {{
                                display: true,
                                title: {{
                                    display: true,
                                    text: 'Date'
                                }}
                            }},
                            y: {{
                                display: true,
                                title: {{
                                    display: true,
                                    text: 'Values'
                                }}
                            }}
                        }}
                    }}
                }});

                var ctxDanger = document.getElementById('dangerChart').getContext('2d');
                var dangerChart = new Chart(ctxDanger, {{
                    type: 'bar',
                    data: {{
                        labels: {danger_thresholds['dates']},
                        datasets: [{{
                            label: 'Danger Threshold Instances',
                            data: {danger_thresholds['counts']},
                            backgroundColor: 'rgba(255, 99, 132, 0.5)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            x: {{
                                display: true,
                                title: {{
                                    display: true,
                                    text: 'Time'
                                }}
                            }},
                            y: {{
                                display: true,
                                title: {{
                                    display: true,
                                    text: 'Count'
                                }}
                            }}
                        }}
                    }}
                }});
            }});
        </script>
    </head>
    <body>
        <h1>PM 2.5 Report</h1>
        
        <div class="tab-buttons">
            <button class="tab-button active" data-tab="sourceInfo" onclick="showTab('sourceInfo')">Overview</button>
            <button class="tab-button" data-tab="dailyMetrics" onclick="showTab('dailyMetrics')">Daily Metrics</button>
            <button class="tab-button" data-tab="dangerInstances" onclick="showTab('dangerInstances')">Danger Threshold Instances</button>
            <button class="tab-button" data-tab="feedData" onclick="showTab('feedData')">Feed Data</button>
        </div>

        <div id="sourceInfo" class="tab active">
            <div class="section">
                <div class="source-info">
                    <div class="card">
                        <p><strong>Source:</strong> {data.source}</p>
                    </div>
                    <div class="card">
                        <p><strong>Device ID:</strong> {data.device_id}</p>
                    </div>
                    <div class="card">
                        <p><strong>Last Updated:</strong> {data.version}</p>
                    </div>
                    <div class="card">
                        <p><strong>Number of Records:</strong> {data.num_of_records}</p>
                    </div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="dataChart"></canvas>
            </div>
        </div>

        <div id="feedData" class="tab">
            <div class="section">
                {feeds_html}
            </div>
        </div>

        <div id="dangerInstances" class="tab">
            <div class="chart-container">
                <canvas id="dangerChart"></canvas>
            </div>
        </div>

        <div id="dailyMetrics" class="tab">
            <div class="section">
                <table class="data-table metrics-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Max</th>
                            <th>Min</th>
                            <th>Avg</th>
                            <th>Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        {metrics_html}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
