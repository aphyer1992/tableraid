import uuid

class EventManager:
    def __init__(self):
        self.listeners = {}

    def register(self, event_name, callback):
        listener_id = uuid.uuid4()
        self.listeners.setdefault(event_name, []).append((listener_id, callback))
        return listener_id

    def deregister(self, event_name, listener_id):
        if event_name in self.listeners:
            self.listeners[event_name] = [
                (lid, cb) for (lid, cb) in self.listeners[event_name] if lid != listener_id
            ]

    def trigger(self, event_name, *args, **kwargs):
        for _, callback in self.listeners.get(event_name, []):
            callback(*args, **kwargs)