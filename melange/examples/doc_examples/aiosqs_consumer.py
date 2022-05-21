import json
from typing import Any

from anyio import run

from melange.aio import AIOSQSConsumer
from melange.serializers import JsonSerializer

serializer = JsonSerializer()


def _(v: str) -> Any:
    value = json.loads(v)
    data = serializer.deserialize(value["data"], value["manifest"])
    return data


host = "http://localhost"
port = 4566

consumer = AIOSQSConsumer(
    "melangetutorial-queue",
    value_deserializer=_,
    endpoint_url=f"{host}:{port}",
    region_name="us-east-1",
    aws_secret_access_key="x",
    aws_access_key_id="x",
    use_ssl=False,
)


async def main() -> None:
    async with consumer:
        print("Listening...")
        async for message in consumer:
            print(message)


if __name__ == "__main__":
    run(main)
