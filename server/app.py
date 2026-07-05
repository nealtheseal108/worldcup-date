"""worldcup-date cloud diary backend — tiny clip sync API (clips stored in Postgres).

Endpoints (all gated by a shared key via the X-Diary-Key header or ?key=):
  GET    /api/health         -> {ok, hasDb}
  GET    /api/clips          -> [{id, sec, lat, lng, t, mime, created, who}]   (metadata only)
  POST   /api/clip           -> {id}      multipart: video=<blob>, sec, lat, lng, t, who
  GET    /api/clip/<id>      -> the video bytes
  DELETE /api/clip/<id>      -> {ok}

`who` is a lightweight attribution string ("neal" / "sidhya" / "guest:<name>"), resolved
client-side from a username (no passwords -- this is a private gift site, not a real
account system). The backend just stores and echoes it back for display.
"""
import os, time, uuid
from flask import Flask, request, jsonify, abort, Response
from flask_cors import CORS
import psycopg2

DB_URL = os.environ.get("DATABASE_URL", "")
KEY = os.environ.get("DIARY_KEY", "")
MAX_BYTES = 40 * 1024 * 1024  # 40 MB per clip

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
    cur.execute("SELECT id,sec,lat,lng,t,mime,created,who FROM clips ORDER BY created ASC")
    rows = cur.fetchall(); cur.close(); c.close()
    return jsonify([
        dict(id=r[0], sec=r[1], lat=r[2], lng=r[3], t=r[4], mime=r[5], created=r[6], who=r[7])
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
    mime = f.mimetype or "video/webm"
    now = int(time.time() * 1000)
    c = conn(); cur = c.cursor()
    cur.execute(
        "INSERT INTO clips(id,sec,lat,lng,t,mime,created,data,who) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (cid, sec, float(lat) if lat else None, float(lng) if lng else None,
         int(t) if t else now, mime, now, psycopg2.Binary(data), who),
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
