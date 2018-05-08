import json

from melange.messaging import EventSerializer


def parse_event_from_sns(sns_message):
    content = sns_message['Records'][0]['Sns']

    # TODO: Add message signature validation logic

    if 'Message' in content:
        content = content['Message']

    try:
        deserialized_dict = json.loads(content)
    except:
        raise Exception('The message content is not a valid json')

    return EventSerializer.instance().deserialize(deserialized_dict)
