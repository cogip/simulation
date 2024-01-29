import httpx
from gpiozero import Button
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont

from cogip.utils import ThreadLoop
from . import logger


class Basket:
    """
    Main basket class.

    Count cherries stored in the basket, display the count on a screen,
    and periodically send current count to the server.
    """
    def __init__(
            self,
            server_url: str,
            refresh_interval: float):
        """
        Class constructor.

        Arguments:
            server_url: server URL
            refresh_interval: Interval between each update of the score (in seconds)
        """
        self.server_url = server_url
        self.refresh_interval = refresh_interval
        self.count: int = 0
        self.sender_loop = ThreadLoop(
            "Count sender loop",
            refresh_interval,
            self.send_count,
            logger=True
        )

        self.button = Button(17, pull_up=True, bounce_time=0.1)
        self.button.when_pressed = self.reset

        self.sensor = Button(27, pull_up=True, bounce_time=0.01)
        self.sensor.when_released = self.add_cherry

        self.display_serial = i2c(port=1, address=0x3C)
        self.display_device = sh1106(self.display_serial)
        self.font = ImageFont.truetype("DejaVuSans.ttf", 80)

    def run(self):
        self.sender_loop.start()
        self.reset()

    def send_count(self):
        try:
            response = httpx.put(f"{self.server_url}/cherries?count={self.count}")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error(f"HTTP Exception for {exc.request.url} - {exc}")

    def reset(self):
        self.count = 0
        self.update_display()

    def add_cherry(self):
        self.count += 1
        self.update_display()

    def update_display(self):
        with canvas(self.display_device) as draw:
            draw.text((12, -15), f"{self.count:02d}", fill="white", font=self.font)
