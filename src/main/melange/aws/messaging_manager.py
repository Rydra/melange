import boto3


class MessagingManager:
    @staticmethod
    def declare_topic(topic_name):
        sns = boto3.resource('sns')
        topic = sns.create_topic(Name=topic_name)
        return topic

    @staticmethod
    def declare_queue(queue_name, sns_topic_to_bind=None):
        sqs_res = boto3.resource('sqs')
        sqs_cli = boto3.client('sqs')
        queue = sqs_res.create_queue(QueueName=queue_name)
        queue_arn = sqs_cli.get_queue_attributes(QueueUrl=queue.url,
                                                 AttributeNames=['QueueArn'])['Attributes']['QueueArn']

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
            """.format(queue_arn, sns_topic_to_bind.arn)
            queue.set_attributes(Attributes={'Policy': policy})

            sns_topic_to_bind.subscribe(Protocol='sqs', Endpoint=queue_arn)

        return queue, queue_arn
