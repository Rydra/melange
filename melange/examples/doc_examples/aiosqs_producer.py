import json
from typing import Any

from anyio import run

from melange.aio import AIOSQSProducer
from melange.serializers import JsonSerializer

serializer = JsonSerializer()


def _(v: Any) -> str:
    data = serializer.serialize(v)
    manifest = serializer.manifest(v)
    return json.dumps({"data": data, "manifest": manifest})


host = "http://localhost"
port = 4566

producer = AIOSQSProducer(
    "melangetutorial-queue",
    value_serializer=_,
    endpoint_url=f"{host}:{port}",
    region_name="us-east-1",
    aws_secret_access_key="x",
    aws_access_key_id="x",
    use_ssl=False,
)


async def main() -> None:
    async with producer:
        key = json.dumps({"id": "mykey"}).encode("utf-8")
        event = {"id": "myID", "description": "mytext"}
        await producer.send(value=event, key=key)


if __name__ == "__main__":
    run(main)
