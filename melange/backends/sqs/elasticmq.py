from typing import Any

from melange.backends.sqs.sqs_backend import BaseSQSBackend


class LocalSQSBackend(BaseSQSBackend):
    """
    Local backend to use with elasticMQ
    """

    def __init__(self, **kwargs: Any) -> None:

        super().__init__(
            extra_settings=dict(
                endpoint_url=f"{kwargs.get('host', 'localhost')}:{kwargs.get('port', 4566)}",
                region_name="us-east-1",
                aws_secret_access_key="x",
                aws_access_key_id="x",
                use_ssl=False,
            ),
            sns_settings=dict(
                endpoint_url=f"{kwargs.get('sns_host', 'localhost')}:{kwargs.get('sns_port', 4566)}",
                aws_secret_access_key="x",
                aws_access_key_id="x",
                region_name="us-east-1",
                use_ssl=False,
            ),
            **kwargs,
        )
