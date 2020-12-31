

class AlreadyPresentException(Exception):
    def __init__(self, element):
        self.element = element

    def __str__(self):
        return(repr(self.element + "already present"))