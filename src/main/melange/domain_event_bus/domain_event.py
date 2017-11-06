from datetime import datetime


class DomainEvent:
    def __init__(self, occurred_on=datetime.now()):
        self.occurred_on = occurred_on

    def get_occurred_on(self):
        return self.occurred_on
