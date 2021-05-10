import os
import pytest
import shutil

from git import Repo

from tests.common import write_roocs_cfg, MINI_CEDA_CACHE_DIR

CEDA_TEST_DATA_REPO_URL = "https://github.com/cedadev/mini-ceda-archive"

write_roocs_cfg()

@pytest.fixture
def load_ceda_test_data():
    """
    This fixture ensures that the required test data repository
    has been cloned to the cache directory within the home directory.
    """
    branch = "master"
    target = os.path.join(MINI_ESGF_CACHE_DIR, branch)

    if not os.path.isdir(MINI_CEDA_CACHE_DIR):
        os.makedirs(MINI_CEDA_CACHE_DIR)

    if not os.path.isdir(target):
        repo = Repo.clone_from(CEDA_TEST_DATA_REPO_URL, target)
        repo.git.checkout(branch)

    elif os.environ.get("ROOCS_AUTO_UPDATE_TEST_DATA", "true").lower() != "false":
        repo = Repo(target)
        repo.git.checkout(branch)
        repo.remotes[0].pull()

