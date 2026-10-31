import unittest

from georange import Coordinate, convert_distance, distance, within_radius


class TestCoordinate(unittest.TestCase):
    """Test the Coordinate class validation and geographic operations."""

    def test_valid_coordinate(self):
        point = Coordinate(39.36336, 16.22622)

        self.assertEqual(point.lat, 39.36336)
        self.assertEqual(point.lon, 16.22622)

    def test_coordinate_from_strings(self):
        point = Coordinate("39.36336", "16.22622")

        self.assertEqual(point.lat, 39.36336)
        self.assertEqual(point.lon, 16.22622)

    def test_latitude_above_maximum(self):
        with self.assertRaises(ValueError):
            Coordinate(91, 10)

    def test_latitude_below_minimum(self):
        with self.assertRaises(ValueError):
            Coordinate(-91, 10)

    def test_longitude_above_maximum(self):
        with self.assertRaises(ValueError):
            Coordinate(10, 181)

    def test_longitude_below_minimum(self):
        with self.assertRaises(ValueError):
            Coordinate(10, -181)

    def test_non_numeric_coordinate(self):
        with self.assertRaises(ValueError):
            Coordinate("text", 10)

    def test_nan_coordinate(self):
        with self.assertRaises(ValueError):
            Coordinate(float("nan"), 10)

    def test_same_coordinate_has_zero_distance_in_kilometers(self):
        point_a = Coordinate(39.36336, 16.22622)
        point_b = Coordinate(39.36336, 16.22622)

        distance_km = point_a.distance_to(point_b)

        self.assertEqual(distance_km, 0.0)

    def test_one_degree_at_equator_in_kilometers(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        distance_km = point_a.distance_to(point_b, "km")

        self.assertGreater(distance_km, 111.0)
        self.assertLess(distance_km, 112.0)

    def test_one_degree_at_equator_in_meters(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        distance_meters = point_a.distance_to(point_b, "m")

        self.assertGreater(distance_meters, 111000.0)
        self.assertLess(distance_meters, 112000.0)

    def test_one_degree_at_equator_in_miles(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        distance_miles = point_a.distance_to(point_b, "mi")

        self.assertGreater(distance_miles, 69.0)
        self.assertLess(distance_miles, 70.0)

    def test_unit_with_spaces_and_uppercase_letters(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        distance_km = point_a.distance_to(point_b, " KM ")

        self.assertGreater(distance_km, 111.0)
        self.assertLess(distance_km, 112.0)

    def test_unsupported_unit(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        with self.assertRaises(ValueError):
            point_a.distance_to(point_b, "yards")

    def test_other_point_is_not_a_coordinate(self):
        point = Coordinate(0, 0)

        with self.assertRaises(TypeError):
            point.distance_to((0, 1))

    def test_is_within_radius_in_kilometers(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        self.assertTrue(
            point_a.is_within_radius(point_b, 112, "km")
        )

        self.assertFalse(
            point_a.is_within_radius(point_b, 111, "km")
        )

    def test_is_within_radius_in_meters(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        self.assertTrue(
            point_a.is_within_radius(point_b, 112000, "m")
        )

        self.assertFalse(
            point_a.is_within_radius(point_b, 111000, "m")
        )

    def test_negative_radius(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        with self.assertRaises(ValueError):
            point_a.is_within_radius(point_b, -1, "km")


class TestDistanceConversion(unittest.TestCase):
    """Test the convert_distance function and public helper functions."""

    def test_meters_to_meters(self):
        result = convert_distance(500, "m")

        self.assertEqual(result, 500.0)

    def test_meters_to_kilometers(self):
        result = convert_distance(1000, "km")

        self.assertEqual(result, 1.0)

    def test_meters_to_miles(self):
        result = convert_distance(1609.344, "mi")

        self.assertAlmostEqual(result, 1.0, places=6)

    def test_conversion_with_unsupported_unit(self):
        with self.assertRaises(ValueError):
            convert_distance(1000, "yards")

    def test_conversion_with_negative_distance(self):
        with self.assertRaises(ValueError):
            convert_distance(-1, "km")

    def test_distance_function_in_kilometers(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        distance_km = distance(point_a, point_b, "km")

        self.assertGreater(distance_km, 111.0)
        self.assertLess(distance_km, 112.0)

    def test_distance_function_with_default_unit(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        distance_km = distance(point_a, point_b)

        self.assertGreater(distance_km, 111.0)
        self.assertLess(distance_km, 112.0)

    def test_within_radius_function(self):
        point_a = Coordinate(0, 0)
        point_b = Coordinate(0, 1)

        self.assertTrue(
            within_radius(point_a, point_b, 112, "km")
        )

        self.assertFalse(
            within_radius(point_a, point_b, 111, "km")
        )

    def test_distance_function_with_invalid_point(self):
        point = Coordinate(0, 0)

        with self.assertRaises(TypeError):
            distance(point, (0, 1), "km")

    def test_as_tuple(self):
        point = Coordinate(39.36336, 16.22622)

        result = point.as_tupla()

        self.assertEqual(
            result,
            (39.36336, 16.22622),
        )


if __name__ == "__main__":
    unittest.main()