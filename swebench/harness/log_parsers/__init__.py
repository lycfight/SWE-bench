from swebench.harness.log_parsers.javascript import MAP_REPO_TO_PARSER_JS
from swebench.harness.log_parsers.python import MAP_REPO_TO_PARSER_PY, parse_log_pytest
from collections import defaultdict

MAP_REPO_TO_PARSER = defaultdict(
    lambda: parse_log_pytest,
    {**MAP_REPO_TO_PARSER_JS, **MAP_REPO_TO_PARSER_PY}
)


__all__ = [
    "MAP_REPO_TO_PARSER",
]
