import logging
from datetime import datetime, timedelta
import time
import datautil.date

try:
    import json
except ImportError:
    import simplejson as json



EU_COUNTRIES = [
    "se", "fi", "dk",  "ee", "lt", "lv", "pl", "de", "nl", "be",
    "fr", "lu", "es", "pt", "it", "gr", "sl", "au", "hu", "ro", "bg", "sk", "cz",
    "mt", "cy", "ie", "uk"
    ]
EEA_COUNTRIES = list(EU_COUNTRIES) + ["is", "no"]

TREATY_COUNTRIES = { "us": 70, "ca": 70, "fr": 70 } # to be completed

WORK_TYPES = [
    "literary",
    "artistic",
    "dramatic",
    "composition",
    "recording",
    "photograph",
    "video",
    "database",
    "law",
    "performance",
    "database",
    "broadcast",
    "film",
    "typographic",
    "collective"
]

ENTITY_TYPES = [
    "person",
    "organization",
    "government",
    "anonymous",
    "pseudonym",
    "computer",
]


def getstruct(blob):
    if type(blob) == str:
        struct = json.loads(blob)
    elif type(blob) == dict:
        struct = blob
    else:
        raise TypeError("Can only load strings or dictionaries.")
        
    return struct

def get_date(indate):
    try:
        return datautil.date.parse(indate).as_datetime()
    except:
        # TODO: this is a hack!!
        return datetime(2000, 1, 1)

class LegalEntity:
    def __init__(self, work, blob=None):
        self.name = None
        self.death_date = None
        self.birth_date = None
        self.country = None
        self.type = None
        self.work = work
        if blob:
            self.load(blob)
        
    def load(self, blob):
        person = getstruct(blob)
        self.name = person.get("name", None)
        bd = person.get("birth_date", None)
        if bd:
            self.birth_date = get_date(bd)
        dd = person.get("death_date", None)
        if dd:
            self.death_date = get_date(dd)
        else:
            if self.birth_date:
                self.death_date = self.birth_date + timedelta(days=36525)    # 100 years
                self.work.assumptions.append("Didn't get date of death for Legal Entity %s: assuming death after 100 years." % self.name)

        self.country = person.get("country", None)
        try:    self.type = person.get("type")
        except: raise ValueError("'type' is a mandatory field for legal entities/persons")
            
    def is_eu(self):
        return self.country in EU_COUNTRIES
    
    def is_eea(self):
        #print EEA_COUNTRIES
        return self.country in EEA_COUNTRIES
        
    def is_treaty(self):
        return TREATY_COUNTRIES.get(self.country, False)


    def death_years(self, when):
        return (when - self.death_date).days / 365.25
        
    
        
                    

class Work:
    def __init__(self, blob=None):
        self.type = None
        self.items = []
        self.authors = []
        self.publishers = []
        self.date = None
        self.creationdate = None
        self.title = None
        self.original = None
        self.country = None
        self.published = True
        self.original = True
        self.changed = False;
        self.assumptions = [] #where all the assumption concerning this work will be collected       
 
        if blob:
            self.load(blob)
        
    def load(self, blob):
        thing = getstruct(blob)
            
        self.title = thing.get("title", None)
        self.original = thing.get("original", True);
        self.authors = [LegalEntity(self,x) for x in thing.get("authors", [])]
        self.publishers = [LegalEntity(self,x) for x in thing.get("publishers", [])]


        self.creationdate = thing.get("creation_date", None)
        if self.creationdate:
            self.creationdate = self.str_to_datetime(self.creationdate)
        try:
            date = thing.get("date")
            self.date = self.str_to_datetime(date)
	except: raise ValueError("'date' is a mandatory field for works.")

        try:    self.type = thing.get("type")
        except: raise ValueError("'type' is a mandatory field for works.")
    

    def str_to_datetime(self, date):
        return get_date(date)

    def is_db(self):
	if self.type == "database": return True   
 
    def is_artistic(self):
        if self.type in ["literary", "dramatic", "artistic", "collective"]: return True
        elif self.type == "photograph" and self.original: return True
        else: return False
    
    def is_corporate(self):
	# is at least one of the authors an organisation?
	for person in self.authors:
		if person.type == "organisation": return True
	return False

    def eea(self):
        # is at least one of the authors a citizen of the EEA?
        for person in self.authors:
            if person.type == "person" and person.is_eea(): return True
        # has the work been published in the EEA?
        return self.country in EEA_COUNTRIES
        
    def treaty(self):
        # is the author a citizen of a Treaty country?
        a = []
        for person in self.authors:
            if person.type == "person": 
                a.append(person.is_treaty())
        if a: return max(a)
        else: return 0
        
        
    def oldest_author(self):
        oldest = 0
        for a in self.authors: 
            if a.death_date and a.death_date.year > oldest:
                oldest = a

        return oldest
        
  
    def oldest_author_death(self):
        death_oldest = 0
        if self.oldest_author():
            death_oldest = self.oldest_author().death_date
        else:
            self.assumptions.append("Didn't get date of death or birth; assuming death after 100 years from creation.")
            death_oldest = self.creationdate + timedelta(days=365*100)

        return death_oldest

      
    def publication_years(self, when):
        return (when - self.date).days / 365.25
        
    def creation_years(self, when):
        return (when - self.creationdate).days / 365.25
        
    def last_changed(self, when):
        date = self.changed or self.date;
        return (when - date).days / 365.25
        
    
   
        
    
        
    
    
