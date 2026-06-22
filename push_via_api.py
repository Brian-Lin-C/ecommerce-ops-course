#!/usr/bin/env python3
"""Push changes in teach-ecommerce-ops to GitHub via API (no proxy needed).
Usage: python3 push_via_api.py
Requires: GH_TOKEN env var or token file.
"""
import urllib.request, urllib.error, base64, json, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
OWNER = "Brian-Lin-C"
REPO = "ecommerce-ops-course"

# Get token
token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not token:
    token_file = os.path.join(os.path.dirname(BASE), ".ghtoken")
    if os.path.exists(token_file):
        with open(token_file) as f:
            token = f.read().strip()
if not token:
    print("Set GH_TOKEN env var or create .ghtoken file")
    sys.exit(1)

# Get changed files from git
result = subprocess.run(
    ["git", "-C", BASE, "diff", "--name-only", "HEAD"],
    capture_output=True, text=True
)
changed = [f for f in result.stdout.strip().split("\n") if f]

# Also include untracked files
result2 = subprocess.run(
    ["git", "-C", BASE, "ls-files", "--others", "--exclude-standard"],
    capture_output=True, text=True
)
changed += [f for f in result2.stdout.strip().split("\n") if f]

if not changed:
    print("No changes to push.")
    sys.exit(0)

print(f"Pushing {len(changed)} files via API...")

for filepath in changed:
    full_path = os.path.join(BASE, filepath)
    if not os.path.exists(full_path):
        print(f"  SKIP {filepath} (deleted)")
        continue

    with open(full_path, "rb") as f:
        content = f.read()

    encoded = base64.b64encode(content).decode()
    data = json.dumps({
        "message": f"Update {filepath}",
        "content": encoded,
        "branch": "master"
    }).encode()

    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{filepath}"
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/vnd.github+json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"  OK  {filepath}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  FAIL {filepath}: {e.code} {body[:150]}")
    except Exception as e:
        print(f"  FAIL {filepath}: {e}")

print("Done.")
