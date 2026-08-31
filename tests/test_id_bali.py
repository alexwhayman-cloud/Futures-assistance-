import unittest
from pathlib import Path

from propdata.regions.indonesia import detect_tenure, resolve_locality
from propdata.schema import PropertyType, TenureFamily, Tier
from propdata.sources.id_bali import BaliListingsSource

FIXTURES = Path(__file__).parent / "fixtures" / "bali"


def warnings_of(prop):
    return " | ".join(prop.raw["_normalisation_warnings"])


class TestLocalityResolution(unittest.TestCase):
    def test_regency_lookup(self):
        code, path = resolve_locality("Villa in Canggu")
        self.assertEqual(code, "51.03")
        self.assertEqual(path, ["Bali", "Badung", "Canggu"])

    def test_sanur_is_denpasar_not_gianyar(self):
        self.assertEqual(resolve_locality("Sanur beachfront")[0], "51.71")

    def test_nusa_penida_is_klungkung(self):
        self.assertEqual(resolve_locality("Land in Nusa Penida")[0], "51.05")

    def test_longest_name_wins_over_substring(self):
        # "nusa penida" must not lose to a shorter entry.
        code, path = resolve_locality("Nusa Penida cliff land")
        self.assertEqual(path[-1], "Nusa Penida")

    def test_unknown_locality_is_none(self):
        self.assertEqual(resolve_locality("Somewhere in Lombok"), (None, []))


class TestTenureDetection(unittest.TestCase):
    def test_indonesian_certificate_terms(self):
        tenure, _ = detect_tenure("Dijual villa Hak Milik (SHM)")
        self.assertEqual(tenure.family, TenureFamily.FREEHOLD)
        self.assertEqual(tenure.local_code, "SHM")
        self.assertIs(tenure.foreign_holdable, False)

    def test_hak_pakai_is_foreign_holdable(self):
        tenure, _ = detect_tenure("Hak Pakai villa")
        self.assertEqual(tenure.family, TenureFamily.USE_RIGHT)
        self.assertIs(tenure.foreign_holdable, True)

    def test_certificate_outranks_sublease(self):
        tenure, warns = detect_tenure("HGB, sewa 22 tahun")
        self.assertEqual(tenure.family, TenureFamily.BUILD_RIGHT)
        self.assertEqual(tenure.years_remaining, 22)
        self.assertTrue(any("more than one tenure term" in w for w in warns))

    def test_marketing_freehold_does_not_assert_a_certificate(self):
        # "Freehold" in a Bali advert is a sales adjective. Mapping it to Hak
        # Milik would assert that a foreign buyer cannot hold it — a legal
        # claim the listing never made.
        tenure, warns = detect_tenure("Rare freehold opportunity")
        self.assertEqual(tenure.family, TenureFamily.FREEHOLD)
        self.assertIsNone(tenure.local_name)
        self.assertIsNone(tenure.foreign_holdable)
        self.assertTrue(any("marketing term" in w for w in warns))

    def test_term_on_a_perpetual_right_is_flagged(self):
        _, warns = detect_tenure("Girik land, 30 years lease")
        self.assertTrue(any("internally inconsistent" in w for w in warns))

    def test_templates_are_not_mutated_between_calls(self):
        detect_tenure("Hak Milik, 25 years remaining")
        tenure, _ = detect_tenure("Hak Milik villa")
        self.assertIsNone(tenure.years_remaining)


class TestBaliListings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.properties = list(BaliListingsSource().run(path=FIXTURES))
        cls.by_slug = {
            p.provenance.source_record_id.rsplit("/", 1)[-1]: p for p in cls.properties
        }

    def test_listings_parsed_from_jsonld_including_graph(self):
        self.assertEqual(len(self.properties), 4)
        self.assertIn("penida-land", self.by_slug)
        self.assertIn("sanur-freehold", self.by_slug)

    def test_land_area_in_are_converts_to_sqm(self):
        # 5 are is 500 sqm. Reading it as 5 sqm is a 100x error.
        prop = self.by_slug["villa-melati-canggu"]
        self.assertEqual(prop.land_area_sqm, 500.0)
        self.assertEqual(prop.floor_area_sqm, 200.0)

    def test_land_and_building_area_are_distinct_fields(self):
        prop = self.by_slug["villa-melati-canggu"]
        self.assertNotEqual(prop.land_area_sqm, prop.floor_area_sqm)

    def test_tenure_and_admin_code_populate(self):
        prop = self.by_slug["villa-melati-canggu"]
        self.assertEqual(prop.legal_tenure.local_code, "HGB")
        self.assertEqual(prop.legal_tenure.years_remaining, 22)
        self.assertEqual(prop.address.admin_code, "51.03")
        self.assertEqual(prop.property_type, PropertyType.VILLA)

    def test_rental_rate_is_not_stored_as_an_asking_price(self):
        # USD 25,000/year is not what the villa costs.
        prop = self.by_slug["seminyak-lease"]
        self.assertIsNone(prop.asking_price)
        self.assertIn("rate per year", warnings_of(prop))

    def test_price_in_description_anchors_to_the_currency(self):
        prop = self.by_slug["penida-land"]
        self.assertEqual(prop.asking_price, 1_500_000_000)
        self.assertEqual(prop.price_currency, "IDR")
        self.assertEqual(prop.land_area_sqm, 1000.0)
        self.assertEqual(prop.property_type, PropertyType.LAND)

    def test_implausible_area_ratio_is_flagged(self):
        prop = self.by_slug["sanur-freehold"]
        self.assertIn("implausible against land area", warnings_of(prop))

    def test_every_record_is_flagged_weak_identity(self):
        for prop in self.properties:
            with self.subTest(prop=prop.property_id):
                self.assertEqual(prop.address.identity_confidence, "weak")
                self.assertIn("do not auto-merge", warnings_of(prop))

    def test_images_are_urls_only(self):
        prop = self.by_slug["villa-melati-canggu"]
        self.assertEqual(len(prop.image_urls), 2)
        self.assertTrue(all(u.startswith("https://") for u in prop.image_urls))

    def test_provenance_marks_portal_tier_and_restricted_licence(self):
        prop = self.by_slug["villa-melati-canggu"]
        self.assertEqual(prop.provenance.tier, Tier.PORTAL)
        self.assertIn("not redistributable", prop.provenance.licence)

    def test_untyped_next_data_yields_nothing(self):
        # Known limitation, pinned rather than hidden: the embedded-state path
        # only yields records when the payload is schema.org-typed. Real
        # __NEXT_DATA__ is portal-specific and needs a per-portal mapper.
        source = BaliListingsSource()
        records = [
            r
            for doc in source.fetch(path=FIXTURES / "next_data_untyped.html")
            for r in source.parse(doc)
        ]
        self.assertEqual(records, [])

    def test_adapter_refuses_to_crawl(self):
        with self.assertRaises(ValueError):
            list(BaliListingsSource().fetch())


if __name__ == "__main__":
    unittest.main()
