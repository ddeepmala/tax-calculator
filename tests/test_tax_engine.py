import sys
import os

# Adjust path to import src modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

from src.tax_engine import run_calculation

def run_tests():
    print("==================================================")
    print("RUNNING INDIAN TAX ENGINE UNIT TESTS FOR FY 2026-27")
    print("==================================================")
    
    # ---------------- TEST 1: Income Rs. 7.5 Lakhs (New Regime should be Zero Tax) ----------------
    print("\n[Test 1] Income: Rs. 7,50,000, New Regime Zero Tax Verification...")
    data1 = {
        "basic_salary": 600000,
        "dearness_allowance": 50000,
        "bonus": 50000,
        "special_allowance": 50000,
        "residential_status": "Resident"
    }
    res1 = run_calculation(data1)
    new_taxable1 = res1['new_regime_breakdown']['taxable_slab_income']
    new_tax1 = res1['new_regime_breakdown']['total_tax']
    print(f"  Gross Salary: Rs. {res1['summary']['gross_salary']:,.2f}")
    print(f"  New Regime Taxable Income: Rs. {new_taxable1:,.2f} (after standard deduction)")
    print(f"  New Regime Tax Payable: Rs. {new_tax1:,.2f}")
    assert new_tax1 == 0.0, f"Expected 0 tax, got {new_tax1}"
    print("  => Test 1 PASSED!")

    # ---------------- TEST 2: Income Rs. 12 Lakhs (New Regime should be Zero Tax) ----------------
    print("\n[Test 2] Income: Rs. 12,00,000, New Regime Limit Verification...")
    data2 = {
        "basic_salary": 1100000,
        "dearness_allowance": 100000,
        "residential_status": "Resident"
    }
    res2 = run_calculation(data2)
    new_taxable2 = res2['new_regime_breakdown']['taxable_slab_income']
    new_tax2 = res2['new_regime_breakdown']['total_tax']
    print(f"  Gross Salary: Rs. {res2['summary']['gross_salary']:,.2f}")
    print(f"  New Regime Taxable Income: Rs. {new_taxable2:,.2f} (after standard deduction)")
    print(f"  New Regime Tax Payable: Rs. {new_tax2:,.2f}")
    assert new_tax2 == 0.0, f"Expected 0 tax, got {new_tax2}"
    print("  => Test 2 PASSED!")

    # ---------------- TEST 3: Income Rs. 12,80,000 (Testing Section 87A Marginal Relief) ----------------
    print("\n[Test 3] Income: Rs. 12,80,000, Marginal Relief Verification...")
    data3 = {
        "basic_salary": 1280000,
        "residential_status": "Resident"
    }
    res3 = run_calculation(data3)
    new_taxable3 = res3['new_regime_breakdown']['taxable_slab_income']
    new_tax_before_cess3 = res3['new_regime_breakdown']['tax_after_rebate']
    marginal_relief3 = res3['new_regime_breakdown']['sec_87a_marginal_relief']
    new_tax_final3 = res3['new_regime_breakdown']['total_tax']
    
    print(f"  Gross Salary: Rs. {res3['summary']['gross_salary']:,.2f}")
    print(f"  Taxable Income after 75k Standard Ded: Rs. {new_taxable3:,.2f}")
    print(f"  Excess income over 12 Lakhs: Rs. {(new_taxable3 - 1200000):,.2f}")
    print(f"  Marginal Relief u/s 87A applied: Rs. {marginal_relief3:,.2f}")
    print(f"  Tax after rebate/relief (before cess): Rs. {new_tax_before_cess3:,.2f}")
    print(f"  Final Tax (with 4% cess): Rs. {new_tax_final3:,.2f}")
    assert new_tax_final3 == 5200.0, f"Expected final tax of 5,200, got {new_tax_final3}"
    print("  => Test 3 PASSED!")

    # ---------------- TEST 4: HRA Calculation (Old Regime) ----------------
    print("\n[Test 4] HRA Exemption (Old Regime) Verification...")
    data4 = {
        "basic_salary": 500000,
        "dearness_allowance": 100000,
        "hra_received": 200000,
        "rent_paid": 150000,
        "city_category": "Metro",
        "residential_status": "Resident"
    }
    res4 = run_calculation(data4)
    hra_ex = res4['old_regime_breakdown']['hra_exemption']
    print(f"  Basic: Rs. 5,00,000, DA: Rs. 1,00,000, HRA Received: Rs. 2,00,000, Rent Paid: Rs. 1,50,000, Metro")
    print(f"  Calculated HRA Exemption: Rs. {hra_ex:,.2f} (Expected: Rs. 90,000.00)")
    assert hra_ex == 90000.0, f"Expected 90,000 HRA exemption, got {hra_ex}"
    print("  => Test 4 PASSED!")

    # ---------------- TEST 5: Surcharge Verification (New Regime @ 6 Crores) ----------------
    print("\n[Test 5] High Income Surcharge Cap Verification (Income: Rs. 6 Crores)...")
    data5 = {
        "basic_salary": 60000000,
        "residential_status": "Resident"
    }
    res5 = run_calculation(data5)
    old_surcharge_rate = res5['old_regime_breakdown']['surcharge'] / res5['old_regime_breakdown']['tax_after_rebate']
    new_surcharge_rate = res5['new_regime_breakdown']['surcharge'] / res5['new_regime_breakdown']['tax_after_rebate']
    print(f"  Old Regime Surcharge rate: {old_surcharge_rate:.2%} (Expected: 37%)")
    print(f"  New Regime Surcharge rate: {new_surcharge_rate:.2%} (Expected: 25%)")
    assert abs(old_surcharge_rate - 0.37) < 0.01, f"Expected 37% Old regime surcharge, got {old_surcharge_rate}"
    assert abs(new_surcharge_rate - 0.25) < 0.01, f"Expected 25% New regime surcharge, got {new_surcharge_rate}"
    print("  => Test 5 PASSED!")

    print("\n==================================================")
    print("ALL TESTS COMPLETED SUCCESSFULLY! TAX ENGINE IS ACCURATE.")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
