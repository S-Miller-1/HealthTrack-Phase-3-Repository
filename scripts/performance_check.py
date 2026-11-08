"""Repeatable local SQLite retrieval microbenchmark; not a production load test."""

import json
import statistics
import tempfile
import time

from datetime import datetime, timezone, timedelta, date
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Patient, VitalSigns, ActivityData
from app.crud import list_records


def run_benchmark():

    with tempfile.TemporaryDirectory() as tmp:

        database_path = Path(tmp) / "benchmark.sqlite"

        engine = create_engine(
            "sqlite:///" + str(database_path)
        )

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        try:
            Base.metadata.create_all(engine)

            with Session(engine) as db:

                patient = Patient(
                    full_name="Synthetic Example",
                    date_of_birth=date(1979, 1, 1),
                    monitoring_consent=True
                )

                db.add(patient)
                db.flush()

                start_time = datetime(
                    2026, 11, 1, tzinfo=timezone.utc
                )

                db.add_all(
                    VitalSigns(
                        patient_id=patient.id,
                        systolic=120 + i % 6,
                        diastolic=75 + i % 5,
                        pulse=65 + i % 8,
                        measured_at=start_time + timedelta(minutes=i)
                    )
                    for i in range(5000)
                )

                db.add_all(
                    ActivityData(
                        patient_id=patient.id,
                        steps=3000 + i,
                        active_minutes=30,
                        activity_date=date(2020, 1, 1) + timedelta(days=i)
                    )
                    for i in range(500)
                )

                db.commit()

                values = []
                items = []

                for _ in range(200):

                    start = time.perf_counter()

                    items = list_records(
                        db,
                        VitalSigns,
                        patient_id=patient.id,
                        start=start_time + timedelta(minutes=1000),
                        end=start_time + timedelta(minutes=3000),
                        date_field="measured_at",
                        limit=50
                    )

                    elapsed = (
                        time.perf_counter() - start
                    ) * 1000

                    values.append(elapsed)

                output = {
                    "context": "Local SQLite synthetic retrieval microbenchmark",
                    "vital_rows": 5000,
                    "activity_rows": 500,
                    "queries": 200,
                    "page_size": len(items),
                    "median_ms": round(
                        statistics.median(values), 3
                    ),
                    "p95_ms": round(
                        sorted(values)[int(len(values) * 0.95) - 1], 3
                    ),
                    "maximum_ms": round(max(values), 3),
                    "caveat": (
                        "Not HTTP throughput, concurrency, "
                        "or production database load."
                    )
                }

                print(json.dumps(output, indent=2))

                results_path = Path(
                    "docs/performance_results.json"
                )

                results_path.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                results_path.write_text(
                    json.dumps(output, indent=2) + "\n",
                    encoding="utf-8"
                )

        finally:
            # Close pooled SQLite connections before Windows
            # attempts to delete the temporary database.
            engine.dispose()


if __name__ == "__main__":
    run_benchmark()