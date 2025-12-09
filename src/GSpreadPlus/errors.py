'''GSpreadPlus Custom Errors'''
class IdentificationError(Exception):
    '''Raised when identification of a resource fails'''

class SetupError(Exception):
    '''Raised when setup or connection to the google document fails'''
