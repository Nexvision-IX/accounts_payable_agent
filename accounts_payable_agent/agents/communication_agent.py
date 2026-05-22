from .base import BaseAgent

class CommunicationAgent(BaseAgent):
    """Communication agent stub — sends notifications / creates tickets."""
    def __init__(self):
        super().__init__("CommunicationAgent")

    def run(self, message: str, recipients: list) -> dict:
        # For demo, just return a summary
        return {"sent": True, "recipients": recipients, "message": message}
