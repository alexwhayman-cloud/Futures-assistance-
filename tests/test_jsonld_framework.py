"""The framework is shared, so its behaviour is tested once, not per country."""

import unittest

from propdata.sources.es_listings import SpainListingsSource
from propdata.sources.id_bali import BaliListingsSource
from propdata.sources.jsonld import JsonLdPortalSource, text_of, types_of, walk

ADAPTERS = [BaliListingsSource, SpainListingsSource]


class TestSharedHelpers(unittest.TestCase):
    def test_walk_reaches_graph_members(self):
        tree = {"@graph": [{"a": 1}, {"b": {"c": 2}}]}
        self.assertEqual(len(list(walk(tree))), 4)

    def test_types_of_handles_string_and_list(self):
        self.assertEqual(types_of({"@type": "House"}), {"house"})
        self.assertEqual(types_of({"@type": ["House", "Product"]}), {"house", "product"})

    def test_text_of_unwraps_nested_shapes(self):
        self.assertEqual(text_of({"value": "  x "}), "x")
        self.assertEqual(text_of(["a", "b"]), "a")
        self.assertIsNone(text_of(""))


class TestAdapterContract(unittest.TestCase):
    def test_every_portal_adapter_declares_its_locale(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter=adapter.id):
                self.assertTrue(issubclass(adapter, JsonLdPortalSource))
                self.assertIn(adapter.default_land_unit, {"sqm", "are"})
                self.assertTrue(adapter.property_type_terms)

    def test_no_portal_adapter_crawls(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter=adapter.id):
                with self.assertRaises(ValueError):
                    list(adapter().fetch())

    def test_portal_tier_carries_a_restricted_licence(self):
        for adapter in ADAPTERS:
            with self.subTest(adapter=adapter.id):
                self.assertIn("not redistributable", adapter.licence)


if __name__ == "__main__":
    unittest.main()
