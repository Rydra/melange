from typing import Any

from melange.backends.sqs.sqs_backend import BaseSQSBackend


class ElasticMQBackend(BaseSQSBackend):
    """
    Local backend to use with elasticMQ
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            extra_settings=dict(
                endpoint_url=f"{kwargs.get('host', 'localhost')}:{kwargs.get('port', 9324)}",
                region_name="elasticmq",
                aws_secret_access_key="x",
                aws_access_key_id="x",
                use_ssl=False,
            ),
            **kwargs,
        )
