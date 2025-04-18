from abc import ABC, abstractmethod
from langchain_core.messages import BaseMessage

class MessageHistory(ABC):
    """
    Abstract class for message history.
    Any message history class implementing this abstract class must define the load and save methods
    """
    @abstractmethod
    def load(self, path: str) -> list[BaseMessage]:
        """
        Takes a chat id and loads all messages corresponding to that chat id as a list of BaseMessage objects
        """
        pass

    @abstractmethod
    def save(self, path: str, new_message: list[BaseMessage]) -> bool:
        """
        Takes a chat id and new Human + AI Message pair as a list and saves it to persistent memory.
        Returns True on success and False otherwise
        """
        pass

    @abstractmethod
    def delete(file_name: str) -> bool:
        """
        Takes a chat id and deletes the memory file and db file associated with that chat.
        Returns True on success and False otherwise.
        """
        pass