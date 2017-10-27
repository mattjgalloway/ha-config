"""
TiVo support for Home Assistant
"""

import voluptuous as vol

from homeassistant.components.media_player import (
    MEDIA_TYPE_CHANNEL,
    SUPPORT_TURN_ON,
    SUPPORT_TURN_OFF,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PREVIOUS_TRACK,
    PLATFORM_SCHEMA,
    MediaPlayerDevice)
from homeassistant.const import (
    CONF_HOST, CONF_PORT, CONF_NAME, STATE_OFF, STATE_ON, STATE_UNKNOWN)
import homeassistant.helpers.config_validation as cv

import logging

import os
import re
import sys
import time

REQUIREMENTS = ['python-tivo==0.0.1']

DEFAULT_NAME = 'TiVo'

SUPPORT_TIVO = SUPPORT_TURN_ON | \
    SUPPORT_TURN_OFF | SUPPORT_NEXT_TRACK | SUPPORT_PREVIOUS_TRACK

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT): cv.positive_int,
})

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the TiVO platform."""
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)

    add_devices([TiVoDevice(hass, name, host, port)])
    return True

class TiVoDevice(MediaPlayerDevice):
    """Representation of a TiVo device."""

    def __init__(self, hass, name, host, port):
        """Initialize the device."""
        from python_tivo import TiVoConnection
        self._hass = hass
        self._name = name
        self._state = STATE_UNKNOWN
        self._channel = None
        self._device = TiVoConnection(host, port)

    def update(self):
        """Retrieve latest state."""
        from python_tivo import TiVoError
        try:
          channel = self._device.fetchCurrentChannel()
          self._channel = channel

          if channel == None:
            self._state = STATE_OFF
          else:
            self._state = STATE_ON
        except TiVoError:
          _LOGGER.error("TiVo failed to update")
          self._state = STATE_UNKNOWN
          self._channel = None

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    # MediaPlayerDevice properties and methods
    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def media_content_type(self):
        """Return the content type of current playing media."""
        return MEDIA_TYPE_CHANNEL

    @property
    def media_title(self):
        """Title of current playing media."""
        if self._channel:
          return "Channel: {}".format(self._channel)
        else:
          return None

    @property
    def media_channel(self):
        """Return the channel current playing media."""
        return self._channel

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_TIVO

    def turn_off(self):
        """Turn off media player."""
        self._state = STATE_OFF
        self._device.setOnState(False)

    def turn_on(self):
        """Turn on the media player."""
        self._state = STATE_ON
        self._device.setOnState(True)

    def media_next_track(self):
        """Send next track command."""
        self._changeChannelWithIRCode("CHANNELUP")

    def media_previous_track(self):
        """Send the previous track command."""
        self._changeChannelWithIRCode("CHANNELDOWN")

    def _changeChannelWithIRCode(self, code):
        """Change the channel with the given IRCODE."""
        from python_tivo.response import FullChannelNam
        responses = self._device.sendIRCode(code)
        if len(responses) > 0:
          lastResponse = responses[-1]
          channel = FullChannelName(lastResponse)
          if channel:
            self._channel = channel
