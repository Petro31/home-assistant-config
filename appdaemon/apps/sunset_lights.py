import appdaemon.plugins.hass.hassapi as hass

from hassdb import extenddict

LEVEL = 'DEBUG'

class SunsetLights(hass.Hass):
    def initialize(self):
        self.extendedargs = extenddict(self.args)

        for line in self.extendedargs.toLines():
            self.log(line, level=LEVEL)

        self.run_at_sunset(self.entities_on)
        self.run_at_sunrise(self.entities_off)

    def entities_on(self, kwargs):
        for obj in self.extendedargs.entities:
            self.turn_on(obj.entity_id)

    def entities_off(self, kwargs):
        for obj in self.extendedargs.entities:
            self.turn_off(obj.entity_id)