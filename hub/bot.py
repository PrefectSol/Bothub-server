from abc import ABC, abstractmethod

class Bot(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def set_state(self, state : dict=None) -> dict:
        pass

    @abstractmethod
    def make_action(self, state : dict) -> dict:
        pass