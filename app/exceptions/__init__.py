""" Script Exceptions """

class Error(Exception):
    """ Base class for all  exceptions """
    def __init__(self, message=None, status_code=400):
        # Call the base class constructor with the parameters it needs
        super().__init__()
        self.message = message
        self.status = status_code

    def __str__(self):
        return self.message

class WebsiteNotFoundError(Error):
    """Thrown when requested website does not exist"""
    code = 404

class ShortestPathNotFoundError(Error):
    """Thrown when requested path does not exist"""
    code = 401