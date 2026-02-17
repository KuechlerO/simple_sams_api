import unittest
from unittest.mock import patch, MagicMock
from simple_sams_api.base import (
    SAMSapi,
    extract_HPO_terms_from_phenopacket,
    extract_disease_terms_from_phenopacket,
    filter_phenopacket_by_onset,
)


class TestSAMSapi_Mocking(unittest.TestCase):
    def setUp(self):
        self.api = SAMSapi()

    @patch("requests.Session.post")
    def test_login_with_username(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        self.api.login_with_username("user", "pass")
        mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_login_with_credentials_file(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        with patch("builtins.open", unittest.mock.mock_open(read_data="user\npass\n")):
            self.api.login_with_credentials_file("fakefile.txt")
        mock_post.assert_called_once()

    @patch("requests.Session.get")
    def test_get_phenopackets(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"id": "1"}]
        mock_get.return_value = mock_response
        result = self.api.get_phenopackets()
        self.assertEqual(result, [{"id": "1"}])

    @patch("requests.Session.get")
    def test_get_phenopacket(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "subject": {"id": "patient1"},
            "phenotypicFeatures": [],
            "diseases": [],
        }
        mock_get.return_value = mock_response
        result = self.api.get_phenopacket("patient1")
        self.assertEqual(result["subject"]["id"], "patient1")
        # Test error case
        mock_response.json.return_value = {"subject": {"id": "other"}}
        with self.assertRaises(RuntimeError):
            self.api.get_phenopacket("patient1")

    def test_loggedIn_property(self):
        self.api.session.cookies.set("SAMSI", "token")
        self.assertTrue(self.api.loggedIn)
        self.api.session.cookies.clear()
        self.assertFalse(self.api.loggedIn)


class TestExtractFunctions(unittest.TestCase):
    def test_extract_HPO_terms_from_phenopacket(self):
        phenopacket = {
            "subject": {"id": "p1"},
            "phenotypicFeatures": [
                {"type": {"id": "HP:0000001", "label": "Phenotype 1"}},
                {"type": {"id": "HP:0000002", "label": "Phenotype 2"}, "excluded": 1},
            ],
        }
        result = extract_HPO_terms_from_phenopacket(phenopacket)
        self.assertEqual(result, "HP:0000001 - Phenotype 1")
        result = extract_HPO_terms_from_phenopacket(phenopacket, ignore_excluded=False)
        self.assertEqual(
            result, "HP:0000001 - Phenotype 1; HP:0000002 - Phenotype 2 (excluded)"
        )
        # No phenotypicFeatures
        phenopacket2 = {"subject": {"id": "p2"}}
        self.assertEqual(extract_HPO_terms_from_phenopacket(phenopacket2), "")

    def test_extract_disease_terms_from_phenopacket(self):
        phenopacket = {
            "subject": {"id": "p1"},
            "diseases": [
                {"term": {"id": "OMIM:1", "label": "Disease 1"}},
                {"term": {"id": "OMIM:2", "label": "Disease 2"}, "excluded": 1},
            ],
        }
        result = extract_disease_terms_from_phenopacket(phenopacket)
        self.assertEqual(result, "OMIM:1 - Disease 1")
        result = extract_disease_terms_from_phenopacket(
            phenopacket, ignore_excluded=False
        )
        self.assertEqual(result, "OMIM:1 - Disease 1; OMIM:2 - Disease 2 (excluded)")
        # No diseases
        phenopacket2 = {"subject": {"id": "p2"}}
        self.assertEqual(extract_disease_terms_from_phenopacket(phenopacket2), "")

    def test_filter_phenopacket_by_onset(self):
        phenopacket = {
            "phenotypicFeatures": [
                {
                    "onset": {"timestamp": "2020-01-01"},
                    "type": {"id": "HP:1", "label": "A"},
                },
                {
                    "onset": {"timestamp": "2021-01-01"},
                    "type": {"id": "HP:2", "label": "B"},
                },
            ],
            "diseases": [
                {
                    "onset": {"timestamp": "2020-01-01"},
                    "term": {"id": "OMIM:1", "label": "D1"},
                },
                {
                    "onset": {"timestamp": "2021-01-01"},
                    "term": {"id": "OMIM:2", "label": "D2"},
                },
            ],
        }
        # Filter by specific timestamp
        filtered = filter_phenopacket_by_onset(dict(phenopacket), "2020-01-01")
        self.assertEqual(len(filtered["phenotypicFeatures"]), 1)
        self.assertEqual(filtered["phenotypicFeatures"][0]["type"]["id"], "HP:1")
        self.assertEqual(len(filtered["diseases"]), 1)
        self.assertEqual(filtered["diseases"][0]["term"]["id"], "OMIM:1")
        # Filter by earliest
        filtered = filter_phenopacket_by_onset(dict(phenopacket), "earliest")
        self.assertEqual(
            filtered["phenotypicFeatures"][0]["onset"]["timestamp"], "2020-01-01"
        )
        # Filter by latest
        filtered = filter_phenopacket_by_onset(dict(phenopacket), "latest")
        self.assertEqual(
            filtered["phenotypicFeatures"][0]["onset"]["timestamp"], "2021-01-01"
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


if __name__ == "__main__":
    unittest.main()
