import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from propdata.db.migrations import LATEST, LegacyDatabase, migrate
from propdata.outreach.campaign import build_outbox
from propdata.outreach.compliance import check_campaign, evaluate
from propdata.outreach.models import (
    Campaign,
    Channel,
    Contact,
    LawfulBasis,
    LegalForm,
    Organisation,
    Suppression,
    normalise_identifier,
)
from propdata.outreach.store import OutreachStore


def gb_campaign(channel=Channel.EMAIL, **kwargs):
    defaults = dict(
        name="Agent partnerships", country="GB", channel=channel,
        purpose="Invite agencies to share listing data",
        sender_name="Acme Data Ltd", sender_address="1 Test Street, London",
        opt_out_url="https://example.test/opt-out",
    )
    defaults.update(kwargs)
    return Campaign(**defaults)


class TestMigrations(unittest.TestCase):
    def test_fresh_database_reaches_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = sqlite3.connect(Path(tmp) / "a.db")
            self.assertEqual(migrate(c), LATEST)

    def test_migration_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = sqlite3.connect(Path(tmp) / "a.db")
            migrate(c)
            self.assertEqual(migrate(c), LATEST)
            count = c.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
            self.assertEqual(count, LATEST)

    def test_unversioned_database_is_refused_not_guessed(self):
        # The properties table changed shape twice before versioning existed,
        # so its columns cannot be inferred.
        with tempfile.TemporaryDirectory() as tmp:
            c = sqlite3.connect(Path(tmp) / "legacy.db")
            c.execute("CREATE TABLE properties (x TEXT)")
            with self.assertRaises(LegacyDatabase):
                migrate(c)


class TestIdentifierNormalisation(unittest.TestCase):
    def test_email_is_case_folded(self):
        # Suppression that misses on a capital letter is not suppression.
        self.assertEqual(
            normalise_identifier(Channel.EMAIL, "  Jo@Example.TEST "),
            "jo@example.test",
        )

    def test_phone_keeps_only_digits_and_plus(self):
        self.assertEqual(
            normalise_identifier(Channel.PHONE, "+44 (0)20 7946 0000"),
            "+4402079460000",
        )


class TestCampaignValidation(unittest.TestCase):
    def test_valid_campaign_passes(self):
        self.assertTrue(check_campaign(gb_campaign()).allowed)

    def test_missing_opt_out_fails_once_not_per_contact(self):
        decision = check_campaign(gb_campaign(opt_out_url="  "))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "missing_opt_out")

    def test_missing_sender_identity_fails(self):
        self.assertEqual(
            check_campaign(gb_campaign(sender_address="")).reason,
            "missing_sender_identity",
        )

    def test_unimplemented_country_is_refused(self):
        # Spain is Tier A but its marketing rules are not written, so the gate
        # refuses rather than applying UK rules to it.
        decision = check_campaign(gb_campaign(country="ES"))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "country_not_implemented")
        self.assertIn("LSSI", decision.detail)


class TestPecrSubscriberType(unittest.TestCase):
    """The distinction that does the real work: corporate vs individual."""

    def setUp(self):
        self.campaign = gb_campaign()
        self.ltd = Organisation(
            country="GB", name="Big Agents Ltd",
            legal_form=LegalForm.LIMITED_COMPANY,
        )
        self.sole = Organisation(
            country="GB", name="Jo Smith Estates", legal_form=LegalForm.SOLE_TRADER
        )

    def contact(self, org, basis):
        return Contact(
            country="GB", org_id=org.org_id, email="jo@example.test",
            lawful_basis=basis,
        )

    def test_limited_company_may_be_emailed_without_consent(self):
        decision = evaluate(
            self.contact(self.ltd, LawfulBasis.LEGITIMATE_INTERESTS),
            self.campaign, organisation=self.ltd,
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "corporate_subscriber")

    def test_sole_trader_may_not(self):
        # A sole trader is a business but an individual subscriber under PECR.
        decision = evaluate(
            self.contact(self.sole, LawfulBasis.LEGITIMATE_INTERESTS),
            self.campaign, organisation=self.sole,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "consent_required")

    def test_sole_trader_with_consent_may(self):
        decision = evaluate(
            self.contact(self.sole, LawfulBasis.CONSENT),
            self.campaign, organisation=self.sole,
        )
        self.assertTrue(decision.allowed)

    def test_corporate_still_needs_a_recorded_basis(self):
        # PECR permits the channel; UK GDPR still governs the personal data.
        decision = evaluate(
            self.contact(self.ltd, LawfulBasis.NONE),
            self.campaign, organisation=self.ltd,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "no_lawful_basis_recorded")

    def test_unknown_legal_form_is_not_treated_as_corporate(self):
        # Misclassifying a sole trader as a company is an unlawful send;
        # the reverse is a missed email. Fail towards the missed email.
        unknown = Organisation(country="GB", name="Someone", legal_form=LegalForm.UNKNOWN)
        decision = evaluate(
            self.contact(unknown, LawfulBasis.LEGITIMATE_INTERESTS),
            self.campaign, organisation=unknown,
        )
        self.assertFalse(decision.allowed)

    def test_post_is_outside_pecr(self):
        decision = evaluate(
            Contact(country="GB", org_id=self.sole.org_id, email="jo@example.test",
                    lawful_basis=LawfulBasis.LEGITIMATE_INTERESTS),
            gb_campaign(channel=Channel.POST), organisation=self.sole,
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "non_electronic_channel")


class TestGateOrdering(unittest.TestCase):
    def test_suppression_outranks_consent(self):
        # An opt-out recorded after consent is a withdrawal of that consent.
        org = Organisation(country="GB", name="X Ltd", legal_form=LegalForm.LIMITED_COMPANY)
        contact = Contact(country="GB", org_id=org.org_id, email="a@b.test",
                          lawful_basis=LawfulBasis.CONSENT)
        decision = evaluate(contact, gb_campaign(), organisation=org, suppressed=True)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "suppressed")

    def test_retention_expiry_blocks(self):
        contact = Contact(
            country="GB", email="a@b.test", lawful_basis=LawfulBasis.CONSENT,
            retain_until=date(2020, 1, 1),
        )
        decision = evaluate(contact, gb_campaign(), today=date(2026, 1, 1))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "retention_expired")

    def test_country_mismatch_blocks(self):
        contact = Contact(country="IE", email="a@b.test", lawful_basis=LawfulBasis.CONSENT)
        self.assertEqual(
            evaluate(contact, gb_campaign()).reason, "country_mismatch"
        )

    def test_missing_identifier_for_channel_blocks(self):
        contact = Contact(country="GB", email="a@b.test", lawful_basis=LawfulBasis.CONSENT)
        self.assertEqual(
            evaluate(contact, gb_campaign(channel=Channel.SMS)).reason,
            "no_identifier",
        )


class TestOutboxAndAudit(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = OutreachStore(Path(self._tmp.name) / "out.db")
        self.ltd = Organisation(
            country="GB", name="Big Agents Ltd",
            legal_form=LegalForm.LIMITED_COMPANY, admin_codes=["E09000001"],
        )
        self.sole = Organisation(
            country="GB", name="Jo Smith Estates", legal_form=LegalForm.SOLE_TRADER,
            admin_codes=["E09000001"],
        )
        for org in (self.ltd, self.sole):
            self.store.save_organisation(org)
        self.contacts = [
            Contact(country="GB", org_id=self.ltd.org_id, email="ok@example.test",
                    lawful_basis=LawfulBasis.LEGITIMATE_INTERESTS),
            Contact(country="GB", org_id=self.sole.org_id, email="sole@example.test",
                    lawful_basis=LawfulBasis.LEGITIMATE_INTERESTS),
            Contact(country="GB", org_id=self.ltd.org_id, email="opted@example.test",
                    lawful_basis=LawfulBasis.LEGITIMATE_INTERESTS),
        ]
        for contact in self.contacts:
            self.store.save_contact(contact)

    def tearDown(self):
        self.store.close()
        self._tmp.cleanup()

    def test_outbox_splits_queued_and_blocked(self):
        result = build_outbox(self.store, gb_campaign(), self.contacts)
        self.assertEqual(len(result.queued), 2)
        self.assertEqual(len(result.blocked), 1)
        self.assertEqual(result.refusal_counts, {"consent_required": 1})

    def test_refusals_are_written_to_the_audit_log(self):
        # "We never contacted them" needs evidence, not an absent row.
        campaign = gb_campaign()
        build_outbox(self.store, campaign, self.contacts)
        blocked = self.store.messages(campaign.campaign_id, status="blocked")
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["decision_reason"], "consent_required")

    def test_suppression_is_checked_at_build_time_against_live_state(self):
        # The classic bug: list built Monday, sent Friday, opt-out Wednesday.
        self.store.suppress(
            Suppression(Channel.EMAIL, "OPTED@example.test", reason="unsubscribed")
        )
        result = build_outbox(self.store, gb_campaign(), self.contacts)
        reasons = {e.decision.reason for e in result.blocked}
        self.assertIn("suppressed", reasons)
        self.assertEqual(len(result.queued), 1)

    def test_suppression_matches_regardless_of_case(self):
        self.store.suppress(Suppression(Channel.EMAIL, "OK@EXAMPLE.TEST", reason="x"))
        self.assertTrue(self.store.is_suppressed(Channel.EMAIL, "ok@example.test"))

    def test_rerunning_does_not_message_twice(self):
        campaign = gb_campaign()
        build_outbox(self.store, campaign, self.contacts)
        second = build_outbox(self.store, campaign, self.contacts)
        self.assertEqual(len(second.queued) + len(second.blocked), 0)
        self.assertEqual(len(self.store.messages(campaign.campaign_id)), 3)

    def test_invalid_campaign_evaluates_nobody(self):
        result = build_outbox(
            self.store, gb_campaign(opt_out_url=""), self.contacts
        )
        self.assertIsNotNone(result.campaign_error)
        self.assertEqual(result.queued, [])
        self.assertEqual(result.blocked, [])

    def test_contacts_can_be_selected_by_area(self):
        found = self.store.contacts(country="GB", admin_codes=["E09000001"])
        self.assertEqual(len(found), 3)
        self.assertEqual(self.store.contacts(country="GB", admin_codes=["E99"]), [])


if __name__ == "__main__":
    unittest.main()
