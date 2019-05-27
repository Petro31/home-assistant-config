import appdaemon.plugins.hass.hassapi as hass

from hassdb import extenddict, Volume

LEVEL = 'DEBUG'

class MediaVolume(hass.Hass):
    def initialize(self):
        self.extendedargs = extenddict(self.args)

        for line in self.extendedargs.toLines():
            self.log(line, level=LEVEL)

        for player in self.extendedargs.media_players:

            self.listen_state(self.track_volume_from_player, 
                entity=player.entity.entity_id, input_number=player.input_number)

            self.listen_state(self.track_volume_from_input_number, 
                entity=player.input_number.entity_id, media_player=player.entity)

    def get_volumes(self, media_id, input_id):
        media_volume = Volume(level = self.get_state(media_id, attribute='volume_level'))
        input_volume = Volume(decibel = self.get_state(input_id))
        
        self.log('{} {}'.format(media_id, media_volume.report), level=LEVEL)
        self.log('{} {}'.format(input_id, input_volume.report), level=LEVEL)
        return media_volume, input_volume

    def track_volume_from_player(self, entity, attribute, old, new, kwargs):
        input_number = kwargs.get('input_number')
        if self.get_state(entity) == 'on':
            media_volume, input_volume = self.get_volumes(entity, input_number.entity_id)
            if media_volume != input_volume:
                self.log('updating {} to {}'.format(input_number.entity_id, media_volume.report), level=LEVEL)
                self.call_service('input_number/set_value', entity_id=input_number.entity_id, value=media_volume.decibel)

        if old == 'on' and new == 'off':
            off_volume = Volume(level = 0.20)
            self.call_service('input_number/set_value', entity_id=input_number.entity_id, value=off_volume.decibel)
        
    def track_volume_from_input_number(self, entity, attribute, old, new, kwargs):
        player = kwargs.get('media_player')
        if self.get_state(player.entity_id) == 'on':
            media_volume, input_volume = self.get_volumes(player.entity_id, entity)
            if media_volume != input_volume:
                self.log('updating {} to {}'.format(player.entity_id, input_volume.report), level=LEVEL)
                self.call_service('media_player/volume_set', entity_id=player.entity_id, volume_level=input_volume.level)