from typing import Any, Optional

from melange.drivers.driver_manager import DriverManager
from melange.drivers.interfaces import MessagingDriver, Topic


class MessagingFactory:
    def __init__(self, driver: Optional[MessagingDriver] = None) -> None:
        self._driver = driver or DriverManager().get_driver()

    def init_queue(
        self,
        queue_name: str,
        *topic_names_to_subscribe: str,
        dlq_name: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        topics = [self.init_topic(t) for t in topic_names_to_subscribe]

        self._driver.declare_queue(
            queue_name,
            *topics,
            dead_letter_queue_name=dlq_name,
            filter_events=kwargs.get("filter_events")
        )

    def init_topic(self, topic_name: str) -> Topic:
        return self._driver.declare_topic(topic_name)
