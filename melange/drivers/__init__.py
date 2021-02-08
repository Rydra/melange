from melange.drivers.driver_manager import DriverManager


def configure_exchange(driver_name, **kwargs):
    DriverManager().use_driver(
        driver_name=driver_name,
        wait_time_seconds=kwargs.get("wait_time_seconds", 10),
        visibility_timeout=kwargs.get("visibility_timeout", 10),
    )
