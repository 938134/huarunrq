"""Config flow for HuaRunRQ integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class HuaRunRQFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HuaRunRQ."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return HuaRunRQOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Validate the input data
            cno = user_input.get("cno")
            scan_interval = user_input.get("scan_interval", 3600)  # Default to 3600 seconds if not provided

            # Create the config entry
            return self.async_create_entry(
                title="HuaRunRQ",
                data={"cno": cno},
                options={"scan_interval": scan_interval}
            )

        # Show the form to the user
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("cno"): str,
                vol.Optional("scan_interval", default=3600): int
            }),
            errors=errors
        )


class HuaRunRQOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for HuaRunRQ integration."""

    def __init__(self, config_entry):
        """Initialize HuaRunRQ options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Update the options with the new scan interval
            return self.async_create_entry(title="", data=user_input)

        # Get the current scan interval from the config entry
        current_scan_interval = self.config_entry.options.get("scan_interval", 3600)

        # Show the form to the user
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("scan_interval", default=current_scan_interval): int
            })
        )