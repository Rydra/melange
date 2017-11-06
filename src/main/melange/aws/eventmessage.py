from datetime import datetime

from marshmallow import Schema, fields


class EventSchema(Schema):
    event_type_name = fields.Str()
    occurred_on = fields.DateTime()


class EventMessage:

    # A constant that subscriber can use in their "listens_to" events to
    # tell they are interested in all the events that happen on their topic
    ALL = 'ALL'

    event_type_name = 'Default'

    def __init__(self, occurred_on=datetime.now()):
        self.occurred_on = occurred_on
        self.event_type_name = self.event_type_name

    def get_occurred_on(self):
        return self.occurred_on

    def get_event_type_name(self):
        return self.event_type_name
