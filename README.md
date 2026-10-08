# CalmBand backend

Flask + SQLAlchemy (SQLite) + AI model (scikit-learn).

## Run

```bash
pip install -r requirements.txt
python -m ml.train                      # trains ml/model.joblib from data/final_cleand_data.csv
flask --app app init-db
flask --app app create-demo             # prints login + child id + device key
flask --app app run --host 0.0.0.0 --port 5000 --debug
python simulate_device.py --device-key <KEY> --subject QU_C2 --speed 20
```

## Tests

```bash
python tests/test_api.py          # end-to-end: auth, device data, alerts, feedback, ownership
```

`tests/make_fake_csv.py` writes a **synthetic** CSV only to smoke-test the pipeline when you do not
have the real one. A model trained on it means nothing; retrain on the real CSV before any real use.

## Project layout

| File | Role |
|---|---|
| `app.py` | creates the app, registers routes |
| `config.py` | all settings (DB url, secret, thresholds) |
| `models.py` | the 4 tables |
| `repositories.py` | **database layer** - the only file that queries tables |
| `services/detection.py` | AI decision, rules fallback, smoothing, alert episodes |
| `auth.py` | JWT for parents, device key for the ESP32 |
| `routes/*.py` | HTTP endpoints |
| `ml/features.py`, `ml/train.py` | features (shared by training and live) and training |
| `cli.py` | database commands |

## Where is the data?

SQLite file `instance/calmband.db`, created automatically on first run (empty).
The CSV is **not** loaded into it: the CSV is only for training the model and for
`simulate_device.py`. Real rows appear when the ESP32 (or the simulator) POSTs readings.

## Tables

```
users(id, name, email*, password_hash, created_at)
children(id, name, owner_id -> users, device_key*, created_at)
readings(id, child_id -> children, timestamp, heart_rate, temperature, gsr,
         acc_x, acc_y, acc_z, motion, above_baseline_pct, risk,
         raw_status, status, engine, device_status)
feedback(id, reading_id -> readings, child_id -> children, user_id -> users, correct, timestamp)
```

## Database commands

```bash
flask --app app init-db
flask --app app db-info                       # tables, columns, row counts
flask --app app show-readings --child 1 --limit 20
flask --app app reset-db --yes                # deletes everything
```

Directly with SQLite:

```bash
sqlite3 instance/calmband.db
.tables
.schema readings
SELECT status, COUNT(*) FROM readings WHERE child_id = 1 GROUP BY status;
SELECT id, timestamp, heart_rate, risk, status FROM readings ORDER BY id DESC LIMIT 10;
```

## API

Two kinds of callers:

* **Parent / dashboard**: `Authorization: Bearer <token>` (from register/login)
* **ESP32**: `X-Device-Key: <device_key>` (returned once when the child is created)

### Authentication
| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/auth/register` | `name, email, password(6+)` | `token, user` |
| POST | `/api/auth/login` | `email, password` | `token, user` |
| GET | `/api/auth/me` | - | `user` |

### Dashboard (token required; a parent only sees his own children, otherwise 404)
| Method | Path | Returns |
|---|---|---|
| GET | `/api/children` | children + `baseline_hr` |
| POST | `/api/children` | `{name}` -> child + `device_key` (shown only now) |
| GET | `/api/children/<id>` | `{id, name}` |
| PATCH | `/api/children/<id>` | `{name}` -> renamed child |
| POST | `/api/children/<id>/rotate-key` | new `device_key` (old one stops working at once) |
| DELETE | `/api/children/<id>` | deletes the child with all readings and feedback |
| GET | `/api/children/<id>/current` | latest reading (404 if none) |
| GET | `/api/children/<id>/readings?limit=300` | oldest -> newest, for the chart |
| GET | `/api/children/<id>/alerts` | alert episodes |
| GET | `/api/children/<id>/summary` | totals, calm %, alert count, avg/baseline HR, feedback |
| POST | `/api/children/<id>/feedback` | `{reading_id, correct}` |
| GET | `/api/children/<id>/feedback` | list |

### Device (device key required)
| Method | Path | Body |
|---|---|---|
| POST | `/api/device/data` | `heart_rate, temperature, gsr` (required); `x, y, z` accelerometer in g (needed for AI); `motion` 0..1 and `status` optional |

Response: `{"status":"success","id":..,"state":"calm|early|distress","engine":"ai|rules"}`

Errors always look like `{"status":"error","message":"..."}`.

### Removed / changed from the old version
* `/api/data` (POST/GET), `/api/readings`, `/api/alerts`, `/api/summary`, `/api/live/*` -> replaced by the routes above (child id is now in the path).
* `/api/live/restart` and `/api/live/jump-to-alert` removed (they only made sense for CSV replay).

## AI model

`status` comes from the model when possible (`engine = "ai"`): it needs the accelerometer
values, at least 10 earlier readings and 30 readings for the child's baseline. Otherwise it
falls back to the original rules (`engine = "rules"`). `risk` is the model probability.
`risk >= threshold` -> distress, `>= 0.6 * threshold` -> early. Set `USE_AI=0` to disable.

Units must match the dataset: accelerometer in g, EDA in microsiemens, temperature in deg C, HR in bpm.
