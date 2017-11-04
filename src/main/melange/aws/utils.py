import json

from melange.aws.event_serializer import EventSerializer


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


def get_fully_qualified_name(obj):
    return obj.__module__ + "." + obj.__class__.__name__
