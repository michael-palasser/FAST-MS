

class AlreadyPresentException(Exception):
    def __init__(self, element):
        self.element = element

    def __str__(self):
        return(repr(self.element + "already present"))

class InvalidInputException(Exception):
    def __init__(self, element, message):
        self.element = element
        self.message = message

    def __str__(self):
        return(repr("Invalid Input: " + self.element + ", " + self.message))