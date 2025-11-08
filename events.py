import uuid
from game_events import GameEvent

class EventManager:
    def __init__(self):
        self.listeners = {}

    def _normalize_event_name(self, event_name):
        """Convert event name to string, supporting both GameEvent enum and string inputs."""
        if isinstance(event_name, GameEvent):
            return event_name.value
        return event_name

    def register(self, event_name, callback):
        """Register a callback for an event. Accepts either GameEvent enum or string."""
        normalized_name = self._normalize_event_name(event_name)
        listener_id = uuid.uuid4()
        self.listeners.setdefault(normalized_name, []).append((listener_id, callback))
        return listener_id

    def deregister(self, event_name, listener_id):
        """Deregister a callback. Accepts either GameEvent enum or string."""
        normalized_name = self._normalize_event_name(event_name)
        if normalized_name in self.listeners:
            self.listeners[normalized_name] = [
                (lid, cb) for (lid, cb) in self.listeners[normalized_name] if lid != listener_id
            ]

    def trigger(self, event_name, *args, **kwargs):
        """Trigger an event. Accepts either GameEvent enum or string."""
        normalized_name = self._normalize_event_name(event_name)
        for _, callback in self.listeners.get(normalized_name, []):
            callback(*args, **kwargs)