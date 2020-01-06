"""Support for Kodak Smart Home."""
from datetime import timedelta
import logging

from kodaksmarthome import KodakSmartHome
import voluptuous as vol

from homeassistant.const import (
    CONF_PASSWORD,
    CONF_REGION,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import track_time_interval

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Data provided by Kodak Smart Home Portal"

NOTIFICATION_ID = "kodaksmarthome_notification"
NOTIFICATION_TITLE = "Kodak Smart Home Setup"

DATA_KODAKSMARTHOME_CAMS = "kodaksmarthome_cams"

DOMAIN = "kodaksmarthome"
DEFAULT_CACHEDB = ".kodaksmarthome_cache.pickle"
DEFAULT_ENTITY_NAMESPACE = "kodaksmarthome"
SIGNAL_UPDATE_KODAKSMARTHOME = "kodaksmarthome_update"

SCAN_INTERVAL = timedelta(seconds=10)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_REGION): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up the Kodak Smart Home Portalponent."""
    conf = config[DOMAIN]
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]
    region = conf[CONF_REGION]
    scan_interval = conf[CONF_SCAN_INTERVAL]

    try:
        hass_kodak = KodakSmartHome(username=username, password=password, region=region)
        hass_kodak.connect()
        if not hass_kodak.is_connected:
            return False

        hass_kodak.disconnect()

        hass.data[DATA_KODAKSMARTHOME_CAMS] = hass_kodak

    except ConnectionError as ex:
        _LOGGER.error("Unable to connect to Kodak Smart Home service: %s", str(ex))
        hass.components.persistent_notification.create(
            "Error: {}<br />"
            "You will need to restart hass after fixing."
            "".format(ex),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID,
        )
        return False

    def service_hub_refresh(service):
        hub_refresh()

    def timer_hub_refresh(event_time):
        hub_refresh()

    def hub_refresh():
        """Call hass_kodak to refresh information."""
        _LOGGER.debug("Updating Kodak Smart Home Hub component")

        hass_kodak.connect()
        dispatcher_send(hass, SIGNAL_UPDATE_KODAKSMARTHOME)
        hass_kodak.disconnect()

    # register service
    hass.services.register(DOMAIN, "update", service_hub_refresh)

    # register scan interval for kodak smart home
    track_time_interval(hass, timer_hub_refresh, scan_interval)

    return True
