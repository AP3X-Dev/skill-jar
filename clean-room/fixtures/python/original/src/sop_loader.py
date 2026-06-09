"""Loads SOP text for a given session. The original wires this into the pipeline."""


class SopLoader:
    def __init__(self, store):
        self.store = store

    def load_for_session(self, session) -> str:
        return self.store.get(session.client_id, "")
