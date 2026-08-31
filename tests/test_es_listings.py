import unittest
from pathlib import Path

from propdata.regions.spain import (
    detect_tenure,
    find_cadastral_reference,
    resolve_locality,
)
from propdata.schema import PropertyType, TenureFamily
from propdata.sources.es_listings import SpainListingsSource

FIXTURES = Path(__file__).parent / "fixtures" / "spain"


def warnings_of(prop):
    return " | ".join(prop.raw["_normalisation_warnings"])


class TestCadastralReference(unittest.TestCase):
    def test_plain_reference(self):
        self.assertEqual(
            find_cadastral_reference("Ref. catastral 9872023VH5797S0001WX"),
            "9872023VH5797S0001WX",
        )

    def test_grouped_reference_is_normalised(self):
        self.assertEqual(
            find_cadastral_reference("9872023 VH5797S 0001 WX"),
            "9872023VH5797S0001WX",
        )

    def test_absent_reference(self):
        self.assertIsNone(find_cadastral_reference("Piso céntrico sin referencia"))


class TestSpanishLocality(unittest.TestCase):
    def test_coastal_town_resolves_to_province(self):
        self.assertEqual(resolve_locality("Villa en Marbella")[0], "29")

    def test_ibiza_is_illes_balears(self):
        code, path = resolve_locality("Apartamento en Ibiza")
        self.assertEqual((code, path[1]), ("07", "Illes Balears"))

    def test_bare_province_name_resolves(self):
        self.assertEqual(resolve_locality("Casa en Segovia")[0], "40")

    def test_unknown_place_is_none(self):
        self.assertEqual(resolve_locality("Casa en Lisboa"), (None, []))


class TestSpanishTenure(unittest.TestCase):
    def test_pleno_dominio_is_freehold(self):
        tenure, _ = detect_tenure("Se vende en pleno dominio")
        self.assertEqual(tenure.family, TenureFamily.FREEHOLD)

    def test_nuda_propiedad_is_not_freehold(self):
        # The discount is the retained lifetime interest, not a bargain.
        tenure, warns = detect_tenure("Se vende la nuda propiedad")
        self.assertEqual(tenure.family, TenureFamily.BARE_OWNERSHIP)
        self.assertTrue(any("not comparable" in w for w in warns))

    def test_longest_term_wins_over_nested_mention(self):
        tenure, _ = detect_tenure("Nuda propiedad con usufructo vitalicio")
        self.assertEqual(tenure.family, TenureFamily.BARE_OWNERSHIP)

    def test_vpo_is_a_restriction_not_a_family(self):
        tenure, warns = detect_tenure("Piso VPO en Sevilla")
        self.assertEqual(tenure.family, TenureFamily.FREEHOLD)
        self.assertIn("price ceiling", tenure.transfer_restriction)
        self.assertTrue(any("not a market price" in w for w in warns))

    def test_silence_is_not_full_ownership(self):
        # Absence of a stated right must not become pleno dominio.
        tenure, _ = detect_tenure("Bonito piso reformado con vistas")
        self.assertIsNone(tenure)

    def test_lifetime_interest_without_a_named_right_is_flagged(self):
        _, warns = detect_tenure("Se vende con inquilino vitalicio")
        self.assertTrue(any("states no right" in w for w in warns))


class TestSpainListings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.properties = list(SpainListingsSource().run(path=FIXTURES))
        cls.by_slug = {
            p.provenance.source_record_id.rsplit("/", 1)[-1]: p for p in cls.properties
        }

    def test_cadastral_reference_gives_authoritative_identity(self):
        # The contrast with Bali: a portal record with a real key.
        prop = self.by_slug["villa-marbella"]
        self.assertEqual(prop.address.identity_confidence, "authoritative")
        self.assertEqual(prop.property_id, "parcel:ES:9872023VH5797S0001WX")
        self.assertNotIn("do not auto-merge", warnings_of(prop))

    def test_spanish_thousands_separator_in_area(self):
        # "parcela 1.100 m2" is 1100 sqm, not 1.1.
        prop = self.by_slug["villa-marbella"]
        self.assertEqual(prop.land_area_sqm, 1100.0)
        self.assertEqual(prop.floor_area_sqm, 320.0)
        self.assertNotIn("implausible", warnings_of(prop))

    def test_listing_without_reference_falls_back_and_says_so(self):
        prop = self.by_slug["nuda-madrid"]
        self.assertTrue(prop.property_id.startswith("addr:ES:"))
        self.assertIn("no referencia catastral", warnings_of(prop))

    def test_nuda_propiedad_price_is_flagged_not_comparable(self):
        prop = self.by_slug["nuda-madrid"]
        self.assertEqual(prop.legal_tenure.family, TenureFamily.BARE_OWNERSHIP)
        self.assertEqual(prop.asking_price, 195_000)
        self.assertIn("not comparable", warnings_of(prop))

    def test_usable_area_substitution_is_recorded(self):
        prop = self.by_slug["nuda-madrid"]
        self.assertEqual(prop.floor_area_sqm, 78.0)
        self.assertIn("superficie útil", warnings_of(prop))

    def test_vpo_restriction_reaches_the_record(self):
        prop = self.by_slug["vpo-sevilla"]
        self.assertIn("price ceiling", prop.legal_tenure.transfer_restriction)

    def test_monthly_rent_is_not_an_asking_price(self):
        # "2.400 € / mes" — Spanish period word, same trap as Bali's per-year.
        prop = self.by_slug["alquiler-ibiza"]
        self.assertIsNone(prop.asking_price)
        self.assertIn("rate per month", warnings_of(prop))

    def test_spanish_property_type_terms(self):
        self.assertEqual(
            self.by_slug["villa-marbella"].property_type, PropertyType.VILLA
        )
        self.assertEqual(self.by_slug["nuda-madrid"].property_type, PropertyType.FLAT)


if __name__ == "__main__":
    unittest.main()
