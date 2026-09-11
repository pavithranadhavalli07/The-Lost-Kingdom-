import datetime

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class BaseAgent:
    """
    Base class for all autonomous AI agents in the system.
    Provides standard lifecycle, status tracking, logging, and state serialization.
    """
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.status = "Active"
        self.last_action = "Initialized and ready"
        self.last_updated = utcnow()
        self.metadata = {}

    def log_action(self, action_summary, meta=None):
        self.last_action = action_summary
        self.last_updated = utcnow()
        if meta:
            self.metadata.update(meta)

    def process(self, event_name, payload, shared_state):
        """
        Execute agent logic in response to system/player events.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def to_dict(self):
        return {
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "last_action": self.last_action,
            "last_updated": self.last_updated.strftime("%H:%M:%S"),
            "metadata": self.metadata
        }
