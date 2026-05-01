import json
from pathlib import Path
from graphify.build import build_from_json
from graphify.export import to_html

extraction = json.loads(Path('/workspaces/codespaces-blank/graphify-out/graph.json').read_text())
analysis = json.loads(Path('/workspaces/codespaces-blank/graphify-out/.graphify_analysis.json').read_text())
labels_raw = json.loads(Path('/workspaces/codespaces-blank/graphify-out/.graphify_labels.json').read_text())

G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
labels = {int(k): v for k, v in labels_raw.items()}

to_html(G, communities, '/workspaces/codespaces-blank/graphify-out/graph.html', community_labels=labels)
print('graph.html written - open in any browser, no server needed')