import subprocess

import pytest


@pytest.fixture(scope="session", autouse=True)
def install_dcgm_snap():
    """Install the snap and enable dcgm-exporter service for testing."""
    snap_build_name = "dcgm_*.snap"

    subprocess.run(
        f"sudo snap install --dangerous {snap_build_name}",
        check=True,
        capture_output=True,
        shell=True,
    )

    subprocess.run("sudo snap start dcgm.dcgm-exporter".split(), check=True)

    yield

    subprocess.run("sudo snap remove --purge dcgm".split(), check=True)
