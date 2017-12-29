import json
import uuid

import boto3


class MessagingManager:
    @staticmethod
    def declare_topic(topic_name):
        sns = boto3.resource('sns')
        topic = sns.create_topic(Name=topic_name)
        return topic

    @staticmethod
    def declare_queue(queue_name, *sns_topic_to_bind):
        sqs_res = boto3.resource('sqs')
        sqs_cli = boto3.client('sqs')
        queue = sqs_res.create_queue(QueueName=queue_name)
        queue_arn = sqs_cli.get_queue_attributes(QueueUrl=queue.url,
                                                 AttributeNames=['QueueArn'])['Attributes']['QueueArn']

        if sns_topic_to_bind:
            statements = []
            for topic in sns_topic_to_bind:
                statement = {
                            'Sid': 'Sid{}'.format(uuid.uuid4()),
                            'Effect': 'Allow',
                            'Principal': '*',
                            'Resource': queue.attributes['QueueArn'],
                            'Action': 'sqs:SendMessage',
                            'Condition': {
                                'ArnEquals': {
                                    'aws:SourceArn': topic.arn
                                }
                            }
                        }

                statements.append(statement)
                topic.subscribe(Protocol='sqs', Endpoint=queue_arn)

            policy = {
                'Version': '2012-10-17',
                'Id': 'sqspolicy',
                'Statement': statements
            }

            queue.set_attributes(Attributes={'Policy': json.dumps(policy)})

        return queue, queue_arn
