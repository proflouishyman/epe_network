#!/usr/bin/env python3
"""
Run the EPE forms creator via the Apps Script Execution API
using the clasp OAuth credentials.
"""
import json, time, urllib.request, urllib.parse, urllib.error, sys

SCRIPT_ID = "1hBT6aIschOZC1AVVwRoPuAWcCez6s1LmShADsqIaqFZSbiOHWewQiBig"
CLASPRC   = "/Users/louishyman/.clasprc.json"

# ── 1. Load / refresh the clasp token ─────────────────────────────────────

def refresh_token(creds):
    """Use the refresh_token to get a fresh access_token."""
    data = urllib.parse.urlencode({
        "client_id":     creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type":    "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp["access_token"]

rc    = json.load(open(CLASPRC))["tokens"]["default"]
token = rc.get("access_token", "")

# Refresh if expired (expiry_date is ms since epoch)
expiry = rc.get("expiry_date", 0)
if not token or time.time() * 1000 > expiry - 60_000:
    print("Refreshing access token...")
    token = refresh_token(rc)

# ── 2. Call the Execution API ──────────────────────────────────────────────

url     = f"https://script.googleapis.com/v1/scripts/{SCRIPT_ID}:run"
payload = json.dumps({"function": "createEPEForms", "devMode": True}).encode()
req     = urllib.request.Request(
    url, data=payload,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
)

print("Running createEPEForms on Apps Script...")
try:
    resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
except urllib.error.HTTPError as e:
    body = json.loads(e.read())
    print("HTTP error:", e.code)
    print(json.dumps(body, indent=2))
    sys.exit(1)

# ── 3. Show result ─────────────────────────────────────────────────────────

if "error" in resp:
    err = resp["error"]
    print("\nScript error:", err.get("message", err))
    # Print any logger output from the script
    for d in err.get("details", []):
        for entry in d.get("scriptStackTraceElements", []):
            print(" at", entry)
elif "response" in resp:
    print("\nScript completed successfully.")
    result = resp["response"].get("result")
    if result:
        print("Return value:", result)
else:
    print("\nResponse:", json.dumps(resp, indent=2))
