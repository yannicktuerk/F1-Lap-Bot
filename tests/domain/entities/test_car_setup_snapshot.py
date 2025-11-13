"""Unit tests for CarSetupSnapshot entity.

Tests cover:
- Valid instantiation with F1 25 setup data
- Validation of all setup parameters
- Entity identity semantics (equality, hashing)
- Setup comparison functionality
"""

import pytest
from src.domain.entities.car_setup_snapshot import CarSetupSnapshot


@pytest.fixture
def valid_setup_data():
    """Fixture providing valid car setup data."""
    return {
        "session_uid": 123456,
        "timestamp_ms": 50000,
        "front_wing": 10,
        "rear_wing": 15,
        "on_throttle": 60,
        "off_throttle": 40,
        "front_camber": -3.5,
        "rear_camber": -1.5,
        "front_toe": 0.1,
        "rear_toe": 0.2,
        "front_suspension": 5,
        "rear_suspension": 6,
        "front_anti_roll_bar": 7,
        "rear_anti_roll_bar": 8,
        "front_suspension_height": 3,
        "rear_suspension_height": 4,
        "brake_pressure": 100,
        "brake_bias": 60,
        "engine_braking": 50,
        "front_left_tyre_pressure": 23.5,
        "front_right_tyre_pressure": 23.5,
        "rear_left_tyre_pressure": 22.0,
        "rear_right_tyre_pressure": 22.0,
        "ballast": 10,
        "fuel_load": 50.0,
    }


@pytest.fixture
def valid_setup(valid_setup_data):
    """Fixture providing a valid CarSetupSnapshot instance."""
    return CarSetupSnapshot(**valid_setup_data)


class TestCarSetupSnapshotInstantiation:
    """Test valid instantiation scenarios."""

    def test_create_with_valid_data(self, valid_setup):
        """Valid setup data should create CarSetupSnapshot successfully."""
        assert valid_setup.session_uid == 123456
        assert valid_setup.front_wing == 10
        assert valid_setup.rear_wing == 15
        assert valid_setup.brake_pressure == 100
        assert valid_setup.setup_id is not None

    def test_setup_id_auto_generated(self, valid_setup_data):
        """Setup ID should be auto-generated if not provided."""
        setup = CarSetupSnapshot(**valid_setup_data)
        assert setup.setup_id is not None
        assert len(setup.setup_id) == 36  # UUID format

    def test_custom_setup_id(self, valid_setup_data):
        """Custom setup ID should be used if provided."""
        custom_id = "test-setup-123"
        setup = CarSetupSnapshot(**valid_setup_data, setup_id=custom_id)
        assert setup.setup_id == custom_id


class TestCarSetupSnapshotValidation:
    """Test parameter validation."""

    def test_front_wing_below_min(self, valid_setup_data):
        """Front wing below minimum should raise ValueError."""
        valid_setup_data["front_wing"] = -1
        with pytest.raises(ValueError, match="front_wing must be in range"):
            CarSetupSnapshot(**valid_setup_data)

    def test_front_wing_above_max(self, valid_setup_data):
        """Front wing above maximum should raise ValueError."""
        valid_setup_data["front_wing"] = 51
        with pytest.raises(ValueError, match="front_wing must be in range"):
            CarSetupSnapshot(**valid_setup_data)

    def test_differential_out_of_range(self, valid_setup_data):
        """Differential value out of range should raise ValueError."""
        valid_setup_data["on_throttle"] = 101
        with pytest.raises(ValueError, match="on_throttle must be in range"):
            CarSetupSnapshot(**valid_setup_data)

    def test_suspension_below_min(self, valid_setup_data):
        """Suspension below minimum should raise ValueError."""
        valid_setup_data["front_suspension"] = 0
        with pytest.raises(ValueError, match="front_suspension must be in range"):
            CarSetupSnapshot(**valid_setup_data)

    def test_suspension_above_max(self, valid_setup_data):
        """Suspension above maximum should raise ValueError."""
        valid_setup_data["rear_suspension"] = 12
        with pytest.raises(ValueError, match="rear_suspension must be in range"):
            CarSetupSnapshot(**valid_setup_data)

    def test_brake_pressure_out_of_range(self, valid_setup_data):
        """Brake pressure out of range should raise ValueError."""
        valid_setup_data["brake_pressure"] = 40
        with pytest.raises(ValueError, match="brake_pressure must be in range"):
            CarSetupSnapshot(**valid_setup_data)

    def test_brake_bias_out_of_range(self, valid_setup_data):
        """Brake bias out of range should raise ValueError."""
        valid_setup_data["brake_bias"] = 45
        with pytest.raises(ValueError, match="brake_bias must be in range"):
            CarSetupSnapshot(**valid_setup_data)

    def test_tyre_pressure_below_min(self, valid_setup_data):
        """Tyre pressure below minimum should raise ValueError."""
        valid_setup_data["front_left_tyre_pressure"] = 18.0
        with pytest.raises(ValueError, match="front_left_tyre_pressure must be in range"):
            CarSetupSnapshot(**valid_setup_data)

    def test_tyre_pressure_above_max(self, valid_setup_data):
        """Tyre pressure above maximum should raise ValueError."""
        valid_setup_data["rear_right_tyre_pressure"] = 31.0
        with pytest.raises(ValueError, match="rear_right_tyre_pressure must be in range"):
            CarSetupSnapshot(**valid_setup_data)

    def test_ballast_out_of_range(self, valid_setup_data):
        """Ballast out of range should raise ValueError."""
        valid_setup_data["ballast"] = 51
        with pytest.raises(ValueError, match="ballast must be in range"):
            CarSetupSnapshot(**valid_setup_data)

    def test_fuel_load_out_of_range(self, valid_setup_data):
        """Fuel load out of range should raise ValueError."""
        valid_setup_data["fuel_load"] = 120.0
        with pytest.raises(ValueError, match="fuel_load must be in range"):
            CarSetupSnapshot(**valid_setup_data)


class TestCarSetupSnapshotEquality:
    """Test entity identity semantics."""

    def test_same_id_equal(self, valid_setup_data):
        """Setups with same ID should be equal."""
        setup_id = "test-123"
        setup1 = CarSetupSnapshot(**valid_setup_data, setup_id=setup_id)
        setup2 = CarSetupSnapshot(**valid_setup_data, setup_id=setup_id)
        assert setup1 == setup2

    def test_different_id_not_equal(self, valid_setup_data):
        """Setups with different IDs should not be equal."""
        setup1 = CarSetupSnapshot(**valid_setup_data)
        setup2 = CarSetupSnapshot(**valid_setup_data)
        assert setup1 != setup2

    def test_same_id_same_hash(self, valid_setup_data):
        """Setups with same ID should have same hash."""
        setup_id = "test-123"
        setup1 = CarSetupSnapshot(**valid_setup_data, setup_id=setup_id)
        setup2 = CarSetupSnapshot(**valid_setup_data, setup_id=setup_id)
        assert hash(setup1) == hash(setup2)

    def test_can_use_in_set(self, valid_setup):
        """CarSetupSnapshot should be usable in sets."""
        setup_set = {valid_setup}
        assert valid_setup in setup_set
        assert len(setup_set) == 1


class TestCarSetupSnapshotComparison:
    """Test setup comparison functionality."""

    def test_compare_identical_setups(self, valid_setup, valid_setup_data):
        """Comparing identical setups should return empty diff."""
        setup2 = CarSetupSnapshot(**valid_setup_data, setup_id="different-id")
        diff = valid_setup.compare_to(setup2)
        assert diff == {}

    def test_compare_different_wings(self, valid_setup, valid_setup_data):
        """Comparing setups with different wings should show differences."""
        valid_setup_data["front_wing"] = 20
        valid_setup_data["rear_wing"] = 25
        setup2 = CarSetupSnapshot(**valid_setup_data)
        diff = valid_setup.compare_to(setup2)
        
        assert "front_wing" in diff
        assert diff["front_wing"]["this"] == 10
        assert diff["front_wing"]["other"] == 20
        assert diff["front_wing"]["diff"] == -10
        
        assert "rear_wing" in diff
        assert diff["rear_wing"]["this"] == 15
        assert diff["rear_wing"]["other"] == 25

    def test_compare_different_pressures(self, valid_setup, valid_setup_data):
        """Comparing setups with different tyre pressures should show differences."""
        valid_setup_data["front_left_tyre_pressure"] = 25.0
        setup2 = CarSetupSnapshot(**valid_setup_data)
        diff = valid_setup.compare_to(setup2)
        
        assert "front_left_tyre_pressure" in diff
        assert diff["front_left_tyre_pressure"]["this"] == 23.5
        assert diff["front_left_tyre_pressure"]["other"] == 25.0
        assert pytest.approx(diff["front_left_tyre_pressure"]["diff"]) == -1.5

    def test_compare_with_non_setup_raises_error(self, valid_setup):
        """Comparing with non-CarSetupSnapshot should raise ValueError."""
        with pytest.raises(ValueError, match="Can only compare with another CarSetupSnapshot"):
            valid_setup.compare_to("not a setup")


class TestCarSetupSnapshotProperties:
    """Test property access."""

    def test_all_properties_accessible(self, valid_setup):
        """All setup properties should be accessible."""
        assert valid_setup.front_wing == 10
        assert valid_setup.rear_wing == 15
        assert valid_setup.on_throttle == 60
        assert valid_setup.off_throttle == 40
        assert valid_setup.front_camber == -3.5
        assert valid_setup.rear_camber == -1.5
        assert valid_setup.front_suspension == 5
        assert valid_setup.rear_suspension == 6
        assert valid_setup.brake_pressure == 100
        assert valid_setup.brake_bias == 60
        assert valid_setup.front_left_tyre_pressure == 23.5
        assert valid_setup.ballast == 10
        assert valid_setup.fuel_load == 50.0

    def test_setup_schema_version(self, valid_setup):
        """Setup should have schema version."""
        assert valid_setup.setup_schema_version == CarSetupSnapshot.CURRENT_SCHEMA_VERSION

    def test_created_at_set(self, valid_setup):
        """Created at timestamp should be set."""
        assert valid_setup.created_at is not None


class TestCarSetupSnapshotEdgeCases:
    """Test edge cases and boundary values."""

    def test_minimum_valid_values(self, valid_setup_data):
        """Setup with minimum valid values should be created."""
        valid_setup_data.update({
            "front_wing": 0,
            "rear_wing": 0,
            "on_throttle": 0,
            "off_throttle": 0,
            "front_suspension": 1,
            "rear_suspension": 1,
            "front_anti_roll_bar": 1,
            "rear_anti_roll_bar": 1,
            "front_suspension_height": 0,
            "rear_suspension_height": 0,
            "brake_pressure": 50,
            "brake_bias": 50,
            "engine_braking": 0,
            "front_left_tyre_pressure": 19.0,
            "front_right_tyre_pressure": 19.0,
            "rear_left_tyre_pressure": 19.0,
            "rear_right_tyre_pressure": 19.0,
            "ballast": 0,
            "fuel_load": 0.0,
        })
        setup = CarSetupSnapshot(**valid_setup_data)
        assert setup.front_wing == 0
        assert setup.brake_pressure == 50

    def test_maximum_valid_values(self, valid_setup_data):
        """Setup with maximum valid values should be created."""
        valid_setup_data.update({
            "front_wing": 50,
            "rear_wing": 50,
            "on_throttle": 100,
            "off_throttle": 100,
            "front_suspension": 11,
            "rear_suspension": 11,
            "front_anti_roll_bar": 11,
            "rear_anti_roll_bar": 11,
            "front_suspension_height": 10,
            "rear_suspension_height": 10,
            "brake_pressure": 120,
            "brake_bias": 70,
            "engine_braking": 100,
            "front_left_tyre_pressure": 30.0,
            "front_right_tyre_pressure": 30.0,
            "rear_left_tyre_pressure": 30.0,
            "rear_right_tyre_pressure": 30.0,
            "ballast": 50,
            "fuel_load": 110.0,
        })
        setup = CarSetupSnapshot(**valid_setup_data)
        assert setup.front_wing == 50
        assert setup.fuel_load == 110.0
