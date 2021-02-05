from typing import Dict, Any, List


class Topic:
    def subscribe(self, *args, **kwargs):
        pass

    def publish(self, *args, **kwargs):
        pass

    def delete(self):
        pass


class Queue:
    @property
    def attributes(self) -> Dict:
        pass

    def set_attributes(self, *args, **kwargs) -> None:
        pass

    def receive_messages(self, *args, **kwargs) -> List[Any]:
        pass

    def delete(self):
        pass
