# Simple SAMS API

This module provides a Python interface for interacting with the [SAMS](https://www.genecascade.org/sams-cgi/Patients.cgi) (Symptom Annotation Made Simple) web service, allowing you to authenticate, retrieve phenopacket data, and extract relevant medical terms for downstream analysis.

## Features
- **Authentication**: Login to SAMS using username/password or credentials file.
- **Phenopacket Retrieval**: Download all phenopackets or a specific phenopacket by patient ID.
- **HPO Term Extraction**: Extract Human Phenotype Ontology (HPO) terms from phenopacket data.
- **Disease Term Extraction**: Extract disease terms (OMIM, ORPHANET) from phenopacket data.
- **Onset Filtering**: Filter phenopacket features and diseases by onset timestamp.

## Usage

### Installation
Simply copy the module into your project and install the required dependencies:

```
pip install requests
```

### Example
```python
from simple_sams_api.base import SAMSapi, extract_HPO_terms_from_phenopacket

# Initialize API and login
api = SAMSapi()
api.login_with_username('your_email', 'your_password')

# Retrieve all phenopackets
phenopackets = api.get_phenopackets()

# Extract HPO terms from a phenopacket
hpo_terms = extract_HPO_terms_from_phenopacket(phenopackets[0])
print(hpo_terms)
# Example output:  "HP:0000001 - Phenotype 1; HP:0000002 - Phenotype 2; ..."
```

## API Reference

### Class: `SAMSapi`
- `login_with_username(username, password)`: Login using username and password.
- `login_with_credentials_file(credentials_file)`: Login using a credentials file (first line: username, second line: password).
- `get_phenopackets()`: Retrieve all phenopackets for the current user.
- `get_phenopacket(patient_id)`: Retrieve a phenopacket for a specific patient.
- `loggedIn`: Property indicating login status.

### Functions
- `extract_HPO_terms_from_phenopacket(phenopacket, ignore_excluded=True)`: Extract HPO terms from a phenopacket.
- `extract_disease_terms_from_phenopacket(phenopacket, ignore_excluded=True)`: Extract disease terms from a phenopacket.
- `filter_phenopacket_by_onset(phenopacket, input_onset_timestamp)`: Filter phenopacket features and diseases by onset timestamp ("earliest", "latest", or specific timestamp).

## Testing
Run `python -m unittest tests/test_base.py`.

## License
MIT License

## Author
Oliver Küchler

## Notes
- Make sure you have access to the SAMS web service and valid credentials.
- For more details, see the docstrings in the source code.
- The GitHub Actions workflow is based on: [Using uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi).
