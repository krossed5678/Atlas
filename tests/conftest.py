import os
import shutil

import pytest

os.environ["ASTRA_DATA_DIR"] = "/tmp/astra-test"

from app.main import init_db


@pytest.fixture(autouse=True)
def isolated_database():
    shutil.rmtree("/tmp/astra-test", ignore_errors=True)
    init_db()
    yield
    shutil.rmtree("/tmp/astra-test", ignore_errors=True)
