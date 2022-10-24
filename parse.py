#!/usr/bin/env python3
import os
import re
import glob
import sys
from models import Person
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

    def export_people(self, onPerson=None):
        # because just the nominees have the info if they won or not
        # print("Nominee file" + self.file_name)
        persons_data = self.get_all_people()
        for current in persons_data:
            person = Person()
            self.parse_properties(current, person)
            self.parse_name(current, person)
            self.parse_prize(current, person)
            # print("Nominee(s){0}".format(person.name))
            self.handler.insert_person(person)
            # onPerson(person, self)

    def get_nominees(self):
        return re.findall(
            'Nominee(?: \\d)?:</b>[\\s\\S]*?(?=<tr><td colspan="2" style="border: 0px;">&nbsp;</td></tr>)',
            self.main)

    # ore than one nominator is posible
    def get_nominators(self):
        return re.findall(
            'Nominator(?: \\d)?:</b>[\\s\\S]*?(?=<tr><td colspan="2" style="border: 0px;">&nbsp;</td></tr>)',
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

    def insert_nominations(self):
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
            '(?<=<td colspan="2" style="border: 0px;">Nomination for Nobel )[\\s\\S]*?(<tr><td colspan="2" style="border: 0px;">&nbsp;</td></tr>)',
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
            prize = re.search('(?<=Nobel ).*(?= \\d{4})', prized).group()
            year = re.search('(?<=' + prize + ' )\\d{4}', prized).group()
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
        name_result = re.findall('(?<=people.php\\?id=)\\d*.*?>\\w*.*?<', text)
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


# adds a missing prize to the given nominee
def add_ch_win_to_nominee(nominee_id: str, year):
    handler = MongoHandler("people")
    person = handler.get_person_by_id(nominee_id)
    person['winner'] = True
    person['nobel'] = person['nobel'] + [{"type": "C", "year": str(year), "name": "Prize in Chemistry"}]
    person['prizes'] = person['prizes'] + "C in "+str(year)+ "|"
    handler.update_person(person)


def insert_missing_nominations():
    add_ch_win_to_nominee("10654", 1967)
    add_ch_win_to_nominee("13019", 1967)
    add_ch_win_to_nominee("11157", 1967)
    add_ch_win_to_nominee("10476", 1968)
    add_ch_win_to_nominee("10669", 1969)
    add_ch_win_to_nominee("3933", 1969)
    add_ch_win_to_nominee("10889", 1970)


def clean_names(handler):
    for person in handler.get_all():
        person['name'] = html.unescape(person['name'])
        handler.update_person(person)


def main(argument):
    handler = MongoHandler("people")
    for file in glob.glob(argument + "**/*.html"):
        parse_html_file(file, handler)
    clean_names(handler)
    insert_missing_nominations()


def parse_html_file(file, handler):
    file = open(file, mode="r", errors="replace")
    data = file.read()
    parser = Parser(data, handler, file.name)
    parser.export_people()
    parser.insert_nominations()
    file.close()


if __name__ == "__main__":
    main(sys.argv[1])
