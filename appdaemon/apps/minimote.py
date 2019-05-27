import appdaemon.plugins.hass.hassapi as hass

from hassdb import extenddict

LEVEL = 'DEBUG'

class Minimotes(hass.Hass):
    def initialize(self):
        self.log(type(self.args), level=LEVEL)
        self.args = extenddict(self.args)

        for line in self.args.toLines():
            self.log(line, level=LEVEL)

        self.minimotes = {}
        for minimote in self.args.minimotes:
            self.minimotes[minimote.entity.entity_id] = minimote

        self.listen_event(self.minimote_button_evt, "zwave.scene_activated")

    def minimote_button_evt(self, event_name, data, kwargs):
        try:
            entity_id = data['entity_id']
            scene = 'scene{}'.format(data['scene_id'])
        except KeyError:
            self.error('No minimote scene information! {}, {}'.format(event_name, data))
            return

        minimote = self.minimotes.get(entity_id)
        if minimote:
            if scene in minimote:
                scene = minimote[scene]
                if any(self.get_state(obj.entity_id) == 'on' for obj in scene.entities):
                    for obj in scene.entities:
                        self.turn_off(obj.entity_id)
                else:
                    for obj in scene.entities:
                        if obj.domain == 'light':
                            self.turn_on(obj.entity_id, brightness = scene.brightness)
                        else:
                            self.turn_on(obj.entity_id)