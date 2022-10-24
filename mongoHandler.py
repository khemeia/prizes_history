from pymongo import MongoClient
from models import Person


class MongoHandler:
    def __init__(self, collection_name="people"):
        self.collection_name = collection_name
        self.client = MongoClient()
        self.db = self.client.nobel
        self.collection = self.db[self.collection_name]

    def insert_person(self, person: Person):
        db_person = self.check_id(self.collection.find_one({"id": person.id}),
                                  person)
        if db_person:
            # this happens because the nominators data
            # doesnt include the prize data
            # so we need to update them
            # if they are then nominees and include the data
            if db_person['prizes'] == '' and person.prizes != '':
                print("updated" + db_person['prizes'])
                if db_person['id'] == -1:
                    return self.collection.replace_one(
                        {"name": db_person["name"]},
                        person.__dict__,
                        upsert=True)
                return self.collection.replace_one({"_id": db_person["_id"]},
                                                   person.__dict__,
                                                   upsert=True)
            return
        self.collection.insert_one(person.__dict__)

    def update_person(self, db_person):
        self.collection.replace_one({"_id": db_person["_id"]},
                                    db_person,
                                    upsert=True)

    def get_person(self, person: Person):
        db_person = self.check_id(self.collection.find_one({"id": person.id}),
                                  person)
        if db_person is None:
            raise Exception("Person {0} not  in databse".format(person.name))
        return db_person

    def check_id(self, db_person, person):
        if db_person:
            if db_person['id'] == -1:
                db_person = self.collection.find_one({"name": person.name})
                if not db_person:
                    return None
                # raise Exception("Person {0} not  in databse".format(
                #     person.name))
            return db_person

    def get_person_by_id(self, person_id):
        db_person = None
        if person_id.isnumeric():
            db_person = self.collection.find_one({"id": person_id})
        else:
            db_person = self.collection.find_one({"name": person_id})
        if db_person is None:
            raise Exception("Person not found by id {0}".format(person_id))
        return db_person

    def get_all(self):
        return self.collection.find()

    def get_winners(self):
        return self.collection.find({"winner": True})

    def insert_relationship(self, relationship):
        self.db.relationships_ch.insert(relationship.__dict__)

    def get_chem_people(self):
        people = self.db.people_chemistry.find()
        db_people = []
        for person in people:
            person_id = -1
            if person['id'] == -1:
                person_id = person['name']
            else:
                person_id = person['name']
            db_people.append(self.get_person_by_id(person_id))
        return db_people

    def get_losers(self):
        return self.collection.find({"winner": False})
