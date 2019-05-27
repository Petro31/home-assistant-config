import appdaemon.plugins.hass.hassapi as hass

from hassdb import extenddict

LEVEL = 'DEBUG'

class ExtendLightToggle(hass.Hass):
    def initialize(self):
        self.extendedargs = extenddict(self.args)

        for line in self.extendedargs.toLines():
            self.log(line, level=LEVEL)

        for switch in self.extendedargs.switches:
            self.listen_state(self.toggle_switch, entity = switch.entity.entity_id, objects = switch.entities)
            
    def toggle_switch(self, entity, attribute, old, new, kwargs):
        objects = kwargs.get('objects')
        if new in ['on']:
            for obj in objects:
                if obj.domain == 'light':
                    self.turn_on(obj.entity_id, **obj.data)
                else:
                    self.turn_on(obj.entity_id) 
        elif new in ['off']:
            for obj in objects:
                if self.get_state(obj.entity_id) in ['on']:
                    self.turn_off(obj.entity_id) 