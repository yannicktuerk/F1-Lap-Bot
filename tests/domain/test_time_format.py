"""Unit tests for TimeFormat value object."""
import pytest
from src.domain.value_objects.time_format import TimeFormat


class TestTimeFormat:
    """Test cases for TimeFormat value object."""
    
    def test_valid_time_formats(self):
        """Test valid time format parsing."""
        # Test mm:ss.mmm format
        time1 = TimeFormat("1:23.456")
        assert time1.minutes == 1
        assert time1.seconds == 23
        assert time1.milliseconds == 456
        assert time1.total_milliseconds == 83456
        
        # Test ss.mmm format
        time2 = TimeFormat("45.678")
        assert time2.minutes == 0
        assert time2.seconds == 45
        assert time2.milliseconds == 678
        assert time2.total_milliseconds == 45678
    
    def test_formatted_display(self):
        """Test formatted display output."""
        time1 = TimeFormat("1:23.456")
        assert str(time1) == "1:23.456"
        
        time2 = TimeFormat("45.678")
        assert str(time2) == "45.678"
        
        time3 = TimeFormat("2:05.123")
        assert str(time3) == "2:05.123"
    
    def test_time_comparison(self):
        """Test time comparison operations."""
        time1 = TimeFormat("1:23.456")
        time2 = TimeFormat("1:23.455")  # 1ms faster
        time3 = TimeFormat("1:23.456")  # same time
        
        assert time2 < time1  # time2 is faster (less time)
        assert time1 > time2  # time1 is slower
        assert time1 == time3  # same time
        assert time2 != time1  # different times
    
    def test_invalid_time_formats(self):
        """Test invalid time format handling."""
        with pytest.raises(ValueError, match="Invalid time format"):
            TimeFormat("invalid")
        
        with pytest.raises(ValueError, match="Invalid time format"):
            TimeFormat("1:60.123")  # Invalid seconds
        
        with pytest.raises(ValueError, match="Invalid time format"):
            TimeFormat("1:23")  # Missing milliseconds
    
    def test_implausible_times(self):
        """Test plausibility validation."""
        # Too fast
        with pytest.raises(ValueError, match="not plausible"):
            TimeFormat("15.123")  # 15 seconds - too fast
        
        # Too slow
        with pytest.raises(ValueError, match="not plausible"):
            TimeFormat("6:00.000")  # 6 minutes - too slow
    
    def test_edge_cases(self):
        """Test edge cases for time validation."""
        # Minimum valid time
        time_min = TimeFormat("30.000")
        assert time_min.total_seconds == 30.0
        
        # Maximum valid time
        time_max = TimeFormat("5:00.000")
        assert time_max.total_seconds == 300.0
        
        # Just below minimum should fail
        with pytest.raises(ValueError):
            TimeFormat("29.999")
        
        # Just above maximum should fail
        with pytest.raises(ValueError):
            TimeFormat("5:00.001")
    
    def test_hash_and_equality(self):
        """Test hash and equality for use in sets/dicts."""
        time1 = TimeFormat("1:23.456")
        time2 = TimeFormat("1:23.456")
        time3 = TimeFormat("1:23.457")
        
        # Same times should be equal and have same hash
        assert time1 == time2
        assert hash(time1) == hash(time2)
        
        # Different times should not be equal
        assert time1 != time3
        
        # Should work in sets
        time_set = {time1, time2, time3}
        assert len(time_set) == 2  # time1 and time2 are the same
