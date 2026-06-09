"""Stage 1 runner — BROKEN: prompt shrunk to 4 lines (B pattern)."""

STAGE1_SYSTEM_PROMPT = """You are the Stage 1 classifier.
Classify the call.
Return JSON.
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
