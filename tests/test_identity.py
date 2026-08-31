"""Country-aware identity. Each test is a case the old global heuristic got wrong."""

import unittest

from propdata.regions import identity
from propdata.regions.identity import Granularity, IdentityTier, PostcodePrecision
from propdata.schema import Address


def addr(country, **kwargs):
    return Address(country=country, **kwargs)


class TestRegistryShape(unittest.TestCase):
    def test_every_entry_is_self_consistent(self):
        for code, entry in identity.REGISTRY.items():
            with self.subTest(country=code):
                self.assertEqual(code, entry.country)
                self.assertIn(entry.confidence, {"high", "medium"})
                # A country with no key must not claim a granularity for it.
                if entry.key_name is None:
                    self.assertIs(entry.granularity, Granularity.NONE)
                # A key field must be a real Address attribute.
                if entry.key_field:
                    self.assertIn(entry.key_field, identity.AUTHORITATIVE_FIELDS)

    def test_unknown_country_degrades_to_weak(self):
        verdict = identity.assess(addr("ZZ", postcode="1234", lines=["1 Test St"]))
        self.assertEqual(verdict.confidence, "weak")
        self.assertIs(verdict.tier, IdentityTier.UNKNOWN)

    def test_missing_country_does_not_raise(self):
        self.assertEqual(identity.get(None).country, "??")


class TestGranularityMatters(unittest.TestCase):
    def test_parcel_key_is_authoritative_for_a_house(self):
        # France: parcelle identifies the plot, and a house is the plot.
        verdict = identity.assess(addr("FR", parcel_id="75105000AB0123"), "house")
        self.assertEqual(verdict.confidence, "authoritative")

    def test_parcel_key_degrades_for_a_flat(self):
        # Same key, same country: every apartment in the building shares it.
        verdict = identity.assess(addr("FR", parcel_id="75105000AB0123"), "flat")
        self.assertEqual(verdict.confidence, "address")
        self.assertIn("cannot distinguish", verdict.reason)

    def test_dwelling_level_key_survives_a_flat(self):
        # Spain's referencia catastral includes the unit.
        verdict = identity.assess(
            addr("ES", parcel_id="9872023VH5797S0001WX"), "flat"
        )
        self.assertEqual(verdict.confidence, "authoritative")


class TestPostcodePrecisionMatters(unittest.TestCase):
    def test_eircode_alone_is_authoritative(self):
        # An Eircode identifies one delivery point. A UK postcode covers ~15
        # addresses and an Indonesian one covers a district — same field.
        verdict = identity.assess(addr("IE", postcode="D02 AF30"))
        self.assertEqual(verdict.confidence, "authoritative")

    def test_uk_postcode_needs_an_address_line(self):
        self.assertEqual(
            identity.assess(addr("GB", postcode="SW1A 1AA")).confidence, "weak"
        )
        self.assertEqual(
            identity.assess(
                addr("GB", postcode="SW1A 1AA", lines=["12 Example St"])
            ).confidence,
            "address",
        )

    def test_indonesian_postcode_is_never_enough(self):
        verdict = identity.assess(
            addr("ID", postcode="80361", lines=["Jalan Pantai Berawa"])
        )
        self.assertEqual(verdict.confidence, "weak")
        self.assertIn("covers a district", verdict.reason)

    def test_singapore_postcode_reaches_building_not_dwelling(self):
        verdict = identity.assess(addr("SG", postcode="238823"))
        self.assertEqual(verdict.confidence, "address")
        self.assertIn("no unit number", verdict.reason)


class TestNamespacedKeys(unittest.TestCase):
    def test_us_apn_is_not_authoritative_unqualified(self):
        # ~3,100 county namespaces and no national one.
        verdict = identity.assess(addr("US", parcel_id="1234-567-890"), "house")
        self.assertEqual(verdict.confidence, "address")
        self.assertIn("county", verdict.reason)

    def test_qualified_apn_is_accepted(self):
        verdict = identity.assess(addr("US", parcel_id="06037:1234-567-890"), "house")
        self.assertEqual(verdict.confidence, "authoritative")


class TestAddressIntegration(unittest.TestCase):
    def test_address_property_delegates(self):
        self.assertEqual(
            addr("GB", uprn="100023336956").identity_confidence, "authoritative"
        )

    def test_assess_identity_takes_property_type(self):
        address = addr("FR", parcel_id="75105000AB0123")
        self.assertEqual(address.assess_identity("house").confidence, "authoritative")
        self.assertEqual(address.assess_identity("flat").confidence, "address")

    def test_reason_names_the_countrys_actual_scheme(self):
        verdict = identity.assess(addr("ES", postcode="29602"))
        self.assertIn("referencia catastral", verdict.reason)


if __name__ == "__main__":
    unittest.main()
