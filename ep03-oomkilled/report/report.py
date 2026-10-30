"""The monthly report: reads every visit, then adds up the fees."""
import time


def read_visits():
    """Stands in for a database. It hands back one visit at a time."""
    for number in range(1, 3_000_001):
        yield f"visit-{number:07d},patient-{number:07d},cardiology,{number % 500}"
        if number % 100_000 == 0:
            print(f"read {number:,} visits", flush=True)
            time.sleep(1)  # a real database takes time too


visits = list(read_visits())
total = sum(int(visit.split(",")[3]) for visit in visits)
print(f"report done: {len(visits):,} visits, total fees {total:,}", flush=True)
