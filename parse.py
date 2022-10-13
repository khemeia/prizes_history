#!/usr/bin/env python3
import sys
import os
import re
from models import Person, Relationship, CategorizedRelationship
from mongoHandler import MongoHandler
import html
properties = [
    "Gender", "Birth", "Death", "Profession", "University", "City", "State",
    "Country"
]
prizes = {
    "Prize in Physics": "P",
    "Prize in Chemistry": "C",
    "Prize in Physiology or Medicine": "PM",
    "Prize in Literature": "L",
    "Peace Prize": "PE"
}


class Parser:
    def __init__(self, html: str, handler: MongoHandler, file_name: str):
        self.main = re.search(
            '(?<=<div id="main")[\\s\\S]*(\\<\\/table\\>)',
            html).group()
        self.file_name = file_name
        self.handler = handler

    def parse(self):
        # alues = re.findall('<td.*>', self.main)
        nominees_data, nominator_data = self.get_people()
        nominees = []
        nominator = Person()
        for nominee in nominees_data:
            person = Person()
            self.parse_properties(nominee, person)
            self.parse_name(nominee, person)
            nominees.append(person)
        self.parse_properties(nominator_data.group(), nominator)
        self.parse_name(nominator_data.group(), nominator)
        for nominee in nominees:
            print("Nominee(s){0}".format(nominee.name))
            print("Nominee Gender: {0}".format(nominee.death))
        print("Nominator: {0}".format(nominator.name))
        self.handler.insert_person(nominator)

    def export_people(self, onPerson):
        # because just the nominees have the info if they won or not
        print("Nominee file" + self.file_name)
        persons_data = self.get_all_people()
        for current in persons_data:
            person = Person()
            self.parse_properties(current, person)
            self.parse_name(current, person)
            self.parse_prize(current, person)
            print("Nominee(s){0}".format(person.name))
            onPerson(person, self)

    def get_nominees(self):
        return re.findall(
            'Nominee(?: \d)?:</b>[\s\S]*?(?=<tr><td colspan="2" style="border: 0px;">&nbsp;</td></tr>)',
            self.main)

    # ore than one nominator is posible
    def get_nominators(self):
        return re.findall(
            'Nominator(?: \d)?:</b>[\s\S]*?(?=<tr><td colspan="2" style="border: 0px;">&nbsp;</td></tr>)',
            self.main)

    # eprecated
    def get_people(self):
        nominees = self.get_nominees()
        nominator = self.get_nominators()
        return [nominees, nominator]

    def get_all_people(self):
        everyone = self.get_nominees()
        everyone.extend(self.get_nominators())
        return everyone

    def get_nominations(self):
        nomination_year, nomination_type = self.get_nomination_data()
        nominees_data, nominators_data = self.get_people()
        nominees = self.parse_basic_info(nominees_data)
        nominators = self.parse_basic_info(nominators_data)
        # rint(nomination_year + " " + nomination_type)
        for nominee in nominees:
            db_nominee = self.handler.get_person(nominee)
            # rint(nominee.id)
            for nominator in nominators:
                db_nominator = self.handler.get_person(nominator)
                keytopush = db_nominator['id']
                if db_nominator['id'] == -1:
                    keytopush = db_nominator['name']
                if db_nominee['nominations'].get(keytopush) is None:
                    db_nominee['nominations'][keytopush] = [{
                        "year":
                        nomination_year,
                        "type":
                        nomination_type
                    }]
                else:
                    value = {nomination_year: nomination_type}
                    if value not in db_nominee['nominations'][keytopush]:
                        db_nominee['nominations'][keytopush].append({
                            "year":
                            nomination_year,
                            "type":
                            nomination_type
                        })
            self.handler.update_person(db_nominee)

    def parse_basic_info(self, persons_data):
        persons = []
        for data in persons_data:
            person = Person()
            self.parse_properties(data, person)
            self.parse_prize(data, person)
            self.parse_name(data, person)
            persons.append(person)
        return persons

    def get_nomination_data(self):
        nomination_data = re.search(
            '(?<=<td colspan="2" style="border: 0px;">Nomination for Nobel )[\s\S]*?(<tr><td colspan="2" style="border: 0px;">&nbsp;</td></tr>)',
            self.main).group()
        nomination_for = prizes[re.search('.*(?=</td>)',
                                          nomination_data).group()]
        year = re.search(
            '(?<=Year:</span></td><td style="border: 0px;">)(.*)(?=</)',
            nomination_data).group()
        return [year, nomination_for]

    @staticmethod
    def parse_prize(text, person):
        found = re.findall('(?<=Awarded the).*(?=</a>)', text)
        if found is None:
            return
        for prized in found:
            prize = re.search('(?<=Nobel ).*(?= \d{4})', prized).group()
            year = re.search('(?<=' + prize + ' )\d{4}', prized).group()
            person.winner = True
            person.prizes += prizes[prize] + " in " + year + "|"
            person.nobel.append({
                "type": prizes[prize],
                "year": year,
                "name": prize
            })

    @staticmethod
    def parse_name(text, person):
        # namearr = text.split('">')
        # return [namearr[0], re.sub("<", "", namearr[1])]
        name_result = re.findall('(?<=people.php\?id=)\d*.*?>\w*.*?<', text)
        if not name_result:
            name = re.search(
                '(?<=Name:</span></td><td style="border: 0px;">)(.*)(?=</)',
                text).group()
            person.name = html.unescape(name)
            person.id = -1
            print("Warning person" + name + "doesnt have an id")
            return
        namearr = (name_result[0]).split('">')
        person.id = namearr[0]
        person.name = html.unescape(re.sub("<", "", namearr[1]))

    # TODO refactor this
    @staticmethod
    def parse_properties(text, person):
        propertiesHash = {}
        for propty in properties:
            match = re.search(
                '(?<={0}:</span></td><td style="border: 0px;">)(.*)(?=</)'.
                format(propty), text)
            if match is None:
                propertiesHash[propty] = None
            else:
                propertiesHash[propty] = match.group()
        person.gender = propertiesHash["Gender"]
        person.birth = propertiesHash["Birth"]
        person.death = propertiesHash["Death"]
        person.profession = propertiesHash["Profession"]
        person.university = propertiesHash["University"]
        person.city = propertiesHash["City"]
        person.state = propertiesHash["State"]
        person.country = propertiesHash["Country"]
