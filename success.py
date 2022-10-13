#!/usr/bin/env python3
import sys
from models import BaseRelationship
from mongoHandler import MongoHandler
import html
import uuid

properties = [
    "Gender", "Birth", "Death", "Profession", "University", "City", "State",
    "Country"
]
prizes = {
    # "Prize in Physics": "P",
    "Prize in Chemistry": "C",
    # "Prize in Physiology or Medicine": "PM",
    # "Prize in Literature": "L",
    # "Peace Prize": "PE"
}


class NobelHelper:
    def __init__(self, handler: MongoHandler):
        self.handler = handler

    def get_succes_by_all_categories(self, output_collection, include_losers):
        nominees = self.handler.get_all()
        for nominee in nominees:
            if len(nominee['nobel']) >= 1 or include_losers:
                for nominator_id, nominations in nominee['nominations'].items(
                ):
                    nominator = self.handler.get_person_by_id(nominator_id)
                    min_year, max_year = self.get_min_max_year_from(
                        nominations)
                    relationship = BaseRelationship(
                        nominator_id, nominator['name'],
                        nominator['prizes'], nominee['id'], nominee['name'],
                        len(nominations), min_year, max_year,
                        nominee['prizes']).__dict__
                    for index, nobel in enumerate(nominee['nobel']):
                        relationship['success ' + str(index) +
                                     " prize"] = nobel['type']
                        for category_name, category_id in prizes.items():
                            success = self.calculate_success_by_category(
                                nominee, nominator_id, category_id, nobel)
                            relationship["success " + str(index) + " " +
                                         category_id] = success[0]
                    relationship = self.fill_relationship_prices_with_zeros(relationship)
                    self.handler.db[output_collection].insert_one(relationship)

    @staticmethod
    def fill_relationship_prices_with_zeros(relationship):
        if "success 0 prize" not in relationship:
            relationship['success 0 prize'] = None
            for category_name, category_id in prizes.items():
                relationship['success 0 ' + category_id] = None

        if "success 1 prize" not in relationship:
            relationship['success 1 prize'] = None
            for category_name, category_id in prizes.items():
                relationship['success 1 ' + category_id] = None
        return relationship

    # returns a tuple with the calculated succes and the number of nominations
    # which were used to calculate it
    def calculate_success_by_category(self, nominee, nominator_id, category,
                                      nobel):
        degree_of_succes = 0
        nominations = []
        year = int(nobel['year'])
        nobel_type = nobel['type']

        nominations, category_nominations = self.get_filtered_nominations(
            nominee['nominations'][nominator_id], category, year, nobel_type)
        if len(nominations) == 0 and len(category_nominations) == 0:
            return [-1, 0]
        elif len(nominations) == 0 and len(category_nominations) >= 1:
            return [
                -0,
                len(category_nominations),
            ]
        sumatory = 0
        min_year = max_year = int(nominations[0]['year'])
        for nomination in nominations:
            nomination_year = int(nomination['year'])
            if nomination_year <= year:
                sumatory += (1 / (year - nomination_year + 1))
                if nomination_year < min_year:
                    min_year = nomination_year
                if nomination_year > max_year:
                    max_year = nomination_year
        degree_of_succes = sumatory / (year - min_year + 1)

        return [degree_of_succes, len(nominations)]

    def get_filtered_nominations(self, nominations, category, year,
                                 nobel_type):
        filtered_nominations = []
        category_nominations = []
        for nomination in nominations:
            if int(nomination['year']) <= year:
                n_type = nomination['type']
                if category is None:
                    filtered_nominations.append(nomination)
                elif n_type == category and n_type == nobel_type:
                    filtered_nominations.append(nomination)
                if n_type == category:
                    category_nominations.append(nomination)

        return [filtered_nominations, category_nominations]

    def get_min_max_year_from(self, nominations):
        min_year = max_year = int(nominations[0]['year'])
        for nomination in nominations:
            nomination_year = int(nomination['year'])
            if nomination_year < min_year:
                min_year = nomination_year
            elif nomination_year > max_year:
                max_year = nomination_year
        return [min_year, max_year]

    def get_zero_success(self, output_collection):
        people = self.handler.get_losers()
        execpt = 0
        for person in people:
            all_nominations = person['nominations']
            if len(all_nominations) > 0:
                for nominator_id, nominations in all_nominations.items():
                    nominator = self.handler.get_person_by_id(nominator_id)
                    min_year, max_year = self.get_min_max_year_from(
                        nominations)
                    baseRelationship = self.get_base_relationship(
                        nominator_id, nominator, person, len(nominations),
                        min_year, max_year)
                    self.handler.db[output_collection].insert_one(
                        self.bloat_zeros(baseRelationship))
            else:
                execpt += 1

    @staticmethod
    def bloat_zeros(relationship):
        relationship['success 1 prize'] = None
        for i in range(1, 3, 1):
            relationship['success ' + str(i) + " prize"] = 0
            for category_name, category_id in prizes.items():
                relationship['success ' + str(i) + " " + category_id] = 0
        return relationship

    def get_base_relationship(self, nominator_id, nominator, nominee,
                              n_nominations, min_year, max_year):
        return BaseRelationship(nominator_id, nominator['name'],
                                nominator['prizes'], nominee['id'],
                                nominee['name'], n_nominations, min_year,
                                max_year, nominee['prizes']).__dict__

    def get_failed_nominations_for_each_year(self):
        # TODO change schema of db , this one doesn't have a table of just
        years = {}
        for person in self.handler.get_all():
            for nominatior_id, nominations in person['nominations'].items():
                for nomination in nominations:
                    year = nomination['year']
                    if not nomination_in_nobels(nomination, person['nobel']):
                        if year in years:
                            years[year] += 1
                        else:
                            years[year] = 1
        return years

    def export_winners_and_losers_to_xml_net(self, file_name):
        self.export_to_xml_net(file_name, "all_ch_success")

    def export_to_xml_net(self, file_name, relationship_collection):
        with open(file_name, 'w') as f:
            self.write_xml_header(f)
            f.write("<graph defaultedgetype=\"directed\" mode=\"static\">\n")
            f.write("<nodes>\n")
            # write nodes
            for person in self.handler.get_all():
                count = 0
                for nominatior_id, nominations in person['nominations'].items():
                    count += len(nominations)
                f.write(self.get_person_as_xml_node(person, count))
            f.write("</nodes>\n")
            # write edges
            success_handler = MongoHandler(relationship_collection)
            f.write("<edges>\n")
            for relationship in success_handler.get_all():
                f.write(self.get_relationship_as_xml(relationship))
            f.write("</edges>\n")
            f.write("</graph>\n")
            f.write("</gexf>")

    def export_to_xml_net_just_nominations(self, file_name):
        with open(file_name, 'w') as f:
            self.write_xml_header(f)
            f.write("<graph defaultedgetype=\"directed\" mode=\"static\">\n")
            f.write("<nodes>\n")
            for person in self.handler.get_all():
                # set count to 1 because we just want to weight the edges
                f.write(self.get_person_as_xml_node(person, 1))
            f.write("</nodes>\n")
            # write edges
            f.write("<edges>\n")
            for person in self.handler.get_all():
                nobel_year = self.get_first_ch_nomination_year(person['nobel'])
                for nominator_id, nominations in person['nominations'].items():
                    nominations_count = 0
                    for nomination in nominations:
                        if nobel_year is None or int(nomination['year']) <= int(nobel_year):
                            nominations_count += 1
                    if nominations_count > 0:
                        f.write("<edge source=\""+str(nominator_id)+"\"")
                        f.write(" target=\""+person['id']+"\"")
                        f.write(" id=\""+str(uuid.uuid1())+"\" ")
                        f.write(" weight=\""+str(nominations_count)+"\"></edge>\n")
            f.write("</edges>\n")
            f.write("</graph>\n")
            f.write("</gexf>")


    def get_relationship_as_xml(self, relationship):
        weight = self.get_best_success(relationship)
        if weight == -1:
            return ""
            # weight = ""
        else:
            if weight is None:
                weight = 0
            weight = "weight=\""+str(weight+1)+"\""
        return ("<edge source=\"" + str(relationship['nominator_id']) +
                "\" target=\"" + str(relationship['nominee_id']) +
                "\" id=\""+str(uuid.uuid1())+"\" "+weight+"></edge>\n")

    # just works for Chemistry
    def get_best_success(self, relationship):
        if relationship['success 1 C'] is None:
            return relationship['success 0 C']
        if relationship['success 0 C'] > relationship['success 1 C']:
            return relationship['success 0 C']
        return relationship['success 1 C']

    def write_xml_header(self, file):
        file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        file.write("<gexf xmlns=\"http://gexf.net/1.3\" version=\"1.3\" xmlns:viz=\"http://gexf.net/1.3/viz\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://gexf.net/1.3 http://gexf.net/1.3/gexf.xsd\">\n")

    def get_person_as_xml_node(self, person, number_of_nominations):
        return ("<node id=\""+str(person['id']) + "\" label=\"" +
                person['name'] + "\">\n<viz:size value=\"" +
                str(number_of_nominations)+"\"/></node>\n")

    # gets the winners which won the award x years apart from their first nomination
    def get_winners_first_nomination_apart(self, years):
        winners = []
        for person in self.handler.get_all():
            if self.is_first_nomination_of_person_x_years_apart_of_prize(person, years):
                winners.append({"id": person['id'],"name": person['name']})
        return winners

    # just works for the chemistry category
    def is_first_nomination_of_person_x_years_apart_of_prize(self, person, years):
        if person['winner']:
            for prize in person['nobel']:
                category = prize['type']
                first_nomination_year = None
                for nominator_id, nominations in person['nominations'].items(
                ):
                    for nomination in nominations:
                        if nomination['type'] == category and (first_nomination_year is None or nomination['year'] < first_nomination_year):
                            first_nomination_year = nomination['year']
                if first_nomination_year is not None and (
                    self.year_is_far_by_x_years(
                        prize['year'], first_nomination_year, years)):
                    return True
        return False

    def year_is_far_by_x_years(self, f_year, s_year, distance):
        actual_distance = int(f_year) - int(s_year)
        return actual_distance == distance

    def get_all_ch_losers(self):
        losers = []
        for person in self.handler.get_all():
            loser, nominations_count, years = self.get_nomination_data(person)
            if loser and nominations_count > 0:
                losers.append({"name": person['name'], "id": person['id'], "nom_count": nominations_count, "n_years": str(len(years))})
        return losers

    def get_nomination_data(self, person):
        # loser = True
        nominations_count = 0
        years = []
        nobel_year = self.get_first_ch_nomination_year(person['nobel'])
        for nominator_id, nominations in person['nominations'].items(
        ):
            for nomination in nominations:
                if nobel_year is None or int(nomination['year']) <= int(nobel_year):
                    nominations_count += 1
                    if nomination['year'] not in years:
                        years.append(nomination['year'])

                #if nomination_in_nobels(nomination, person['nobel']):
                    # dont break here if you want to count the nominations after winning
                #    break
        return (nobel_year is None, nominations_count, years)

    def get_first_ch_nomination_year(self, nobels):
        min_year = None
        for nobel in nobels:
            if (min_year is None or int(nobel['year']) < min_year) and nobel['type'] == "C" :
                min_year = int(nobel['year'])
        return min_year

    def get_all_ch_winners(self):
        winners = []
        for person in self.handler.get_all():
            loser, nominations_count, years = self.get_nomination_data(person)
            if not loser and nominations_count > 0:
                winners.append({"name": person['name'], "id": person['id'], "nom_count": nominations_count, "n_years": str(len(years))})
        return winners

    def write_all_ch_losers_to_file(self):
        with open("losers", 'w') as f:
            f.write(str(self.get_all_ch_losers()))

    def output_nominations_to_xml(self, xml_file):
        return False


def clean_all_names():
    people_handler = MongoHandler("people")
    for person in people_handler.get_all():
        person['name'] = html.unescape(person['name'])
        people_handler.update_person(person)
    success_handler = MongoHandler("ch_success")
    for relationship in success_handler.get_all():
        relationship['nominator_id'] = html.unescape(relationship['nominator_id'])
        relationship['nominee_id'] = html.unescape(relationship['nominee_id'])
        success_handler.update_person(relationship)


# checks if the nomination was succesfull
def nomination_in_nobels(nomination, nobels):
    for nobel in nobels:
        if (nobel['type'] == nomination['type'] and
                int(nobel['year']) >= int(nomination['year'])):
            return True
    return False


# adds a missing prize to the given nominee
def add_ch_win_to_nominee(nominee_id: str, year):
    handler = MongoHandler("people")
    person = handler.get_person_by_id(nominee_id)
    person['winner'] = True
    person['nobel'] = person['nobel'] + [{"type": "C", "year": str(year), "name": "Prize in Chemistry"}]
    person['prizes'] = person['prizes'] + "C in "+str(year)+ "|"
    handler.update_person(person)


# def main(output_collection):
    # handler = MongoHandler("people")
    # helper = NobelHelper(handler)
    # helper.get_succes_by_all_categories(output_collection)
    # helper.get_zero_success(output_collection)


# if __name__ == "__main__":
#     main(sys.argv[1])
