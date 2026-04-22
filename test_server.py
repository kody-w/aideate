#!/usr/bin/env python3
"""
AIdeate Server API — Test Suite

Tests the REST API endpoints of server.py:
  /api/info, /api/sync, /api/session, /api/join, /api/vote, /api/unvote

Run: python3 test_server.py
"""

import http.client
import json
import subprocess
import sys
import time
import os

PORT = 18765
server_proc = None
PASS = 0
FAIL = 0


def start_server():
    global server_proc
    env = os.environ.copy()
    server_proc = subprocess.Popen(
        [sys.executable, "server.py", str(PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
    )
    time.sleep(1.5)
    if server_proc.poll() is not None:
        print("FATAL: Server failed to start")
        sys.exit(1)


def stop_server():
    global server_proc
    if server_proc:
        server_proc.terminate()
        server_proc.wait(timeout=5)


def req(method, path, body=None):
    conn = http.client.HTTPConnection("localhost", PORT, timeout=5)
    headers = {"Content-Type": "application/json"} if body else {}
    payload = json.dumps(body).encode() if body else None
    conn.request(method, path, body=payload, headers=headers)
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    return resp.status, data


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}")


def test_info():
    print("\n── GET /api/info ──")
    status, data = req("GET", "/api/info")
    check("Returns 200", status == 200)
    check("Has ip field", "ip" in data)
    check("Has port field", data.get("port") == PORT)
    check("IP is not empty", len(data.get("ip", "")) > 0)


def test_sync():
    print("\n── POST /api/sync ──")
    state = {
        "sessionId": "test-session-123",
        "workshopName": "Test Workshop",
        "companyName": "Contoso",
        "phase": "vote",
        "ideas": [
            {"id": 1001, "name": "Automate reports", "dept": "IT", "desc": "Weekly reports take too long", "votes": 0, "voters": []},
            {"id": 1002, "name": "AI customer support", "dept": "Support", "desc": "Chatbot for tier 1", "votes": 1, "voters": ["Alice"]},
            {"id": 1003, "name": "Predictive maintenance", "dept": "Ops", "desc": "ML for equipment", "votes": 0, "voters": [], "submitter": "Bob"},
        ],
        "participants": [
            {"id": 2001, "name": "Alice", "title": "CTO", "initials": "AC"},
            {"id": 2002, "name": "Bob", "title": "VP Ops", "initials": "BO"},
        ],
        "votesPerPerson": 2,
        "departments": ["IT", "Support", "Ops"],
    }
    status, data = req("POST", "/api/sync", state)
    check("Returns 200", status == 200)
    check("Response has ok=true", data.get("ok") is True)
    check("remoteParticipants is list", isinstance(data.get("remoteParticipants"), list))
    check("remoteVotes is list", isinstance(data.get("remoteVotes"), list))


def test_session():
    print("\n── GET /api/session ──")
    status, data = req("GET", "/api/session")
    check("Returns 200", status == 200)
    check("Has sessionId", data.get("sessionId") == "test-session-123")
    check("Has workshopName", data.get("workshopName") == "Test Workshop")
    check("Phase is vote", data.get("phase") == "vote")
    check("Has 3 ideas", len(data.get("ideas", [])) == 3)
    check("Has 2 participants", len(data.get("participants", [])) == 2)
    check("votesPerPerson is 2", data.get("votesPerPerson") == 2)
    check("First idea has name", data["ideas"][0].get("name") == "Automate reports")


def test_join():
    print("\n── POST /api/join ──")
    # Valid join
    status, data = req("POST", "/api/join", {"name": "Charlie", "title": "Engineer"})
    check("Returns 201", status == 201)
    check("Has id", "id" in data)
    check("Name is Charlie", data.get("name") == "Charlie")
    check("Has initials", data.get("initials") == "CH")
    check("Marked remote", data.get("remote") is True)

    # Duplicate join returns existing
    status2, data2 = req("POST", "/api/join", {"name": "Charlie"})
    check("Duplicate join returns 200", status2 == 200)
    check("Same id returned", data2.get("id") == data.get("id"))

    # Empty name
    status3, data3 = req("POST", "/api/join", {"name": ""})
    check("Empty name returns 400", status3 == 400)

    # Second participant
    status4, data4 = req("POST", "/api/join", {"name": "Diana", "title": "PM"})
    check("Second join returns 201", status4 == 201)
    check("Diana has initials DI", data4.get("initials") == "DI" or data4.get("initials") == "D")

    return data.get("id"), data4.get("id")  # charlieId, dianaId


def test_vote(charlie_id, diana_id):
    print("\n── POST /api/vote ──")
    # Charlie votes for idea 1001
    status, data = req("POST", "/api/vote", {"participantId": charlie_id, "ideaId": 1001, "voterName": "Charlie"})
    check("Vote returns 201", status == 201)
    check("Vote has ok=true", data.get("ok") is True)

    # Charlie votes for idea 1002
    status2, data2 = req("POST", "/api/vote", {"participantId": charlie_id, "ideaId": 1002, "voterName": "Charlie"})
    check("Second vote returns 201", status2 == 201)

    # Charlie tries 3rd vote (over limit of 2)
    status3, data3 = req("POST", "/api/vote", {"participantId": charlie_id, "ideaId": 1003, "voterName": "Charlie"})
    check("Over-limit vote returns 409", status3 == 409)
    check("Error mentions votes used", "votes used" in data3.get("error", "").lower() or "all" in data3.get("error", "").lower())

    # Charlie tries duplicate vote on same idea
    # First unvote one to free up, then try duplicate
    # Actually Charlie already has 2 votes, so duplicate check won't fire.
    # Let's test with Diana
    s5, d5 = req("POST", "/api/vote", {"participantId": diana_id, "ideaId": 1001, "voterName": "Diana"})
    check("Diana votes returns 201", s5 == 201)

    s6, d6 = req("POST", "/api/vote", {"participantId": diana_id, "ideaId": 1001, "voterName": "Diana"})
    check("Duplicate vote returns 409", s6 == 409)
    check("Error mentions already voted", "already" in d6.get("error", "").lower())

    # Invalid participant
    s7, d7 = req("POST", "/api/vote", {"participantId": 99999, "ideaId": 1001, "voterName": "Nobody"})
    check("Unknown participant returns 404", s7 == 404)

    # Missing fields
    s8, d8 = req("POST", "/api/vote", {"participantId": charlie_id})
    check("Missing ideaId returns 400", s8 == 400)


def test_unvote():
    print("\n── POST /api/unvote ──")
    # Remove Charlie's vote for idea 1001
    status, data = req("POST", "/api/unvote", {"voterName": "Charlie", "ideaId": 1001})
    check("Unvote returns 200", status == 200)
    check("removed=1", data.get("removed") == 1)

    # Try removing non-existent vote
    status2, data2 = req("POST", "/api/unvote", {"voterName": "Charlie", "ideaId": 1001})
    check("Double unvote returns 404", status2 == 404)

    # Charlie can now vote again (1 used, limit 2)
    charlie_id = None
    s, d = req("GET", "/api/session")
    for rp in d.get("remoteParticipants", []):
        if rp["name"] == "Charlie":
            charlie_id = rp["id"]
            break

    if charlie_id:
        s3, d3 = req("POST", "/api/vote", {"participantId": charlie_id, "ideaId": 1003, "voterName": "Charlie"})
        check("Re-vote after unvote works (201)", s3 == 201)


def test_session_after_votes():
    print("\n── GET /api/session (after votes) ──")
    status, data = req("GET", "/api/session")
    check("Returns 200", status == 200)
    check("remoteVotes has entries", len(data.get("remoteVotes", [])) > 0)
    check("remoteParticipants has 2", len(data.get("remoteParticipants", [])) == 2)

    # Verify vote details
    charlie_votes = [v for v in data["remoteVotes"] if v["voterName"] == "Charlie"]
    diana_votes = [v for v in data["remoteVotes"] if v["voterName"] == "Diana"]
    check("Charlie has 2 remote votes", len(charlie_votes) == 2)
    check("Diana has 1 remote vote", len(diana_votes) == 1)


def test_static_files():
    print("\n── Static file serving ──")
    conn = http.client.HTTPConnection("localhost", PORT, timeout=5)

    conn.request("GET", "/index.html")
    resp = conn.getresponse()
    body = resp.read()
    check("index.html serves (200)", resp.status == 200)
    check("index.html has content", len(body) > 1000)
    conn.close()

    conn = http.client.HTTPConnection("localhost", PORT, timeout=5)
    conn.request("GET", "/join.html")
    resp = conn.getresponse()
    body = resp.read()
    check("join.html serves (200)", resp.status == 200)
    check("join.html has content", len(body) > 1000)
    conn.close()


def main():
    global PASS, FAIL

    print("🧪 AIdeate Server — Test Suite")
    print("══════════════════════════════════════")

    print("\nStarting server on port", PORT, "...")
    start_server()

    try:
        test_info()
        test_sync()
        test_session()
        charlie_id, diana_id = test_join()
        test_vote(charlie_id, diana_id)
        test_unvote()
        test_session_after_votes()
        test_static_files()
    finally:
        stop_server()

    total = PASS + FAIL
    print(f"\n══════════════════════════════════════")
    print(f"  ✓ {PASS} passed · ✗ {FAIL} failed · {total} total")
    if FAIL:
        print(f"  ❌ SOME TESTS FAILED")
        sys.exit(1)
    else:
        print(f"  🎉 ALL TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
