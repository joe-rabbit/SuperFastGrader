import json, copy
from pathlib import Path
from datetime import datetime

_PHASE_DEFAULT = {'text': '', 'grade': '', 'updated': ''}

_DEFAULTS = {
    'video_url':  '',   # YouTube / Drive / any web video link
    'repo_url':   '',   # GitHub / GitLab repo
    'report_url': '',   # Google Drive PDF or web report
    'pdfpath':    '',   # local PDF (copied to uploads/)
    'zippath':    '',   # local ZIP (copied to uploads/)
    'notes': {
        'phase1': copy.deepcopy(_PHASE_DEFAULT),
        'phase2': copy.deepcopy(_PHASE_DEFAULT),
        'phase3': copy.deepcopy(_PHASE_DEFAULT),
    }
}


class DataManager:
    def __init__(self, path: Path):
        self.path = path
        self._data = None
        self.reload()

    def reload(self):
        with open(self.path, encoding='utf-8') as f:
            self._data = json.load(f)
        self._fill_defaults()

    def _fill_defaults(self):
        for g in self._data['groups']:
            # migrate old 'videopath' key → 'video_url'
            if 'videopath' in g and not g.get('video_url'):
                g['video_url'] = g.pop('videopath')
            elif 'videopath' in g:
                g.pop('videopath')
            for k, v in _DEFAULTS.items():
                if k not in g:
                    g[k] = copy.deepcopy(v)
            # ensure all phases exist
            for phase in ['phase1', 'phase2', 'phase3']:
                g['notes'].setdefault(phase, copy.deepcopy(_PHASE_DEFAULT))
                for field in ['text', 'grade', 'updated']:
                    g['notes'][phase].setdefault(field, '')

    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    @property
    def groups(self):
        return self._data['groups']

    def get_group(self, gid: str):
        for g in self._data['groups']:
            if g['group'] == gid:
                return g
        return None

    def save_notes(self, gid: str, phase: str, text: str, grade: str):
        g = self.get_group(gid)
        if g:
            g['notes'][phase] = {
                'text': text,
                'grade': grade,
                'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
            }
            self.save()
            return True
        return False

    def save_field(self, gid: str, key: str, value: str):
        """Save any top-level field on a group."""
        g = self.get_group(gid)
        if g:
            g[key] = value
            self.save()
            return True
        return False
