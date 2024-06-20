

class AlreadyPresentException(Exception):
    '''
    Thrown when the user tries to save a unique value in the database which is already present
    '''
    def __init__(self, element):
        '''
        :param (str) element: corresponding value which is already stored in the database
        '''
        self.element = element

    def __str__(self):
        return(repr(self.element + "already present"))

class InvalidInputException(Exception):
    '''
    Thrown if the user makes an invalid input
    '''
    def __init__(self, element, message):
        '''
        :param (str) element: invalid element
        :param (str) message:
        '''
        self.element = str(element)
        self.message = str(message)

    def __str__(self):
        return(repr("Invalid Input: " + self.element + " <br>" + self.message))

    def getMessage(self):
        return self.message


class InvalidIsotopePatternException(Exception):
    '''
    Thrown if the stored isotope pattern is different to the calculated one
    '''
    def __init__(self, fragment, message):
        '''
        :param (str) fragment: name of the corresponding fragment
        :param (str) message:
        '''
        self.fragment = fragment
        self.message = message

    def __str__(self):
        return(repr("Stored Isotope Pattern is deprecated: " + self.fragment + " " + self.message))


class CanceledException(Exception):
    '''
    Thrown if the user pressed "Cancel" when editing sequences, fragmentations,....
    '''
    def __init__(self, message):
        '''
        :param (str) message:
        '''
        self.message = message
