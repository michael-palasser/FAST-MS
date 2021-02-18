

class AlreadyPresentException(Exception):
    def __init__(self, element):
        self.element = element

    def __str__(self):
        return(repr(self.element + "already present"))

class UnvalidInputException(Exception):
    def __init__(self, element, message):
        self.element = element
        self.message = message

    def __str__(self):
        return(repr("Unvalid Input: " + self.element + ", " + self.message))



class UnvalidIsotopePatternException(Exception):
    def __init__(self, fragment, message):
        self.fragment = fragment
        self.message = message

    def __str__(self):
        return(repr("Stored Isotope Pattern is deprecated: " + self.fragment + " " + self.message))