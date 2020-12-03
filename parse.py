class DbtLogParser:
    def __init__(self):
        self.set_environment()

    def set_environment(self, line_no: int = None, line: str = None):
        self.line_no = line_no
        self.line = line



