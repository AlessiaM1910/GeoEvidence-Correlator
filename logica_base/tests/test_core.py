import os
import sys

CARTELLA_LOGICA = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if CARTELLA_LOGICA not in sys.path:
    sys.path.insert(0, CARTELLA_LOGICA)
import unittest

from core import (
    haversine_distance,
    is_within_radius,
    filter_points,
)


class TestCore(unittest.TestCase):

    def test_distanza_identica_zero(self):
        distanza = haversine_distance(
            39.36336,
            16.22622,
            39.36336,
            16.22622,
        )

        self.assertEqual(distanza, 0.0)

    def test_distanza_un_grado_equatore(self):
        distanza = haversine_distance(
            0,
            0,
            0,
            1,
        )

        self.assertGreater(distanza, 111.0)
        self.assertLess(distanza, 112.0)

    def test_is_within_radius(self):
        risultato = is_within_radius(
            0,
            1,
            0,
            0,
            112,
        )

        self.assertTrue(risultato)

    def test_fuori_dal_raggio(self):
        risultato = is_within_radius(
            0,
            1,
            0,
            0,
            111,
        )

        self.assertFalse(risultato)

    def test_raggio_zero_stesso_punto(self):
        risultato = is_within_radius(
            39.36336,
            16.22622,
            39.36336,
            16.22622,
            0,
        )

        self.assertTrue(risultato)

    def test_raggio_negativo_non_valido(self):
        with self.assertRaises(ValueError):
            is_within_radius(
                0,
                0,
                0,
                1,
                -1,
            )

    def test_filter_points_restuisce_solo_quelli_nel_raggio(self):
        punti = [
            (0, 2, "lontano"),
            (0, 0, "centro"),
            (0, 1, "vicino"),
        ]

        risultati = filter_points(
            punti,
            0,
            0,
            112,
        )

        nomi = []

        for nome, distanza in risultati:
            nomi.append(nome)

        self.assertEqual(
            nomi,
            ["centro", "vicino"],
        )

    def test_filter_points_ordina_per_distanza(self):
        punti = [
            (0, 1, "vicino"),
            (0, 0, "centro"),
        ]

        risultati = filter_points(
            punti,
            0,
            0,
            112,
        )

        self.assertEqual(
            risultati[0][0],
            "centro",
        )

        self.assertEqual(
            risultati[1][0],
            "vicino",
        )


if __name__ == "__main__":
    unittest.main()