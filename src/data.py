import os
from typing import Optional
from redis_om import HashModel, Field
from redis.exceptions import ConnectionError
from datetime import datetime, timezone, date

REDIS = True
PM_DANGER_THRESHOLD = float(os.getenv("PM_DANGER_THRESHOLD", default=30.0))


class DeviceRecord(HashModel):
    app: Optional[str] = Field(None)
    device_id: Optional[str] = Field(None)
    s_t0: Optional[float] = Field(None)
    s_h0: Optional[float] = Field(None)
    s_d0: Optional[float] = Field(None)
    gps_lat: Optional[float] = Field(None)
    gps_lon: Optional[float] = Field(None)
    timestamp: Optional[datetime] = Field(None)


class DailyMetrics(HashModel):
    max: Optional[float]
    min: Optional[float]
    avg: Optional[float]
    count: Optional[int]


class DeviceHistory(HashModel):
    source: Optional[str] = Field(None)
    device_id: Optional[str] = Field(None)
    version: Optional[str] = Field(None)
    num_of_records: Optional[int] = Field(None)
    feeds: Optional[dict[str, dict[datetime, DeviceRecord]]]
    danger_threshold_instances: Optional[list]
    daily_metrics: Optional[dict[date, DailyMetrics]]

    def __init__(self, **data):
        super().__init__(**data)
        try:
            for record in DeviceRecord.all_pks():
                record_data = DeviceRecord.get(record)
                if record_data.app in self.feeds.keys():
                    self.feeds[record_data.app][record_data.timestamp] = record_data
                else:
                    self.feeds[record_data.app] = {record_data.timestamp: record_data}

                self.__check_danger_threshold(record_data)
                self.__check_daily_average(record_data)
                self.num_of_records += 1
        except ConnectionError:
            global REDIS
            REDIS = False
            pass

    def add_record(self, project: str, timestamp: str, record: DeviceRecord):
        global REDIS
        datetime_object_from_string = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        datetime_object_from_string = datetime_object_from_string.replace(
            tzinfo=timezone.utc
        )

        if project not in self.feeds:
            self.feeds[project] = {}

        if datetime_object_from_string not in self.feeds[project]:
            self.__check_danger_threshold(record)
            self.__check_daily_average(record)
            self.feeds[project][datetime_object_from_string] = record

            if REDIS:
                record.save()

            self.version = timestamp
            self.num_of_records += 1
            return True
        return False

    def __check_danger_threshold(self, record: DeviceRecord):
        if float(record.s_d0) > PM_DANGER_THRESHOLD:
            self.danger_threshold_instances.append(record.timestamp)

    def __check_daily_average(self, record: DeviceRecord):
        date = record.timestamp.date()
        if date in self.daily_metrics.keys():
            # Recalculate average
            total_sum_old_values = (
                self.daily_metrics[date].avg * self.daily_metrics[date].count
            )
            total_sum_new_values = total_sum_old_values + record.s_d0
            self.daily_metrics[date].count += 1

            self.daily_metrics[date].avg = round(
                total_sum_new_values / self.daily_metrics[date].count, 1
            )

            # Recalculate max value
            if self.daily_metrics[date].max < record.s_d0:
                self.daily_metrics[date].max = record.s_d0

            # Recalculate min value
            if self.daily_metrics[date].min > record.s_d0:
                self.daily_metrics[date].min = record.s_d0
        else:
            metrics = DailyMetrics(
                **{
                    "max": record.s_d0,
                    "min": record.s_d0,
                    "avg": record.s_d0,
                    "count": 1,
                }
            )

            self.daily_metrics[date] = metrics
