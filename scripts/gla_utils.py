import datetime
from lxml import etree
import re


class TagBuilder:
    def __init__(self, namespace, address):
        self.namespace = namespace
        self.address = address

        self.ns = {"dc": "http://purl.org/dc/elements/1.1/",
                   "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                   "foaf": "http://xmlns.com/foaf/0.1/",
                   "xsd": "http://www.w3.org/2001/XMLSchema#",
                   "owl": "http://www.w3.org/2002/07/owl#",
                   "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                   "role": "http://www.loc.gov/loc.terms/relators/",
                   "collex": "http://www.collex.org/schema#",
                   "dcterms": "http://purl.org/dc/terms/",
                   self.namespace: self.address}

    def build_ns_tag(self, ns_key, tag_name, attrib=tuple(), text=""):
        e = etree.Element("{{{0}}}{1}".format(self.ns[ns_key], tag_name))
        if text:
            e.text = text
        if attrib:
            ns, link = attrib
            e.attrib[ns] = link
        return e

    def root(self):
        return etree.Element("{{{}}}RDF".format(self.ns['rdf']), nsmap=self.ns)

    def item(self, weblink):
        attrib = ("{{{0}}}about".format(self.ns["rdf"]), weblink)
        return self.build_ns_tag(self.namespace, self.namespace, attrib=attrib)

    def alternative_title(self, text):
        return self.build_ns_tag("dcterms", "alternative", text=text)

    def archive(self, text):
        return self.build_ns_tag("collex", "archive", text=text)

    def collex_date(self, label="", value=""):
        collex_tag = self.build_ns_tag(ns_key="collex", tag_name="date")
        collex_label = self.build_ns_tag(ns_key="rdfs", tag_name="label", text=label)
        collex_value = self.build_ns_tag(ns_key="rdf", tag_name="value", text=value)

        collex_tag.append(collex_label)
        collex_tag.append(collex_value)

        date = self.dc_date("")
        date.append(collex_tag)

        return date

    def dc_date(self, text):
        return self.build_ns_tag("dc", "date", text=text)

    def discipline(self, text):
        return self.build_ns_tag("collex", "discipline", text=text)

    def federation(self, text="GLA"):
        return self.build_ns_tag("collex", "federation", text=text)

    def genre(self, text):
        return self.build_ns_tag("collex", "genre", text=text)

    def identifier(self, text):
        return self.build_ns_tag("dc", "identifier", text=text)

    def language(self, text):
        return self.build_ns_tag("dc", "language", text=text)

    def role(self, text, role_type):
        return self.build_ns_tag("role", role_type.upper(), text=text)

    def seeAlso(self, weblink):
        attrib = ("{{{0}}}resource".format(self.ns["rdf"]), weblink)
        return self.build_ns_tag("rdfs", "seeAlso", attrib=attrib)

    def source(self, text):
        return self.build_ns_tag("dc", "source", text=text)

    def subject(self, text):
        return self.build_ns_tag("dc", "subject", text=text)

    def thumbnail(self, weblink):
        attrib = ("{{{0}}}resource".format(self.ns["rdf"]), weblink)
        return self.build_ns_tag("collex", "thumbnail", attrib=attrib)

    def title(self, text):
        return self.build_ns_tag("dc", "title", text=text)

    def type_(self, text):
        return self.build_ns_tag("dc", "type", text=text)


class ValidationException(Exception):
    pass



class CollexValidator:
    def __init__(self, local_ns, local_ns_address):
        self.ns = {"dc": "http://purl.org/dc/elements/1.1/",
                   "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                   "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                   "role": "http://www.loc.gov/loc.terms/relators/",
                   "collex": "http://www.collex.org/schema#",
                   "dcterms": "http://purl.org/dc/terms/",
                   local_ns: local_ns_address}

        self.roles = ["AUT", "EDT", "PBL", "TRL", "CRE", "ETR", "EGR",
                      "OWN", "ART", "ARC", "BND", "BKD", "BKP", "CLL",
                      "CTG", "COL", "CLR", "CWT", "COM", "CMT", "CRE",
                      "DUB", "FAC", "ILU", "ILL", "LTG", "PRT", "POP",
                      "PRM", "RPS", "RBR", "SCR", "SCL", "TYD", "TYG",
                      "WDE", "WDC"]

        self.required_fields = ["rdfs:seeAlso",
                                "collex:federation",
                                "collex:archive",
                                "dc:type",
                                "dc:title",
                                "collex:genre",
                                "collex:discipline",
                                "dc:date"]

        self.single_fields = ["dc:language",
                              "dc:title",
                              "collex:fulltext",
                              "dcterms:hasPart",
                              "collex:thumbnail",
                              "collex:image",
                              "collex:text",
                              "collex:source_sgml",
                              "collex:source_html",
                              "collex:freeculture",
                              "collex:date",
                              "collex:archive",
                              "rdf:value",
                              "rdfs:label"]

        self.genre_terms = ["Bibliography",
                            "Catalog",
                            "Citation",
                            "Collection",
                            "Correspondence",
                            "Criticism",
                            "Drama",
                            "Ephemera"
                            "Fiction",
                            "Historiography",
                            "Law",
                            "Life Writing",
                            "Liturgy",
                            "Musical Analysis",
                            "Music, Other",
                            "Musical Recording",
                            "Musical Score",
                            "Nonfiction",
                            "Paratext",
                            "Philosophy",
                            "Photograph",
                            "Poetry",
                            "Religion",
                            "Religion, Other",
                            "Reference Works",
                            "Review",
                            "Scripture",
                            "Sermon",
                            "Translation",
                            "Travel Writing",
                            "Unspecified",
                            "Visual Art"]

        self.discipline_terms = ["Anthropology",
                                 "Archaeology",
                                 "Architecture",
                                 "Art History",
                                 "Book History",
                                 "Classics and Ancient History",
                                 "Ethnic Studies",
                                 "Film Studies",
                                 "Gender Studies",
                                 "Geography",
                                 "History",
                                 "Law",
                                 "Literature",
                                 "Manuscript Studies",
                                 "Math",
                                 "Musicology",
                                 "Philosophy",
                                 "Religious Studies",
                                 "Science",
                                 "Theater Studies"]

    def validate_rdf(self, tree):
        errors = ""
        for item in tree.xpath("//rdf:RDF", namespaces=self.ns)[0].iterchildren():
            error_string = self.validate_object(item)
            if error_string:
                errors += error_string + "\n"
        return errors

    def validate_object(self, item):
        error_string = ""

        error_string += self.check_required_fields(item)
        error_string += self.check_for_role(item)
        error_string += self.check_discipline_terms(item)
        error_string += self.check_genre_terms(item)
        error_string += self.check_fields_that_can_only_have_one_instance(item)
        error_string += self.check_date_fields(item)

        return error_string

    def check_date_fields(self, item):
        error_string = ""
        for date in self.get_child_tags(tagname="dc:date", parent=item):
            error_string += self.validate_date(date)
        return error_string

    def check_fields_that_can_only_have_one_instance(self, item):
        error_string = ""
        for field in self.single_fields:
            if len(self.get_child_tags(tagname=field, parent=item)) > 1:
                error_string += "Too many {} fields -- can only be one".format(field)
        return error_string

    def check_required_fields(self, item):
        error_string = ""
        for field in self.required_fields:
            if len(self.get_child_tags(tagname=field, parent=item)) == 0:
                error_string += "Required field {} is missing".format(field)
        return error_string

    def check_for_role(self, item):
        error_string = ""
        roles = []
        for role in self.roles:
            roles += self.get_child_tags(tagname="role:{}".format(role), parent=item)

        if not roles:
            error_string = "At least one role is required"

        return error_string

    def check_discipline_terms(self, item):
        error_string = ""
        discipline_tags = self.get_child_tags(tagname="collex:discipline", parent=item)
        for tag in discipline_tags:
            if not any([tag.text == discipline for discipline in self.discipline_terms]):
                error_string += "{} is not a valid discipline term".format(tag.text)
        return error_string

    def check_genre_terms(self, item):
        error_string = ""
        genre_tags = self.get_child_tags(tagname="collex:genre", parent=item)
        for tag in genre_tags:
            if not any([tag.text == genre for genre in self.genre_terms]):
                error_string += "{} is not a valid genre term".format(tag.text)
        return error_string

    # TODO: write tests for disciplines and genres

    def get_child_tags(self, tagname, parent):
        return parent.xpath("{}".format(tagname), namespaces=self.ns)

    def validate_date(self, date_element):
        if len(date_element) > 0:
            return self.validate_collex_date_tag(date_element)

        date = date_element.text

        if not date:
            return "There must be a date (no text found in dc:date tag)"

        if date == "Uncertain":
            return ""

        if not is_integer(date):
            return "Date tags only accept numeric characters"

        if int(date) > datetime.date.today().year:
            return "Date is in the future!"

        return ""

    def validate_collex_date_tag(self, dc_date_element):
        if len(dc_date_element) > 1:
            return "Too many collex:date tags in the dc:date field -- only one allowed"

        collex_date_element = dc_date_element[0]
        if len(collex_date_element) != 2:
            return "Collex date element does not have the proper single rdfs:label and single rdf:value field"

        if len(collex_date_element.xpath("rdfs:label", namespaces=self.ns)) != 1:
            return "Either zero or too many rdfs:label tags in the collex:date element -- must be exactly one"

        if len(collex_date_element.xpath("rdf:value", namespaces=self.ns)) != 1:
            return "Either zero or too many rdf:value tags in the collex:date element -- must be exactly one"

        value = collex_date_element.xpath("rdf:value", namespaces=self.ns)[0]
        if not self.is_valid_collex_date_value(value.text):
            return "The rdf:value portion of the collex:date tag is not formatted correctly"

        return ""

    @staticmethod
    def is_valid_collex_date_value(text):
        allowed_chars = "1234567890 ,u"
        if not all([char in allowed_chars for char in text]):
            return False

        year_regex = r"[012][0-9][0-9u][0-9u]"
        if len(re.findall(year_regex, text)) == 0:
            return False

        return True


def is_integer(date):
    try:
        int(date)
        return True
    except TypeError:
        return False
    except ValueError:
        return False



