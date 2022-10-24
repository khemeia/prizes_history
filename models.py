class Person:
    def __init__(self):
        self.name = None
        self.id = None
        self.gender = None
        self.birth = None
        self.death = None
        self.profession = None
        self.university = None
        self.city = None
        self.state = None
        self.country = None
        self.winner = False
        self.nobel = []
        self.nominations = {}
        self.prizes = ""


class BaseRelationship:
    def __init__(self, nominator_id, nominator_name, nominator_NP, nominee_id,
                 nominee_name, n_nominations, first_nomination, last_nomin_y,
                 nominee_NP):
        self.nominator_id = nominator_id
        self.nominator_name = nominator_name
        self.nominator_NP = nominator_NP
        self.nominee_id = nominee_id
        self.nominee_name = nominee_name
        self.n_nominations = n_nominations
        self.first_nomin_y = first_nomination
        self.last_nomin_y = last_nomin_y
        self.nominee_NP = nominee_NP
