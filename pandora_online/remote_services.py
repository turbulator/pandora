"""Trigger remote services on a vehicle."""

from enum import Enum
import datetime
import logging
import time
import requests


_LOGGER = logging.getLogger(__name__)

#: time in seconds to wait before updating the vehicle state from the server
_UPDATE_AFTER_REMOTE_SERVICE_DELAY = 10



class _Services(Enum):
    """Enumeration of possible services to be executed."""
    REMOTE_SEAT_HEATER = 'ENABLE_HEATER'


class RemoteServiceStatus:  # pylint: disable=too-few-public-methods
    """Wraps the status of the execution of a remote service."""

    def __init__(self, response: dict):
        """Construct a new object from a dict."""
        status = response['executionStatus']
        self.state = ExecutionState(status['status'])
        self.event_id = status['eventId']

    @staticmethod
    def _parse_timestamp(timestamp: str) -> datetime.datetime:
        """Parse the timestamp format from the response."""
        offset = int(timestamp[-3:])
        time_zone = datetime.timezone(datetime.timedelta(hours=offset))
        result = datetime.datetime.strptime(timestamp[:-3], TIME_FORMAT)
        result.replace(tzinfo=time_zone)
        return result


class RemoteServices:
    """Trigger remote services on a vehicle."""

    def __init__(self, account, vehicle):
        """Constructor."""
        self._account = account
        self._vehicle = vehicle

    def trigger_remote_seat_heater(self) -> RemoteServiceStatus:
        """Trigger the vehicle to sound its horn.

        A state update is NOT triggered after this, as the vehicle state is unchanged.
        """
        _LOGGER.debug('Triggering remote seat heater')
        # needs to be called via POST, GET is not working
        result = self._trigger_remote_service(_Services.REMOTE_SEAT_HEATER)
        self._trigger_state_update()
        return result

    def _trigger_remote_service(self, service_id: _Services) -> requests.Response:
        """Trigger a generic remote service.

        You can choose if you want a POST or a GET operation.
        """
        data = {
            'id': self._vehicle.id,
            'command': '33'}

        response = self._account.send_request('https://p-on.ru/api/devices/command', data=data, post=True, tolerant=True)

        return response


    def _trigger_state_update(self) -> None:
        time.sleep(_UPDATE_AFTER_REMOTE_SERVICE_DELAY)
        self._account.update_vehicle_states()
