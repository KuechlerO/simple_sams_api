import unittest
from simple_sams_api.base import (
    SAMSapi,
    extract_HPO_terms_from_phenopacket,
    extract_disease_terms_from_phenopacket,
)


class TestSAMSapiLive(unittest.TestCase):
    def setUp(self):
        self.api = SAMSapi()
        self.api.login_with_username(
            "testtest", "testtest"
        )  # Use valid credentials for live testing

    def test_login_and_get_phenopackets(self):
        # This test will actually attempt to log in and fetch phenopackets
        # Make sure to have valid credentials in credentials.txt for this test to pass
        self.assertTrue(self.api.loggedIn)
        phenopackets = self.api.get_phenopackets()
        self.assertIsInstance(phenopackets, list)

    def test_content_of_phenopackets(self):
        phenopackets = self.api.get_phenopackets()

        # Verify: Total of 4 patients
        self.assertEqual(len(phenopackets), 4)
        # Verify: Each phenopacket has required keys
        for phenopacket in phenopackets:
            self.assertIn("subject", phenopacket)
            self.assertIn("id", phenopacket["subject"])
            self.assertIn("phenotypicFeatures", phenopacket)
            if phenopacket["subject"]["id"] == "TREX1":
                self.assertNotIn("diseases", phenopacket)
            elif phenopacket["subject"]["id"] == "test_Lupus":
                self.assertIn("diseases", phenopacket)
                self.assertIn(
                    "ORPHA:300345 - Autosomal systemic lupus erythematosus",
                    extract_disease_terms_from_phenopacket(phenopacket),
                )

            # If ID == TREX1: No Suicide Behaviours, but Migraine without aura
            if phenopacket["subject"]["id"] == "TREX1":
                self.assertNotIn(
                    "Suicide behaviors",
                    extract_HPO_terms_from_phenopacket(phenopacket),
                )
                self.assertIn(
                    "Migraine without aura",
                    extract_HPO_terms_from_phenopacket(phenopacket),
                )
                self.assertIn(
                    "Suicide behaviors",
                    extract_HPO_terms_from_phenopacket(
                        phenopacket, ignore_excluded=False
                    ),
                )
