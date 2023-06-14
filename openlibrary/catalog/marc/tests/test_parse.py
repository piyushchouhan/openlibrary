import pytest

from openlibrary.catalog.marc.parse import (
    read_author_person,
    read_edition,
    NoTitle,
    SeeAlsoAsTitle,
)
from openlibrary.catalog.marc.marc_binary import MarcBinary
from openlibrary.catalog.marc.marc_xml import DataField, MarcXml
from lxml import etree
from pathlib import Path
import json
from collections.abc import Iterable

collection_tag = '{http://www.loc.gov/MARC21/slim}collection'
record_tag = '{http://www.loc.gov/MARC21/slim}record'

xml_samples = [
    '39002054008678.yale.edu',
    'flatlandromanceo00abbouoft',
    'nybc200247',
    'secretcodeofsucc00stjo',
    'warofrebellionco1473unit',
    'zweibchersatir01horauoft',
    'onquietcomedyint00brid',
    '00schlgoog',
    '0descriptionofta1682unit',
    '1733mmoiresdel00vill',
    '13dipolarcycload00burk',
    'bijouorannualofl1828cole',
    'soilsurveyrepor00statgoog',
    'cu31924091184469',  # MARC XML collection record
    'engineercorpsofh00sher',
]

bin_samples = [
    'bijouorannualofl1828cole_meta.mrc',
    'onquietcomedyint00brid_meta.mrc',  # LCCN with leading characters
    'merchantsfromcat00ben_meta.mrc',
    'memoirsofjosephf00fouc_meta.mrc',  # MARC8 encoded with e-acute
    'equalsign_title.mrc',  # Title ending in '='
    'bpl_0486266893.mrc',
    'flatlandromanceo00abbouoft_meta.mrc',
    'histoirereligieu05cr_meta.mrc',
    'ithaca_college_75002321.mrc',
    'lc_0444897283.mrc',
    'lc_1416500308.mrc',
    'ocm00400866.mrc',
    'secretcodeofsucc00stjo_meta.mrc',
    'uoft_4351105_1626.mrc',
    'warofrebellionco1473unit_meta.mrc',
    'wrapped_lines.mrc',
    'wwu_51323556.mrc',
    'zweibchersatir01horauoft_meta.mrc',
    'talis_two_authors.mrc',
    'talis_no_title.mrc',
    'talis_740.mrc',
    'talis_245p.mrc',
    'talis_856.mrc',
    'talis_multi_work_tiles.mrc',
    'talis_empty_245.mrc',
    'ithaca_two_856u.mrc',
    'collingswood_bad_008.mrc',
    'collingswood_520aa.mrc',
    'upei_broken_008.mrc',
    'upei_short_008.mrc',
    'diebrokeradical400poll_meta.mrc',
    'cu31924091184469_meta.mrc',
    'engineercorpsofh00sher_meta.mrc',
    'henrywardbeecher00robauoft_meta.mrc',
    'thewilliamsrecord_vol29b_meta.mrc',
    '13dipolarcycload00burk_meta.mrc',
    '880_alternate_script.mrc',
    '880_table_of_contents.mrc',
    '880_Nihon_no_chasho.mrc',
    '880_publisher_unlinked.mrc',
    '880_arabic_french_many_linkages.mrc',
    'test-publish-sn-sl.mrc',
    'test-publish-sn-sl-nd.mrc',
]

TEST_DATA = f'{Path(__file__).parent}/test_data'


class TestParseMARCXML:
    @pytest.mark.parametrize('i', xml_samples)
    def test_xml(self, i):
        expect_filename = f'{TEST_DATA}/xml_expect/{i}.json'
        path = f'{TEST_DATA}/xml_input/{i}_marc.xml'
        element = etree.parse(open(path)).getroot()
        # Handle MARC XML collection elements in our test_data expectations:
        if element.tag == collection_tag and element[0].tag == record_tag:
            element = element[0]
        rec = MarcXml(element)
        edition_marc_xml = read_edition(rec)
        assert edition_marc_xml
        j = json.load(open(expect_filename))
        assert j, 'Unable to open test data: %s' % expect_filename
        msg = (
            f'Processed MARCXML values do not match expectations in {expect_filename}.'
        )
        assert sorted(edition_marc_xml) == sorted(j), msg
        msg += ' Key: '
        for key, value in edition_marc_xml.items():
            if isinstance(value, Iterable):  # can not sort a list of dicts
                assert len(value) == len(j[key]), msg + key
                for item in j[key]:
                    assert item in value, msg + key
            else:
                assert value == j[key], msg + key


class TestParseMARCBinary:
    @pytest.mark.parametrize('i', bin_samples)
    def test_binary(self, i):
        expect_filename = f'{TEST_DATA}/bin_expect/{i}'.replace('.mrc', '.json')
        with open(f'{TEST_DATA}/bin_input/{i}', 'rb') as f:
            rec = MarcBinary(f.read())
        edition_marc_bin = read_edition(rec)
        assert edition_marc_bin
        if not Path(expect_filename).is_file():
            # Missing test expectations file. Create a template from the input, but fail the current test.
            data = json.dumps(edition_marc_bin, indent=2)
            pytest.fail(
                f'Expectations file {expect_filename} not found: Please review and commit this JSON:\n{data}'
            )
        j = json.load(open(expect_filename))
        assert j, f'Unable to open test data: {expect_filename}'
        assert sorted(edition_marc_bin) == sorted(
            j
        ), f'Processed binary MARC fields do not match expectations in {expect_filename}'
        msg = f'Processed binary MARC values do not match expectations in {expect_filename}'
        for key, value in edition_marc_bin.items():
            if isinstance(value, Iterable):  # can not sort a list of dicts
                assert len(value) == len(j[key]), msg
                for item in j[key]:
                    assert item in value, f'{msg}. Key: {key}'
            else:
                assert value == j[key], msg

    def test_raises_see_also(self):
        filename = f'{TEST_DATA}/bin_input/talis_see_also.mrc'
        with open(filename, 'rb') as f:
            rec = MarcBinary(f.read())
        with pytest.raises(SeeAlsoAsTitle):
            read_edition(rec)

    def test_raises_no_title(self):
        filename = f'{TEST_DATA}/bin_input/talis_no_title2.mrc'
        with open(filename, 'rb') as f:
            rec = MarcBinary(f.read())
        with pytest.raises(NoTitle):
            read_edition(rec)


class TestParse:
    def test_read_author_person(self):
        xml_author = """
        <datafield xmlns="http://www.loc.gov/MARC21/slim" tag="100" ind1="1" ind2="0">
          <subfield code="a">Rein, Wilhelm,</subfield>
          <subfield code="d">1809-1865</subfield>
        </datafield>"""
        test_field = DataField(None, etree.fromstring(xml_author))
        result = read_author_person(test_field)

        # Name order remains unchanged from MARC order
        assert result['name'] == result['personal_name'] == 'Rein, Wilhelm'
        assert result['birth_date'] == '1809'
        assert result['death_date'] == '1865'
        assert result['entity_type'] == 'person'
