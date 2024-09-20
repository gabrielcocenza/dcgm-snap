import subprocess

import pytest


@pytest.fixture(scope="session", autouse=True)
def install_dcgm_snap():
    """Install the snap and enable dcgm-exporter service for testing."""
    snap_build_name = "dcgm_*.snap"

    subprocess.check_call(
        f"sudo snap install --dangerous {snap_build_name}",
        shell=True,
    )

    subprocess.check_call("sudo snap start dcgm.dcgm-exporter".split())

    yield

    subprocess.check_call("sudo snap remove --purge dcgm".split())
