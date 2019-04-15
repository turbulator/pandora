"""
Reads vehicle status from BMW connected drive portal.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.bmw_connected_drive/
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.components.pandora import DOMAIN as PANDORA_DOMAIN
from homeassistant.const import STATE_OFF, STATE_ON


DEPENDENCIES = ['pandora']

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    'engine_state': ['engine state', 'moving'],
    'connection_state': ['connection state', 'connectivity'],
}

#SENSOR_TYPES_ELEC.update(SENSOR_TYPES)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the BMW sensors."""
    accounts = hass.data[PANDORA_DOMAIN]
    _LOGGER.debug('Found Pandora accounts: %s',
                  ', '.join([a.name for a in accounts]))
    devices = []
    for account in accounts:
        for vehicle in account.account.vehicles:
#            _LOGGER.debug('BMW with a high voltage battery')
            for key, value in sorted(SENSOR_TYPES.items()):
                device = PandoraSensor(account, vehicle, key,
                                                 value[0], value[1])
                devices.append(device)
    add_entities(devices, True)


class PandoraSensor(BinarySensorDevice):
    """Representation of a BMW vehicle binary sensor."""

    def __init__(self, account, vehicle, attribute: str, sensor_name,
                 device_class):
        """Constructor."""
        self._account = account
        self._vehicle = vehicle
        self._attribute = attribute
        self._name = '{} {}'.format(self._vehicle.name, sensor_name)
        self._sensor_name = sensor_name
        self._device_class = device_class
        self._state = None

    @property
    def should_poll(self) -> bool:
        """Return False.

        Data update is triggered from BMWConnectedDriveEntity.
        """
        return False

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def device_class(self):
        """Return the class of the binary sensor."""
        return self._device_class

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes of the binary sensor."""
        vehicle_state = self._vehicle.state
        result = {
            'car': self._vehicle.name
        }

        if self._attribute == 'engine_state':
            if vehicle_state.bit_state_1 & 0x00000004:
                result['engine_state'] = 'running'
            else:
                result['engine_state'] = 'stopped'
        elif self._attribute == 'connection_state':
            if vehicle_state.online == 1:
                result['connection state'] = 'online'
            else:
                result['connection state'] = 'offline'

        return sorted(result.items())


    def update(self):
#        """Read new state data from the library."""
        vehicle_state = self._vehicle.state

        if self._attribute == 'engine_state':
            if vehicle_state.bit_state_1 & 0x00000004:
                self._state = True
            else:
                self._state = False
        elif self._attribute == 'connection_state':
            if vehicle_state.online == 1:
                self._state = True
            else:
                self._state = False


    def update_callback(self):
        """Schedule a state update."""
        self.schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Add callback after being added to hass.

        Show latest data after startup.
        """
        self._account.add_update_listener(self.update_callback)
