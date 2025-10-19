class InvalidNumberError(Exception):
    """
    Raise exception when numbers are not valid
    """
    def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)

class ReportGenerationError(Exception):
    """
    Raise exception when report generation is failed
    """
    def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)
