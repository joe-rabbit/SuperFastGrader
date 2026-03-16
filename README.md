# CSE 412 — Grading Projects

A web-based tool for reviewing, grading, and managing student group project submissions.

## How to Run

from a terminal run:

```bash
python app.py
```

Opens automatically in your browser at `http://localhost:5000`.

---

## Features

| Tab        | Description                                                               |
| ---------- | ------------------------------------------------------------------------- |
| **Info**   | Group members, project name, notes status                                 |
| **Links**  | Save video, repo, and report URLs — open in browser                       |
| **PDF**    | Upload and view the group's PDF report inline                             |
| **Code**   | Upload a ZIP file — browse the file tree and view syntax-highlighted code |
| **Notes**  | Write Phase 1 / Phase 2 / Phase 3 feedback with embedded video viewer     |
| **Search** | Live search across all groups by name, project, or member                 |
| **Graph**  | Visual graph of group → members → project relationships                   |

---

## Notes Storage


---

## File Structure

```
CanvasLMS/
├── app.py                         # Flask app entry point
├── run.bat                        # Double-click to start
├── requirements.txt
├── student_group_projects.json    # All group data + notes
├── templates/
│   └── index.html                 # Frontend UI
├── uploads/                       # Per-group uploaded files
│   └── <group_id>/
│       ├── report.pdf
│       ├── demo.mp4
│       └── project.zip
└── modules/
    ├── data.py                    # JSON read/write
    ├── graph_db.py                # NetworkX graph
    └── search_engine.py           # Search index
```

---

## Requirements

```
flask
networkx
matplotlib
```

Install with:

```bash
pip install flask networkx matplotlib
```
