from typing import ClassVar, Mapping, Any, Dict, Optional, List, cast
from typing_extensions import Self

from viam.module.types import Reconfigurable
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily

from viam.components.sensor import Sensor
from viam.logging import getLogger

import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP

LOGGER = getLogger(__name__)

class mcp3xxx(Sensor, Reconfigurable):
    # Defines new model's colon-delimited-triplet
    MODEL: ClassVar[Model] = Model(ModelFamily("viamlabs", "sensor"), "mcp300x")

    # Creates class parameters
    sensor_pin: int

    # Constructor
    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        sensor = cls(config.name)
        sensor.reconfigure(config, dependencies)
        return sensor

    # Validates JSON Configuration
    @classmethod
    def validate(cls, config: ComponentConfig):
        sensor_pin = config.attributes.fields["sensor_pin"].number_value
        channel_map = config.attributes.fields["channel_map"].struct_value

        if sensor_pin == "":
            raise Exception("A sensor_pin must be defined")
        
        if channel_map == "":
            raise Exception("Channel map must be defined, refers to sensor type and which channel it connects to")

        return

    # Handles attribute reconfiguration
    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        # Initializes the resource instance
        self.sensor_pin = int(config.attributes.fields["sensor_pin"].number_value)
        self.channel_map = dict(config.attributes.fields["channel_map"].struct_value)
        LOGGER.info(f"Channel map is {self.channel_map}")
        return

    """ Implements the methods the Viam RDK defines for the Sensor API (rdk:components:sensor) """
    # Implements the Viam Sensor API's get_readings() method
    async def get_readings(
        self, *, extra: Optional[Mapping[str, Any]] = None, timeout: Optional[float] = None, **kwargs
    ) -> Mapping[str, Any]:
        """
        Obtains the measurements/data specific to this sensor.
        Returns:
            Mapping[str, Any]: The measurements. Can be of any type.
        """

        # Dictionary 
        readings = {}

        # Sensor Pin Logic
        # Creates the SPI bus
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

        # Creates the cs (chip select) with a gpio pin variable, we are using 24 GPIO 8 (SPI Chip Select 0), so 8 for the config
        my_pin = f"D{self.sensor_pin}"
        # utils.py file maps the pin using map_pin_gpio[24] = 8
        cs = digitalio.DigitalInOut(getattr(board, my_pin))

        # Creates the MCP3008 object, works with MCP3002 and MCP3004 since it is all encompassing
        mcp = MCP.MCP3008(spi, cs)

        # Iterates over values
        for label, channel in self.channel_map.items():
            LOGGER.info(f"loop channel is {channel} and loop label is {label}")
            # Create an analog input channel
            chan = int(channel)
            readings[label] = mcp.read(chan)

        # Return readings
        return readings
