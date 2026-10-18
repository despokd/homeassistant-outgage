"""Tests for the OutGage config flow."""

import socket

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.outgage.const import (
    CONF_OUTGAUGE_ID,
    CONF_TIMEOUT,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)


async def test_user_flow(hass: HomeAssistant, free_port: int) -> None:
    """A free port creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    user_input = {CONF_HOST: "127.0.0.1", CONF_PORT: free_port, CONF_OUTGAUGE_ID: 0}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == user_input


async def test_cannot_bind(hass: HomeAssistant) -> None:
    """A port in use shows an error."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as busy:
        busy.bind(("127.0.0.1", 0))
        port = busy.getsockname()[1]
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "127.0.0.1", CONF_PORT: port, CONF_OUTGAUGE_ID: 0},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_bind"}


async def test_single_instance(hass: HomeAssistant) -> None:
    """Only one entry is allowed."""
    MockConfigEntry(domain=DOMAIN, data={}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow(hass: HomeAssistant, free_port: int) -> None:
    """Options can be changed."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1", CONF_PORT: free_port, CONF_OUTGAUGE_ID: 0},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_UPDATE_INTERVAL: 0.5, CONF_TIMEOUT: 10}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_UPDATE_INTERVAL: 0.5, CONF_TIMEOUT: 10}
    await hass.config_entries.async_unload(entry.entry_id)
