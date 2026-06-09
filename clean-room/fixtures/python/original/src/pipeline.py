"""Pipeline entry point — wires SopLoader → Stage1Runner correctly."""

from sop_loader import SopLoader
from stage1 import Stage1Runner
from call_state import CallSopState


def main(session, store, client) -> dict:
    loader = SopLoader(store)
    runner = Stage1Runner(client)
    state = CallSopState()

    sop_text = loader.load_for_session(session)
    result = runner.run(session, client_sop_text=sop_text)
    for chunk in session.chunks:
        state.apply_alerts(chunk)
    return {"result": result, "state": state}
