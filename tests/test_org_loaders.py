import tempfile
import unittest
from pathlib import Path

from propdata.outreach.compliance import evaluate
from propdata.outreach.loaders.companies_house import CompaniesHouseSource
from propdata.outreach.loaders.hmrc_aml import HmrcAmlSource
from propdata.outreach.loaders.matching import (
    match_to_companies_house,
    normalise_name,
)
from propdata.outreach.models import (
    Campaign,
    Channel,
    Contact,
    LawfulBasis,
    LegalForm,
)
from propdata.outreach.store import OutreachStore

FIXTURES = Path(__file__).parent / "fixtures" / "registers"
CH_FILE = FIXTURES / "companies_house_sample.csv"
HMRC_FILE = FIXTURES / "hmrc_aml_sample.csv"


class TestCompaniesHouse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orgs = CompaniesHouseSource().load_all(CH_FILE)
        cls.by_name = {o.name: o for o in cls.orgs}

    def test_legal_form_comes_from_the_register(self):
        self.assertEqual(
            self.by_name["THAMES RESIDENTIAL LTD"].legal_form,
            LegalForm.LIMITED_COMPANY,
        )
        self.assertEqual(
            self.by_name["NORTHERN LETTINGS LLP"].legal_form, LegalForm.LLP
        )
        self.assertEqual(self.by_name["BIG PROPERTY PLC"].legal_form, LegalForm.PLC)

    def test_scottish_partnership_is_recognised(self):
        # Separate legal personality, unlike partnerships elsewhere in the UK.
        self.assertEqual(
            self.by_name["HIGHLAND PROPERTY PARTNERSHIP"].legal_form,
            LegalForm.SCOTTISH_PARTNERSHIP,
        )

    def test_unmapped_category_falls_back_to_other_and_says_so(self):
        # OTHER is not corporate for PECR, so an unmapped category fails safe.
        org = self.by_name["ODD FORM ESTATES"]
        self.assertEqual(org.legal_form, LegalForm.OTHER)
        self.assertIn("unmapped CompanyCategory", org.notes)

    def test_dissolved_companies_are_excluded(self):
        self.assertNotIn("DISSOLVED AGENTS LTD", self.by_name)

    def test_non_estate_agency_sic_codes_are_excluded(self):
        self.assertNotIn("CORNER SHOP LTD", self.by_name)

    def test_no_contact_details_are_produced(self):
        # The register publishes no email addresses; this loader must not
        # appear to supply a send list.
        self.assertTrue(all(not hasattr(o, "email") for o in self.orgs))


class TestHmrcAml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orgs = HmrcAmlSource().load_all(HMRC_FILE)
        cls.by_name = {o.name: o for o in cls.orgs}

    def test_legal_form_is_never_inferred_from_the_name(self):
        # "Thames Residential Ltd" is almost certainly a company, and almost
        # certainly is not evidence. Guessing corporate authorises an email.
        org = self.by_name["Thames Residential Ltd"]
        self.assertEqual(org.legal_form, LegalForm.UNKNOWN)
        self.assertIn("suggests incorporation", org.notes)
        self.assertIn("not acted on", org.notes)

    def test_sole_trader_style_entries_are_kept(self):
        # The coverage Companies House structurally cannot provide.
        self.assertIn("J. Smith Estates", self.by_name)

    def test_deregistered_is_not_read_as_registered(self):
        # "deregistered" contains "registered" as a substring.
        self.assertNotIn("Deregistered Agents", self.by_name)

    def test_other_sectors_are_excluded(self):
        self.assertNotIn("Some Accountants LLP", self.by_name)

    def test_source_declares_it_cannot_evidence_legal_form(self):
        self.assertFalse(HmrcAmlSource.evidences_legal_form)
        self.assertTrue(CompaniesHouseSource.evidences_legal_form)


class TestNameNormalisation(unittest.TestCase):
    def test_legal_suffixes_are_stripped_repeatedly(self):
        self.assertEqual(normalise_name("The Smith Estates Co Ltd"), "smith estates")
        self.assertEqual(normalise_name("SMITH ESTATES"), "smith estates")
        self.assertEqual(normalise_name("Smith Estates Limited"), "smith estates")

    def test_a_name_of_only_suffixes_does_not_collapse_to_empty(self):
        # Otherwise every such name would match every other.
        self.assertTrue(normalise_name("The Company Ltd"))
        self.assertNotEqual(normalise_name("The Company Ltd"), normalise_name("Ltd"))

    def test_non_legal_words_are_kept(self):
        # Stripping "group" or "properties" would merge distinct businesses.
        self.assertIn("group", normalise_name("Smith Group Ltd"))


class TestMatching(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.companies = CompaniesHouseSource().load_all(CH_FILE)
        cls.report = match_to_companies_house(
            HmrcAmlSource().load_all(HMRC_FILE), cls.companies
        )

    def test_unique_match_evidences_the_legal_form(self):
        matched = {o.name: o for o in self.report.matched}
        self.assertEqual(
            matched["Thames Residential Ltd"].legal_form, LegalForm.LIMITED_COMPANY
        )
        self.assertEqual(matched["Thames Residential Ltd"].company_number, "01234567")
        self.assertIn("evidenced by Companies House", matched["Thames Residential Ltd"].notes)

    def test_ambiguous_match_is_refused_not_guessed(self):
        # Two companies share the name once suffixes are stripped. Picking
        # either would assign a legal form on a coin flip.
        self.assertIn("Ambiguous Estates Ltd", self.report.ambiguous)
        unmatched = {o.name: o for o in self.report.unmatched}
        self.assertEqual(
            unmatched["Ambiguous Estates Ltd"].legal_form, LegalForm.UNKNOWN
        )
        self.assertIn("share this name", unmatched["Ambiguous Estates Ltd"].notes)

    def test_unmatched_is_flagged_as_probable_sole_trader(self):
        unmatched = {o.name: o for o in self.report.unmatched}
        self.assertIn("likely", unmatched["J. Smith Estates"].notes)

    def test_inputs_are_not_mutated(self):
        originals = HmrcAmlSource().load_all(HMRC_FILE)
        match_to_companies_house(originals, self.companies)
        self.assertTrue(all(o.legal_form is LegalForm.UNKNOWN for o in originals))


class TestLoaderToGate(unittest.TestCase):
    """The chain end to end: register -> match -> compliance decision."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = OutreachStore(Path(self._tmp.name) / "orgs.db")
        companies = CompaniesHouseSource().load_all(CH_FILE)
        report = match_to_companies_house(
            HmrcAmlSource().load_all(HMRC_FILE), companies
        )
        for org in companies + report.matched + report.unmatched:
            self.store.save_organisation(org)
        self.by_name = {
            o.name: o for o in companies + report.matched + report.unmatched
        }
        self.campaign = Campaign(
            name="UK agency partnerships", country="GB", channel=Channel.EMAIL,
            purpose="listing data partnership", sender_name="Acme Data Ltd",
            sender_address="1 Test Street, London", opt_out_url="https://x.test/out",
        )

    def tearDown(self):
        self.store.close()
        self._tmp.cleanup()

    def decide(self, org_name):
        org = self.by_name[org_name]
        contact = Contact(
            country="GB", org_id=org.org_id, email="a@b.test",
            lawful_basis=LawfulBasis.LEGITIMATE_INTERESTS,
        )
        return evaluate(contact, self.campaign, organisation=org)

    def test_matched_company_may_be_emailed(self):
        decision = self.decide("Thames Residential Ltd")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "corporate_subscriber")

    def test_probable_sole_trader_is_blocked(self):
        decision = self.decide("J. Smith Estates")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "consent_required")

    def test_ambiguous_organisation_is_blocked(self):
        # Refusing to guess at load time propagates to refusing to send.
        self.assertFalse(self.decide("Ambiguous Estates Ltd").allowed)

    def test_unmapped_company_category_is_blocked(self):
        self.assertFalse(self.decide("ODD FORM ESTATES").allowed)


if __name__ == "__main__":
    unittest.main()
