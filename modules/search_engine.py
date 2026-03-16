import re
from collections import defaultdict


class SearchEngine:
    def __init__(self, groups):
        self._groups = groups
        self._index  = defaultdict(set)
        self._build()

    def _tokenize(self, text):
        return re.findall(r'[a-z0-9]+', text.lower())

    def _build(self):
        for g in self._groups:
            doc_id = g['group']
            tokens = (
                self._tokenize(g['project']) +
                self._tokenize(g['group']) +
                [t for name in g['members'] for t in self._tokenize(name)]
            )
            for t in tokens:
                self._index[t].add(doc_id)

    def search(self, query: str):
        tokens = self._tokenize(query)
        if not tokens:
            return list(self._groups)
        scores  = defaultdict(int)
        for t in tokens:
            for key in self._index:
                if key.startswith(t):
                    for doc_id in self._index[key]:
                        scores[doc_id] += 1
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        gmap   = {g['group']: g for g in self._groups}
        return [gmap[doc_id] for doc_id, _ in ranked if doc_id in gmap]
