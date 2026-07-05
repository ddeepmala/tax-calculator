import os
import json

# Load tax config
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'taxConfig.json')

def load_tax_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

TAX_CONFIG = load_tax_config()

def calculate_hra_exemption(basic, da, hra_received, rent_paid, is_metro):
    """
    Calculate HRA exemption u/s 10(13A) under Old Tax Regime.
    """
    if hra_received <= 0 or rent_paid <= 0:
        return 0.0
    
    salary_for_hra = basic + da
    if salary_for_hra <= 0:
        return 0.0
        
    limit_1 = hra_received
    limit_2 = max(0.0, rent_paid - 0.1 * salary_for_hra)
    city_factor = 0.5 if is_metro else 0.4
    limit_3 = city_factor * salary_for_hra
    
    return float(min(limit_1, limit_2, limit_3))

def calculate_slab_tax(income, slabs):
    """
    Calculate progressive slab tax.
    """
    if income <= 0:
        return 0.0
        
    tax = 0.0
    prev_limit = 0.0
    
    for slab in slabs:
        limit = slab['limit']
        rate = slab['rate']
        
        if limit is None:
            # Last slab (above limit)
            tax += (income - prev_limit) * rate
            break
        elif income > limit:
            tax += (limit - prev_limit) * rate
            prev_limit = limit
        else:
            tax += (income - prev_limit) * rate
            break
            
    return float(tax)

def calculate_surcharge_and_relief(income, tax_before_surcharge, is_new_regime):
    """
    Calculate surcharge on tax and apply surcharge marginal relief if applicable.
    """
    surcharge_config = TAX_CONFIG['new_regime']['surcharge'] if is_new_regime else TAX_CONFIG['old_regime']['surcharge']
    limits = surcharge_config['limits']
    max_rate = surcharge_config['max_rate']
    
    # Find applicable surcharge rate
    applicable_rate = 0.0
    threshold = 0.0
    
    # Surcharge thresholds in India: 50L, 1Cr, 2Cr, 5Cr (Old Regime only, New capped at 2Cr rate of 25%)
    for idx in range(len(limits)):
        limit = limits[idx]
        if income > limit['threshold']:
            applicable_rate = limit['rate']
            threshold = limit['threshold']
    
    # Special rule: for income above 5Cr, if old regime, surcharge is 37%. If new regime, it's 25%.
    if income > 50000000:
        applicable_rate = max_rate
        threshold = 50000000
        
    if applicable_rate <= 0:
        return 0.0, 0.0 # No surcharge
        
    # Calculate base surcharge
    base_surcharge = tax_before_surcharge * applicable_rate
    total_tax_with_surcharge = tax_before_surcharge + base_surcharge
    
    # Surcharge Marginal Relief Calculation:
    # Tax on income should not exceed: (Tax on Threshold) + (Income - Threshold)
    # 1. Calculate tax on threshold
    tax_on_threshold = calculate_slab_tax_only_for_surcharge(threshold, is_new_regime)
    
    # 2. Surcharge on threshold
    prev_surcharge_rate = 0.0
    for limit in limits:
        if threshold > limit['threshold']:
            prev_surcharge_rate = limit['rate']
    if threshold == 50000000 and is_new_regime:
        prev_surcharge_rate = 0.25 # New regime capped at 25%
    elif threshold == 50000000 and not is_new_regime:
        prev_surcharge_rate = 0.25 # threshold 5Cr means previous threshold was 2Cr (rate 25%)
        
    surcharge_on_threshold = tax_on_threshold * prev_surcharge_rate
    total_tax_at_threshold = tax_on_threshold + surcharge_on_threshold
    
    # 3. Maximum tax cap
    max_tax_cap = total_tax_at_threshold + (income - threshold)
    
    # If total tax with surcharge exceeds the cap, apply relief
    if total_tax_with_surcharge > max_tax_cap:
        relief = total_tax_with_surcharge - max_tax_cap
        surcharge = base_surcharge - relief
        return float(max(0.0, surcharge)), float(relief)
        
    return float(base_surcharge), 0.0

def calculate_slab_tax_only_for_surcharge(income, is_new_regime):
    """
    Helper to calculate slab tax at a threshold for surcharge marginal relief.
    Uses standard adult slabs.
    """
    if is_new_regime:
        slabs = TAX_CONFIG['new_regime']['slabs']
    else:
        slabs = TAX_CONFIG['old_regime']['slabs_under_60']
    return calculate_slab_tax(income, slabs)

def run_calculation(data):
    """
    Main calculation engine function.
    Accepts input dictionary and computes Old vs New tax regimes.
    """
    # 1. Extract and sanitize inputs
    name = data.get('name', 'Taxpayer')
    age = int(data.get('age', 30))
    gender = data.get('gender', 'Male')
    residential_status = data.get('residential_status', 'Resident')
    employment_sector = data.get('employment_sector', 'Private')
    city_category = data.get('city_category', 'Metro')
    is_metro = (city_category == 'Metro')
    is_resident = (residential_status == 'Resident')
    
    # Salary Heads
    basic = float(data.get('basic_salary', 0.0))
    da = float(data.get('dearness_allowance', 0.0))
    bonus = float(data.get('bonus', 0.0))
    commission = float(data.get('commission', 0.0))
    special_allowance = float(data.get('special_allowance', 0.0))
    other_taxable_allowances = float(data.get('other_taxable_allowances', 0.0))
    employer_pf = float(data.get('employer_pf', 0.0))
    employee_pf_input = float(data.get('employee_pf', 0.0))
    gratuity = float(data.get('gratuity', 0.0))
    leave_encashment = float(data.get('leave_encashment', 0.0))
    pension = float(data.get('pension_income', 0.0))
    other_salary = float(data.get('other_salary_income', 0.0))
    children_education_allowance = float(data.get('children_education_allowance', 0.0))
    hostel_allowance = float(data.get('hostel_allowance', 0.0))
    
    # Exempt Allowances (Old Regime inputs)
    hra_received = float(data.get('hra_received', 0.0))
    rent_paid = float(data.get('rent_paid', 0.0))
    lta_received = float(data.get('lta_received', 0.0))
    tel_reimb = float(data.get('telephone_reimbursement', 0.0))
    int_reimb = float(data.get('internet_reimbursement', 0.0))
    fuel_reimb = float(data.get('fuel_reimbursement', 0.0))
    driver_reimb = float(data.get('driver_reimbursement', 0.0))
    meal_coupons = float(data.get('meal_coupons', 0.0))
    uniform_allow = float(data.get('uniform_allowance', 0.0))
    books_allow = float(data.get('books_allowance', 0.0))
    prof_dev = float(data.get('prof_dev_reimbursement', 0.0))
    other_exempt = float(data.get('other_exempt_reimbursements', 0.0))
    
    # Income from Other Sources
    savings_interest = float(data.get('savings_interest', 0.0))
    fd_interest = float(data.get('fd_interest', 0.0))
    dividend_income = float(data.get('dividend_income', 0.0))
    rental_income = float(data.get('rental_income', 0.0))
    stcg_equity = float(data.get('stcg_equity', 0.0))
    ltcg_equity = float(data.get('ltcg_equity', 0.0))
    other_income = float(data.get('other_income', 0.0))
    
    # Deductions (Old Regime)
    ppf = float(data.get('ppf', 0.0))
    elss = float(data.get('elss', 0.0))
    life_insurance = float(data.get('life_insurance', 0.0))
    sukanya = float(data.get('sukanya_samriddhi', 0.0))
    nsc = float(data.get('nsc', 0.0))
    tax_fd = float(data.get('tax_saving_fd', 0.0))
    home_loan_principal = float(data.get('home_loan_principal', 0.0))
    tuition_fees = float(data.get('tuition_fees', 0.0))
    other_80c = float(data.get('other_80c', 0.0))
    
    nps_additional_80ccd_1b = float(data.get('nps_additional_80ccd_1b', 0.0))
    health_insurance_self = float(data.get('health_insurance_self', 0.0))
    health_insurance_parents = float(data.get('health_insurance_parents', 0.0))
    is_parents_senior = data.get('is_parents_senior', False)
    education_loan_interest = float(data.get('education_loan_interest', 0.0))
    donations_80g = float(data.get('donations_80g', 0.0))
    
    home_loan_interest_self_occupied = float(data.get('home_loan_interest_self_occupied', 0.0))
    home_loan_interest_let_out = float(data.get('home_loan_interest_let_out', 0.0))
    
    other_80ee = float(data.get('other_deductions_80ee', 0.0))
    other_80eea = float(data.get('other_deductions_80eea', 0.0))
    other_80u = float(data.get('other_deductions_80u', 0.0))
    other_80dd = float(data.get('other_deductions_80dd', 0.0))
    
    # New Regime Inputs
    employer_nps_contribution = float(data.get('employer_nps_contribution', 0.0))
    agniveer_corpus = float(data.get('agniveer_corpus_contribution', 0.0))

    # --- Calculations ---
    # Gross Salary components input by user (including HRA received and new allowances)
    gross_salary = (basic + da + bonus + commission + special_allowance + 
                    other_taxable_allowances + employer_pf + gratuity + 
                    leave_encashment + pension + other_salary + 
                    hra_received + children_education_allowance + hostel_allowance)
    
    # ---------------- OLD REGIME COMPUTATION ----------------
    # 1. Exemptions (Old Regime)
    hra_exemption = calculate_hra_exemption(basic, da, hra_received, rent_paid, is_metro)
    
    # Children Education and Hostel Allowance Exemptions (Old Regime u/s 10(14))
    children_education_exemption = min(children_education_allowance, TAX_CONFIG['deduction_limits']['allowance_exemptions']['children_education_limit_annual'])
    hostel_exemption = min(hostel_allowance, TAX_CONFIG['deduction_limits']['allowance_exemptions']['hostel_limit_annual'])
    
    # Official reimbursements that are exempt upon proof (for old regime)
    exempt_reimbursements = (tel_reimb + int_reimb + fuel_reimb + driver_reimb + 
                             meal_coupons + uniform_allow + books_allow + prof_dev + 
                             other_exempt)
    
    # Standard deduction & professional tax (PT is capped at 2500 by default if salary is high enough)
    pt_deduction = 2500.0 if gross_salary > 150000 else 0.0
    old_std_deduction = float(TAX_CONFIG['old_regime']['standard_deduction'])
    
    # Net Salary (Old)
    old_net_salary = max(0.0, gross_salary - hra_exemption - lta_received - exempt_reimbursements - children_education_exemption - hostel_exemption - old_std_deduction - pt_deduction)
    
    # 2. House Property Income (Old)
    # Rental income standard deduction is 30%
    old_hp_income = 0.0
    if rental_income > 0:
        net_annual_value = rental_income * 0.7 # 30% standard deduction u/s 24(a)
        old_hp_income = net_annual_value - home_loan_interest_let_out
    
    # Interest on self occupied property is capped at 2L negative u/s 24(b)
    self_occupied_loss = min(home_loan_interest_self_occupied, TAX_CONFIG['deduction_limits']['sec_24b']['self_occupied'])
    old_hp_income -= self_occupied_loss
    
    # Set off of house property loss against other heads capped at 2L u/s 24(b)
    if old_hp_income < -200000:
        old_hp_loss_carried_forward = abs(old_hp_income) - 200000
        old_hp_income_offset = -200000.0
    else:
        old_hp_loss_carried_forward = 0.0
        old_hp_income_offset = old_hp_income
        
    # 3. Other Sources Income (Old)
    old_other_sources = savings_interest + fd_interest + dividend_income + other_income
    
    # 4. Gross Taxable Income (Old) (excluding Capital Gains for separate taxation)
    old_gti_slab = old_net_salary + old_hp_income_offset + old_other_sources
    
    # 5. Chapter VI-A Deductions (Old Regime)
    # Section 80C
    total_80c_entered = (employee_pf_input + ppf + elss + life_insurance + sukanya + 
                         nsc + tax_fd + home_loan_principal + tuition_fees + other_80c)
    eligible_80c = min(total_80c_entered, TAX_CONFIG['deduction_limits']['sec_80c'])
    
    # Section 80CCD(1B) - Additional NPS
    eligible_80ccd_1b = min(nps_additional_80ccd_1b, TAX_CONFIG['deduction_limits']['sec_80ccd_1b'])
    
    # Section 80D - Health Insurance
    self_limit_80d = TAX_CONFIG['deduction_limits']['sec_80d']['self_family_senior'] if age >= 60 else TAX_CONFIG['deduction_limits']['sec_80d']['self_family_general']
    parents_limit_80d = TAX_CONFIG['deduction_limits']['sec_80d']['parents_senior'] if is_parents_senior else TAX_CONFIG['deduction_limits']['sec_80d']['parents_general']
    
    eligible_80d_self = min(health_insurance_self, self_limit_80d)
    eligible_80d_parents = min(health_insurance_parents, parents_limit_80d)
    eligible_80d = eligible_80d_self + eligible_80d_parents
    
    # Section 80TTA / 80TTB - Savings / Deposit Interest
    if age >= 60:
        # Senior citizens get 80TTB up to 50k on all interest
        eligible_interest_deduction = min(savings_interest + fd_interest, TAX_CONFIG['deduction_limits']['sec_80ttb'])
        sec_name = "80TTB"
    else:
        # Non-seniors get 80TTA up to 10k on savings interest only
        eligible_interest_deduction = min(savings_interest, TAX_CONFIG['deduction_limits']['sec_80tta'])
        sec_name = "80TTA"
        
    # Other Deductions
    eligible_80ee = min(other_80ee, TAX_CONFIG['deduction_limits']['sec_80ee'])
    eligible_80eea = min(other_80eea, TAX_CONFIG['deduction_limits']['sec_80eea'])
    
    # Employer NPS contribution (Section 80CCD(2)) - 14% for gov, 10% for private in old regime
    nps_factor = 0.14 if employment_sector in ['Central Government', 'State Government', 'PSU'] else 0.10
    max_employer_nps_old = (basic + da) * nps_factor
    eligible_employer_nps_old = min(employer_nps_contribution, max_employer_nps_old)
    
    total_deductions = (eligible_80c + eligible_80ccd_1b + eligible_80d + 
                        eligible_interest_deduction + education_loan_interest + 
                        donations_80g + eligible_80ee + eligible_80eea + 
                        other_80u + other_80dd + eligible_employer_nps_old)
    
    # Deductions cannot exceed Gross Slab Income
    eligible_deductions_old = min(total_deductions, max(0.0, old_gti_slab))
    
    # Net Taxable Slab Income (Old)
    old_taxable_slab_income = max(0.0, old_gti_slab - eligible_deductions_old)
    
    # Total Income (Old)
    old_total_income = old_taxable_slab_income + stcg_equity + ltcg_equity
    
    # 6. Slab Tax Calculation (Old)
    if age >= 80:
        old_slabs = TAX_CONFIG['old_regime']['slabs_above_80']
    elif age >= 60:
        old_slabs = TAX_CONFIG['old_regime']['slabs_60_to_80']
    else:
        old_slabs = TAX_CONFIG['old_regime']['slabs_under_60']
        
    old_slab_tax = calculate_slab_tax(old_taxable_slab_income, old_slabs)
    
    # 7. Capital Gains Tax (Old) with Unexhausted Basic Exemption Shifting
    # Old regime exemption limit
    old_basic_exemption = 500000 if age >= 80 else (300000 if age >= 60 else 250000)
    unused_exemption_old = max(0.0, old_basic_exemption - old_taxable_slab_income)
    
    # Exemption for 112A (LTCG) is 1.25L
    remaining_ltcg_old = max(0.0, ltcg_equity - 125000.0)
    
    if is_resident and unused_exemption_old > 0:
        # Offset STCG first
        stcg_offset_old = min(stcg_equity, unused_exemption_old)
        taxable_stcg_old = stcg_equity - stcg_offset_old
        unused_exemption_old -= stcg_offset_old
        
        # Offset remaining LTCG next
        ltcg_offset_old = min(remaining_ltcg_old, unused_exemption_old)
        taxable_ltcg_old = remaining_ltcg_old - ltcg_offset_old
    else:
        taxable_stcg_old = stcg_equity
        taxable_ltcg_old = remaining_ltcg_old
        
    old_stcg_tax = taxable_stcg_old * 0.20
    old_ltcg_tax = taxable_ltcg_old * 0.125
    old_cg_tax = old_stcg_tax + old_ltcg_tax
    
    # Total Tax before rebate (Old)
    old_tax_before_rebate = old_slab_tax + old_cg_tax
    
    # 8. Rebate u/s 87A (Old)
    old_rebate = 0.0
    if is_resident and old_total_income <= TAX_CONFIG['old_regime']['rebate_87a']['threshold']:
        # Note: Rebate u/s 87A is not allowed against LTCG 112A
        old_rebate = min(old_slab_tax + old_stcg_tax, TAX_CONFIG['old_regime']['rebate_87a']['max_rebate'])
        
    old_tax_after_rebate = max(0.0, old_tax_before_rebate - old_rebate)
    
    # 9. Surcharge & Surcharge Marginal Relief (Old)
    old_surcharge, old_surcharge_relief = calculate_surcharge_and_relief(old_total_income, old_tax_after_rebate, is_new_regime=False)
    
    # Surcharge cap of 15% on Capital Gains (STCG and LTCG) and Dividend
    if old_surcharge > 0:
        # If surcharge is active and is higher than 15% (i.e. 25% or 37%)
        # Cap surcharge on cg_tax at 15%
        surcharge_config = TAX_CONFIG['old_regime']['surcharge']
        rate_applied = 0.0
        for limit in surcharge_config['limits']:
            if old_total_income > limit['threshold']:
                rate_applied = limit['rate']
        if old_total_income > 50000000:
            rate_applied = surcharge_config['max_rate']
            
        if rate_applied > 0.15:
            base_cg_tax = old_cg_tax
            base_slab_tax = old_tax_after_rebate - base_cg_tax
            old_surcharge = (base_slab_tax * rate_applied) + (base_cg_tax * 0.15)
            
    # 10. Health & Education Cess (Old)
    old_cess = (old_tax_after_rebate + old_surcharge) * TAX_CONFIG['general']['cess_rate']
    
    # Final Tax (Old)
    old_final_tax = old_tax_after_rebate + old_surcharge + old_cess


    # ---------------- NEW REGIME COMPUTATION ----------------
    # 1. Standard Deduction (New)
    new_std_deduction = float(TAX_CONFIG['new_regime']['standard_deduction'])
    
    # Net Salary (New)
    new_net_salary = max(0.0, gross_salary - new_std_deduction)
    
    # 2. House Property Income (New)
    # Rental income standard deduction is 30%
    new_hp_income = 0.0
    if rental_income > 0:
        # HP loss cannot be set off against other heads under New Regime.
        # But interest can be deducted from rental income. Net HP income cannot be negative (no offset).
        net_annual_value_new = rental_income * 0.7
        new_hp_income = max(0.0, net_annual_value_new - home_loan_interest_let_out)
        
    # Self-occupied property interest is NOT allowed under New Regime
    
    # 3. Other Sources Income (New)
    new_other_sources = savings_interest + fd_interest + dividend_income + other_income
    
    # 4. Gross Taxable Income (New) (excluding Capital Gains for separate taxation)
    new_gti_slab = new_net_salary + new_hp_income + new_other_sources
    
    # 5. Allowed Deductions (New Regime)
    # Employer NPS contribution (Section 80CCD(2)) - 14% of Basic + DA for all
    max_employer_nps_new = (basic + da) * 0.14
    eligible_employer_nps_new = min(employer_nps_contribution, max_employer_nps_new)
    
    # Agniveer Corpus (Section 80CCH)
    eligible_deductions_new = min(eligible_employer_nps_new + agniveer_corpus, max(0.0, new_gti_slab))
    
    # Net Taxable Slab Income (New)
    new_taxable_slab_income = max(0.0, new_gti_slab - eligible_deductions_new)
    
    # Total Income (New)
    new_total_income = new_taxable_slab_income + stcg_equity + ltcg_equity
    
    # 6. Slab Tax Calculation (New) - FY 2026-27 Slabs
    new_slabs = TAX_CONFIG['new_regime']['slabs']
    new_slab_tax = calculate_slab_tax(new_taxable_slab_income, new_slabs)
    
    # 7. Capital Gains Tax (New) with Unexhausted Basic Exemption Shifting
    new_basic_exemption = 400000.0 # FY 2026-27 basic exemption is 4L
    unused_exemption_new = max(0.0, new_basic_exemption - new_taxable_slab_income)
    
    # Exemption for 112A (LTCG) is 1.25L
    remaining_ltcg_new = max(0.0, ltcg_equity - 125000.0)
    
    if is_resident and unused_exemption_new > 0:
        # Offset STCG first
        stcg_offset_new = min(stcg_equity, unused_exemption_new)
        taxable_stcg_new = stcg_equity - stcg_offset_new
        unused_exemption_new -= stcg_offset_new
        
        # Offset remaining LTCG next
        ltcg_offset_new = min(remaining_ltcg_new, unused_exemption_new)
        taxable_ltcg_new = remaining_ltcg_new - ltcg_offset_new
    else:
        taxable_stcg_new = stcg_equity
        taxable_ltcg_new = remaining_ltcg_new
        
    new_stcg_tax = taxable_stcg_new * 0.20
    new_ltcg_tax = taxable_ltcg_new * 0.125
    new_cg_tax = new_stcg_tax + new_ltcg_tax
    
    # Total Tax before rebate (New)
    new_tax_before_rebate = new_slab_tax + new_cg_tax
    
    # 8. Rebate u/s 87A and Marginal Relief (New)
    new_rebate = 0.0
    new_marginal_relief = 0.0
    
    if is_resident:
        # Rebate is available up to ₹60,000 for income up to ₹12 Lakhs
        # Note: Rebate is not allowed against LTCG 112A tax
        if new_total_income <= TAX_CONFIG['new_regime']['rebate_87a']['threshold']:
            new_rebate = min(new_slab_tax + new_stcg_tax, TAX_CONFIG['new_regime']['rebate_87a']['max_rebate'])
            new_tax_after_rebate = max(0.0, new_tax_before_rebate - new_rebate)
        else:
            # Check for marginal relief (income between 12L and 12.75L)
            new_tax_after_rebate = new_tax_before_rebate
            excess_income_new = new_total_income - TAX_CONFIG['new_regime']['rebate_87a']['threshold']
            
            # Tax before cess (excluding LTCG 112A from rebate, but marginal relief applies to total tax)
            # Standard rule: tax payable before cess cannot exceed excess income above 12L (excluding LTCG 112A)
            # If the calculated tax (before cess, excluding LTCG 112A) exceeds the excess income,
            # marginal relief reduces the tax to exactly the excess income.
            tax_subject_to_relief = new_slab_tax + new_stcg_tax
            if tax_subject_to_relief > excess_income_new:
                new_marginal_relief = tax_subject_to_relief - excess_income_new
                new_tax_after_rebate = excess_income_new + new_ltcg_tax
            else:
                new_marginal_relief = 0.0
                new_tax_after_rebate = new_tax_before_rebate
    else:
        new_tax_after_rebate = new_tax_before_rebate
        
    # 9. Surcharge & Surcharge Marginal Relief (New)
    new_surcharge, new_surcharge_relief = calculate_surcharge_and_relief(new_total_income, new_tax_after_rebate, is_new_regime=True)
    
    # Surcharge cap of 15% on Capital Gains (STCG and LTCG) and Dividend
    if new_surcharge > 0:
        # Under new regime, surcharge is capped at 25% anyway
        surcharge_config = TAX_CONFIG['new_regime']['surcharge']
        rate_applied = 0.0
        for limit in surcharge_config['limits']:
            if new_total_income > limit['threshold']:
                rate_applied = limit['rate']
        if new_total_income > 20000000:
            rate_applied = surcharge_config['max_rate']
            
        if rate_applied > 0.15:
            base_cg_tax = new_cg_tax
            base_slab_tax = new_tax_after_rebate - base_cg_tax
            new_surcharge = (base_slab_tax * rate_applied) + (base_cg_tax * 0.15)
            
    # 10. Health & Education Cess (New)
    new_cess = (new_tax_after_rebate + new_surcharge) * TAX_CONFIG['general']['cess_rate']
    
    # Final Tax (New)
    new_final_tax = new_tax_after_rebate + new_surcharge + new_cess


    # --- Regime Comparison & Recommendation ---
    tax_saved = abs(old_final_tax - new_final_tax)
    
    if new_final_tax < old_final_tax:
        recommended_regime = "New Tax Regime"
        savings_text = f"New Regime is better by ₹{tax_saved:,.2f}"
        percentage_saved = (tax_saved / old_final_tax * 100) if old_final_tax > 0 else 0.0
        recommendation_details = (
            f"By choosing the New Tax Regime, you will save ₹{tax_saved:,.0f} "
            f"({percentage_saved:.1f}% less tax than the Old Tax Regime)."
        )
    elif old_final_tax < new_final_tax:
        recommended_regime = "Old Tax Regime"
        savings_text = f"Old Regime is better by ₹{tax_saved:,.2f}"
        percentage_saved = (tax_saved / new_final_tax * 100) if new_final_tax > 0 else 0.0
        recommendation_details = (
            f"By choosing the Old Tax Regime and maximizing your deductions, you will save ₹{tax_saved:,.0f} "
            f"({percentage_saved:.1f}% less tax than the New Tax Regime)."
        )
    else:
        recommended_regime = "New Tax Regime" # Default if equal
        savings_text = "Both regimes have identical tax liability"
        percentage_saved = 0.0
        recommendation_details = (
            "Both regimes result in the same tax liability of ₹0. "
            "It is recommended to choose the New Tax Regime as it requires no documentation or investments."
        )

    # Optimization Advice
    optimization_suggestions = []
    if recommended_regime == "New Tax Regime":
        # Check if they can switch to Old Regime by increasing deductions
        # Target: how much more deductions do they need to make Old Regime better?
        # Difference in taxable income needed = (Old Tax - New Tax) / average tax rate
        pass
    
    # Pack result response
    result = {
      "personal_details": {
        "name": name,
        "age": age,
        "gender": gender,
        "residential_status": residential_status,
        "employment_sector": employment_sector,
        "city_category": city_category
      },
      "summary": {
        "gross_salary": gross_salary,
        "old_taxable_income": old_total_income,
        "new_taxable_income": new_total_income,
        "old_tax_payable": old_final_tax,
        "new_tax_payable": new_final_tax,
        "tax_saved": tax_saved,
        "percentage_saved": percentage_saved,
        "recommended_regime": recommended_regime,
        "savings_text": savings_text,
        "recommendation_details": recommendation_details
      },
      "old_regime_breakdown": {
        "gross_salary": gross_salary,
        "hra_received": hra_received,
        "children_education_allowance": children_education_allowance,
        "hostel_allowance": hostel_allowance,
        "children_education_exemption": children_education_exemption,
        "hostel_exemption": hostel_exemption,
        "hra_exemption": hra_exemption,
        "lta_exemption": lta_received,
        "reimbursements_exemption": exempt_reimbursements,
        "standard_deduction": old_std_deduction,
        "professional_tax": pt_deduction,
        "net_salary": old_net_salary,
        "house_property_income": old_hp_income_offset,
        "house_property_loss_cf": old_hp_loss_carried_forward,
        "other_sources_income": old_other_sources,
        "gross_taxable_slab_income": old_gti_slab,
        "deductions": {
          "sec_80c": eligible_80c,
          "sec_80ccd_1b": eligible_80ccd_1b,
          "sec_80d": eligible_80d,
          "interest_deduction": eligible_interest_deduction,
          "interest_deduction_sec": sec_name,
          "sec_80e": education_loan_interest,
          "sec_80g": donations_80g,
          "sec_80ee": eligible_80ee,
          "sec_80eea": eligible_80eea,
          "sec_80u": other_80u,
          "sec_80dd": other_80dd,
          "sec_80ccd_2_employer": eligible_employer_nps_old,
          "total_deductions_eligible": eligible_deductions_old
        },
        "taxable_slab_income": old_taxable_slab_income,
        "stcg_equity": stcg_equity,
        "ltcg_equity": ltcg_equity,
        "stcg_taxable_after_shifting": taxable_stcg_old,
        "ltcg_taxable_after_shifting": taxable_ltcg_old,
        "slab_tax": old_slab_tax,
        "stcg_tax": old_stcg_tax,
        "ltcg_tax": old_ltcg_tax,
        "tax_before_rebate": old_tax_before_rebate,
        "sec_87a_rebate": old_rebate,
        "tax_after_rebate": old_tax_after_rebate,
        "surcharge": old_surcharge,
        "surcharge_marginal_relief": old_surcharge_relief,
        "cess": old_cess,
        "total_tax": old_final_tax
      },
      "new_regime_breakdown": {
        "gross_salary": gross_salary,
        "hra_received": hra_received,
        "children_education_allowance": children_education_allowance,
        "hostel_allowance": hostel_allowance,
        "children_education_exemption": 0.0,
        "hostel_exemption": 0.0,
        "standard_deduction": new_std_deduction,
        "net_salary": new_net_salary,
        "house_property_income": new_hp_income,
        "other_sources_income": new_other_sources,
        "gross_taxable_slab_income": new_gti_slab,
        "deductions": {
          "sec_80ccd_2_employer": eligible_employer_nps_new,
          "sec_80cch_agniveer": agniveer_corpus,
          "total_deductions_eligible": eligible_deductions_new
        },
        "taxable_slab_income": new_taxable_slab_income,
        "stcg_equity": stcg_equity,
        "ltcg_equity": ltcg_equity,
        "stcg_taxable_after_shifting": taxable_stcg_new,
        "ltcg_taxable_after_shifting": taxable_ltcg_new,
        "slab_tax": new_slab_tax,
        "stcg_tax": new_stcg_tax,
        "ltcg_tax": new_ltcg_tax,
        "tax_before_rebate": new_tax_before_rebate,
        "sec_87a_rebate": new_rebate,
        "sec_87a_marginal_relief": new_marginal_relief,
        "tax_after_rebate": new_tax_after_rebate,
        "surcharge": new_surcharge,
        "surcharge_marginal_relief": new_surcharge_relief,
        "cess": new_cess,
        "total_tax": new_final_tax
      }
    }
    
    return result
