from datetime import timedelta
import telnetlib

from homeassistant.components.switch import (
    ENTITY_ID_FORMAT, PLATFORM_SCHEMA, SwitchDevice)
from homeassistant.const import (
    CONF_COMMAND_OFF, CONF_COMMAND_ON, CONF_NAME, CONF_PORT, CONF_RESOURCE,
    CONF_SWITCHES, CONF_PASSWORD)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# Set defaults as per ADCP standard
DEFAULT_COMMAND_OFF = "pic_pos_sel {picture_memory}"
DEFAULT_COMMAND_ON = "pic_pos_sel {picture_memory}"
DEFAULT_NAME = 'Projector Picture Memory'
DEFAULT_PORT = 53595

# Validation of the user's configuration
SWITCH_SCHEMA = vol.Schema({
    vol.Required(CONF_COMMAND_OFF, default=DEFAULT_COMMAND_OFF): cv.string,
    vol.Required(CONF_COMMAND_ON, default=DEFAULT_COMMAND_ON): cv.string,
    vol.Required(CONF_RESOURCE): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_PASSWORD): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SWITCHES): vol.Schema({cv.slug: SWITCH_SCHEMA}),
})

# Polling interval for checking on/off (standby) of projector
SCAN_INTERVAL = timedelta(seconds=10)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Find and return projectors controlled by ADCP commands."""
    devices = config.get(CONF_SWITCHES, {})
    switches = []

    for object_id, device_config in devices.items():

        switches.append(
            TelnetSwitch(
                hass,
                object_id,
                device_config.get(CONF_RESOURCE),
                device_config.get(CONF_PORT),
                device_config.get(CONF_PASSWORD),
                device_config.get(CONF_NAME, object_id),
                device_config.get(CONF_COMMAND_ON),
                device_config.get(CONF_COMMAND_OFF),
            )
        )

    if not switches:
        _LOGGER.error("No switches added")
        return

    add_entities(switches)


class TelnetSwitch(SwitchDevice):
    """Representation of a projector as a switch, that can be toggled using ADCP commands."""

    def __init__(self, hass, object_id, resource, port, password, name, command_on, command_off):
        """Initialize the switch."""
        self._hass = hass
        self.entity_id = ENTITY_ID_FORMAT.format(object_id)
        self._resource = resource
        self._port = port
        self._password = password
        self._name = name
        self._command_on = command_on
        self._command_off = command_off
        self._state = None
        self._telnet = None

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        picture_memory = kwargs.get('picture_memory', '1.85_1')
        self._telnet = telnetlib.Telnet(self._resource, self._port)
        self._telnet.read_until(b"Password:")
        self._telnet.write(self._password.encode('ascii') + b"\n")
        self._telnet.read_until(b"OK")
        self._telnet.write((self._command_on.format(picture_memory=picture_memory)).encode('ascii') + b"\n")
        self._telnet.read_until(b"OK")
        self._telnet.close()
        self._state = True

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        picture_memory = kwargs.get('picture_memory', '1.85_1')
        self._telnet = telnetlib.Telnet(self._resource, self._port)
        self._telnet.read_until(b"Password:")
        self._telnet.write(self._password.encode('ascii') + b"\n")
        self._telnet.read_until(b"OK")
        self._telnet.write((self._command_off.format(picture_memory=picture_memory)).encode('ascii') + b"\n")
        self._telnet.read_until(b"OK")
        self._telnet.close()
        self._state = False
