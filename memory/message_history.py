import os
import json
from langchain_core.messages import BaseMessage
from langchain_core.messages import messages_from_dict
from langchain_core.messages.base import messages_to_dict

class JSONMessageHistory:
    def __init__(self, root_path: str):
        """
        Initialize the folder structure to store memory and db.
        Take root folder path for storage from user and create /memory and /db inside
        """
        self.data_directory = root_path
        self.memory_directory = os.path.join(self.data_directory, "memory")
        self.db_directory = os.path.join(self.data_directory, "db")
        
        os.makedirs(self.data_directory, exist_ok=True)
        os.makedirs(self.memory_directory, exist_ok=True)
        os.makedirs(self.db_directory, exist_ok=True)

    def load(self, file_name: str) -> list[BaseMessage | None]:
        """
        Given the file path for a json file,
        load the file and return the list of messages in that file
        """
        history = None
        file_path = os.path.join(self.memory_directory, file_name)
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                pass
            history = []

        with open(file_path, "r") as f:
            try:
                history = messages_from_dict(json.load(f))
            except json.JSONDecodeError:
                history = []

        return history
    
    def save(self, file_name:str, messages: list[BaseMessage]) -> bool:
        """
        Given a list of Human and AI messages, save it to the appropriate json file.
        If saved successfully, return True, else return False
        """
        file_path = os.path.join(self.memory_directory, file_name)
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            # create a new file if not already exists
            with open(file_path, "w") as f:
                pass
            # return True
        
        message_history = self.load(file_name)
        message_history.extend(messages)
        messages_dict = messages_to_dict(message_history)

        # write the messages dictionary to json file
        with open(file_path, "w") as f:
            json.dump(messages_dict, f)

        return True
