import appdaemon.plugins.hass.hassapi as hass

from hassdb import extenddict

LEVEL = 'DEBUG'

class ZoneCycler(hass.Hass):
    def initialize(self):
        self.extendedargs = extenddict(self.args)

        self.log(self.extendedargs, level=LEVEL)
        
        self.input_select = self.extendedargs.input_select
        
        self.media_players = {}
        for i, player in enumerate(self.extendedargs.media_players):
            self.listen_state(self.track_player_state,
                entity = player.entity.entity_id, player = player)
            self.media_players['{}'.format(i+1)] = player
            
    def track_player_state(self, entity, attribute, old, new, kwargs):
        player = kwargs.get('player')

        self.log("{}.{}: {} -> {}".format(player.entity.object_id, attribute, old, new), level=LEVEL)

        if attribute == 'state':
            if old != new and new == 'on':
                if all([ self.get_state(obj.entity.entity_id) == 'on' for obj in self.media_players.values() ]):
                    to_state = 'all'
                    self.log("{}.attributes.option -> {}".format(self.input_select.entity_id, to_state), level=LEVEL)
                    self.call_service(r'input_select/select_option',
                        entity_id = self.input_select.entity_id, option = to_state)
                else:
                    for option, obj in self.media_players.items():
                        if obj.entity.entity_id == player.entity.entity_id:
                            self.log("{}.attributes.option -> {}".format(self.input_select.entity_id, option), level=LEVEL)
                            self.call_service(r'input_select/select_option',
                                entity_id = self.input_select.entity_id, option = option)
            if old != new and new == 'off':
                on_players = [ obj for obj in self.media_players.values() if self.get_state(obj.entity.entity_id) == 'on' ]
                if len(on_players) >= 1:
                    on_player = on_players[0]
                    for option, obj in self.media_players.items():
                        if obj.entity.entity_id == on_player.entity.entity_id:
                            self.log("{}.attributes.option -> {}".format(self.input_select.entity_id, option), level=LEVEL)
                            self.call_service(r'input_select/select_option',
                                entity_id = self.input_select.entity_id, option = option)
                else:
                    to_state = 'off'
                    self.log("{}.attributes.option -> {}".format(self.input_select.entity_id, to_state), level=LEVEL)
                    self.call_service(r'input_select/select_option',
                        entity_id = self.input_select.entity_id, option = to_state)