import pytest
import tarfile
import subprocess

@pytest.fixture
def download_example_data(tmp_path):
    repo_url = "https://github.com/example/temp-data-repo.git"  # Replace with your repo URL
    clone_path = tmp_path / "temp-data"
    # Clone the Git repository into the temporary directory
    subprocess.run(["git", "clone", repo_url, str(clone_path)], check=True)
    for dataset in ["example-2d", "example-3d"]:
        tar_path = tmp_path / f"{dataset}.tar.gz"
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall()
    return clone_path

import pytest
from nbmake.nbresult import NotebookTest

@pytest.mark.parametrize("notebook_path", ["notebooks/test_notebook.ipynb"])
def test_notebook(notebook_path, extract_temp_data, tmp_path):
    # Get the path to the extracted data
    extracted_data_path = extract_temp_data

    # Replace the placeholder in the notebook with the extracted data path
    notebook_path_with_data = tmp_path / "test_notebook_with_data.ipynb"
    with open(notebook_path, "r") as original_nb, open(notebook_path_with_data, "w") as modified_nb:
        modified_nb.write(original_nb.read().replace("PLACEHOLDER_PATH", str(extracted_data_path)))

    # Execute the notebook
    NotebookTest(str(notebook_path_with_data)).run()
