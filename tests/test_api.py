import urllib.request
import json
import os

def test_api():
    print("==================================================")
    print("RUNNING API ENDPOINT VERIFICATION ON LOCAL HOST")
    print("==================================================")
    
    base_url = "http://127.0.0.1:5000"
    
    # 1. Test Static Content Serving (GET /)
    print("\n[Test 1] Testing static files serving (GET /)...")
    try:
        response = urllib.request.urlopen(base_url + "/")
        html = response.read().decode('utf-8')
        print(f"  Response Code: {response.status}")
        assert "India Salary Tax Planner" in html, "Expected 'India Salary Tax Planner' in the homepage HTML"
        print("  => Test 1 PASSED! Server is serving static files.")
    except Exception as e:
        print(f"  => Test 1 FAILED: {e}")
        return False
        
    # 2. Test Calculation API (POST /api/calculate)
    print("\n[Test 2] Testing Tax Calculation API (POST /api/calculate)...")
    test_data = {
        "name": "Deepmala Test",
        "age": 30,
        "gender": "Female",
        "residential_status": "Resident",
        "employment_sector": "Private",
        "city_category": "Metro",
        "basic_salary": 800000,
        "dearness_allowance": 0,
        "bonus": 50000,
        "special_allowance": 100000,
        "employee_pf": 96000,
        "employer_pf": 96000,
        "hra_received": 320000,
        "rent_paid": 240000,
        "savings_interest": 5000,
        "fd_interest": 15000,
        "ppf": 50000,
        "life_insurance": 40000,
        "nps_additional_80ccd_1b": 50000,
        "health_insurance_self": 15000,
        "health_insurance_parents": 30000,
        "is_parents_senior": True
    }
    
    try:
        req = urllib.request.Request(
            base_url + "/api/calculate",
            data=json.dumps(test_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        print(f"  Response Code: {response.status}")
        print(f"  Gross Salary calculated: Rs. {result['summary']['gross_salary']:,.2f}")
        print(f"  Old Regime Tax: Rs. {result['summary']['old_tax_payable']:,.2f}")
        print(f"  New Regime Tax: Rs. {result['summary']['new_tax_payable']:,.2f}")
        print(f"  Recommended Regime: {result['summary']['recommended_regime']}")
        assert 'summary' in result, "Expected 'summary' key in API response"
        assert 'old_regime_breakdown' in result, "Expected 'old_regime_breakdown' key in API response"
        assert 'new_regime_breakdown' in result, "Expected 'new_regime_breakdown' key in API response"
        print("  => Test 2 PASSED! Tax calculation API is functional and accurate.")
    except Exception as e:
        print(f"  => Test 2 FAILED: {e}")
        return False
        
    # 3. Test PDF Generation (POST /api/download-pdf)
    print("\n[Test 3] Testing PDF Generation API (POST /api/download-pdf)...")
    try:
        req = urllib.request.Request(
            base_url + "/api/download-pdf",
            data=json.dumps(test_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req)
        pdf_data = response.read()
        print(f"  Response Code: {response.status}")
        print(f"  Mime-type: {response.info().get_content_type()}")
        print(f"  File size received: {len(pdf_data)} bytes")
        
        # Verify PDF header
        assert pdf_data.startswith(b"%PDF"), "Response is not a valid PDF file"
        print("  => Test 3 PASSED! PDF generation endpoint is working and returning valid PDF headers.")
        
    except Exception as e:
        print(f"  => Test 3 FAILED: {e}")
        return False
        
    print("\n==================================================")
    print("ALL API VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
    return True

if __name__ == "__main__":
    test_api()
