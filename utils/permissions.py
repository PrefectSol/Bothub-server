class Permissions:
    def __init__(self, is_host_manage: bool = False, 
                       is_bot_manage: bool = False,
                       is_view: bool = False):
        self._permissions = (is_host_manage, is_bot_manage, is_view)
                
        
    def get_host_permission(self) -> bool:
        return self._permissions[0]
    

    def get_bot_permission(self) -> bool:
        return self._permissions[1]
    
    
    def get_view_permission(self) -> bool:
        return self._permissions[2]
    