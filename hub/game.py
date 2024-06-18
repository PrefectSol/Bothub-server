from abc import ABC, abstractmethod


class Game(ABC):
    def __init__(self):
        self._players_count = None
        self._is_playing = None
        
        
    @property
    def players_count(self):
        return self._players_count


    @players_count.setter
    def players_count(self, count):
        self._players_count = count


    @property
    def is_playing(self):
        return self._is_playing


    @is_playing.setter
    def is_playing(self, status):
        self._is_playing = status

        
    @abstractmethod
    def set_state(self):
        pass
    
    
    @abstractmethod
    def get_state(self) -> dict:
        pass
    

    @abstractmethod
    def add_client(self, client_info, bot_impl) -> bool:
        pass
    
    
    @abstractmethod
    def step(self) -> None:
        pass
    
    
    @abstractmethod
    def get_log(self) -> str:
        pass