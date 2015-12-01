from lxml import etree
import csv

from gla.gla_utils import TagBuilder, CollexValidator


def main(ns_name, ns_address, input_filename, output_filename):
    tb = TagBuilder(ns_name, ns_address)
    tree = tb.root()
    with open(input_filename, mode="r") as f:
        reader = csv.DictReader(f)
        for dct in reader:
            for key, value in dct.items():
                dct[key] = value.decode("utf-8")
            tree.append(make_item_rdf(dct, tb, ns_name=ns_name))

    validator = CollexValidator(ns_name, ns_address)
    print(validator.validate_rdf(tree))

    with open(output_filename, mode="w") as f:
        f.write(etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="utf-8"))


def make_item_rdf(dct, tb, ns_name):
    item = tb.item(weblink=dct["about_link"])
    type_ = normalize_type(get_format_text(dct))

    # required fields
    item.append(tb.seeAlso(weblink=dct["about_link"]))
    item.append(tb.archive(ns_name))
    item.append(tb.federation("GLA"))
    item.append(tb.discipline("History"))
    if type_ == "Map":
        item.append(tb.discipline("Geography"))
    item.append(tb.thumbnail(weblink=dct.get("thumb_link", "")))

    if type_ == "Still Image":
        item.append(tb.genre("Photograph"))
    else:
        item.append(tb.genre("Unspecified"))

    item.append(make_date_tag(dct, tb))

    item.append(tb.type_(type_))
    item.append(tb.title(construct_title(dct)))

    # optional fields
    for key, value in dct.items():
        value = value.strip()
        if not value:
            continue
        if "subject" in key or "location" in key:
            item.append(tb.subject(value))
        if "creator" in key:
            item.append(tb.role(value, "CRE"))
        if "identifier" in key:
            item.append(tb.identifier(" ".join(value.split())))
        if "description" in key:
            item.append(tb.alternative_title(value))
        if "source" in key:
            item.append(tb.source(value))


    return item


def make_date_tag(dct, tb):
    year_begin = dct.get("year_begin", "")
    year_end = dct.get("year_end", "")
    if year_begin and year_end:
        string = "c. {}-{}".format(year_begin, year_end)
        formal_string = "{},{}".format(year_begin, year_end)

        return tb.collex_date(label=string, value=formal_string)

    elif year_begin:
        return tb.collex_date(label=year_begin, value=year_begin)
    elif year_end:
        return tb.collex_date(label=year_end, value=year_end)
    else:
        return tb.dc_date("Uncertain")

def construct_title(dct):
    source = unicode(dct.get("source", "")).strip()
    title = unicode(dct.get("title", "")).strip()
    if source:
        title = u"{}: {}".format(source, title)

    return title.replace(u"&", u"&amp;")


def get_format_text(dct):
    format = dct.get("format", "")
    if not format:
        format = dct.get("type", "")
    return format


def normalize_type(string):
    illustrations = ["illustration", "woodcut", "engraving", "etching"]
    books = ["book", "dictionar", "text"]
    string = string.lower()
    if "map" in string:
        return "Map"
    elif "drawing" in string:
        return "Drawing"
    elif "manuscript" in string:
        return "Manuscript"
    elif any([word in string for word in illustrations]):
        return "Illustration"
    elif any([word in string for word in books]):
        return "Codex"
    elif "image" in string or "photograph" in string:
        return "Still Image"
    else:
        return "Codex"

if __name__ == "__main__":
    main(ns_name="nb-ayer",
         ns_address="https://www.nb-ayer.org/fake-schema#",
         input_filename="newberry_ayer.csv",
         output_filename="newberry_ayer.xml")
