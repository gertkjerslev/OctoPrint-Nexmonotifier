# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import nexmo
import os


class NexmonotifierPlugin(octoprint.plugin.EventHandlerPlugin,
                          octoprint.plugin.SettingsPlugin,
                          octoprint.plugin.AssetPlugin,
                          octoprint.plugin.TemplatePlugin,
                          octoprint.plugin.StartupPlugin):

    # put your plugin's default settings here

    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            enabled=False,
            secret="",
            api_key="",
            phone_number="",
            message_format=dict(body="Job complete: {filename} done printing after {elapsed_time}",
                                flashsms=False)
        )

    def get_settings_version(self):
        return 1

    # TemplatePlugin
    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=False)]

    def on_event(self, event, payload):
        if event != "PrintDone":
            return

        if not self._settings.get(['enabled']):
            return

        filename = os.path.basename(payload["file"])

        import datetime
        import octoprint.util
        elapsed_time = octoprint.util.get_formatted_timedelta(datetime.timedelta(seconds=payload["time"]))

        tags = {'filename': filename, 'elapsed_time': elapsed_time}
        message = self._settings.get(["message_format", "body"]).format(**tags)
        secret = self._settings.get(["secret"])
        api_key = self._settings.get(["api_key"])
        phone_number = self._settings.get(["phone_number"])
        message_class = 1
        client = nexmo.Client(key=api_key, secret=secret)

        if self._settings.get(["flashsms"]):
            message_class = 0

        response = client.send_message(
            {'from': 'Nexmonotifier', 'to': phone_number, 'text': message, 'message-class': message_class})

        try:
            response = response['messages'][0]

            if response['status'] == '0':
                # log message id
                self._logger.info(response['message-id'])
            else:
                # log nexmo error if any
                self._logger.info(response['error-text'])


        except Exception as e:
            # report problem sending sms
            self._logger.exception("SMS notification error: %s" % (str(e)))
        else:
            # report notification was sent
            self._logger.info("Print notification sent to %s" % (self._settings.get(['phone_number'])))

    ##~~ Softwareupdate hook
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
        # for details.
        return dict(
            nexmonotifier=dict(
                displayName="Nexmonotifier",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="gfk76",
                repo="OctoPrint-Nexmonotifier",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/gfk76/OctoPrint-Nexmonotifier/archive/{target_version}.zip"
            )
        )


__plugin_name__ = "Nexmo Notifier"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = NexmonotifierPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
