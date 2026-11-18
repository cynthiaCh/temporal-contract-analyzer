"""Stage a small allowlisted public-only Docker context; no Docker or API calls."""
import argparse
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def public_inputs(benchmark):
    files = {
        'Dockerfile': REPO / 'containers/tempoevo/Dockerfile.rebuild',
        'install_public_runtime.py': REPO / 'containers/tempoevo/install_public_runtime.py',
        'smoke_public_runtime.py': REPO / 'containers/tempoevo/smoke_public_runtime.py',
        'tools/setup_swe_tempoc.py': benchmark / 'tools/setup_swe_tempoc.py',
    }
    for name in ('document-submit-ports', 'vanilla-js', 'vue2', 'vue3', 'react18'):
        for filename in ('package.json', 'package-lock.json'):
            relative = 'runtimes/' + name + '/' + filename
            files[relative] = benchmark / relative
    for filename in ('package.json', 'package-lock.json'):
        files['parser/' + filename] = REPO / 'temporal_contract_analyzer/javascript' / filename
    return files


def prepare(benchmark, output):
    benchmark, output = Path(benchmark).resolve(), Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('Use a new output directory; existing files are never overwritten')
    for source_root in (benchmark, REPO):
        if output.resolve() == source_root or source_root in output.resolve().parents:
            raise ValueError('Build context must be outside both source repositories')
    files = public_inputs(benchmark)
    # Read and validate all allowlisted inputs before creating output.
    content = {}
    for relative, source in files.items():
        root = benchmark if source.is_relative_to(benchmark) else REPO
        if not source.is_file() or any(p.is_symlink() for p in (source, *source.parents)):
            raise ValueError('Public inputs must be regular files without symlinked parents: ' + str(source))
        if not source.resolve().is_relative_to(root):
            raise ValueError('Public input escaped its source repository')
        content[relative] = source.read_bytes()
    manifest = dict(schema_version='tempoevo-public-solver-build-inputs-v1',
                    historical_image_equivalence=False,
                    benchmark_root=str(benchmark), analyzer_root=str(REPO),
                    source_policy='Only listed public toolchain installer and package locks; no cases/scorers/references/credentials',
                    files={p: hashlib.sha256(b).hexdigest() for p, b in sorted(content.items())})
    output.mkdir(parents=True, exist_ok=False)
    for relative, data in content.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (output / 'public-inputs.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return dict(status='staged_not_built', context=str(output), files=len(content) + 1,
                source_bytes=sum(map(len, content.values())), docker_calls=0, model_calls=0,
                public_inputs_sha256=hashlib.sha256((output / 'public-inputs.json').read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.benchmark_root, args.output), indent=2))


if __name__ == '__main__':
    main()
