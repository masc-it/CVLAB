
from cvlab.model.app import App

class Component(object):
    """
        
        Generic component class.

    """

    def __init__(self, app: App) -> None:
        self.app = app

        self.project = self.app.project
        self.io = app.io
        self.viewport = app.viewport
    
    def main(self):
        raise NotImplementedError()

