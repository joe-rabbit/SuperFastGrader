from collections import defaultdict

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False


class GraphDB:
    def __init__(self, groups):
        self.G = nx.DiGraph() if HAS_NX else None
        self._index = {}
        self._member_index = defaultdict(list)
        self._project_index = defaultdict(list)
        self._build(groups)

    def _build(self, groups):
        for g in groups:
            gid  = f"group:{g['group']}"
            proj = f"project:{g['project']}"
            self._index[g['group']] = g
            self._project_index[g['project'].lower()].append(g['group'])

            if self.G is not None:
                self.G.add_node(gid,  kind='group',   label=f"G{g['group']}")
                self.G.add_node(proj, kind='project',  label=g['project'][:20])
                self.G.add_edge(gid, proj, rel='BUILDS')

            for name in g['members']:
                mid = f"member:{name}"
                self._member_index[name.lower()].append(g['group'])
                if self.G is not None:
                    self.G.add_node(mid, kind='member', label=name.split()[0])
                    self.G.add_edge(gid, mid, rel='HAS_MEMBER')

    def get_group(self, gid):
        return self._index.get(gid)

    def all_groups(self):
        return list(self._index.values())

    def members_of(self, gid):
        g = self._index.get(gid)
        return g['members'] if g else []

    def groups_of_member(self, name):
        key = name.lower()
        hits = []
        for k, gids in self._member_index.items():
            if key in k:
                hits.extend(gids)
        return list(set(hits))

    def coworkers(self, name):
        result = []
        for gid in self.groups_of_member(name):
            for m in self._index[gid]['members']:
                if m.lower() != name.lower() and m not in result:
                    result.append(m)
        return result

    def path_between(self, name_a, name_b):
        if not HAS_NX:
            return None
        try:
            return nx.shortest_path(
                self.G.to_undirected(),
                f"member:{name_a}",
                f"member:{name_b}",
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def subgraph_for(self, gid):
        if not HAS_NX:
            return None
        g = self._index.get(gid)
        if not g:
            return None
        nodes = ([f"group:{gid}", f"project:{g['project']}"] +
                 [f"member:{m}" for m in g['members']])
        return self.G.subgraph(nodes)
