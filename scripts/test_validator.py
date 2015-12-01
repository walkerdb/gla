from copy import deepcopy
import unittest

from lxml import etree

from gla_utils import CollexValidator

class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = CollexValidator(local_ns="test", local_ns_address="http://test.org/#")
        self.tree = etree.parse("test_rdf.rdf")
        self.test_item = self.tree.xpath("//test:test", namespaces=self.validator.ns)[0]

    def test_passes_if_item_meets_minimum_reqs(self):
        self.assertEquals("", self.validator.validate_object(self.test_item))

    def test_invalid_if_item_is_missing_a_required_field(self):
        invalid_item = deepcopy(self.test_item)
        dc_title = invalid_item.xpath("dc:title", namespaces=self.validator.ns)[0]
        invalid_item.remove(dc_title)

        self.assertEquals("Required field dc:title is missing\n", self.validator.validate_object(invalid_item))
        del invalid_item

    def test_invalid_if_item_has_more_than_one_field_with_singular_restriction(self):
        invalid_item = deepcopy(self.test_item)
        tag = etree.Element("{{{0}}}title".format(self.validator.ns["dc"]))
        tag.text = "extra title tag"
        invalid_item.append(tag)

        self.assertEquals("Too many dc:title unique_fields -- can only be one\n", self.validator.validate_object(invalid_item))
        del invalid_item

    def test_invalid_dc_dates_are_caught(self):
        date_tag = etree.Element("{{{0}}}date".format(self.validator.ns["dc"]))

        date_tag.text = "1982"
        self.assertEquals("", self.validator.validate_date(date_tag))

        date_tag.text = "Uncertain"
        self.assertEquals("", self.validator.validate_date(date_tag))

        date_tag.text = "123a"
        self.assertEquals("Date tags only accept numeric characters", self.validator.validate_date(date_tag))

        date_tag.text = "2100"
        self.assertEquals("Date is in the future!", self.validator.validate_date(date_tag))

    def test_valid_collex_dates_pass(self):
        date_tag = etree.Element("{{{0}}}date".format(self.validator.ns["dc"]))
        date_tag.append(self.make_collex_date(label="1900-1952", value="1900, 1952"))

        self.assertEquals("", self.validator.validate_date(date_tag))

    def test_catch_multiple_collex_dates_in_one_dcdate(self):
        date_tag = etree.Element("{{{0}}}date".format(self.validator.ns["dc"]))
        date_tag.append(self.make_collex_date(label="1900-1952", value="1900, 1952"))
        date_tag.append(self.make_collex_date(label="1900-1952", value="1900, 1952"))

        self.assertEquals("Too many collex:date tags in the dc:date field -- only one allowed", self.validator.validate_date(date_tag))

    def test_collex_date_value_valid_if_follows_standard(self):
        self.assertTrue(self.validator.is_valid_collex_date_value("1991, 2000"))
        self.assertTrue(self.validator.is_valid_collex_date_value("199u"))
        self.assertTrue(self.validator.is_valid_collex_date_value("19uu,200u"))

    def test_collex_date_value_invalid_if_not_standard(self):
        self.assertFalse(self.validator.is_valid_collex_date_value("1991-2000"))
        self.assertFalse(self.validator.is_valid_collex_date_value("190, 12"))
        self.assertFalse(self.validator.is_valid_collex_date_value("3000"))

    def make_collex_date(self, label="", value=""):
        collex_tag = etree.Element("{{{0}}}date".format(self.validator.ns["collex"]))
        collex_label = etree.Element("{{{0}}}label".format(self.validator.ns["rdfs"]))
        collex_value = etree.Element("{{{0}}}value".format(self.validator.ns["rdf"]))

        collex_label.text = label
        collex_value.text = value
        collex_tag.append(collex_label)
        collex_tag.append(collex_value)

        return collex_tag