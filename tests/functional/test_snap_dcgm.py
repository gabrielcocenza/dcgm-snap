import json
import subprocess
import urllib.request

import pytest
from tenacity import Retrying, retry, stop_after_delay, wait_fixed


@retry(wait=wait_fixed(5), stop=stop_after_delay(30))
def test_dcgm_exporter():
    """Test of the dcgm-exporter service and its endpoint."""
    dcgm_exporter_service = "snap.dcgm.dcgm-exporter"
    endpoint = "http://localhost:9400/metrics"

    assert 0 == subprocess.call(
        f"sudo systemctl is-active --quiet {dcgm_exporter_service}".split()
    ), f"{dcgm_exporter_service} is not running"

    # Check the exporter endpoint, will raise an exception if the endpoint is not reachable
    response = urllib.request.urlopen(endpoint)

    # The output of the exporter endpoint is not tested
    # as in a virtual environment it will not have any GPU metrics
    assert 200 == response.getcode(), "DCGM exporter endpoint returned an error"


def test_dcgm_nv_hostengine():
    """Check the dcgm-nv-hostengine service."""
    nv_hostengine_service = "snap.dcgm.nv-hostengine"
    nv_hostengine_port = 5555

    assert 0 == subprocess.call(
        f"sudo systemctl is-active --quiet {nv_hostengine_service}".split()
    ), f"{nv_hostengine_service} is not running"

    assert 0 == subprocess.call(
        f"nc -z localhost {nv_hostengine_port}".split()
    ), f"{nv_hostengine_service} is not listening on port {nv_hostengine_port}"


def test_dcgmi():
    """Test of the dcgmi command."""
    result = subprocess.run(
        "dcgm.dcgmi discovery -l".split(), check=True, capture_output=True, text=True
    )

    # Test if the command is working and outputs a table with the GPU ID
    # The table will be empty in a virtual environment, but the command should still work
    assert "GPU ID" in result.stdout.strip(), "DCGMI didn't produce the expected table"


@pytest.mark.parametrize(
    "service, config, new_value",
    [
        ("dcgm.dcgm-exporter", "dcgm-exporter-address", ":9466"),
        ("dcgm.nv-hostengine", "nv-hostengine-port", "5566"),
    ],
)
def test_dcgm_bind_config(service: str, config: str, new_value: str):
    """Test snap bind configuration."""
    result = subprocess.run(
        "sudo snap get dcgm -d".split(), check=True, capture_output=True, text=True
    )
    dcgm_snap_config = json.loads(result.stdout.strip())
    assert config in dcgm_snap_config, f"{config} is not in the snap configuration"
    old_value = dcgm_snap_config[config]

    def set_config_and_check(value: str):
        assert 0 == subprocess.call(
            f"sudo snap set dcgm {config}={value}".split()
        ), f"Failed to set {config} to {new_value}"

        # restart the service to apply the configuration
        subprocess.run(f"sudo snap restart {service}".split(), check=True)

        for attempt in Retrying(wait=wait_fixed(2), stop=stop_after_delay(10)):
            with attempt:
                assert 0 == subprocess.call(
                    f"nc -z localhost {value.lstrip(':')}".split()
                ), f"{service} is not listening on {value}"

    # Check new config
    set_config_and_check(new_value)

    # Revert back
    set_config_and_check(str(old_value))
