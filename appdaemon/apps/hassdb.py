import json
import shelve
from datetime import timedelta, datetime, time

def indentedLine(depth, line): return '{}{}'.format(depth*'  ', line)

def nth_weekday(the_date, nth_week, week_day):
    temp = the_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    adj = (week_day - temp.weekday()) % 7
    temp += timedelta(days=adj)
    temp += timedelta(weeks=nth_week-1)
    return temp.date()

def NotifyMessage(message):
    dt = datetime.now()
    return "[{}] {}".format(dt.strftime('%-I:%M:%S %p'), message)

class baseObject(object):
    def __init__(self, kwargs):
        self.platform = kwargs.get('platform')
        if self.platform:
            kwargs.pop('platform')
    @property
    def isValid(self): return self.platform != None
    
class timeObject(baseObject):
    """ creates a time object to work with.  defaults tooday at midnight """
    def __init__(self, **kwargs):
        super(timeObject, self).__init__(kwargs)
        timestring = kwargs.get('at') or "00:00:00"
        self._time = datetime.strptime(timestring, "%H:%M:%S").time()
    @property
    def time(self):
        return self._time

class dateObject(baseObject):
    """ defaults to jan. 1st.  Ment for choosing first x of week x in month x"""
    def __init__(self, **kwargs):
        super(dateObject, self).__init__(kwargs)
        month = kwargs.get('month') or 1 # jan
        week = kwargs.get('week') or 1 # first week
        day = kwargs.get('day') or 0 # monday
        d = datetime(datetime.now().year, month, 1)
        self._date = nth_weekday(d, week, day)
    @property
    def date(self):
        return self._date

class baseentity(object):
    def __init__(self, domain, object_id):
        self.domain = domain
        self.object_id = object_id
    @property
    def entity_id(self):
        return '{}.{}'.format(self.domain, self.object_id)
    @entity_id.setter
    def entity_id(self, value):
        domain, object_id = value.split('.')
        self.domain = domain
        self.object_id = object_id

class data(dict):
    def __init__(self, d):
        self.__slots__ = [ k for k in d ]
        super(data, self).__init__(d)
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("'data' object has no attribute '{}'".format(name))

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            if name in self.__slots__:
                self[name] = value
            else:
                raise AttributeError("'data' object has no attribute '{}'".format(name))
        else:
            dict.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("'data' object has no attribute '{}'".format(name))

    def __setitem__(self, name, value):
        if name in self.__slots__:
            dict.__setitem__(self, name, value)
        else:
            raise KeyError("'{}'".format(name))

class dataentity(baseentity):
    def __init__(self, domain, object_id, default_data, **kwargs):
        super(dataentity, self).__init__(domain, object_id)
        self._data = data(default_data)
        for k in self._data:
            if k in kwargs:
                self._data[k] = kwargs[k]
    @property
    def data(self): return self._data

class lightentity(dataentity):
    def __init__(self, domain, object_id, **kwargs):
        defaults = {'brightness':255}
        super(lightentity, self).__init__(domain, object_id, defaults, **kwargs)

class servicentity(dataentity):
    def __init__(self, domain, object_id, default_data, **kwargs):
        super(servicentity, self).__init__(domain, object_id, default_data, **kwargs)
    @property
    def service(self): return r"{}/{}".format(self.domain, self.object_id)

class notifyentity(servicentity):
    def __init__(self, domain, object_id, **kwargs):
        defaults = {'push':{'badge': 5}}
        super(notifyentity, self).__init__(domain, object_id, defaults, **kwargs)

class extenddict(dict):
    """ wraps a dictionary into an object.
    
    ways to access attributes/keys:
    
      dict['key']
      dict.key 
      dict.get('key')
    """
    def __init__(self, indict):
        temp = {}
        for key, value in indict.items():
            if key not in dir(dict):
                value = self._objectify(value)
                temp[key] = value
        super(extenddict, self).__init__(temp)

    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("'extenddict' object has no attribute '{}'".format(name))

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("'data' object has no attribute '{}'".format(name))

    def _objectify(self, value):
        """ recursive function to dig deeper in dictionary """
        if isinstance(value, (tuple, list)): 
            return [ self._objectify(v) for v in value ]
        elif isinstance(value, dict):
            platform = value.get('platform')
            if platform:
                if platform == 'time':
                    return timeObject(**value)
                elif platform == 'date':
                    return dateObject(**value)
                else:
                    return baseObject(value)
            else:
                try:
                    return extenddict(value)
                except TypeError:
                    raise TypeError("Value must be a dictionary: {}".format(type(value)))
        else:
            if isinstance(value, str):
                if '.' in value:
                    try:
                        domain, object_id = value.split('.')
                    except ValueError:
                        return value
                    
                    if domain == 'light':
                        return lightentity(domain, object_id)
                    elif domain == 'notify':
                        return notifyentity(domain, object_id)
                    else:
                        return baseentity(domain, object_id)
                else:
                    return value
            else:
                return value

    def _walkSelf(self, key, value, stream, depth, firstItem=False):
        depth += 1
        if isinstance(value, (tuple, list)):
            stream.append(indentedLine(depth, '{}:'.format(key)))
            for v in value:
                self._walkSelf('-', v, stream, depth-1)
        elif isinstance(value, dict):
            if key and key != '-':
                stream.append(indentedLine(depth, '{}:'.format(key)))
            for i, kvp in enumerate(value.items()):
                self._walkSelf(kvp[0], kvp[1], stream, depth, i==0)
        else:
            if key == '-':
                line = "{} {}".format(key, value)
                stream.append(indentedLine(depth, line))
            else:
                line = "{}: {}".format(key, value)
                if firstItem:
                    stream.append(indentedLine(depth-1, '- {}'.format(line)))
                else:
                    stream.append(indentedLine(depth, line))

    def toLines(self): 
        stream = []
        for key, value in self.items():
            self._walkSelf(key, value, stream, -1)
        return stream

    def toString(self):
        return '\n'.join(self.toLines())

class Volume(object):
    def __init__(self, level=None, decibel=None):
        self._level = None
        if level:
            setattr(self, 'level', level)
        elif decibel:
            setattr(self, 'decibel', decibel)
    @property
    def report(self):
        return "{:.2f} ({:.1f} db)".format(self.level, self.decibel)
    @property
    def level(self): return self._level
    @level.setter
    def level(self, value):
        try:
            self._level = float(value)
        except ValueError:
            raise ValueError("could not convert string to float: '{}'".format(value))
    @property
    def decibel(self):
        if self.level != None:
            return ((self.level - 1.0) * 100.0)
        else:
            return self.level
    @decibel.setter
    def decibel(self, value):
        try:
            value = float(value)
            self._level = (value / 100.0 + 1.0)
        except ValueError:
            raise ValueError("could not convert string to float: '{}'".format(value))

    def __eq__(self, other):
        if isinstance(other, type(self)):
            if self.level != None and other.level != None:
                return self.level == other.level
            else:
                return False
        return False
        
class StateDatabase(object):
    def __init__(self, filename):
        self._filename = filename

    def write(self, entity_id, state):
        with shelve.open(self._filename) as db:
            db[entity_id] = json.dumps({'state':state})

    def read(self, entity_id):
        with shelve.open(self._filename) as db:
            if entity_id in db.keys():
                state_dict = json.loads(db[entity_id])
                return state_dict['state']
            else:
                return ""

class StateManager(dict):
    restore = True
    
class RestoreStateManager(object):
    def __init__(self):
        self._managers = {}
        
    def add_manager(self, name):
        if name not in self._managers:
            self._managers[name] = StateManager()
            
    def get_state(self, name, entity_id):
        if name in self._managers:
            if entity_id in self._managers[name]:
                return self._managers[name][entity_id]
            else:
                KeyError("'{}'".format(entity_id))
        else:
            raise KeyError("'{}'".format(name))
    
    def set_state(self, name, entity_id, value):
        if name in self._managers:
            self._managers[name][entity_id] = value
        else:
            raise KeyError("'{}'".format(name))
    
    def __getitem__(self, name):
        if name in self._managers:
            return self._managers[name]
        else:
            raise KeyError("'{}'".format(name))

def join_english(inlist, conjunction='and'):
    if len(inlist) == 0:
        return ""
    elif len(inlist) == 1:
        return inlist[0]
    elif len(inlist) == 2:
        return ' {} '.format(conjunction).join(inlist)
    else:
        people = ', '.join(inlist[:-1])
        return "{}, {} {}".format(people, conjunction, inlist[-1])

class PeopleTracker(object):
    def __init__(self, parent, entities):
        self._parent = parent # this is a pointer to the parent object.
        self._entites = entities
        self._people = None
        self._company = False
        self.update()

    def setcompanystatus(self, entity):
        self._company = self._parent.get_state(entity.entity_id) in ['enabled']

    def update(self):
        people = []
        if self._company:
            people.append('Guests')
        for obj in self._entites:
            if self._parent.get_state(obj.entity_id) in [ 'home' ]:
                name = self._parent.get_state(obj.entity_id, attribute='friendly_name')
                name = name.lower().replace(' iphone','').strip()
                if name.endswith("'s"):
                    name = name[:-2]
                name = name.title()

                # this is an oddball.
                if name not in people and name[:-1] not in people:
                    people.append(name)
        self._people = people

    @property
    def people(self): return self._people

    @property
    def present(self): return self.count > 0

    @property
    def count(self): return len(self._people)

    @property
    def at_home(self):
        if not self.present:
            return "No one is home."
        else:
            people = join_english(self._people, 'and')
            conjunction = 'is' if self.count == 1 else 'are'
            return "{} {} home.".format(people, conjunction)

    @property
    def or_conjunction_list(self):
        if self.present:
            return join_english(self._people, 'or')
        else:
            return "Unknown"

    @property
    def list(self): return self._people

    @property
    def log(self):
        return "Occupants: {}.".format(join_english(self._people))

    def used_the_door(self, name):
        if not self.present:
            return "Unknown person used the {}.".format(name)
        else:
            people = join_english(self._people, 'or')
            return "{} used the {}.".format(people, name)