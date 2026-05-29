from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """
    Base class for all Agent tools.

    Every tool should define:
    - name
    - description
    - input_schema
    - run()
    """

    name: str
    description: str
    input_schema: dict[str, Any]

    @abstractmethod
    def run(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        pass