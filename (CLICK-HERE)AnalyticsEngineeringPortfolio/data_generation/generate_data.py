"""
Netflix Security AE Portfolio — Synthetic Data Generator

Generates ~50k login events, ~150k request logs, and ~3k device records
with injected security anomalies: ATO, credential stuffing, and DDoS patterns.
Run once from the project root with the ae-env activated.
"""
import duckdb
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd

DB_PATH = (
    "/Users/adamniebylski/Desktop/codecademy-git-test/"
    "Showcase_Projects/(CLICK-HERE)AnalyticsEngineeringPortfolio/"
    "netflix_security.duckdb"
)

random.seed(42)

# ── Date window ──────────────────────────────────────────────────────────────
END_TS   = datetime(2026, 5, 1, 23, 59, 59)
START_TS = END_TS - timedelta(days=30)

# ── Attack infrastructure ────────────────────────────────────────────────────
N_NORMAL_USERS  = 480
N_ATO_VICTIMS   = 15   # users 1–15 will have ATO patterns injected
N_TOTAL_USERS   = N_NORMAL_USERS + N_ATO_VICTIMS

CREDENTIAL_STUFFING_IPS = [
    "45.33.32.156", "45.33.32.157", "45.33.32.158",
    "45.33.32.159", "45.33.32.160",
]
DDOS_BOT_IPS = ["198.51.100.10", "198.51.100.11", "203.0.113.42"]

# ── Reference data ───────────────────────────────────────────────────────────
COUNTRIES        = ["US", "GB", "DE", "FR", "CA", "AU", "JP", "BR", "IN", "MX"]
ATTACK_COUNTRIES = ["RU", "CN", "NG", "RO", "IR"]
DEVICE_TYPES     = ["mobile", "desktop", "tablet", "smart_tv"]
OS_BY_DEVICE     = {
    "mobile":   ["iOS", "Android"],
    "desktop":  ["Windows", "macOS", "Linux"],
    "tablet":   ["iOS", "Android"],
    "smart_tv": ["tvOS", "Tizen", "Roku OS"],
}
BROWSER_BY_OS = {
    "iOS":      ["Safari", "Netflix App", "Chrome"],
    "Android":  ["Chrome", "Netflix App", "Firefox"],
    "Windows":  ["Chrome", "Edge", "Firefox"],
    "macOS":    ["Safari", "Chrome", "Firefox"],
    "Linux":    ["Firefox", "Chrome"],
    "tvOS":     ["Netflix App"],
    "Tizen":    ["Netflix App"],
    "Roku OS":  ["Netflix App"],
}
USER_AGENTS = {
    ("iOS", "Safari"):       "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    ("iOS", "Chrome"):       "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) CriOS/120.0.6099.119",
    ("iOS", "Netflix App"):  "Netflix/8.0 (iOS; iPhone)",
    ("Android", "Chrome"):   "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0",
    ("Android", "Firefox"):  "Mozilla/5.0 (Android 14; Mobile) Gecko/122.0 Firefox/122.0",
    ("Android", "Netflix App"): "Netflix/8.0 (Android; Pixel 7)",
    ("Windows", "Chrome"):   "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36 Chrome/121.0",
    ("Windows", "Edge"):     "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36 Edg/121.0",
    ("Windows", "Firefox"):  "Mozilla/5.0 (Windows NT 10.0; Win64; rv:122.0) Firefox/122.0",
    ("macOS", "Safari"):     "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15",
    ("macOS", "Chrome"):     "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Chrome/121.0",
    ("macOS", "Firefox"):    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:122.0) Firefox/122.0",
    ("Linux", "Firefox"):    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Firefox/122.0",
    ("Linux", "Chrome"):     "Mozilla/5.0 (X11; Linux x86_64) Chrome/121.0",
    ("tvOS", "Netflix App"): "Netflix/8.0 (Apple TV; tvOS 17.0)",
    ("Tizen", "Netflix App"):"Netflix/8.0 (Samsung Smart TV; Tizen 7.0)",
    ("Roku OS", "Netflix App"): "Netflix/8.0 (Roku; RokuOS 12.0)",
}
ENDPOINTS = [
    "/api/login", "/api/profiles", "/api/browse", "/api/play",
    "/api/search", "/api/account", "/api/billing", "/api/logout",
    "/health", "/api/recommendations",
]


# ── Helpers ──────────────────────────────────────────────────────────────────
def rand_ts(start=START_TS, end=END_TS):
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta))

def rand_ip():
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def ua(os_name, browser):
    return USER_AGENTS.get((os_name, browser), "Mozilla/5.0 (Unknown)")


# ── Build user profiles ───────────────────────────────────────────────────────
profiles = {}
for uid in range(1, N_TOTAL_USERS + 1):
    d_type    = random.choice(DEVICE_TYPES)
    os_name   = random.choice(OS_BY_DEVICE[d_type])
    browser   = random.choice(BROWSER_BY_OS[os_name])
    profiles[uid] = {
        "home_ips":       [rand_ip() for _ in range(random.randint(1, 3))],
        "primary_country": random.choice(COUNTRIES),
        "is_ato_victim":  uid <= N_ATO_VICTIMS,
        "devices": []   # list of (device_id, device_type, os, browser, is_trusted)
    }

# ── Generate devices ──────────────────────────────────────────────────────────
device_rows = []
for uid, p in profiles.items():
    n_devices = random.randint(1, 2) if p["is_ato_victim"] else random.randint(1, 3)
    for i in range(n_devices):
        d_type   = random.choice(DEVICE_TYPES)
        os_name  = random.choice(OS_BY_DEVICE[d_type])
        browser  = random.choice(BROWSER_BY_OS[os_name])
        did      = str(uuid.uuid4())
        trusted  = (i == 0)
        first_ts = rand_ts(START_TS, END_TS - timedelta(days=15))
        last_ts  = rand_ts(first_ts, END_TS)
        p["devices"].append((did, d_type, os_name, browser, trusted))
        device_rows.append({
            "device_id":    did,
            "user_id":      uid,
            "device_type":  d_type,
            "os":           os_name,
            "browser":      browser,
            "first_seen_at": first_ts,
            "last_seen_at":  last_ts,
            "is_trusted":    trusted,
        })

# ── Generate login events ─────────────────────────────────────────────────────
login_rows = []

for uid, p in profiles.items():
    if p["is_ato_victim"]:
        # High failure rate, many IPs, then a successful takeover at the end
        attack_ips = [rand_ip() for _ in range(random.randint(5, 15))]
        all_ips    = p["home_ips"] + attack_ips
        n_events   = random.randint(80, 200)

        for _ in range(n_events - 1):
            ip         = random.choice(all_ips)
            did, _, os_n, br, _ = random.choice(p["devices"])
            country    = random.choice(ATTACK_COUNTRIES + [p["primary_country"]] * 2)
            ts         = rand_ts(START_TS, END_TS - timedelta(hours=2))
            success    = random.random() < 0.12

            login_rows.append({
                "event_id":        str(uuid.uuid4()),
                "user_id":         uid,
                "ip_address":      ip,
                "device_id":       did,
                "event_timestamp": ts,
                "success":         success,
                "country_code":    country,
                "user_agent":      ua(os_n, br),
            })

        # Final successful takeover from a brand-new device
        takeover_did  = str(uuid.uuid4())
        takeover_os   = random.choice(["Windows", "Linux"])
        takeover_br   = random.choice(BROWSER_BY_OS[takeover_os])
        takeover_ts   = rand_ts(END_TS - timedelta(hours=2), END_TS)

        login_rows.append({
            "event_id":        str(uuid.uuid4()),
            "user_id":         uid,
            "ip_address":      rand_ip(),
            "device_id":       takeover_did,
            "event_timestamp": takeover_ts,
            "success":         True,
            "country_code":    random.choice(ATTACK_COUNTRIES),
            "user_agent":      ua(takeover_os, takeover_br),
        })
        device_rows.append({
            "device_id":    takeover_did,
            "user_id":      uid,
            "device_type":  "desktop",
            "os":           takeover_os,
            "browser":      takeover_br,
            "first_seen_at": takeover_ts,
            "last_seen_at":  takeover_ts,
            "is_trusted":    False,
        })

    else:
        # Normal user: low failure rate, consistent home IPs
        for _ in range(random.randint(5, 25)):
            ip         = random.choice(p["home_ips"])
            did, _, os_n, br, _ = random.choice(p["devices"])
            ts         = rand_ts()
            success    = random.random() < 0.92

            login_rows.append({
                "event_id":        str(uuid.uuid4()),
                "user_id":         uid,
                "ip_address":      ip,
                "device_id":       did,
                "event_timestamp": ts,
                "success":         success,
                "country_code":    p["primary_country"],
                "user_agent":      ua(os_n, br),
            })

# Credential stuffing: each CS IP targets many accounts
all_uids = list(range(1, N_TOTAL_USERS + 1))
for cs_ip in CREDENTIAL_STUFFING_IPS:
    targets = random.sample(all_uids, random.randint(70, 130))
    for target_uid in targets:
        for _ in range(random.randint(1, 5)):
            ts = rand_ts()
            login_rows.append({
                "event_id":        str(uuid.uuid4()),
                "user_id":         target_uid,
                "ip_address":      cs_ip,
                "device_id":       str(uuid.uuid4()),  # headless browser — new device each hit
                "event_timestamp": ts,
                "success":         random.random() < 0.04,
                "country_code":    random.choice(ATTACK_COUNTRIES),
                "user_agent":      "python-requests/2.28.0",
            })

# ── Generate request logs ─────────────────────────────────────────────────────
request_rows = []
normal_ips = [ip for p in profiles.values() for ip in p["home_ips"]]

# Normal traffic
for _ in range(120_000):
    ts       = rand_ts()
    endpoint = random.choice(ENDPOINTS)
    method   = "POST" if endpoint in ["/api/login", "/api/billing"] and random.random() < 0.5 else "GET"
    status   = random.choices([200, 304, 404, 429, 500], weights=[80, 10, 5, 3, 2])[0]
    resp_ms  = max(10, min(5000, int(random.gauss(200, 80))))
    request_rows.append({
        "request_id":        str(uuid.uuid4()),
        "ip_address":        random.choice(normal_ips),
        "request_timestamp": ts,
        "endpoint":          endpoint,
        "http_method":       method,
        "status_code":       status,
        "response_time_ms":  resp_ms,
        "user_agent":        "Mozilla/5.0",
    })

# Credential stuffing IPs also generate elevated request volume
for cs_ip in CREDENTIAL_STUFFING_IPS:
    for _ in range(random.randint(800, 2000)):
        ts = rand_ts()
        request_rows.append({
            "request_id":        str(uuid.uuid4()),
            "ip_address":        cs_ip,
            "request_timestamp": ts,
            "endpoint":          "/api/login",
            "http_method":       "POST",
            "status_code":       random.choice([200, 401, 403]),
            "response_time_ms":  random.randint(50, 300),
            "user_agent":        "python-requests/2.28.0",
        })

# DDoS bots: massive volume, few endpoints
for ddos_ip in DDOS_BOT_IPS:
    for _ in range(random.randint(10_000, 20_000)):
        ts = rand_ts()
        request_rows.append({
            "request_id":        str(uuid.uuid4()),
            "ip_address":        ddos_ip,
            "request_timestamp": ts,
            "endpoint":          random.choice(["/api/browse", "/api/play", "/api/search"]),
            "http_method":       "GET",
            "status_code":       random.choices([200, 429, 503], weights=[60, 30, 10])[0],
            "response_time_ms":  random.randint(5, 100),
            "user_agent":        "Mozilla/5.0 (compatible; Bot/1.0)",
        })

# ── Write to DuckDB ───────────────────────────────────────────────────────────
print(f"\nConnecting to DuckDB at:\n  {DB_PATH}\n")
conn = duckdb.connect(DB_PATH)

devices_df  = pd.DataFrame(device_rows)
logins_df   = pd.DataFrame(login_rows)
requests_df = pd.DataFrame(request_rows)

print(f"Writing raw_devices        ({len(devices_df):>8,} rows)...")
conn.register("devices_df",  devices_df)
conn.execute("CREATE OR REPLACE TABLE raw_devices AS SELECT * FROM devices_df")

print(f"Writing raw_login_events   ({len(logins_df):>8,} rows)...")
conn.register("logins_df",   logins_df)
conn.execute("CREATE OR REPLACE TABLE raw_login_events AS SELECT * FROM logins_df")

print(f"Writing raw_request_logs   ({len(requests_df):>8,} rows)...")
conn.register("requests_df", requests_df)
conn.execute("CREATE OR REPLACE TABLE raw_request_logs AS SELECT * FROM requests_df")

conn.close()
print("\nDone! Run `dbt run` from the netflix_security/ directory next.")
