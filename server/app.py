"""worldcup-date cloud diary backend — tiny clip sync API (clips stored in Postgres).

Endpoints (all gated by a shared key via the X-Diary-Key header or ?key=):
  GET    /api/health         -> {ok, hasDb}
  GET    /api/clips          -> [{id, sec, lat, lng, t, mime, created, who, score, minute, play}]
  POST   /api/clip           -> {id}      multipart: video=<blob>, sec, lat, lng, t, who, score, minute, play
  GET    /api/clip/<id>      -> the video bytes
  DELETE /api/clip/<id>      -> {ok}
  GET    /api/state          -> {key: {v, who, updated}}   every synced interactive-state key
  PUT    /api/state/<key>    -> {ok}      json body: {v: <any json-able value>, who}

`score`/`minute`/`play` are an optional live-match snapshot the client attaches at capture time
(e.g. "USA 1-0 BEL", "34'", "⚽ Goal · 31'") -- only present when a photo/clip was taken while
the couple's tracked match was actually live. Plain strings, opaque to the backend.

`who` is a lightweight attribution string ("neal" / "sidhya" / "guest:<name>"), resolved
client-side from a username (no passwords -- this is a private gift site, not a real
account system). The backend just stores and echoes it back for display.

`/api/state` is a small generic key-value store: every interactive bit of shared state
(picks, bingo, missions, passport stamps, flight log, etc.) is written here the moment it
changes on either phone, so both devices converge on the same values instead of each
holding its own localStorage silo. One row per key -- the whole app has maybe a dozen keys,
so a single "give me everything" GET is simpler and cheap enough than per-key fetches.
"""
import os, time, uuid
from flask import Flask, request, jsonify, abort, Response
from flask_cors import CORS
import psycopg2

DB_URL = os.environ.get("DATABASE_URL", "")
KEY = os.environ.get("DIARY_KEY", "")
MAX_BYTES = 80 * 1024 * 1024  # 80 MB per clip -- real camera-roll videos run bigger than the app's own short recordings

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES + 1024 * 1024
CORS(app)  # the diary is gated by the shared key, so any origin may call it


def conn():
    return psycopg2.connect(DB_URL, sslmode="require")


def init_db():
    c = conn()
    cur = c.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS clips(
            id TEXT PRIMARY KEY, sec TEXT, lat DOUBLE PRECISION, lng DOUBLE PRECISION,
            t BIGINT, mime TEXT, created BIGINT, data BYTEA)"""
    )
    cur.execute("ALTER TABLE clips ADD COLUMN IF NOT EXISTS who TEXT")  # older rows just come back who=NULL
    cur.execute("ALTER TABLE clips ADD COLUMN IF NOT EXISTS score TEXT")
    cur.execute("ALTER TABLE clips ADD COLUMN IF NOT EXISTS minute TEXT")
    cur.execute("ALTER TABLE clips ADD COLUMN IF NOT EXISTS play TEXT")
    cur.execute(
        """CREATE TABLE IF NOT EXISTS state(
            k TEXT PRIMARY KEY, v TEXT, who TEXT, updated BIGINT)"""
    )
    c.commit()
    cur.close()
    c.close()


try:
    if DB_URL:
        init_db()
except Exception as e:  # don't crash boot; /api/health will report
    print("init_db error:", e)


def check_key():
    k = request.headers.get("X-Diary-Key") or request.args.get("key", "")
    if KEY and k != KEY:
        abort(401)


@app.route("/")
def index():
    return "worldcup-date diary backend \U0001f49c"


@app.route("/api/health")
def health():
    return jsonify(ok=True, hasDb=bool(DB_URL))


@app.route("/api/clips")
def list_clips():
    check_key()
    c = conn(); cur = c.cursor()
    cur.execute("SELECT id,sec,lat,lng,t,mime,created,who,score,minute,play FROM clips ORDER BY created ASC")
    rows = cur.fetchall(); cur.close(); c.close()
    return jsonify([
        dict(id=r[0], sec=r[1], lat=r[2], lng=r[3], t=r[4], mime=r[5], created=r[6], who=r[7],
             score=r[8], minute=r[9], play=r[10])
        for r in rows
    ])


@app.route("/api/clip", methods=["POST"])
def add_clip():
    check_key()
    f = request.files.get("video")
    if not f:
        abort(400, "no video")
    data = f.read()
    if len(data) > MAX_BYTES:
        abort(413, "clip too big")
    cid = uuid.uuid4().hex
    sec = request.form.get("sec", "s0")
    lat = request.form.get("lat"); lng = request.form.get("lng"); t = request.form.get("t")
    who = (request.form.get("who") or "")[:60]  # "neal" / "sidhya" / "guest:<name>", resolved client-side
    score = (request.form.get("score") or "")[:40] or None
    minute = (request.form.get("minute") or "")[:20] or None
    play = (request.form.get("play") or "")[:200] or None
    mime = f.mimetype or "video/webm"
    now = int(time.time() * 1000)
    c = conn(); cur = c.cursor()
    cur.execute(
        """INSERT INTO clips(id,sec,lat,lng,t,mime,created,data,who,score,minute,play)
           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (cid, sec, float(lat) if lat else None, float(lng) if lng else None,
         int(t) if t else now, mime, now, psycopg2.Binary(data), who, score, minute, play),
    )
    c.commit(); cur.close(); c.close()
    return jsonify(id=cid)


@app.route("/api/clip/<cid>")
def get_clip(cid):
    check_key()
    c = conn(); cur = c.cursor()
    cur.execute("SELECT mime,data FROM clips WHERE id=%s", (cid,))
    row = cur.fetchone(); cur.close(); c.close()
    if not row:
        abort(404)
    return Response(bytes(row[1]), mimetype=row[0] or "video/webm")


@app.route("/api/clip/<cid>", methods=["DELETE"])
def del_clip(cid):
    check_key()
    c = conn(); cur = c.cursor()
    cur.execute("DELETE FROM clips WHERE id=%s", (cid,))
    c.commit(); cur.close(); c.close()
    return jsonify(ok=True)


@app.route("/api/state")
def get_state():
    check_key()
    c = conn(); cur = c.cursor()
    cur.execute("SELECT k,v,who,updated FROM state")
    rows = cur.fetchall(); cur.close(); c.close()
    return jsonify({r[0]: dict(v=r[1], who=r[2], updated=r[3]) for r in rows})


@app.route("/api/state/<key>", methods=["PUT"])
def put_state(key):
    check_key()
    body = request.get_json(silent=True) or {}
    v = body.get("v")
    if v is None:
        abort(400, "no v")
    who = (body.get("who") or "")[:60]
    now = int(time.time() * 1000)
    c = conn(); cur = c.cursor()
    cur.execute(
        """INSERT INTO state(k,v,who,updated) VALUES(%s,%s,%s,%s)
           ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v, who=EXCLUDED.who, updated=EXCLUDED.updated""",
        (key, str(v), who, now),
    )
    c.commit(); cur.close(); c.close()
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
