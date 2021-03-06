import os
from unittest import TestCase, skip

import pytest
import requests_mock

from data import responses
from models import InitiativeImport, InitiativeGroup
from platformen.nlvoorelkaar import NLvoorElkaar


class TestNLvoorElkaarSupplyPlatformSource(TestCase):

    @requests_mock.Mocker()
    def setUp(self, request_mock):
        self.response = responses.read("nlvoorelkaar_supply.html")

        scraper = NLvoorElkaar()
        self.source = scraper._sources[0]

        self.url = "https://www.nlvoorelkaar.nl/hulpaanbod/179582"
        request_mock.get(self.url, text=self.response, status_code=200)
        self.request_mock = request_mock

        self.actual = InitiativeImport(source_id=179582, source_uri=self.url)
        scraper._sources[0].complete(self.actual)

    def test_table_name(self):
        assert self.actual.name == "Aanbod van Joeri"

    def test_table_category(self):
        assert self.actual.category == "Coronahulp"

    def test_table_organisation_kind(self):
        assert self.actual.organisation_kind == "een vrijwilliger"

    def test_helpsupply_organiser(self):
        assert(self.actual.organiser == "Joeri")

    def test_description(self):
        assert self.actual.description.startswith("Naast het schrijven van mijn scriptie zou ik graag mensen helpen")

    def test_alternative_place_regex(self):
        assert self.actual.location == "Amstelveen"

    @skip("Test methods for debugging specific items")
    def test_missing_plaats(self):
        scraper = NLvoorElkaar()
        item = scraper._sources[0].complete(InitiativeImport(
            source_id=179582,
            source_uri="https://www.nlvoorelkaar.nl/hulpaanbod/179582"
        ))


class TestNLvoorElkaarDemandPlatformSource(TestCase):

    @requests_mock.Mocker()
    def setUp(self, request_mock):
        self.response = responses.read("nlvoorelkaar_demand.html")
 
        scraper = NLvoorElkaar()
        self.source = scraper._sources[1]

        self.url = "https://www.nlvoorelkaar.nl/hulpvragen/183242"
        request_mock.get(self.url, text=self.response, status_code=200)
        self.request_mock = request_mock

        self.actual = InitiativeImport(source_id=183242, source_uri=self.url)
        scraper._sources[1].complete(self.actual)

    def test_table_name(self):
        assert self.actual.name == "Huishoudelijke ondersteuning en boodschappen"

    def test_table_category(self):
        assert self.actual.category == "Boodschappen, Huishoudelijk, Coronahulp"

    def test_helpdemand_organiser(self):
        assert(self.actual.organiser == "Gemeente Roosendaal")

    def test_description(self):
        assert self.actual.description.startswith("Mevrouw heeft haar arm gebroken en is opzoek naar iemand die haar kan ondersteunen")

    def test_alternative_place_regex(self):
        assert self.actual.location == "West (Roosendaal)"

    @pytest.mark.skip(reason="Test methods for debugging specific items")
    def test_missing_plaats(self):
        scraper = NLvoorElkaar()
        item = scraper._sources[0].complete(InitiativeImport(
            source_id=179582,
            source_uri="https://www.nlvoorelkaar.nl/hulpvragen/183242"
        ))


class TestNLvoorElkaarPlatform(TestCase):
    def setUp(self):
        self.scraper = NLvoorElkaar()

    def test_should_support_group_restricting(self):
        assert self.scraper.supports_group(InitiativeGroup.SUPPLY)
        assert self.scraper.supports_group(InitiativeGroup.DEMAND)

    def test_should_have_deleted_other_source(self):
        self.scraper.set_group(InitiativeGroup.DEMAND)
        assert 1 == len(self.scraper.sources())
        assert InitiativeGroup.DEMAND == self.scraper.sources()[0].config.group