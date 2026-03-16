"""
Flask backend
Run: python app.py  (opens browser automatically)
"""

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    send_from_directory,
    Response,
)
from pathlib import Path
from modules.data import DataManager
from modules.search_engine import SearchEngine
from modules.graph_db import GraphDB
import io, zipfile, webbrowser, threading, time

BASE = Path(__file__).parent
UPLOAD_DIR = BASE / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

dm = DataManager(BASE / "student_group_projects.json")
se = SearchEngine(dm.groups)
gdb = GraphDB(dm.groups)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB

EXT_CODE = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".java",
    ".cpp",
    ".c",
    ".json",
    ".xml",
    ".md",
    ".sh",
    ".sql",
    ".cs",
    ".go",
    ".rb",
    ".php",
    ".rs",
    ".kt",
    ".swift",
    ".yml",
    ".yaml",
    ".txt",
    ".toml",
}
EXT_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".html": "html",
    ".css": "css",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".json": "json",
    ".xml": "xml",
    ".md": "markdown",
    ".sh": "bash",
    ".sql": "sql",
    ".cs": "csharp",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".rs": "rust",
    ".kt": "kotlin",
    ".swift": "swift",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".txt": "text",
    ".toml": "toml",
}


@app.route("/")
def index():
    return render_template("index.html", group_count=len(dm.groups))


@app.route("/uploads/<gid>/<path:filename>")
def serve_upload(gid, filename):
    return send_from_directory(str(UPLOAD_DIR / gid), filename)


@app.route("/api/groups")
def api_groups():
    return jsonify(dm.groups)


@app.route("/api/group/<gid>")
def api_group(gid):
    g = dm.get_group(gid)
    return (jsonify(g) if g else jsonify({"error": "Not found"})), (200 if g else 404)


@app.route("/api/group/<gid>/notes", methods=["POST"])
def api_save_notes(gid):
    d = request.json
    dm.save_notes(gid, d["phase"], d["text"], "")
    return jsonify({"ok": True})


@app.route("/api/group/<gid>/field", methods=["POST"])
def api_save_field(gid):
    d = request.json
    dm.save_field(gid, d["key"], d["value"])
    return jsonify({"ok": True})


@app.route("/api/group/<gid>/upload/<filetype>", methods=["POST"])
def api_upload(gid, filetype):
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "No file"}), 400
    dest = UPLOAD_DIR / gid
    dest.mkdir(exist_ok=True)
    fname = Path(f.filename).name
    f.save(str(dest / fname))
    key_map = {
        "pdf": ("pdfpath", fname),
        "zip": ("zippath", fname),
        "video": ("video_url", f"/uploads/{gid}/{fname}"),
    }
    key, value = key_map.get(filetype, (filetype + "path", fname))
    dm.save_field(gid, key, value)
    return jsonify({"ok": True, "filename": fname, "value": value})


@app.route("/api/group/<gid>/zip-tree")
def api_zip_tree(gid):
    g = dm.get_group(gid)
    zipname = g.get("zippath", "") if g else ""
    if not zipname:
        return jsonify({"files": []})
    zippath = UPLOAD_DIR / gid / zipname
    if not zippath.exists():
        return jsonify({"files": []})
    files = []
    with zipfile.ZipFile(zippath) as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith("/") and Path(name).suffix.lower() in EXT_CODE:
                files.append(name)
    return jsonify({"files": files})


@app.route("/api/group/<gid>/zip-file")
def api_zip_file(gid):
    g = dm.get_group(gid)
    zipname = g.get("zippath", "") if g else ""
    filepath = request.args.get("path", "")
    if not zipname or not filepath:
        return jsonify({"error": "Missing params"}), 400
    zippath = UPLOAD_DIR / gid / zipname
    if not zippath.exists():
        return jsonify({"error": "ZIP not found"}), 404
    with zipfile.ZipFile(zippath) as zf:
        content = zf.read(filepath).decode("utf-8", errors="replace")
    lang = EXT_LANG.get(Path(filepath).suffix.lower(), "text")
    return jsonify(
        {
            "content": content,
            "lang": lang,
            "path": filepath,
            "lines": len(content.splitlines()),
        }
    )


@app.route("/api/group/<gid>/graph.png")
def api_graph(gid):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import networkx as nx
        from matplotlib.patches import Patch

        full = request.args.get("full", "0") == "1"
        G_src = gdb.G if full else gdb.subgraph_for(gid)

        fig, ax = plt.subplots(figsize=(10, 7 if not full else 13))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        MAROON = "#8B0000"
        colors = {"group": MAROON, "member": "#2980b9", "project": "#27ae60"}
        nc = [
            colors.get(G_src.nodes[n].get("kind", "group"), "#aaa") for n in G_src.nodes
        ]
        labels = {
            n: G_src.nodes[n].get("label", n.split(":")[-1][:15]) for n in G_src.nodes
        }
        pos = nx.spring_layout(G_src, seed=42, k=2.5 if full else 3)
        nx.draw_networkx(
            G_src,
            pos,
            ax=ax,
            labels=labels,
            node_color=nc,
            node_size=600 if full else 1200,
            font_size=7 if full else 9,
            font_color="white",
            edge_color="#ccc",
            arrows=True,
            arrowsize=12,
        )
        ax.legend(
            handles=[
                Patch(color=MAROON, label="Group"),
                Patch(color="#2980b9", label="Member"),
                Patch(color="#27ae60", label="Project"),
            ],
            fontsize=10,
            loc="lower left",
        )
        g_data = dm.get_group(gid)
        title = (
            f'Group {gid} — {g_data["project"]}' if not full else "All Groups Network"
        )
        ax.set_title(title, fontsize=13, color=MAROON, pad=12)
        ax.axis("off")
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return Response(buf.getvalue(), mimetype="image/png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    return jsonify(se.search(q) if q else dm.groups)


if __name__ == "__main__":

    def _open_browser():
        time.sleep(1.2)
        webbrowser.open("http://localhost:5000")

    threading.Thread(target=_open_browser, daemon=True).start()
    app.run(port=5000, debug=False, use_reloader=False)
