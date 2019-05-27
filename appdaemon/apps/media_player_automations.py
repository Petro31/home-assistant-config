import appdaemon.plugins.hass.hassapi as hass

from hassdb import extenddict

LEVEL = 'DEBUG'

class MediaPlayerAutomations(hass.Hass): 
    def initialize(self):
        self.extendedargs = extenddict(self.args)

        self.log(self.extendedargs, level=LEVEL)

        for line in self.extendedargs.toLines():
            self.log(line, level=LEVEL)

        for player in self.extendedargs.media_players:

            self.listen_state(self.track_player_state, 
                entity=player.entity.entity_id, player=player)

    def track_player_state(self, entity, attribute, old, new, kwargs):
        player = kwargs.get('player')

        self.log("{}.{}: {} -> {}".format(player.entity.object_id, attribute, old, new), level=LEVEL)

        # if the player is the state we are looking for:
        self.log(player.turn_off, level=LEVEL)
        if attribute == 'state':
            if old != new:
                if new == player.turn_on:
                    for obj in player.entities:
                        state = self.get_state(obj.entity_id)
                        self.log("{} is {}".format(obj.entity_id, state), level=LEVEL)
                        if state == 'off':
                            self.log("turn on {}".format(obj.object_id))
                            if obj.domain == 'light':
                                self.turn_on(obj.entity_id, **obj.data)
                            else:
                                self.turn_on(obj.entity_id)
                
                if new in player.turn_off:
                    for obj in player.entities:
                        state = self.get_state(obj.entity_id)
                        self.log("{} is {}".format(obj.entity_id, state), level=LEVEL)
                        if self.get_state(obj.entity_id) == 'on':
                            self.log("turn off {}".format(obj.object_id))
                            self.turn_off(obj.entity_id)