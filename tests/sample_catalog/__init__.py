from __future__ import annotations


class DummyFunction:
    def __call__(self, *args, **kwargs):  # pragma: no cover - trivial
        return args, kwargs


def _make_version(version: str):
    return {
        'version': version,
        'description': f'Demo function v{version}',
        'function': DummyFunction(),
        'metadata': {'version': version}
    }


function_catalog = {
    'demo_function': {
        '1': _make_version('1'),
        '2': _make_version('2')
    }
}
