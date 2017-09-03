import json


def parse_event_from_sns(sns_message, event_serializer):
    content = sns_message['Records'][0]['Sns']

    # TODO: Add message signature validation logic

    if 'Message' in content:
        content = content['Message']

    try:
        deserialized_dict = json.loads(content)
    except:
        raise Exception('The message content is not a valid json')

    return event_serializer.deserialize(deserialized_dict)
