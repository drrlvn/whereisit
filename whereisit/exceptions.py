class PostOfficeError(Exception):
    def __init__(self, tracking, json):
        super().__init__(f'{tracking}: {json}')
        self.tracking = tracking
        self.json = json
