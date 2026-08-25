"""Small helpers shared by the CLI-based modules (app/moderation.py,
app/generation.py) -- both shell out to the `claude` Code CLI and need to
pull structured JSON back out of its plain-text stdout.
"""

import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    """Pull the first {...} or [...] JSON block out of a model response."""
    match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", text)
    if not match:
        raise ValueError(f"No JSON found in model response: {text[:200]}")
    return json.loads(match.group(0))
