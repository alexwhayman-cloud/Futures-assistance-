import sqlite3
import tempfile
import unittest
from pathlib import Path

from propdata.schema import BuiltForm, Occupancy, PropertyType, Tier
from propdata.sources.uk_epc import UkEpcSource
from propdata.storage import Store

FIXTURE = Path(__file__).parent / "fixtures" / "uk_epc_sample.csv"


class TestUkEpcNormalisation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = UkEpcSource()
        cls.properties = list(cls.source.run(path=FIXTURE))
        cls.by_lmk = {p.provenance.source_record_id: p for p in cls.properties}

    def test_rows_without_a_certificate_key_are_dropped(self):
        # The fixture has 5 data rows; one has an empty LMK-KEY.
        self.assertEqual(len(self.properties), 4)

    def test_attributes_map_to_enums(self):
        prop = self.by_lmk["1111111111111111111111111"]
        self.assertEqual(prop.property_type, PropertyType.HOUSE)
        self.assertEqual(prop.built_form, BuiltForm.SEMI_DETACHED)
        self.assertEqual(prop.floor_area_sqm, 94.5)
        self.assertEqual(prop.habitable_rooms, 5)
        self.assertEqual(prop.construction_age_band, "1950-1966")

    def test_enclosed_terrace_folds_into_mid_terrace(self):
        prop = self.by_lmk["2222222222222222222222222"]
        self.assertEqual(prop.built_form, BuiltForm.MID_TERRACE)

    def test_epc_tenure_is_occupancy_not_legal_tenure(self):
        # The whole point of splitting the two fields: "Owner-occupied" must
        # never be silently promoted to freehold.
        prop = self.by_lmk["1111111111111111111111111"]
        self.assertEqual(prop.occupancy, Occupancy.OWNER_OCCUPIED)
        # EPC carries no certificate type at all, so tenure stays absent
        # rather than being invented from the occupancy column.
        self.assertIsNone(prop.legal_tenure)

        rented = self.by_lmk["2222222222222222222222222"]
        self.assertEqual(rented.occupancy, Occupancy.RENTED_PRIVATE)

    def test_sentinel_row_normalises_without_raising(self):
        prop = self.by_lmk["4444444444444444444444444"]
        self.assertEqual(prop.property_type, PropertyType.UNKNOWN)
        self.assertEqual(prop.built_form, BuiltForm.UNKNOWN)
        self.assertIsNone(prop.floor_area_sqm)
        self.assertIsNone(prop.habitable_rooms)
        self.assertIsNone(prop.energy.current_band)
        self.assertIsNone(prop.energy.assessed_on)

    def test_uprn_drives_identity_and_collides_across_certificates(self):
        first = self.by_lmk["1111111111111111111111111"]
        later = self.by_lmk["3333333333333333333333333"]
        self.assertEqual(first.property_id, "uprn:GB:100023336956")
        self.assertEqual(first.property_id, later.property_id)

    def test_missing_uprn_falls_back_to_address_hash(self):
        prop = self.by_lmk["2222222222222222222222222"]
        self.assertTrue(prop.property_id.startswith("addr:GB:"))

    def test_provenance_is_populated(self):
        prop = self.by_lmk["1111111111111111111111111"]
        self.assertEqual(prop.provenance.source_id, "uk-epc")
        self.assertEqual(prop.provenance.tier, Tier.REGISTER)
        self.assertIn("OGL", prop.provenance.licence)


class TestStore(unittest.TestCase):
    def test_certificates_collapse_to_properties_keeping_latest(self):
        properties = list(UkEpcSource().run(path=FIXTURE))
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            with Store(db) as store:
                processed = store.write(properties)
                self.assertEqual(processed, 4)
                # Two certificates share a UPRN, so they are one property.
                self.assertEqual(store.count(), 3)

                row = store.connection.execute(
                    "SELECT energy_band, assessed_on FROM properties "
                    "WHERE property_id = 'uprn:GB:100023336956'"
                ).fetchone()
                # 2023 re-assessment wins over the 2019 one, regardless of
                # the order rows happened to be read in.
                self.assertEqual(row[0], "C")
                self.assertEqual(row[1], "2023-06-14")

    def test_raw_payload_is_retained_for_renormalisation(self):
        properties = list(UkEpcSource().run(path=FIXTURE))
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            with Store(db) as store:
                store.write(properties)
                count = store.connection.execute(
                    "SELECT COUNT(*) FROM raw_records"
                ).fetchone()[0]
                self.assertEqual(count, 3)

    def test_reingesting_is_idempotent(self):
        properties = list(UkEpcSource().run(path=FIXTURE))
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            with Store(db) as store:
                store.write(properties)
                store.write(properties)
                self.assertEqual(store.count(), 3)


if __name__ == "__main__":
    unittest.main()


class TestFetchPaths(unittest.TestCase):
    def test_relative_path_is_accepted(self):
        # source_url is a file:// URI, and Path.as_uri() rejects relative
        # paths — so fetch must resolve before building it.
        import os

        cwd = os.getcwd()
        os.chdir(FIXTURE.parent.parent.parent)
        try:
            source = UkEpcSource()
            documents = list(source.fetch(path="tests/fixtures/uk_epc_sample.csv"))
            self.assertEqual(len(documents), 1)
            self.assertTrue(documents[0].url.startswith("file://"))
        finally:
            os.chdir(cwd)

    def test_missing_path_raises_clearly(self):
        with self.assertRaises(ValueError):
            list(UkEpcSource().fetch())
        with self.assertRaises(FileNotFoundError):
            list(UkEpcSource().fetch(path="/nonexistent/certificates.csv"))
