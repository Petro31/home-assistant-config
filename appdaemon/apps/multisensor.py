import appdaemon.plugins.hass.hassapi as hass

from hassdb import extenddict
from datetime import datetime

LEVEL = 'DEBUG'

class MultisensorLights(hass.Hass):
    def initialize(self):
        
        self.timers = {}
        self.extendedargs = extenddict(self.args)

        for line in self.extendedargs.toLines():
            self.log(line, level=LEVEL)

        for multisensor in self.extendedargs.multisensors: 
            self.listen_state(self.track_multisensor_movement, entity=multisensor.entity.entity_id, multisensor=multisensor)
            
    def track_multisensor_movement(self, entity, attribute, old, new, kwargs):
        multisensor = kwargs.get('multisensor')
        if old == 'off' and new == 'on' :
            try:
                self.cancel_timer(self.timers[entity])
            except KeyError:
                self.log('Tried to cancel a timer for {}, but none existed!'.format(entity), level=LEVEL)

            self.timers[entity] = self.run_in(self.turn_off_entities, seconds=multisensor.duration, multisensor=multisensor)

            if multisensor.after.time <= datetime.now().time() <= multisensor.before.time:
                brightness = multisensor.between.brightness
            else:
                brightness = multisensor.outside.brightness

            for obj in multisensor.entities:
                if obj.domain == 'light':
                    self.turn_on(entity.id, brightness=brightness)

    def turn_off_entities(self, kwargs):
        multisensor = kwargs.get('multisensor')
        for obj in multisensor.entities:
            self.turn_off(obj.entity_id)