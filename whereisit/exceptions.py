class PostOfficeError(Exception):
    def __init__(self, tracking, json):
        super().__init__('{}: {}'.format(tracking, json))
        self.tracking = tracking
        self.json = json
