import json

from melange.drivers.aws import parse_event_from_sns


class TestUtils:

    def test_parse_event_from_sns(self):
        sns_event = {
            'Records': [
                {
                    'Sns': {
                        'Message': json.dumps({'event_type_name': 'some_name', 'value': 'some_message'})
                    }
                }
            ]
        }

        parsed_event = parse_event_from_sns(sns_event)

        assert parsed_event['value'] == 'some_message'
