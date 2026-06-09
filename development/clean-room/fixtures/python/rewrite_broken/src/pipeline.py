"""Pipeline — BROKEN: SOP loader never threaded into Stage 1 (E pattern).

Stage1Runner.run is called with client_sop_text="" at every site. The loader
exists, the pipeline instantiates it, but no wire connects the two.
"""

from sop_loader import SopLoader
from stage1 import Stage1Runner
from call_state import CallSopState


def main(session, store, client) -> dict:
    loader = SopLoader(store)
    runner = Stage1Runner(client)
    state = CallSopState()

    # BROKEN: loader created but never called; client_sop_text passed empty.
    result = runner.run(session, client_sop_text="")
    for chunk in session.chunks:
        state.apply_alerts(chunk)
    return {"result": result, "state": state}
