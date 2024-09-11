from abc import ABC, abstractmethod


class ABCBot(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def set_state(self, state: dict = None) -> dict:
        pass

    @abstractmethod
    def get_action(self, state) -> dict:
        pass

