import appdaemon.plugins.hass.hassapi as hass

#from importlib import reload
#import hassdb
#reload(hassdb)

from hassdb import extenddict, StateDatabase, PeopleTracker, RestoreStateManager, NotifyMessage

LEVEL = 'INFO'
RESTORE_LOCATION = r"/config/appdaemon/door_messages"

class Doorsensors(hass.Hass): 
    def initialize(self):
        self.extendedargs = extenddict(self.args)

        self.log(self.extendedargs, level=LEVEL)

        for line in self.extendedargs.toLines():
            self.log(line, level=LEVEL)

        # object for tracking who's home based on device trackers.
        self.people = PeopleTracker(self, self.extendedargs.device_trackers)

        company = self.extendedargs.company
        self.people.setcompanystatus(company)
        self.people.update()

        self.listen_state(self.track_company, entity = company.entity_id, company = company)

        # read/write database for states persisiting during shutdown/restart.
        self.database = StateDatabase(RESTORE_LOCATION)

        self.timers = {}

        self.log(self.people.log, level=LEVEL)

        # managers for restoring lights to previous state after a door opens.
        self.managers = RestoreStateManager()

        for sensor in self.extendedargs.door_sensors:

            self.managers.add_manager(sensor.entity.entity_id)

            self.listen_state(self.door_tracker, entity = sensor.entity.entity_id, sensor = sensor)
            
            #Setup new state object
            entity_id = 'sensor.{}_message'.format(sensor.entity.object_id)
            state = self.database.read(entity_id)
            friendly_name = '{} User'.format(self.get_state(sensor.entity.entity_id, attribute='friendly_name'))
            attributes = { 'friendly_name':friendly_name, 'icon':'mdi:door' }
            
            # set the state inside home assistant.
            self.set_state(entity_id, state = state, attributes = attributes)

    def track_company(self, entity, attribute, old, new, kwargs):
        company = kwargs.get('company')
        self.people.setcompanystatus(company)
        self.people.update()

    def turn_on_object(self, obj):
        if obj.domain == 'light':
            self.turn_on(obj.entity_id, **obj.data)
        else:
            self.turn_on(obj.entity_id)

    def door_tracker(self, entity, attribute, old, new, kwargs):
        sensor = kwargs.get('sensor')

        timer_kwargs = {'seconds' : 0, 'sensor' : sensor, 'entity_state' : new }
        
        # make a series of names for timers.  Notification timer, Light on/off timer, and Timer for alert (unknown person entering house).
        light_name, nofity_name, alert_name = [ '{}.{}'.format(entity, n) for n in ['entities','notify','alert'] ]

        # cancel notifier
        try:
            self.cancel_timer(self.timers[nofity_name])
        except KeyError:
            self.log('Tried to cancel timer {}, but none existed!'.format(nofity_name), level=LEVEL)

        if new in ['off', 'closed', '23']:
            # cancel light timer.
            try:
                self.cancel_timer(self.timers[light_name])
            except KeyError:
                self.log('Tried to cancel timer {}, but none existed!'.format(light_name), level=LEVEL)
            
            # start new light timer.  Light & Timer are only in affect after dark.
            if self.sun_down():
                timer_kwargs['seconds'] = self.extendedargs.durations.light
                self.timers[light_name] = self.run_in(self.restore_states, **timer_kwargs)
        
        if new in ['on', 'open', '22']:
            
            # Start notification timer.  This is if the door is left open for x seconds.
            timer_kwargs['seconds'] = self.extendedargs.durations.notify
            self.timers[nofity_name] = self.run_in(self.notify_door_open, **timer_kwargs)

            # Turn on lights
            if self.sun_down():
                for obj in sensor.entities:
                    if self.managers[entity].restore:

                        state = self.get_state(obj.entity_id)
                        self.managers[entity][obj.entity_id] = state

                        self.log(self.timers, level=LEVEL)
                        self.log("Storing state: {} for {}".format(state, obj.entity_id), level=LEVEL)

                    # turn on the light / switch
                    self.turn_on_object(obj)
                        
                if self.managers[entity].restore:
                    self.managers[entity].restore = False

            # Send Notifications
            self.people.update() # Find out who is home.
            self.log(self.people.log, level=LEVEL)

            # Get name of the door in question and make a notification message
            name = self.get_door_friendly_name(entity)
            message = NotifyMessage(self.people.used_the_door(name))

            # Setup new state object
            self.set_door_user_state(sensor.entity.object_id)

            # Send the notification
            self.service_message(message)

            # start an alert service in 30 seconds if people aren't home.
            if not self.people.present:
                timer_kwargs['seconds'] = self.extendedargs.durations.intruder
                self.timers[alert_name] = self.run_in(self.nofity_about_intruder, **timer_kwargs)

    def set_door_user_state(self, entity_id):
        #setup the new object.
        entity_id ='sensor.{}_message'.format(entity_id)
        state = self.people.or_conjunction_list
        self.database.write(entity_id, state)

        # Set the state in Home Assistant
        self.set_state(entity_id, state=state)
        
    def get_door_friendly_name(self, entity_id):
        name = self.get_state(entity_id, attribute='friendly_name')
        return name.replace("Status", "").strip().lower()
                
    def restore_states(self, kwargs):
        sensor = kwargs.get('sensor')
        entity = sensor.entity.entity_id

        # flag that we restored.
        self.managers[entity].restore = True
        for obj in sensor.entities:

            # get the state to restore to.
            state = self.managers.get_state(entity, obj.entity_id)
            self.log("Recalling state: {} for {}".format(state, obj.entity_id), level=LEVEL)

            if self.get_state(obj.entity_id) != state:
                if state == 'on':
                    self.turn_on_object(obj)
                elif state == 'off':
                    self.turn_off(obj.entity_id)

    def notify_door_open(self, kwargs):
        # setup notification
        sensor = kwargs.get('sensor')
        new = kwargs.get('entity_state')
        name = self.get_door_friendly_name(sensor.entity.entity_id).capitalize()
        message = NotifyMessage('{} has been {} for more than {} seconds.'.format(name, new, self.extendedargs.durations.notify))

        # send notifications
        self.service_message(message)

    def nofity_about_intruder(self, kwargs):
        sensor = kwargs.get('sensor')
        name = self.get_door_friendly_name(sensor.entity.entity_id)

        self.people.update()
        if self.people.present:
            message = 'The person who used {} was {}'.format(name, self.people.or_conjunction_list)
        else:
            message = 'The person who used {} is still unknown!'.format(name)

        self.set_door_user_state(sensor.entity.object_id)
        self.service_message(message)

    def service_message(self, message):
        for service in self.extendedargs.notify_services:
            self.call_service(service.service, message=message, data=service.data)