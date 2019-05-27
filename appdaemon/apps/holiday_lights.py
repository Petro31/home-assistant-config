import appdaemon.plugins.hass.hassapi as hass

from hassdb import extenddict
from datetime import datetime
from copy import copy

LEVEL = 'DEBUG' 

class HolidayLights(hass.Hass):
    def initialize(self):
        self.extendedargs = extenddict(self.args)
        for line in self.extendedargs.toLines():
            self.log(line, level=LEVEL)        

        self.seasons = {}

        for season in self.extendedargs.seasons:
            self.seasons[season.name] = season

            self.log(season.name, level=LEVEL)

            start, end = self.evaluateDates(season.start.date, season.end.date)
            date_format = '%m-%d-%Y'
            self.log(' start: {}'.format(start.strftime(date_format)), level=LEVEL)
            self.log(' end: {}'.format(end.strftime(date_format)), level=LEVEL)

            self.log(' currently {}'.format(self.seasonStatus(season)), level=LEVEL)

            time_format = '%I:%M %p' 
            self.log(' lights on at {}'.format(str(season.turn_on.time.strftime(time_format))), level=LEVEL)
            self.run_daily(self.run_turn_on, season.turn_on.time, season=season.name)
            self.log(' lights off at {}'.format(str(season.turn_off.time.strftime(time_format))), level=LEVEL)
            self.run_daily(self.run_turn_off, season.turn_off.time, season=season.name)

    def seasonStatus(self, season):
        return 'in season' if self.inSeason(season) else 'out of season'

    def evaluateDates(self, start, end):
        if end < start:
            return start, end.replace(year=datetime.now().year+1)
        else:
            return start, end

    def inSeason(self, season):
        ''' checks if we are in season. '''
        start, end = self.evaluateDates(season.start.date, season.end.date)
        return start <= datetime.now().date() <= end

    def _run_season(self, func, kwargs):
        name = kwargs.get('season')
        if name:
            season = self.seasons.get(name)
            if season and self.inSeason(season):
                self.log('({}) {}'.format(func, season.name), level=LEVEL)
                for obj in season.entities:
                    getattr(self, func)(obj.entity_id)

    def run_turn_on(self, kwargs):
        self._run_season('turn_on', kwargs)

    def run_turn_off(self, kwargs):
        self._run_season('turn_off', kwargs)