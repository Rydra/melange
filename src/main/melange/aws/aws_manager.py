import json

import boto3


class AWSManager:
    @staticmethod
    def declare_topic(topic_name):
        sns = boto3.resource('sns')
        topic = sns.create_topic(Name=topic_name)
        return topic

    @staticmethod
    def declare_queue(queue_name, sns_topic_to_bind=None, dead_letter_queue_name=None):
        sqs_res = boto3.resource('sqs')

        queue = sqs_res.create_queue(QueueName=queue_name)

        if sns_topic_to_bind:
            policy = """
            {{
              "Version": "2012-10-17",
              "Id": "sqspolicy",
              "Statement": [
                {{
                  "Sid": "First",
                  "Effect": "Allow",
                  "Principal": "*",
                  "Resource":"{}",
                  "Action": "sqs:SendMessage",
                  "Condition": {{
                    "ArnEquals": {{
                      "aws:SourceArn": "{}"
                    }}
                  }}
                }}
              ]
            }}
            """.format(queue.attributes['QueueArn'], sns_topic_to_bind.arn)
            queue.set_attributes(Attributes={'Policy': policy})
            sns_topic_to_bind.subscribe(Protocol='sqs', Endpoint=queue.attributes['QueueArn'])

        dead_letter_queue = None
        if dead_letter_queue_name:
            dead_letter_queue = sqs_res.create_queue(QueueName=dead_letter_queue_name)

            redrive_policy = {
                'deadLetterTargetArn': dead_letter_queue.attributes['QueueArn'],
                'maxReceiveCount': '4'
            }

            queue.set_attributes(Attributes={'RedrivePolicy': json.dumps(redrive_policy)})

        return queue, dead_letter_queue
