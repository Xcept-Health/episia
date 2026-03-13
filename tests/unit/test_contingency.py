"""
Test suite for contingency.py module.
"""

import unittest
import numpy as np
from epitools.stats.contingency import Table2x2, risk_ratio, odds_ratio


class TestTable2x2(unittest.TestCase):
    """Test cases for Table2x2 class."""
    
    def test_initialization(self):
        """Test table initialization and basic properties."""
        table = Table2x2(10, 20, 30, 40)
        
        self.assertEqual(table.a, 10)
        self.assertEqual(table.b, 20)
        self.assertEqual(table.c, 30)
        self.assertEqual(table.d, 40)
        self.assertEqual(table.total, 100)
    
    def test_risk_calculation(self):
        """Test risk calculations."""
        table = Table2x2(10, 20, 30, 40)
        
        # Risk exposed = 10 / (10 + 30) = 0.25
        self.assertAlmostEqual(table.risk_exposed, 0.25)
        
        # Risk unexposed = 20 / (20 + 40) = 0.333...
        self.assertAlmostEqual(table.risk_unexposed, 1/3)
    
    def test_risk_ratio(self):
        """Test risk ratio calculation."""
        table = Table2x2(10, 20, 30, 40)
        result = table.risk_ratio()
        
        # RR = 0.25 / 0.333... = 0.75
        self.assertAlmostEqual(result.estimate, 0.75, places=4)
        self.assertTrue(result.ci_lower < result.estimate < result.ci_upper)
    
    def test_odds_ratio(self):
        """Test odds ratio calculation."""
        table = Table2x2(10, 20, 30, 40)
        result = table.odds_ratio()
        
        # OR = (10*40)/(20*30) = 400/600 = 0.666...
        self.assertAlmostEqual(result.estimate, 2/3, places=4)
        self.assertTrue(result.ci_lower < result.estimate < result.ci_upper)
    
    def test_risk_difference(self):
        """Test risk difference calculation."""
        table = Table2x2(10, 20, 30, 40)
        result = table.risk_difference()
        
        # RD = 0.25 - 0.333... = -0.0833...
        self.assertAlmostEqual(result['estimate'], -1/12, places=4)
    
    def test_chi_square(self):
        """Test chi-square test."""
        table = Table2x2(10, 20, 30, 40)
        result = table.chi_square(correction=True)
        
        self.assertIn('chi2', result)
        self.assertIn('p_value', result)
        self.assertIn('df', result)
        self.assertEqual(result['df'], 1)
    
    def test_summary(self):
        """Test comprehensive summary method."""
        table = Table2x2(10, 20, 30, 40)
        summary = table.summary()
        
        self.assertIn('risk_ratio', summary)
        self.assertIn('odds_ratio', summary)
        self.assertIn('risk_difference', summary)
        self.assertIn('attributable_fractions', summary)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_risk_ratio_function(self):
        """Test risk_ratio convenience function."""
        result = risk_ratio(10, 20, 30, 40)
        self.assertAlmostEqual(result.estimate, 0.75, places=4)
    
    def test_odds_ratio_function(self):
        """Test odds_ratio convenience function."""
        result = odds_ratio(10, 20, 30, 40)
        self.assertAlmostEqual(result.estimate, 2/3, places=4)


if __name__ == '__main__':
    unittest.main()