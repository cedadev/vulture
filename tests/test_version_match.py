import pytest
import importlib
from unittest.mock import patch

import cfchecker
import vulture


def test_version_match_fails_if_set_wrong():
    """
    We decided that the version of vulture should match that of the 
    cf-checker deployed within it. This will keep things simple
    for traceability and users. So this test checks the import raises
    the required error.
    """
    with patch('cfchecker.__version__') as mock_version:
        mock_version.return_value = "0.0.bad" 

        with pytest.raises(Exception, match=r"Version mismatch between 'vulture' .+ and 'cfchecker' \(.+\)"):
            importlib.reload(vulture)
        

def test_version_match_is_fine():
    import vulture
    assert vulture.__version__ == cfchecker.__version__
