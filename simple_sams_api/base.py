from typing import List
import requests
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

SAMS_URL = "https://www.genecascade.org/sams-cgi"
LOGIN_URL = f"{SAMS_URL}/login.cgi"
EXPORT_PHENOPACKETS_URL = f"{SAMS_URL}/ExportPhenopacket.cgi?export_all=1"
EXPORT_PHENOPACKET_BY_ID_URL = (
    f"{SAMS_URL}/export_phenopacket.cgi?external_id={{patient_id}}"
)


@dataclass
class SAMSapi:
    session: requests.Session = field(default_factory=requests.Session)
    phenopackets: dict = None

    @property
    def loggedIn(self):
        return "SAMSI" in self.session.cookies

    def _login(self, username, password):
        data = {"email": username, "password": password}
        resp = self.session.post(LOGIN_URL, data=data)
        resp.raise_for_status()

    def login_with_credentials_file(self, credentials_file: str):
        """Login to SAMS using credentials from a file

        Args:
            credentials_file (str): Path to the file containing the credentials (first line username, second line password)

        Returns:
            SAMS: Instance of SAMS
        """
        with open(credentials_file) as f:
            username, password = [l.strip() for l in f.readlines()]
        self._login(username, password)

    def login_with_username(self, username: str, password: str):
        """Login to SAMS using username and password

        Args:
            username (str): Name of the user
            password (str): Password of the user

        Returns:
            SAMS: Instance of SAMS
        """
        self._login(username, password)

    def get_phenopackets(self) -> List[dict]:
        """Load all phenopackets from SAMS for the current user

        Returns:
            List[dict]: List of phenopackets
        """
        resp = self.session.get(EXPORT_PHENOPACKETS_URL)
        resp.raise_for_status()
        all_data = resp.json()
        return all_data

    def get_phenopacket(self, patient_id: str) -> dict:
        """Get phenopacket for a specific patient

        Args:
            patient_id (str): ID of the patient

        Raises:
            RuntimeError: If the phenopacket for the patient could not be found

        Returns:
            dict: Phenopacket for the patient
        """
        resp = self.session.get(
            EXPORT_PHENOPACKET_BY_ID_URL.format(patient_id=patient_id)
        )
        resp.raise_for_status()
        patient_data = resp.json()
        if patient_data["subject"]["id"] != patient_id:
            raise RuntimeError(
                f"Failed to obtain phenopacket for external id {patient_id}"
            )
        return patient_data


def extract_HPO_terms_from_phenopacket(
    phenopacket: dict, ignore_excluded: bool = True
) -> str:
    """Extract HPO terms of a given phenopacket

    Args:
        phenopacket (dict): Phenopacket containing phenotypic features
        ignore_excluded (bool, optional): Whether to ignore excluded phenotypic features. Defaults to True.

    Returns:
        str: String of HPO terms for the phenopacket in the format "HP:0000001 - Phenotype 1; HP:0000002 - Phenotype 2; ..."
             If feature is excluded, it will be marked as "HP:0000001 - Phenotype 1 (excluded)"
    """
    # Check if key exists
    if "phenotypicFeatures" not in phenopacket:
        sams_entry = phenopacket["subject"]["id"]
        logger.warning(f"SAMS: No phenotypicFeatures found for {sams_entry}")
        return ""

    else:
        phenotypes = phenopacket["phenotypicFeatures"]  # Get HPO terms from phenopacket

        pheno_strings = []
        for feature in phenotypes:
            pheno_string = f"{feature['type']['id']} - {feature['type']['label']}"

            if feature.get("excluded", 0):
                if ignore_excluded:
                    continue
                else:
                    pheno_string += " (excluded)"

            pheno_strings.append(pheno_string)

        return "; ".join(pheno_strings)


def extract_disease_terms_from_phenopacket(
    phenopacket: dict, ignore_excluded: bool = True
) -> str:
    """Extract disease terms (OMIM, ORPHANET)of a given phenopacket

    Args:
        phenopacket (dict): Phenopacket containing diseases
        ignore_excluded (bool, optional): Whether to ignore excluded diseases. Defaults to True.

    Returns:
        str: String of disease terms for the phenopacket in the format "OMIM:0000001 - Disease 1; OMIM:0000002 - Disease 2; ..."
    """
    if "diseases" not in phenopacket:
        sams_entry = phenopacket["subject"]["id"]
        logger.warning(f"SAMS: No diseases found for {sams_entry}")
        return ""

    else:
        diseases = phenopacket["diseases"]  # Get disease terms from phenopacket

        disease_strings = []
        for disease in diseases:
            disease_string = f"{disease['term']['id']} - {disease['term']['label']}"

            if disease.get("excluded", 0):
                if ignore_excluded:
                    continue
                else:
                    disease_string += " (excluded)"

            disease_strings.append(disease_string)
        return "; ".join(disease_strings)


def filter_phenopacket_by_onset(phenopacket: dict, input_onset_timestamp: str) -> dict:
    """Filter phenopacket by onset timestamp

    Args:
        phenopacket (dict): Phenopacket containing phenotypic features
        input_onset_timestamp (str): Onset timestamp to filter by (e.g. "2026-02-12T00:00:00Z")
        If set to "earliest", it will filter by the earliest onset timestamp in the phenopacket,
        If set to "latest", it will filter by the latest onset timestamp in the phenopacket

    Returns:
        dict: Filtered phenopacket containing only phenotypic features with the given onset timestamp
    """

    def compute_onset_timestamp(onset: str) -> str:
        if onset == "earliest":
            onset = min(
                feature["onset"]["timestamp"]
                for feature in phenopacket.get("phenotypicFeatures", [])
            )
        elif onset == "latest":
            onset = max(
                feature["onset"]["timestamp"]
                for feature in phenopacket.get("phenotypicFeatures", [])
            )
        return onset

    onset_timestamp = compute_onset_timestamp(input_onset_timestamp)

    filered_phenotypes = []
    filtered_diseases = []
    for feature in phenopacket.get("phenotypicFeatures", []):
        if feature["onset"]["timestamp"] == onset_timestamp:
            filered_phenotypes.append(feature)
    for disease in phenopacket.get("diseases", []):
        if disease["onset"]["timestamp"] == onset_timestamp:
            filtered_diseases.append(disease)

    phenopacket["phenotypicFeatures"] = filered_phenotypes
    phenopacket["diseases"] = filtered_diseases
    return phenopacket
