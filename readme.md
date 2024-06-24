# PM Analyzer

PM Analyzer is an application designed to fetch and analyze air quality data from the PM25 LASS network. This application utilizes FastAPI to provide a web interface and API endpoints for accessing the data. The application continuously updates the data by fetching it periodically from the LASS network.

## Features

- Fetches initial air quality data on startup.
- Periodically updates data from the LASS network.
- Provides API endpoints to access the data and derived metrics.
- Logs data fetches and updates.

## Installation

**1. Clone the repository:**

```bash
git clone [<repository-url>](https://github.com/jaicjacob/PM_Analyzer.git)
cd pm_analyzer

```

**2. Install Python & Poetry:**

```bash
curl -sSL https://install.python-poetry.org | python3 - |
pip install poetry

```

**3. Install dependencies:**

```bash
poetry install
```

Usage
Run the application:

```bash
poetry run service
# Runs the application by default on http://localhost:8000
```

**3. Access the API endpoints:**

**_Root Endpoint:_** Returns the HTML representation of the data store.

```bash
GET localhost:8000/
```

**_Get Data Endpoint:_** Returns the entire data store and visualizes the current data using a simple HTML webpage for easy visualization.

```bash
GET localhost:8000/data
```

**_Get Danger Thresholds Endpoint:_** Returns instances where the danger threshold was exceeded.

```bash
GET localhost:8000/data/danger
```

**_Get Metrics Endpoint:_** Returns daily metrics. Optionally, specify a date to filter the metrics.

```bash
GET localhost:8000/data/metrics/?date=<YYYY-MM-DD>
```

**4. Code Overview:**

**Class: PM_Analyzer**
The main class of the application. It sets up the FastAPI application and defines the endpoints.

**init**(self)
Initializes the FastAPI app and sets up the endpoints. Initializes the data store and logger.

**fetch_data_onStartup**(self)
Fetches initial data from the LASS network on application startup and processes the data.

**fetch_data_periodically**(self)
Periodically fetches the latest data from the LASS network and processes the data.

**lifespan**(self, app: FastAPI)
Manages the lifespan of the FastAPI app, ensuring that data fetching starts on startup and stops on shutdown.

**process_init_response**(self, response_data: dict)
Processes the initial response data from the LASS network, updating the data store.

**process_response**(self, response_data: dict)
Processes periodic response data from the LASS network, updating the data store.

**5. Data Models**

**_DeviceHistory_**
Represents the history of device records, including source, device ID, version, number of records, feeds, danger threshold instances, and daily metrics.

**_DeviceRecord_**
Represents a single record from a device, including device ID, sensor readings, GPS coordinates, and timestamp.

**_Logging_**
The application uses the uvicorn logger to log information about data fetches and updates.

**6. Persistant Storage**

The persistant storage solution can be tailor made to suit the application by modifying the data classes however for this application REDIS used.

```bash
set REDIS_OM_URL=localhost:6379
```

The above environment can be overwritten by the persistant storage solution or else can be made to work by running a redis instance using docker. In case it's not available the exception is handled by the application to cache the data local to the environment.

**7. Configuration:**

```bash
set PM_DANGER_THRESHOLD=30 #Default PM Danger threshold
set DEVICE_ID=08BEAC0AB2DE #Default device ID for PM2.5 data
```
