"""
Reads vehicle status from BMW connected drive portal.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.bmw_connected_drive/
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from . import DOMAIN as PANDORA_DOMAIN
from homeassistant.const import STATE_OFF, STATE_ON


DEPENDENCIES = ['pandora']

_LOGGER = logging.getLogger(__name__)


SENSOR_TYPES = {
    'connection_state': ["Connection state", "", "",  'connectivity', False, "online", 0x00000001, 0x00000000],
    'engine_state': ["Engine state", "mdi:fan", "mdi:fan-off", "", True, "bit_state_1", 0x00000004, 0x00000000],
    'lock_state': ["Lock", "mdi:lock-open", "mdi:lock", "lock", True, "bit_state_1", 0x00000001, 0x00000001],
    'left_front_door': ["Left Front Door", "mdi:car-door", "mdi:car-door", "door", True, "bit_state_1", 0x00200000, 0x00000000],
    'right_front_door': ["Right Front Door", "mdi:car-door", "mdi:car-door", "door", True, "bit_state_1", 0x00400000, 0x00000000],
    'left_back_door': ["Left Back Door", "mdi:car-door", "mdi:car-door", "door", True, "bit_state_1", 0x00800000, 0x00000000],
    'right_back_door': ["Right Back Door", "mdi:car-door", "mdi:car-door", "door", True, "bit_state_1", 0x01000000, 0x00000000],
    'trunk': ["Trunk", "mdi:car-back", "mdi:car-back", "door", True, "bit_state_1", 0x02000000, 0x00000000],
    'hood': ["Hood", "mdi:car", "mdi:car", "door", True, "bit_state_1", 0x04000000, 0x00000000],
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the BMW sensors."""
    accounts = hass.data[PANDORA_DOMAIN]
    _LOGGER.debug('Found Pandora accounts: %s',
                  ', '.join([a.name for a in accounts]))
    devices = []
    for account in accounts:
        for vehicle in account.account.vehicles:
            for parameter, _ in sorted(SENSOR_TYPES.items()):
                name = SENSOR_TYPES[parameter][0]
                icon_on = SENSOR_TYPES[parameter][1]
                icon_off = SENSOR_TYPES[parameter][2]
                device_class = SENSOR_TYPES[parameter][3]
                state_sensitive = SENSOR_TYPES[parameter][4]
                attribute = SENSOR_TYPES[parameter][5]
                bit_mask = SENSOR_TYPES[parameter][6]
                xor_mask = SENSOR_TYPES[parameter][7]

                device = PandoraSensor(account, 
                                       vehicle,
                                       name,
                                       icon_on,
                                       icon_off,
                                       device_class,
                                       attribute,
                                       bit_mask,
                                       xor_mask,
                                       state_sensitive)
                devices.append(device)

    add_entities(devices, True)


class PandoraSensor(BinarySensorDevice):
    """Representation of a BMW vehicle binary sensor."""

    def __init__(self, account, vehicle, name: str, icon_on: str, icon_off: str, device_class: str, attribute: str, bit_mask: int, xor_mask: int, state_sensitive: bool):
        """Constructor."""
        self._vehicle = vehicle
        self._account = account
        self._name = '{} {}'.format(self._vehicle.name, name)
        self._state = None
        self._icon_on = icon_on
        self._icon_off = icon_off
        self._device_class = device_class
        self._attribute = attribute
        self._bit_mask = bit_mask
        self._xor_mask = xor_mask
        self._state_sensitive = state_sensitive

    @property
    def should_poll(self) -> bool:
        """Return False.

        Data update is triggered from BMWConnectedDriveEntity.
        """
        return False

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return self._name

    @property
    def device_class(self) -> str:
        """Return the class of the binary sensor."""
        return self._device_class

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    @property
    def icon(self) -> str:
        """Return the icon of the binary sensor."""
        if self._state:
            return self._icon_on
        else:
            return self._icon_off

    @property
    def is_on(self) -> bool:
        """Return the state of the binary sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            'car': self._vehicle.name
        }

    def update(self):
        """Read new state data from the library."""
        vehicle_state = self._vehicle.state

        if vehicle_state.online == 1 or self._state_sensitive == False:
            self._available = True
            if getattr(vehicle_state, self._attribute) & self._bit_mask ^ self._xor_mask:
                self._state = True
            else:
                self._state = False
        else:
            self._available = False

    def update_callback(self):
        """Schedule a state update."""
        self.schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Add callback after being added to hass.

        Show latest data after startup.
        """
        self._account.add_update_listener(self.update_callback)
