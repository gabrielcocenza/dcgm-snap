import json
import os
import subprocess
import urllib.request
from contextlib import contextmanager

import pytest
from tenacity import retry, stop_after_delay, wait_fixed


@retry(wait=wait_fixed(2), stop=stop_after_delay(10))
def _check_service_active(service: str) -> None:
    """Check if a service is active."""
    assert 0 == subprocess.call(
        f"sudo systemctl is-active --quiet {service}".split()
    ), f"{service} is not running"


@retry(wait=wait_fixed(2), stop=stop_after_delay(10))
def _check_service_failed(service: str) -> None:
    """Check if a service is in a failed state."""
    assert 0 == subprocess.call(
        f"sudo systemctl is-failed --quiet {service}".split()
    ), f"{service} is running"


@retry(wait=wait_fixed(5), stop=stop_after_delay(30))
def _check_endpoint(endpoint: str) -> None:
    """Check if an endpoint is reachable."""
    response = urllib.request.urlopen(endpoint)  # will raise if not reachable
    status_code = response.getcode()
    assert status_code == 200, f"Endpoint {endpoint} returned status code {status_code}"


class TestDCGMComponents:
    def test_dcgm_exporter(self) -> None:
        """Test of the dcgm-exporter service and its endpoint."""
        dcgm_exporter_service = "snap.dcgm.dcgm-exporter"
        endpoint = "http://localhost:9400/metrics"

        _check_service_active(dcgm_exporter_service)
        # The output of the exporter endpoint is not tested
        # as in a virtual environment it will not have any GPU metrics
        _check_endpoint(endpoint)

    def test_dcgm_nv_hostengine(self) -> None:
        """Check the dcgm-nv-hostengine service."""
        nv_hostengine_service = "snap.dcgm.nv-hostengine"
        nv_hostengine_port = 5555

        _check_service_active(nv_hostengine_service)

        assert 0 == subprocess.call(
            f"nc -z localhost {nv_hostengine_port}".split()
        ), f"{nv_hostengine_service} is not listening on port {nv_hostengine_port}"

    def test_dcgmi(self) -> None:
        """Test of the dcgmi command."""
        result = subprocess.check_output("dcgm.dcgmi discovery -l".split(), text=True)

        # Test if the command is working and outputs a table with the GPU ID
        # The table will be empty in a virtual environment, but the command should still work
        assert "GPU ID" in result.strip(), "DCGMI didn't produce the expected table"


class TestDCGMConfigs:
    @classmethod
    @retry(wait=wait_fixed(2), stop=stop_after_delay(10))
    def set_config(cls, service: str, config: str, value: str) -> None:
        """Set a configuration value for a snap service."""
        assert 0 == subprocess.call(
            f"sudo snap set dcgm {config}={value}".split()
        ), f"Failed to set {config} to {value}"

        subprocess.check_call(f"sudo snap restart {service}".split())

    @classmethod
    @retry(wait=wait_fixed(2), stop=stop_after_delay(10))
    def unset_config(cls, service: str, config: str) -> None:
        """Unset a configuration value for a snap service."""
        assert 0 == subprocess.call(
            f"sudo snap unset dcgm {config}".split()
        ), f"Failed to unset {config}"

        subprocess.check_call(f"sudo snap restart {service}".split())

    @classmethod
    @retry(wait=wait_fixed(2), stop=stop_after_delay(10))
    def check_bind_config(cls, service: str, bind: str) -> None:
        """Check if a service is listening on a specific bind."""
        assert 0 == subprocess.call(
            f"nc -z localhost {bind.lstrip(':')}".split()
        ), f"{service} is not listening on {bind}"

    @classmethod
    def get_config(cls, config: str) -> str:
        """Check if a configuration exists in the snap configuration.

        :return: The value of the current configuration
        """
        result = subprocess.check_output("sudo snap get dcgm -d".split(), text=True)
        dcgm_snap_config = json.loads(result.strip())
        assert config in dcgm_snap_config, f"{config} is not in the snap configuration"
        return str(dcgm_snap_config[config])

    @classmethod
    @retry(wait=wait_fixed(2), stop=stop_after_delay(10))
    def check_metric_config(cls, metric_file: str = "") -> None:
        """Check if the metric file is loaded in the dcgm-exporter service.

        :param metric_file: The metric file to check for, if empty check if nothing is loaded
        """
        result = subprocess.check_output("ps -C dcgm-exporter -o cmd".split(), text=True)

        if metric_file:
            assert f"-f {metric_file}" in result, f"Metric file {metric_file} is not loaded"
        else:
            assert "-f" not in result.split(), "Metric file is loaded, but should not be"

    @contextmanager
    def bind_config(self, service, config, new_value):
        """Set up a context manager to test snap bind configuration."""
        old_value = self.get_config(config)
        try:
            self.set_config(service, config, new_value)
            yield
        finally:
            # Revert back
            self.set_config(service, config, old_value)
            self.check_bind_config(service, old_value)

    @pytest.mark.parametrize(
        "service, config, new_value",
        [
            ("dcgm.dcgm-exporter", "dcgm-exporter-address", ":9466"),
            ("dcgm.nv-hostengine", "nv-hostengine-port", "5566"),
        ],
    )
    def test_valid_bind_config(self, service: str, config: str, new_value: str) -> None:
        """Test valid snap bind configuration."""
        with self.bind_config(service, config, new_value):
            self.check_bind_config(service, new_value)

    @pytest.mark.parametrize(
        "service, config, new_value",
        [
            ("dcgm.dcgm-exporter", "dcgm-exporter-address", "test"),
            ("dcgm.nv-hostengine", "nv-hostengine-port", "test"),
        ],
    )
    def test_invalid_bind_config(self, service: str, config: str, new_value: str) -> None:
        """Test invalid snap bind configuration."""
        with self.bind_config(service, config, new_value):
            _check_service_failed(f"snap.{service}")

    @classmethod
    @pytest.fixture
    def metric_setup(cls):
        """Fixture for metric configuration tests."""
        cls.service = "dcgm.dcgm-exporter"
        cls.config = "dcgm-exporter-metrics-file"
        cls.endpoint = "http://localhost:9400/metrics"
        cls.snap_common = "/var/snap/dcgm/common"

        cls.get_config(cls.config)

        yield

        # Revert back
        cls.unset_config(cls.service, cls.config)
        cls.check_metric_config()

    @pytest.mark.usefixtures("metric_setup")
    def test_empty_metric(self) -> None:
        """Test with an empty metric file.

        Empty files will not be passed to the exporter
        """
        metric_file = "empty-metrics.csv"
        metric_file_path = os.path.join(self.snap_common, metric_file)
        # $SNAP_COMMON requires root permissions to create a file
        subprocess.check_call(f"sudo touch {metric_file_path}".split())

        self.set_config(self.service, self.config, metric_file)
        self.check_metric_config()
        _check_endpoint(self.endpoint)

    @pytest.mark.usefixtures("metric_setup")
    def test_non_existing_metric(self) -> None:
        """Test with a non-existing metric file.

        Non-existing files will not be passed to the exporter.
        """
        self.set_config(self.service, self.config, "unknown.csv")
        self.check_metric_config()
        _check_endpoint(self.endpoint)

    @pytest.mark.usefixtures("metric_setup")
    def test_invalid_metric(self) -> None:
        """Test with an invalid metric file.

        The exporter will fail to start due to the invalid metric file
        """
        metric_file = "invalid-metrics.csv"
        metric_file_path = os.path.join(self.snap_common, metric_file)
        # $SNAP_COMMON requires root permissions to create a file
        subprocess.check_call(f"echo 'test' | sudo tee {metric_file_path}", shell=True)

        self.set_config(self.service, self.config, metric_file)
        _check_service_failed(f"snap.{self.service}")

    @pytest.mark.usefixtures("metric_setup")
    def test_valid_metric(self) -> None:
        """Test with a valid metric file.

        The endpoint is reachable with the specified metrics
        """
        metric_file = "valid-metrics.csv"
        metric_file_path = os.path.join(self.snap_common, metric_file)
        subprocess.check_call(
            f"echo 'DCGM_FI_DRIVER_VERSION, label, Driver Version' | sudo tee {metric_file_path}",
            shell=True,
        )

        self.set_config(self.service, self.config, metric_file)
        self.check_metric_config(metric_file_path)
        _check_endpoint(self.endpoint)
