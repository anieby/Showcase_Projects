"""
Step 1 of the pipeline: generate synthetic Netflix security data.

This creates three raw tables in the DuckDB database:
  - raw_login_events   (~11k rows)
  - raw_request_logs   (~175k rows)
  - raw_devices        (~965 rows)

Attack patterns injected:
  - Account Takeover (ATO): users 1-15 have high failure rates + many IPs
  - Credential Stuffing: 5 specific IPs try hundreds of accounts
  - DDoS: 3 specific IPs send 10k-20k requests each
"""
import duckdb
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd

# ── Where to write the database ───────────────────────────────────────────────
# This path matches what's in ~/.dbt/profiles.yml
DB_PATH = (
    "/Users/adamniebylski/Desktop/codecademy-git-test/"
    "Showcase_Projects/(CLICK-HERE)AnalyticsEngineeringPortfolio/"
    "netflix_security.duckdb"
)

# Seed makes the random data reproducible — same results every run
random.seed(42)

# ── Time window: last 30 days of data ─────────────────────────────────────────
END_TS   = datetime(2026, 5, 1, 23, 59, 59)
START_TS = END_TS - timedelta(days=30)

# ── Attack infrastructure — specific IPs we'll use for attacks ────────────────
N_NORMAL_USERS = 480
N_ATO_VICTIMS  = 15    # users 1-15 will have attack patterns
N_TOTAL_USERS  = N_NORMAL_USERS + N_ATO_VICTIMS

CREDENTIAL_STUFFING_IPS = [
    "45.33.32.156", "45.33.32.157", "45.33.32.158",
    "45.33.32.159", "45.33.32.160",
]
DDOS_BOT_IPS = ["198.51.100.10", "198.51.100.11", "203.0.113.42"]

# ── Reference lists ───────────────────────────────────────────────────────────
COUNTRIES        = ["US", "GB", "DE", "FR", "CA", "AU", "JP", "BR", "IN", "MX"]
ATTACK_COUNTRIES = ["RU", "CN", "NG", "RO", "IR"]

DEVICE_TYPES = ["mobile", "desktop", "tablet", "smart_tv"]
OS_BY_DEVICE = {
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
# Realistic user-agent strings per OS/browser combo
USER_AGENTS = {
    ("iOS",     "Safari"):       "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    ("iOS",     "Chrome"):       "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) CriOS/120.0.6099.119",
    ("iOS",     "Netflix App"):  "Netflix/8.0 (iOS; iPhone)",
    ("Android", "Chrome"):       "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0",
    ("Android", "Firefox"):      "Mozilla/5.0 (Android 14; Mobile) Gecko/122.0 Firefox/122.0",
    ("Android", "Netflix App"):  "Netflix/8.0 (Android; Pixel 7)",
    ("Windows", "Chrome"):       "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36 Chrome/121.0",
    ("Windows", "Edge"):         "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36 Edg/121.0",
    ("Windows", "Firefox"):      "Mozilla/5.0 (Windows NT 10.0; Win64; rv:122.0) Firefox/122.0",
    ("macOS",   "Safari"):       "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15",
    ("macOS",   "Chrome"):       "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Chrome/121.0",
    ("macOS",   "Firefox"):      "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:122.0) Firefox/122.0",
    ("Linux",   "Firefox"):      "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Firefox/122.0",
    ("Linux",   "Chrome"):       "Mozilla/5.0 (X11; Linux x86_64) Chrome/121.0",
    ("tvOS",    "Netflix App"):  "Netflix/8.0 (Apple TV; tvOS 17.0)",
    ("Tizen",   "Netflix App"):  "Netflix/8.0 (Samsung Smart TV; Tizen 7.0)",
    ("Roku OS", "Netflix App"):  "Netflix/8.0 (Roku; RokuOS 12.0)",
}
ENDPOINTS = [
    "/api/login", "/api/profiles", "/api/browse", "/api/play",
    "/api/search", "/api/account", "/api/billing", "/api/logout",
    "/health", "/api/recommendations",
]


# ── Helper functions ──────────────────────────────────────────────────────────
def rand_ts(start=START_TS, end=END_TS):
    """Return a random timestamp between start and end."""
    seconds_range = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, seconds_range))

def rand_ip():
    """Return a random IPv4 address."""
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def get_ua(os_name, browser):
    """Look up a realistic user-agent string."""
    return USER_AGENTS.get((os_name, browser), "Mozilla/5.0 (Unknown)")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE A — Build user profiles
# Each user gets: home IPs, a primary country, and a list of devices.
# ═══════════════════════════════════════════════════════════════════════════════
profiles = {}
for uid in range(1, N_TOTAL_USERS + 1):
    profiles[uid] = {
        "home_ips":        [rand_ip() for _ in range(random.randint(1, 3))],
        "primary_country": random.choice(COUNTRIES),
        "is_ato_victim":   uid <= N_ATO_VICTIMS,
        "devices":         [],   # filled in Phase B
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE B — Generate raw_devices
# Each user gets 1-3 devices. The first device is "trusted".
# ATO victims also get a mysterious new untrusted device added later.
# ═══════════════════════════════════════════════════════════════════════════════
device_rows = []

for uid, p in profiles.items():
    n_devices = random.randint(1, 2) if p["is_ato_victim"] else random.randint(1, 3)

    for i in range(n_devices):
        d_type  = random.choice(DEVICE_TYPES)
        os_name = random.choice(OS_BY_DEVICE[d_type])
        browser = random.choice(BROWSER_BY_OS[os_name])
        did     = str(uuid.uuid4())
        trusted = (i == 0)   # first device per user is trusted
        first_ts = rand_ts(START_TS, END_TS - timedelta(days=15))
        last_ts  = rand_ts(first_ts, END_TS)

        # Save so login events can reference the same device IDs
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


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C — Generate raw_login_events
# Two behaviors: normal users (low failure rate) vs ATO victims (high failure rate)
# Then append credential stuffing events on top.
# ═══════════════════════════════════════════════════════════════════════════════
login_rows = []

for uid, p in profiles.items():

    if p["is_ato_victim"]:
        # ── ATO pattern ──────────────────────────────────────────────────────
        # Many login attempts from many different IPs, mostly failing.
        # At the very end: one success from a brand-new device = the takeover.

        attack_ips = [rand_ip() for _ in range(random.randint(5, 15))]
        all_ips    = p["home_ips"] + attack_ips
        n_events   = random.randint(80, 200)

        # N-1 events: mix of failures and rare successes from attack IPs
        for _ in range(n_events - 1):
            ip      = random.choice(all_ips)
            did, _, os_n, br, _ = random.choice(p["devices"])
            country = random.choice(ATTACK_COUNTRIES + [p["primary_country"]] * 2)
            ts      = rand_ts(START_TS, END_TS - timedelta(hours=2))
            success = random.random() < 0.12   # 88% failure rate

            login_rows.append({
                "event_id":        str(uuid.uuid4()),
                "user_id":         uid,
                "ip_address":      ip,
                "device_id":       did,
                "event_timestamp": ts,
                "success":         success,
                "country_code":    country,
                "user_agent":      get_ua(os_n, br),
            })

        # Final event: successful takeover from a brand-new device/IP
        takeover_did = str(uuid.uuid4())
        takeover_os  = random.choice(["Windows", "Linux"])
        takeover_br  = random.choice(BROWSER_BY_OS[takeover_os])
        takeover_ts  = rand_ts(END_TS - timedelta(hours=2), END_TS)

        login_rows.append({
            "event_id":        str(uuid.uuid4()),
            "user_id":         uid,
            "ip_address":      rand_ip(),
            "device_id":       takeover_did,
            "event_timestamp": takeover_ts,
            "success":         True,
            "country_code":    random.choice(ATTACK_COUNTRIES),
            "user_agent":      get_ua(takeover_os, takeover_br),
        })
        # Register the attacker's device so it shows up in raw_devices as untrusted
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
        # ── Normal user pattern ───────────────────────────────────────────────
        # A few logins from their home IPs, mostly successful.

        for _ in range(random.randint(5, 25)):
            ip      = random.choice(p["home_ips"])
            did, _, os_n, br, _ = random.choice(p["devices"])
            ts      = rand_ts()
            success = random.random() < 0.92   # 92% success rate

            login_rows.append({
                "event_id":        str(uuid.uuid4()),
                "user_id":         uid,
                "ip_address":      ip,
                "device_id":       did,
                "event_timestamp": ts,
                "success":         success,
                "country_code":    p["primary_country"],
                "user_agent":      get_ua(os_n, br),
            })

# ── Credential stuffing: each CS IP blasts many accounts ─────────────────────
all_uids = list(range(1, N_TOTAL_USERS + 1))
for cs_ip in CREDENTIAL_STUFFING_IPS:
    targets = random.sample(all_uids, random.randint(70, 130))
    for target_uid in targets:
        for _ in range(random.randint(1, 5)):
            login_rows.append({
                "event_id":        str(uuid.uuid4()),
                "user_id":         target_uid,
                "ip_address":      cs_ip,
                "device_id":       str(uuid.uuid4()),  # new device UUID every hit (headless browser)
                "event_timestamp": rand_ts(),
                "success":         random.random() < 0.04,  # 96% fail rate
                "country_code":    random.choice(ATTACK_COUNTRIES),
                "user_agent":      "python-requests/2.28.0",  # bot fingerprint
            })


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE D — Generate raw_request_logs
# Three traffic types: normal users, CS bots (elevated), DDoS bots (massive).
# ═══════════════════════════════════════════════════════════════════════════════
request_rows = []
normal_ips = [ip for p in profiles.values() for ip in p["home_ips"]]

# Normal traffic — 120k requests spread across all user IPs
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

# Credential stuffing IPs — also show up in request logs at elevated volume
for cs_ip in CREDENTIAL_STUFFING_IPS:
    for _ in range(random.randint(800, 2000)):
        request_rows.append({
            "request_id":        str(uuid.uuid4()),
            "ip_address":        cs_ip,
            "request_timestamp": rand_ts(),
            "endpoint":          "/api/login",
            "http_method":       "POST",
            "status_code":       random.choice([200, 401, 403]),
            "response_time_ms":  random.randint(50, 300),
            "user_agent":        "python-requests/2.28.0",
        })

# DDoS bots — massive volume, only 3 endpoints, suspicious user-agent
for ddos_ip in DDOS_BOT_IPS:
    for _ in range(random.randint(10_000, 20_000)):
        request_rows.append({
            "request_id":        str(uuid.uuid4()),
            "ip_address":        ddos_ip,
            "request_timestamp": rand_ts(),
            "endpoint":          random.choice(["/api/browse", "/api/play", "/api/search"]),
            "http_method":       "GET",
            "status_code":       random.choices([200, 429, 503], weights=[60, 30, 10])[0],
            "response_time_ms":  random.randint(5, 100),
            "user_agent":        "Mozilla/5.0 (compatible; Bot/1.0)",
        })


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE E — Write everything to DuckDB
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\nConnecting to DuckDB...")
conn = duckdb.connect(DB_PATH)

# Convert Python lists-of-dicts to pandas DataFrames, then hand to DuckDB.
# DuckDB can read a registered DataFrame directly in SQL — very fast.

devices_df  = pd.DataFrame(device_rows)
logins_df   = pd.DataFrame(login_rows)
requests_df = pd.DataFrame(request_rows)

print(f"Writing raw_devices        ({len(devices_df):>8,} rows)...")
conn.register("devices_df", devices_df)
conn.execute("CREATE OR REPLACE TABLE raw_devices AS SELECT * FROM devices_df")

print(f"Writing raw_login_events   ({len(logins_df):>8,} rows)...")
conn.register("logins_df", logins_df)
conn.execute("CREATE OR REPLACE TABLE raw_login_events AS SELECT * FROM logins_df")

print(f"Writing raw_request_logs   ({len(requests_df):>8,} rows)...")
conn.register("requests_df", requests_df)
conn.execute("CREATE OR REPLACE TABLE raw_request_logs AS SELECT * FROM requests_df")

conn.close()

print("\nDone!")
print(f"  Devices:       {len(devices_df):,}")
print(f"  Login events:  {len(logins_df):,}")
print(f"  Request logs:  {len(requests_df):,}")
print("\nNext: run `dbt run` inside the netflix_security/ folder.")
