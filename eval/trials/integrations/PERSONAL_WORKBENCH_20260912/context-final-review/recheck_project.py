"""Independent, offline regression of only the remaining project URL boundary."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from markdown_it import MarkdownIt

BASE = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ROOT = OUT / 'fixture'
SCRIPT = BASE / 'scripts/workbench_context.py'
source = SCRIPT.read_bytes()
fingerprint = hashlib.sha256(source).hexdigest()
packet = json.loads((OUT / 'inputs/full_context.json').read_text())
cases = [
    ('cross_workspace', 'https://linear.app/other/project/foreign', 2),
    ('wrong_route', 'https://linear.app/reviewspace/issue/YYH-71', 2),
    ('wrong_host', 'https://example.invalid/reviewspace/project/p-seven', 2),
    ('valid_opaque_slug', 'https://linear.app/reviewspace/project/p-seven-0123abcd', 0),
]
results = []
for name, url, expected in cases:
    value = copy.deepcopy(packet)
    value['project']['url'] = url
    input_path = OUT / 'inputs' / ('project_final_' + name + '.json')
    input_path.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    command = [sys.executable, str(SCRIPT), '--root', str(ROOT), 'build',
               '--input', str(input_path), '--output',
               '.derived/linear/contexts/project_final_' + fingerprint[:8] + '_' + name]
    proc = subprocess.run(command, capture_output=True, text=True,
                          env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    result = {'case': name, 'command': command, 'expected_returncode': expected,
              'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}
    if proc.returncode == 0:
        response = json.loads(proc.stdout)
        body = Path(response['context']).read_text()
        urls = [child.attrGet('href') for token in MarkdownIt().parse(body)
                for child in token.children or [] if child.type == 'link_open']
        result['project_link_rendered'] = url in urls
        result['project_description_verbatim'] = value['project']['description'] in body
    results.append(result)
    print(name, proc.returncode, expected)
evidence = {'source_sha256': fingerprint, 'source_unchanged_during_check': source == SCRIPT.read_bytes(),
            'results': results, 'online_scope': 'No online calls or real new-session execution were performed.'}
archive = OUT / 'reviewed-source-final/scripts/workbench_context.py'
archive.parent.mkdir(parents=True, exist_ok=True)
archive.write_bytes(source)
(OUT / 'project-final-check.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
