from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    """
    Base class for all AP agents.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic and return updated context.
        """
        pass

    def validate_input(self, context: Dict[str, Any]):
        """
        Optional pre-validation.
        Override if required.
        """
        return

    def log(self, msg: str):
        print(f"[{self.name}] {msg}")

    def execute(self, context: Dict[str, Any]):

        self.validate_input(context)

        self.log("Started")

        try:
            output = self.run(context)

            output.setdefault("audit_log", []).append(
                {
                    "agent": self.name,
                    "status": "SUCCESS"
                }
            )

            return output

        except Exception as e:

            context.setdefault("audit_log", []).append(
                {
                    "agent": self.name,
                    "status": "FAILED",
                    "error": str(e)
                }
            )

            raise