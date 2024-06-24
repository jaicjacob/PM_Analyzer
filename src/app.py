import os
import httpx
import asyncio
import logging
import datetime
from typing import Optional
from pydantic import ValidationError
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException

from src.html import HTMLResponse, generate_html
from src.data import DeviceHistory, DeviceRecord, DailyMetrics

DEVICE_ID = str(os.getenv("DEVICE_ID", default="08BEAC0AB2DE"))


class PM_Analyzer:
    def __init__(self):
        self.app = FastAPI(lifespan=self.lifespan)
        self.data_store: DeviceHistory = {}
        self.log = logging.getLogger("uvicorn")

        @self.app.get("/")
        async def read_root() -> HTMLResponse:
            return generate_html(self.data_store)

        @self.app.get("/data", response_model=DeviceHistory)
        async def get_data():
            return self.data_store

        @self.app.get("/data/danger", response_model=list[datetime.datetime])
        async def get_danger_thresholds():
            return self.data_store.danger_threshold_instances

        @self.app.get(
            "/data/metrics/", response_model=dict[datetime.date, DailyMetrics]
        )
        async def get_metrics(date: Optional[datetime.date] = Query(None)):
            if date:
                if date in self.data_store.daily_metrics.keys():
                    return {date: self.data_store.daily_metrics[date]}
                else:
                    raise HTTPException(
                        status_code=404, detail="Data not found in the specified date!"
                    )
            else:
                return self.data_store.daily_metrics

    async def fetch_data_onStartup(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://pm25.lass-net.org/API-1.0.0/device/{DEVICE_ID}/history/?format=JSON"
            )
            try:
                data = response.json()
                self.process_init_response(data)
            except (ValueError, ValidationError) as e:
                print(f"Failed to update data_store: {e}")

    async def fetch_data_periodically(self):
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"https://pm25.lass-net.org/API-1.0.0/device/{DEVICE_ID}/latest/?format=JSON"
                    )
                    self.process_response(response.json())
                except (ValueError, ValidationError) as e:
                    print(f"Failed to update data_store: {e}")
                except Exception as e:
                    self.log.error(str(e))
                finally:
                    await asyncio.sleep(1)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        try:
            await self.fetch_data_onStartup()
            task = asyncio.create_task(self.fetch_data_periodically())
            yield
            task.cancel()
            await task
        except asyncio.exceptions.CancelledError:
            pass

    def process_init_response(self, response_data: dict) -> dict:
        self.data_store = DeviceHistory(
            **{
                "source": response_data.get("source"),
                "device_id": response_data.get("device_id"),
                "version": response_data.get("version"),
                "num_of_records": 0,
                "feeds": {"AirBox": {}},
                "danger_threshold_instances": [],
                "daily_metrics": {},
            }
        )

        for feed in response_data["feeds"]:
            for project in feed.keys():
                for entry in feed[project]:
                    for key in entry.keys():
                        record = DeviceRecord(**entry[key])
                        self.data_store.add_record(project, key, record)

    def process_response(self, response_data: dict) -> dict:
        for feed in response_data["feeds"]:
            for project in feed.keys():
                record = DeviceRecord(
                    **{
                        "app": project,
                        "device_id": feed[project]["device_id"],
                        "s_t0": feed[project]["s_t0"],
                        "s_h0": feed[project]["s_h0"],
                        "s_d0": feed[project]["s_d0"],
                        "gps_lat": feed[project]["gps_lat"],
                        "gps_lon": feed[project]["gps_lon"],
                        "timestamp": feed[project]["timestamp"],
                    }
                )

                response = self.data_store.add_record(
                    project, feed[project]["timestamp"], record
                )
                if response:
                    self.log.info(
                        f"Added record with timestamp {feed[project]['timestamp']}"
                    )
                else:
                    self.log.info(
                        f"Record with timestamp {feed[project]['timestamp']} already exists"
                    )


def main():
    import uvicorn

    try:
        service = PM_Analyzer()
        uvicorn.run(service.app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
