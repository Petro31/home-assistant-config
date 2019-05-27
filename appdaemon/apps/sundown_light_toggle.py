import appdaemon.plugins.hass.hassapi as hass

from hassdb import extenddict

LEVEL = 'DEBUG'

class SunDownLightToggle(hass.Hass):
    def initialize(self):
        self.extendedargs = extenddict(self.args)

        for line in self.extendedargs.toLines():
            self.log(line, level=LEVEL)

        for switch in self.extendedargs.switches:
            self.listen_state(self.turn_on_after_sun_down, entity = switch.entity.entity_id, objects = switch.entities)
            
    def turn_on_after_sun_down(self, entity, attribute, old, new, kwargs):
        objects = kwargs.get('objects')
        if self.sun_down():
            if new in ['on']:
                for obj in objects:
                    if obj.domain == 'light':
                        self.turn_on(obj.entity_id, **obj.data)
                    else:
                        self.turn_on(obj.entity_id) 