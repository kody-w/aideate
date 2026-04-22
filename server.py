#!/usr/bin/env python3
"""
AIdeate Workshop Server — Local-first HTTP + REST API

Serves static files AND provides a REST API for audience voting.
Replaces `python3 -m http.server` with interactive features.

Endpoints:
  GET  /api/session         — Current session state (ideas, phase, participants, votes)
  POST /api/join             — Participant joins: {name, title?} → {id, name, initials}
  POST /api/vote             — Cast a vote: {participantId, ideaId} → OK/error
  POST /api/unvote           — Remove a vote: {participantId, ideaId} → OK/error
  POST /api/sync             — Facilitator pushes full state from localStorage
  GET  /api/info             — Server info (LAN IP, port, session ID)
"""

import http.server
import json
import os
import socket
import sys
import time
import threading
import urllib.parse

# ════════════════════════════════════════
# SESSION STATE (in-memory, synced from facilitator)
# ════════════════════════════════════════
session = {
    "sessionId": "",
    "workshopName": "",
    "companyName": "",
    "phase": "ideate",
    "participants": [],
    "ideas": [],
    "votesPerPerson": 2,
    "departments": [],
    "remoteParticipants": [],  # joined via QR
    "remoteVotes": [],         # {participantId, ideaId, voterName, timestamp}
    "lastSync": 0
}
lock = threading.Lock()


def get_lan_ip():
    """Get the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def json_response(handler, data, status=200):
    """Send a JSON response."""
    body = json.dumps(data).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def read_body(handler):
    """Read and parse JSON request body."""
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


class AIdeateHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with REST API for audience voting."""

    def log_message(self, format, *args):
        # Quieter logging — only show API calls
        msg = format % args
        if "/api/" in msg:
            sys.stderr.write(f"  [API] {msg}\n")

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/session":
            self._handle_get_session()
        elif parsed.path == "/api/info":
            self._handle_info()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/join":
            self._handle_join()
        elif parsed.path == "/api/vote":
            self._handle_vote()
        elif parsed.path == "/api/unvote":
            self._handle_unvote()
        elif parsed.path == "/api/sync":
            self._handle_sync()
        else:
            self.send_error(404)

    # ── GET /api/session ──
    def _handle_get_session(self):
        with lock:
            # Return a view suitable for participants
            data = {
                "sessionId": session["sessionId"],
                "workshopName": session["workshopName"],
                "companyName": session["companyName"],
                "phase": session["phase"],
                "ideas": [
                    {
                        "id": idea.get("id"),
                        "name": idea.get("name"),
                        "dept": idea.get("dept"),
                        "desc": idea.get("desc", ""),
                        "votes": idea.get("votes", 0),
                        "voters": idea.get("voters", []),
                    }
                    for idea in session.get("ideas", [])
                ],
                "participants": session.get("participants", []),
                "remoteParticipants": session.get("remoteParticipants", []),
                "votesPerPerson": session.get("votesPerPerson", 2),
                "remoteVotes": session.get("remoteVotes", []),
                "lastSync": session.get("lastSync", 0),
            }
        json_response(self, data)

    # ── GET /api/info ──
    def _handle_info(self):
        json_response(self, {
            "ip": get_lan_ip(),
            "port": self.server.server_address[1],
            "sessionId": session.get("sessionId", ""),
        })

    # ── POST /api/join ──
    def _handle_join(self):
        try:
            body = read_body(self)
        except Exception:
            json_response(self, {"error": "Invalid JSON"}, 400)
            return

        name = (body.get("name") or "").strip()
        if not name:
            json_response(self, {"error": "Name is required"}, 400)
            return

        title = (body.get("title") or "").strip()
        initials = "".join(w[0] for w in name.split() if w).upper()[:2]
        if len(initials) < 2:
            initials = name[:2].upper()
        pid = int(time.time() * 1000)

        participant = {
            "id": pid,
            "name": name,
            "title": title,
            "initials": initials,
            "remote": True,
            "joinedAt": time.time(),
        }

        with lock:
            # Check for duplicate name
            existing = [p for p in session["remoteParticipants"] if p["name"] == name]
            if existing:
                # Return existing participant
                json_response(self, existing[0])
                return

            session["remoteParticipants"].append(participant)

        sys.stderr.write(f"  👤 Joined: {name} ({title or 'no title'})\n")
        json_response(self, participant, 201)

    # ── POST /api/vote ──
    def _handle_vote(self):
        try:
            body = read_body(self)
        except Exception:
            json_response(self, {"error": "Invalid JSON"}, 400)
            return

        participant_id = body.get("participantId")
        idea_id = body.get("ideaId")
        voter_name = body.get("voterName", "")

        if not participant_id or not idea_id:
            json_response(self, {"error": "participantId and ideaId required"}, 400)
            return

        with lock:
            # Find the voter
            voter = None
            for p in session["remoteParticipants"]:
                if p["id"] == participant_id:
                    voter = p
                    break
            if not voter:
                # Also check facilitator participants
                for p in session.get("participants", []):
                    if p["id"] == participant_id:
                        voter = p
                        break

            if not voter:
                json_response(self, {"error": "Participant not found"}, 404)
                return

            v_name = voter_name or voter["name"]

            # Count votes used by this voter
            votes_used = sum(
                1 for v in session["remoteVotes"]
                if v["voterName"] == v_name
            )
            # Also count votes in facilitator state
            for idea in session.get("ideas", []):
                votes_used += (idea.get("voters") or []).count(v_name)
            # Subtract remote votes already counted (avoid double-counting)
            for v in session["remoteVotes"]:
                if v["voterName"] == v_name:
                    for idea in session.get("ideas", []):
                        if idea.get("id") == v["ideaId"] and v_name in (idea.get("voters") or []):
                            votes_used -= 1

            max_votes = session.get("votesPerPerson", 2)
            if votes_used >= max_votes:
                json_response(self, {"error": f"All {max_votes} votes used"}, 409)
                return

            # Check duplicate vote on same idea
            for v in session["remoteVotes"]:
                if v["voterName"] == v_name and v["ideaId"] == idea_id:
                    json_response(self, {"error": "Already voted for this idea"}, 409)
                    return
            # Also check in facilitator state
            for idea in session.get("ideas", []):
                if idea.get("id") == idea_id and v_name in (idea.get("voters") or []):
                    json_response(self, {"error": "Already voted for this idea"}, 409)
                    return

            vote = {
                "participantId": participant_id,
                "ideaId": idea_id,
                "voterName": v_name,
                "timestamp": time.time(),
            }
            session["remoteVotes"].append(vote)

        idea_name = ""
        for idea in session.get("ideas", []):
            if idea.get("id") == idea_id:
                idea_name = idea.get("name", "")
                break

        sys.stderr.write(f"  🗳️  Vote: {v_name} → {idea_name}\n")
        json_response(self, {"ok": True, "vote": vote}, 201)

    # ── POST /api/unvote ──
    def _handle_unvote(self):
        try:
            body = read_body(self)
        except Exception:
            json_response(self, {"error": "Invalid JSON"}, 400)
            return

        voter_name = body.get("voterName", "")
        idea_id = body.get("ideaId")

        if not voter_name or not idea_id:
            json_response(self, {"error": "voterName and ideaId required"}, 400)
            return

        with lock:
            before = len(session["remoteVotes"])
            session["remoteVotes"] = [
                v for v in session["remoteVotes"]
                if not (v["voterName"] == voter_name and v["ideaId"] == idea_id)
            ]
            removed = before - len(session["remoteVotes"])

        if removed:
            json_response(self, {"ok": True, "removed": removed})
        else:
            json_response(self, {"error": "Vote not found"}, 404)

    # ── POST /api/sync ──
    def _handle_sync(self):
        """Facilitator pushes full state from localStorage."""
        try:
            body = read_body(self)
        except Exception:
            json_response(self, {"error": "Invalid JSON"}, 400)
            return

        with lock:
            session["sessionId"] = body.get("sessionId", session["sessionId"])
            session["workshopName"] = body.get("workshopName", "")
            session["companyName"] = body.get("companyName", "")
            session["phase"] = body.get("phase", "ideate")
            session["ideas"] = body.get("ideas", [])
            session["participants"] = body.get("participants", [])
            session["votesPerPerson"] = body.get("votesPerPerson", 2)
            session["departments"] = body.get("departments", [])
            session["lastSync"] = time.time()

        json_response(self, {
            "ok": True,
            "remoteParticipants": session["remoteParticipants"],
            "remoteVotes": session["remoteVotes"],
        })


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(directory)

    lan_ip = get_lan_ip()

    handler = AIdeateHandler
    server = http.server.HTTPServer(("0.0.0.0", port), handler)

    print(f"")
    print(f"  🚀 AIdeate Workshop Server")
    print(f"  ══════════════════════════════════════")
    print(f"  Presenter:  http://localhost:{port}/index.html")
    print(f"  Join URL:   http://{lan_ip}:{port}/join.html")
    print(f"  ──────────────────────────────────────")
    print(f"  LAN IP:     {lan_ip}")
    print(f"  Port:       {port}")
    print(f"  ══════════════════════════════════════")
    print(f"  Press Ctrl+C to stop")
    print(f"")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
