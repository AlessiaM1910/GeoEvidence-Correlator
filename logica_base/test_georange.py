import unittest

from georange import Coordinate, converti_distanza, distance, within_radius

class TestCoordinate(unittest.TestCase):

    def test_coordinate_valida(self):
        punto = Coordinate(39.36336, 16.22622)

        self.assertEqual(punto.lat, 39.36336)
        self.assertEqual(punto.lon, 16.22622)

    def test_coordinate_da_stringhe(self):
        punto = Coordinate("39.36336", "16.22622")

        self.assertEqual(punto.lat, 39.36336)
        self.assertEqual(punto.lon, 16.22622)

    def test_latitudine_troppo_alta(self):
        with self.assertRaises(ValueError):
            Coordinate(91, 10)

    def test_latitudine_troppo_bassa(self):
        with self.assertRaises(ValueError):
            Coordinate(-91, 10)

    def test_longitudine_troppo_alta(self):
        with self.assertRaises(ValueError):
            Coordinate(10, 181)

    def test_longitudine_troppo_bassa(self):
        with self.assertRaises(ValueError):
            Coordinate(10, -181)

    def test_coordinata_non_numerica(self):
        with self.assertRaises(ValueError):
            Coordinate("testo", 10)

    def test_coordinata_nan(self):
        with self.assertRaises(ValueError):
            Coordinate(float("nan"), 10)

    def test_distanza_identica_zero_km(self):
        punto_a = Coordinate(39.36336, 16.22622)
        punto_b = Coordinate(39.36336, 16.22622)

        distanza = punto_a.distanza(punto_b)

        self.assertEqual(distanza, 0.0)

    def test_distanza_un_grado_equatore_in_km(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        distanza = punto_a.distanza(punto_b, "km")

        self.assertGreater(distanza, 111.0)
        self.assertLess(distanza, 112.0)

    def test_distanza_un_grado_equatore_in_metri(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        distanza = punto_a.distanza(punto_b, "m")

        self.assertGreater(distanza, 111000.0)
        self.assertLess(distanza, 112000.0)

    def test_distanza_un_grado_equatore_in_miglia(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        distanza = punto_a.distanza(punto_b, "mi")

        self.assertGreater(distanza, 69.0)
        self.assertLess(distanza, 70.0)

    def test_unita_con_spazi_e_maiuscole(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        distanza = punto_a.distanza(punto_b, " KM ")

        self.assertGreater(distanza, 111.0)
        self.assertLess(distanza, 112.0)

    def test_unita_non_valida(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        with self.assertRaises(ValueError):
            punto_a.distanza(punto_b, "yards")

    def test_altro_punto_non_coordinate(self):
        punto = Coordinate(0, 0)

        with self.assertRaises(TypeError):
            punto.distanza((0, 1))

    def test_rientra_nel_raggio_in_km(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        self.assertTrue(
            punto_a.rientra_nel_raggio(punto_b, 112, "km")
        )

        self.assertFalse(
            punto_a.rientra_nel_raggio(punto_b, 111, "km")
        )

    def test_rientra_nel_raggio_in_metri(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        self.assertTrue(
            punto_a.rientra_nel_raggio(punto_b, 112000, "m")
        )

        self.assertFalse(
            punto_a.rientra_nel_raggio(punto_b, 111000, "m")
        )

    def test_raggio_negativo(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        with self.assertRaises(ValueError):
            punto_a.rientra_nel_raggio(punto_b, -1, "km")


class TestConversioneDistanza(unittest.TestCase):

    def test_metri_in_metri(self):
        risultato = converti_distanza(500, "m")

        self.assertEqual(risultato, 500.0)

    def test_metri_in_km(self):
        risultato = converti_distanza(1000, "km")

        self.assertEqual(risultato, 1.0)

    def test_metri_in_miglia(self):
        risultato = converti_distanza(1609.344, "mi")

        self.assertAlmostEqual(risultato, 1.0, places=6)

    def test_conversione_con_unita_non_valida(self):
        with self.assertRaises(ValueError):
            converti_distanza(1000, "yards")

    def test_conversione_con_distanza_negativa(self):
        with self.assertRaises(ValueError):
            converti_distanza(-1, "km")

    def test_distance_esterna_in_km(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        distanza = distance(punto_a, punto_b, "km")

        self.assertGreater(distanza, 111.0)
        self.assertLess(distanza, 112.0)

    def test_distance_esterna_unita_default(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        distanza = distance(punto_a, punto_b)

        self.assertGreater(distanza, 111.0)
        self.assertLess(distanza, 112.0)

    def test_within_radius_esterna(self):
        punto_a = Coordinate(0, 0)
        punto_b = Coordinate(0, 1)

        self.assertTrue(
            within_radius(punto_a, punto_b, 112, "km")
        )

        self.assertFalse(
            within_radius(punto_a, punto_b, 111, "km")
        )

    def test_distance_esterna_con_punto_non_valido(self):
        punto = Coordinate(0, 0)

        with self.assertRaises(TypeError):
            distance(punto, (0, 1), "km")

    def test_as_tuple(self):
        punto = Coordinate(39.36336, 16.22622)

        risultato = punto.restituisci_tupla()

        self.assertEqual(
            risultato,
            (39.36336, 16.22622),
        )

if __name__ == "__main__":
    unittest.main()