import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ai_service

print("model=", os.getenv("GEMINI_MODEL"))
print("key_set=", bool(os.getenv("GEMINI_API_KEY")))

prompt = (
    'Return JSON only: '
    '{"version":1,"tone":"professional","business_post":"Thanks for your feedback."}'
)

try:
    out = ai_service._call_gemini(prompt)
    print("raw_out=", out[:500])
except Exception as exc:
    print("gemini_error=", repr(exc))
    traceback.print_exc()
