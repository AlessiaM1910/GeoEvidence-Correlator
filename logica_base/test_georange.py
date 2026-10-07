import unittest

from georange import Coordinate


class CoordinateTests(unittest.TestCase):

    def test_coordinate_valida(self):
        punto = Coordinate(39.36336, 16.22622)

        self.assertEqual(punto.lat, 39.36336)
        self.assertEqual(punto.lon, 16.22622)

    def test_coordinate_stringa_valida(self):
        punto = Coordinate("39.36336", "16.22622")

        self.assertEqual(punto.lat, 39.36336)
        self.assertEqual(punto.lon, 16.22622)

    def test_latitudine_non_valida(self):
        self.assertRaises(
            ValueError,
            Coordinate,
            95,
            16,
        )

    def test_longitudine_non_valida(self):
        self.assertRaises(
            ValueError,
            Coordinate,
            39,
            200,
        )

    def test_distanza_stesso_punto(self):
        punto_a = Coordinate(39.36336, 16.22622)
        punto_b = Coordinate(39.36336, 16.22622)

        distanza = punto_a.distanza(punto_b)

        self.assertAlmostEqual(distanza, 0.0)

    def test_distanza_un_grado_all_equatore(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        distanza = punto_a.distanza(punto_b)

        self.assertAlmostEqual(
            distanza,
            111.195,
            places=2,
        )

    def test_antipodi(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 180)

        distanza = punto_a.distanza(punto_b)

        self.assertTrue(distanza > 20000)
        self.assertTrue(distanza < 20020)

    def test_raggio_zero_stesso_punto(self):
        punto_a = Coordinate(39.36336, 16.22622)
        punto_b = Coordinate(39.36336, 16.22622)

        esito = punto_a.rientra_nel_raggio(
            punto_b,
            0,
        )

        self.assertTrue(esito)

    def test_punto_diverso_fuori_raggio_zero(self):
        punto_a = Coordinate(39.36336, 16.22622)
        punto_b = Coordinate(39.35680, 16.22790)

        esito = punto_a.rientra_nel_raggio(
            punto_b,
            0,
        )

        self.assertFalse(esito)

    def test_punto_dentro_raggio(self):
        punto_a = Coordinate(39.36000, 16.22000)
        punto_b = Coordinate(39.36336, 16.22622)

        esito = punto_a.rientra_nel_raggio(
            punto_b,
            2,
        )

        self.assertTrue(esito)

    def test_raggio_negativo_non_valido(self):
        punto_a = Coordinate(39.36000, 16.22000)
        punto_b = Coordinate(39.36336, 16.22622)

        self.assertRaises(
            ValueError,
            punto_a.rientra_nel_raggio,
            punto_b,
            -1,
        )

    def test_altro_punto_non_valido(self):
        punto = Coordinate(39.36336, 16.22622)

        self.assertRaises(
            TypeError,
            punto.distanza,
            "non sono una coordinata",
        )


if __name__ == "__main__":
    unittest.main()