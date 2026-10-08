"""Pretend to be the ESP32: replay one child from the dataset into the API.

  python simulate_device.py --device-key <KEY> --subject QU_C2 --speed 20

--speed 20  = send 20 readings per second (1 = real time).
Get the device key from:  flask --app app create-demo   (or POST /api/children)
"""
import argparse
import time
from pathlib import Path

import pandas as pd
import requests

CSV = Path(__file__).resolve().parent / "data" / "final_cleand_data.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:5000")
    ap.add_argument("--device-key", required=True)
    ap.add_argument("--subject", default="QU_C2")
    ap.add_argument("--speed", type=float, default=20)
    ap.add_argument("--limit", type=int, default=0, help="stop after N readings (0 = all)")
    a = ap.parse_args()

    df = pd.read_csv(CSV)
    df = df[(df.subject_id == a.subject) & df.hr.notna()].sort_values("time_s")
    if a.limit:
        df = df.head(a.limit)
    headers = {"X-Device-Key": a.device_key}
    for i, r in enumerate(df.itertuples(), start=1):
        body = {"heart_rate": r.hr, "temperature": r.temp, "gsr": r.eda,
                "x": r.x, "y": r.y, "z": r.z}
        resp = requests.post(f"{a.url}/api/device/data", json=body, headers=headers, timeout=5)
        if resp.status_code != 201:
            print("error:", resp.status_code, resp.text)
            break
        if i % 50 == 0:
            print(i, resp.json())
        time.sleep(1 / a.speed)


if __name__ == "__main__":
    main()
