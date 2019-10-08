"""
Reads vehicle status from BMW connected drive portal.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.bmw_connected_drive/
"""
import logging

from . import DOMAIN as PANDORA_DOMAIN
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.const import (CONF_UNIT_SYSTEM_IMPERIAL, VOLUME_LITERS,
                                 VOLUME_GALLONS, LENGTH_KILOMETERS,
                                 LENGTH_MILES, TEMP_CELSIUS)

DEPENDENCIES = ['pandora']

_LOGGER = logging.getLogger(__name__)

ATTR_TO_HA_METRIC = {
    'mileage': ['mdi:cloud', LENGTH_KILOMETERS],
    'fuel': ['mdi:cloud', 'Prc'],
    'cabin_temp': ['mdi:thermometer', TEMP_CELSIUS],
    'engine_temp': ['mdi:thermometer', TEMP_CELSIUS],
    'out_temp': ['mdi:thermometer', TEMP_CELSIUS],
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    attribute_info = ATTR_TO_HA_METRIC

    accounts = hass.data[PANDORA_DOMAIN]
    _LOGGER.debug('Found Pandora accounts: %s',
                  ', '.join([a.name for a in accounts]))
    devices = []
    attributes = ['mileage', 'fuel', 'cabin_temp', 'engine_temp', 'out_temp']
    for account in accounts:
        for vehicle in account.account.vehicles:
            for attribute in attributes:
                device = PandoraSensor(account, vehicle,
                                       attribute,
                                       attribute_info)
                devices.append(device)

    add_entities(devices, True)


class PandoraSensor(Entity):
    """Representation of a BMW vehicle sensor."""

    def __init__(self, account, vehicle, attribute: str, attribute_info):
        """Constructor."""
        self._vehicle = vehicle
        self._account = account
        self._attribute = attribute
        self._state = None
        self._name = '{} {}'.format(self._vehicle.name, self._attribute)
        self._attribute_info = attribute_info

    @property
    def should_poll(self) -> bool:
        """Return False.

        Data update is triggered from BMWConnectedDriveEntity.
        """
        return False

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor.

        The return type of this call depends on the attribute that
        is configured.
        """
        return self._state

    @property
    def unit_of_measurement(self) -> str:
        """Get the unit of measurement."""
        _, unit = self._attribute_info.get(self._attribute, [None, None])
        return unit

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            'car': self._vehicle.name
        }

    def update(self) -> None:
        """Read new state data from the library."""
        _LOGGER.debug('Updating %s', self._vehicle.name)
        vehicle_state = self._vehicle.state
        self._state = getattr(vehicle_state, self._attribute)

    def update_callback(self):
        """Schedule a state update."""
        self.schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Add callback after being added to hass.

        Show latest data after startup.
        """
        self._account.add_update_listener(self.update_callback)
