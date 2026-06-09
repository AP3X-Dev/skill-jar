"""Stage 1 runner — expects client_sop_text populated by caller."""

STAGE1_SYSTEM_PROMPT = """You are the Stage 1 classifier.

Given a transcript and the client SOP, produce a structured classification
of the call's functional status, outside location, and speaker intent.

Rules:
1. Always honor the SOP's fee-tier table.
2. If the transcript mentions a membership tier, prefer latest-wins semantics.
3. Normalize trade types through the canonical list but pass-through unknown values.
4. If the transcript is ambiguous, fall back to the time-period filter.
5. Emit a JSON object with fields: functional_status, outside_location,
   membership_tier, trade_type, sop_span, and confidence.

Edge cases:
- Empty transcript → return all-null object with confidence 0.
- Unicode surrogate pairs preserved round-trip.
- Ignore filler like "uh" and "um" when computing word_overlap.

Validation:
- sop_span MUST refer to a real line range in the provided client_sop.
- confidence MUST be in [0, 1].
- Reject the response if any field is missing.
"""


class Stage1Runner:
    def __init__(self, client):
        self.client = client

    def run(self, session, client_sop_text: str = "") -> dict:
        if not client_sop_text:
            return {"functional_status": None}
        return self.client.classify(
            prompt=STAGE1_SYSTEM_PROMPT,
            transcript=session.transcript,
            sop=client_sop_text,
        )
