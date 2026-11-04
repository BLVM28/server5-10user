"""Analytical NRMSE cases, including the previously incorrect tiny-reference case."""
import unittest
from precision_metrics import nrmse_from_sums


class PrecisionMetricTests(unittest.TestCase):
    def test_exact_zero_output_error(self):
        self.assertEqual(nrmse_from_sums(0, 25, 2), 0)

    def test_zero_reference_and_zero_error(self):
        self.assertEqual(nrmse_from_sums(0, 0, 25344), 0)

    def test_zero_prediction_has_unit_relative_error(self):
        self.assertEqual(nrmse_from_sums(25, 25, 2), 1)

    def test_ten_percent_error(self):
        self.assertAlmostEqual(nrmse_from_sums(0.25, 25, 2), 0.1, places=15)

    def test_tiny_reference_uses_rms_floor(self):
        # All 25,344 references are 1e-10; all predictions are zero.
        # RMSE=1e-10, denominator=1e-8 -> 1%, not the previous 100%.
        self.assertAlmostEqual(nrmse_from_sums(25344e-20, 25344e-20, 25344), 0.01, places=15)

    def test_zero_reference_nonzero_prediction(self):
        # Every prediction is 1e-9 against zero -> 10% of the floor.
        self.assertAlmostEqual(nrmse_from_sums(8e-18, 0, 8), 0.1, places=15)

    def test_exact_floor(self):
        self.assertAlmostEqual(nrmse_from_sums(4e-16, 4e-16, 4), 1, places=15)

    def test_below_floor(self):
        self.assertAlmostEqual(nrmse_from_sums(0.99**2 * 1e-16, 0.99**2 * 1e-16, 1), 0.99, places=15)

    def test_above_floor(self):
        self.assertAlmostEqual(nrmse_from_sums(1.01**2 * 1e-16, 1.01**2 * 1e-16, 1), 1, places=15)

    def test_repeating_a_batch_does_not_change_error(self):
        self.assertAlmostEqual(nrmse_from_sums(25, 2500, 200), 0.1, places=15)

    def test_aggregate_energy_not_mean_of_sample_ratios(self):
        # References [0,1], predictions [0,1.2]: aggregate error is 20%.
        self.assertAlmostEqual(nrmse_from_sums(0.04, 1, 2), 0.2, places=15)

    def test_invalid_element_counts(self):
        for elements in (0, -1, 0.5, True):
            with self.subTest(elements=elements):
                with self.assertRaises(ValueError):
                    nrmse_from_sums(1, 1, elements)

    def test_invalid_energies(self):
        for value in (-1, float('inf'), float('nan')):
            for error, reference in ((value, 1), (1, value)):
                with self.subTest(error=error, reference=reference):
                    with self.assertRaises(ValueError):
                        nrmse_from_sums(error, reference, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
