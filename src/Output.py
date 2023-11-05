from io import TextIOWrapper


class AbstractOutput(object):
    def __init__(self):
        self.data = {"traveltimes": [],
                     "avgspeeds": [],
                     "p": [],
                     "numcars": []}

    def write(self, data: str):
        pass

    def save(self, d):
        """Deprecated"""
        self.data.append(d)


class FileOutput(AbstractOutput):
    def __init__(self, file: TextIOWrapper):
        super().__init__()
        self.file = file

    def write(self, data: str):
        super().write(data)
        self.file.write(data)
        





