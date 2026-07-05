/* ==========================================================================
   GLOBAL APP STATE
   ========================================================================== */
let currentStep = 1;
const totalSteps = 6;
let lastCalculationResult = null;

// Chart references for cleanup
let comparisonChart = null;
let breakupChart = null;
let projectionChart = null;

// Slabs for client-side projections
const NEW_SLABS = [
    { limit: 400000, rate: 0.00 },
    { limit: 800000, rate: 0.05 },
    { limit: 1200000, rate: 0.10 },
    { limit: 1600000, rate: 0.15 },
    { limit: 2000000, rate: 0.20 },
    { limit: 2400000, rate: 0.25 },
    { limit: null, rate: 0.30 }
];

const OLD_SLABS_UNDER_60 = [
    { limit: 250000, rate: 0.00 },
    { limit: 500000, rate: 0.05 },
    { limit: 1000000, rate: 0.20 },
    { limit: null, rate: 0.30 }
];

const OLD_SLABS_60_TO_80 = [
    { limit: 300000, rate: 0.00 },
    { limit: 500000, rate: 0.05 },
    { limit: 1000000, rate: 0.20 },
    { limit: null, rate: 0.30 }
];

const OLD_SLABS_ABOVE_80 = [
    { limit: 500000, rate: 0.00 },
    { limit: 1000000, rate: 0.20 },
    { limit: null, rate: 0.30 }
];

/* ==========================================================================
   INIT & EVENT LISTENERS
   ========================================================================== */
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    setupWizard();
    setupLiveSalaryUpdates();
    setupFormSubmission();
    setupDashboardActions();
});

/* ==========================================================================
   THEME MANAGER (DARK / LIGHT MODE)
   ========================================================================== */
function initTheme() {
    const themeToggleBtn = document.getElementById("themeToggleBtn");
    const savedTheme = localStorage.getItem("theme") || "light";
    
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);
    
    themeToggleBtn.addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme");
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        
        document.documentElement.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
        updateThemeIcon(newTheme);
        
        // Redraw charts with correct grid/text colors if dashboard is active
        if (lastCalculationResult) {
            renderCharts(lastCalculationResult);
        }
    });
}

function updateThemeIcon(theme) {
    const icon = document.querySelector("#themeToggleBtn i");
    if (theme === "dark") {
        icon.className = "fa-solid fa-sun";
    } else {
        icon.className = "fa-solid fa-moon";
    }
}

/* ==========================================================================
   FORM WIZARD CONTROLLER
   ========================================================================== */
function setupWizard() {
    const startCalcBtn = document.getElementById("startCalcBtn");
    const backToHomeBtn = document.getElementById("backToHomeBtn");
    const prevStepBtn = document.getElementById("prevStepBtn");
    const nextStepBtn = document.getElementById("nextStepBtn");
    const calculateTaxBtn = document.getElementById("calculateTaxBtn");
    const sidebarSteps = document.querySelectorAll(".step-item");
    
    // Start button
    startCalcBtn.addEventListener("click", () => {
        document.getElementById("landingSection").classList.add("hidden");
        document.getElementById("calculatorSection").classList.remove("hidden");
        showStep(1);
    });
    
    // Back to home
    backToHomeBtn.addEventListener("click", () => {
        document.getElementById("calculatorSection").classList.add("hidden");
        document.getElementById("landingSection").classList.remove("hidden");
    });
    
    // Next step
    nextStepBtn.addEventListener("click", () => {
        if (validateStep(currentStep)) {
            // Auto copy employee PF to 80C PF on Step 2 transition
            if (currentStep === 2) {
                syncPFTo80C();
            }
            if (currentStep < totalSteps) {
                markStepCompleted(currentStep);
                currentStep++;
                showStep(currentStep);
            }
        }
    });
    
    // Prev step
    prevStepBtn.addEventListener("click", () => {
        if (currentStep > 1) {
            currentStep--;
            showStep(currentStep);
        }
    });
    
    // Sidebar step clicking (only to already completed or previous steps)
    sidebarSteps.forEach(item => {
        item.addEventListener("click", () => {
            const stepNum = parseInt(item.getAttribute("data-step"));
            if (stepNum < currentStep) {
                currentStep = stepNum;
                showStep(currentStep);
            } else if (stepNum > currentStep && validateStep(currentStep)) {
                // Allow jumping forward only if current step validates
                let isValid = true;
                for (let i = currentStep; i < stepNum; i++) {
                    if (!validateStep(i)) {
                        isValid = false;
                        currentStep = i;
                        showStep(currentStep);
                        break;
                    }
                    markStepCompleted(i);
                }
                if (isValid) {
                    currentStep = stepNum;
                    showStep(currentStep);
                }
            }
        });
    });
}

function showStep(step) {
    currentStep = step;
    
    // Toggle active form step panels
    document.querySelectorAll(".form-step-content").forEach(panel => {
        panel.classList.add("hidden");
        panel.classList.remove("active");
    });
    
    const activePanel = document.querySelector(`.form-step-content[data-step="${step}"]`);
    activePanel.classList.remove("hidden");
    activePanel.classList.add("active");
    
    // Toggle active sidebar labels
    document.querySelectorAll(".step-item").forEach(item => {
        item.classList.remove("active");
    });
    document.querySelector(`.step-item[data-step="${step}"]`).classList.add("active");
    
    // Update progress bar percentage
    const fillPercent = (step / totalSteps) * 100;
    document.getElementById("progressBarFill").style.width = `${fillPercent}%`;
    
    // Button visibility logic
    const prevStepBtn = document.getElementById("prevStepBtn");
    const nextStepBtn = document.getElementById("nextStepBtn");
    const calculateTaxBtn = document.getElementById("calculateTaxBtn");
    
    if (step === 1) {
        prevStepBtn.classList.add("hidden");
    } else {
        prevStepBtn.classList.remove("hidden");
    }
    
    if (step === totalSteps) {
        nextStepBtn.classList.add("hidden");
        calculateTaxBtn.classList.remove("hidden");
    } else {
        nextStepBtn.classList.remove("hidden");
        calculateTaxBtn.classList.add("hidden");
    }
    
    // Scroll wizard header into view
    document.querySelector(".wizard-header").scrollIntoView({ behavior: 'smooth' });
}

function markStepCompleted(step) {
    document.querySelector(`.step-item[data-step="${step}"]`).classList.add("completed");
}

function validateStep(step) {
    const activePanel = document.querySelector(`.form-step-content[data-step="${step}"]`);
    const inputs = activePanel.querySelectorAll("input[required], select[required]");
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            showInputError(input, "This field is required.");
        } else if (input.type === "number") {
            const val = parseFloat(input.value);
            const min = parseFloat(input.getAttribute("min"));
            const max = parseFloat(input.getAttribute("max"));
            
            if (val < 0) {
                isValid = false;
                showInputError(input, "Value cannot be negative.");
            } else if (!isNaN(min) && val < min) {
                isValid = false;
                showInputError(input, `Minimum value is ${min}.`);
            } else if (!isNaN(max) && val > max) {
                isValid = false;
                showInputError(input, `Maximum value is ${max}.`);
            } else {
                clearInputError(input);
            }
        } else {
            clearInputError(input);
        }
    });
    
    return isValid;
}

function showInputError(input, message) {
    clearInputError(input);
    input.classList.add("input-error");
    const errorText = document.createElement("small");
    errorText.className = "error-message";
    errorText.style.color = "var(--accent-red)";
    errorText.style.fontSize = "0.75rem";
    errorText.style.marginTop = "0.25rem";
    errorText.innerText = message;
    input.parentNode.appendChild(errorText);
}

function clearInputError(input) {
    input.classList.remove("input-error");
    const existingError = input.parentNode.querySelector(".error-message");
    if (existingError) {
        existingError.remove();
    }
}

// Automatically mirror Employee PF to 80C PF
function syncPFTo80C() {
    const employeePFVal = document.getElementById("employee_pf").value;
    // Set in the 80C sections
    const defaultPFInput = document.getElementById("ppf"); // Just copy value, or we'll add a PF label in 80C. We'll handle it during collection!
}

/* ==========================================================================
   LIVE GROSS SALARY CALCULATOR
   ========================================================================== */
function setupLiveSalaryUpdates() {
    const salaryInputs = [
        'basic_salary', 'dearness_allowance', 'bonus', 'commission', 'special_allowance', 
        'other_taxable_allowances', 'employer_pf', 'gratuity', 'leave_encashment', 
        'pension_income', 'other_salary_income'
    ];
    
    salaryInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener("input", updateLiveGrossSalary);
        }
    });
}

function updateLiveGrossSalary() {
    const salaryInputs = [
        'basic_salary', 'dearness_allowance', 'bonus', 'commission', 'special_allowance', 
        'other_taxable_allowances', 'employer_pf', 'gratuity', 'leave_encashment', 
        'pension_income', 'other_salary_income'
    ];
    
    let gross = 0;
    salaryInputs.forEach(id => {
        const val = parseFloat(document.getElementById(id).value) || 0;
        gross += val;
    });
    
    document.getElementById("liveGrossSalary").innerText = gross.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/* ==========================================================================
   API COMPUTATION TRIGGER
   ========================================================================== */
function setupFormSubmission() {
    const form = document.getElementById("taxForm");
    const loadingOverlay = document.getElementById("loadingOverlay");
    
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        if (!validateStep(currentStep)) return;
        
        // Collect form data
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => {
            const numVal = parseFloat(value);
            if (!isNaN(numVal) && key !== 'name') {
                data[key] = numVal;
            } else if (key === 'is_parents_senior') {
                data[key] = true; // Checked
            } else {
                data[key] = value;
            }
        });
        
        // Handle checkbox explicitly
        data['is_parents_senior'] = document.getElementById("is_parents_senior").checked;
        
        // Show spinner
        loadingOverlay.classList.remove("hidden");
        
        try {
            const response = await fetch("/api/calculate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || "Tax computation failed. Check inputs.");
            }
            
            lastCalculationResult = result;
            displayResults(result);
            
        } catch (error) {
            showNotification(error.message);
        } finally {
            loadingOverlay.classList.add("hidden");
        }
    });
}

/* ==========================================================================
   RENDER COMPUTATION RESULTS
   ========================================================================== */
function displayResults(res) {
    document.getElementById("calculatorSection").classList.add("hidden");
    document.getElementById("resultsSection").classList.remove("hidden");
    
    const s = res.summary;
    const old_br = res.old_regime_breakdown;
    const new_br = res.new_regime_breakdown;
    
    // 1. Recommendation Banner
    const banner = document.getElementById("recommendationBanner");
    const title = document.getElementById("recommendationTitle");
    const desc = document.getElementById("recommendationDesc");
    const icon = document.querySelector(".recommendation-icon i");
    
    if (s.recommended_regime === "New Tax Regime") {
        banner.style.backgroundColor = "var(--accent-green-light)";
        banner.style.borderColor = "var(--accent-green)";
        title.style.color = "var(--accent-green)";
        icon.style.color = "var(--accent-green)";
        icon.className = "fa-solid fa-award";
        title.innerText = "Recommended: New Tax Regime";
    } else {
        banner.style.backgroundColor = "rgba(30, 58, 138, 0.08)";
        banner.style.borderColor = "var(--primary-navy)";
        title.style.color = "var(--primary-navy)";
        icon.style.color = "var(--primary-navy)";
        icon.className = "fa-solid fa-gem";
        title.innerText = "Recommended: Old Tax Regime";
    }
    desc.innerText = s.recommendation_details;
    
    // 2. Metrics Card Updates
    document.getElementById("metricGrossSalary").innerText = `Rs. ${s.gross_salary.toLocaleString('en-IN')}`;
    document.getElementById("metricOldTaxable").innerText = `Rs. ${s.old_taxable_income.toLocaleString('en-IN')}`;
    document.getElementById("metricNewTaxable").innerText = `Rs. ${s.new_taxable_income.toLocaleString('en-IN')}`;
    
    document.getElementById("metricOldTaxPayable").innerText = `Rs. ${s.old_tax_payable.toLocaleString('en-IN')}`;
    document.getElementById("metricNewTaxPayable").innerText = `Rs. ${s.new_tax_payable.toLocaleString('en-IN')}`;
    document.getElementById("metricTaxSaved").innerText = `Rs. ${s.tax_saved.toLocaleString('en-IN')}`;
    document.getElementById("metricPercentSaved").innerText = `${s.percentage_saved.toFixed(1)}% Tax Savings`;
    
    // 3. Render side-by-side table
    renderBreakdownTable(old_br, new_br);
    
    // 4. Render Charts
    renderCharts(res);
    
    // Scroll to dashboard top
    document.getElementById("resultsSection").scrollIntoView({ behavior: 'smooth' });
}

function renderBreakdownTable(old_br, new_br) {
    const tableBody = document.getElementById("breakdownTableBody");
    
    const rows = [
        { label: "Gross Salary (A)", oldVal: old_br.gross_salary, newVal: new_br.gross_salary, class: "total-row" },
        { label: "Less: HRA Exemption u/s 10(13A)", oldVal: old_br.hra_exemption, newVal: null, isDisallowed: true },
        { label: "Less: LTA Exemption u/s 10(5)", oldVal: old_br.lta_exemption, newVal: null, isDisallowed: true },
        { label: "Less: Exempt Reimbursements (official use)", oldVal: old_br.reimbursements_exemption, newVal: null, isDisallowed: true },
        { label: "Less: Standard Deduction u/s 16(ia)", oldVal: old_br.standard_deduction, newVal: new_br.standard_deduction },
        { label: "Less: Professional Tax u/s 16(iii)", oldVal: old_br.professional_tax, newVal: null, isDisallowed: true },
        { label: "Net Salary Income (B)", oldVal: old_br.net_salary, newVal: new_br.net_salary, class: "total-row" },
        { label: "Add: Income from House Property (C)", oldVal: old_br.house_property_income, newVal: new_br.house_property_income },
        { label: "Add: Income from Other Sources (D)", oldVal: old_br.other_sources_income, newVal: new_br.other_sources_income },
        { label: "Less: Section 80C Deductions (PPF, EPF, ELSS etc)", oldVal: old_br.deductions.sec_80c, newVal: null, isDisallowed: true },
        { label: "Less: Section 80CCD(1B) (NPS Additional)", oldVal: old_br.deductions.sec_80ccd_1b, newVal: null, isDisallowed: true },
        { label: "Less: Section 80D (Health Insurance)", oldVal: old_br.deductions.sec_80d, newVal: null, isDisallowed: true },
        { label: "Less: Interest Deductions (80TTA / 80TTB)", oldVal: old_br.deductions.interest_deduction, newVal: null, isDisallowed: true },
        { label: "Less: Employer NPS Contribution u/s 80CCD(2)", oldVal: old_br.deductions.sec_80ccd_2_employer, newVal: new_br.deductions.sec_80ccd_2_employer },
        { label: "Less: Other deductions (80E, 80G, 80U etc.)", oldVal: (old_br.deductions.sec_80e + old_br.deductions.sec_80g + old_br.deductions.sec_80ee + old_br.deductions.sec_80eea + old_br.deductions.sec_80u + old_br.deductions.sec_80dd), newVal: new_br.deductions.sec_80cch_agniveer },
        { label: "Total Eligible Deductions (E)", oldVal: old_br.deductions.total_deductions_eligible, newVal: new_br.deductions.total_deductions_eligible, class: "total-row" },
        { label: "Net Taxable Income (F = B+C+D-E)", oldVal: old_br.taxable_slab_income, newVal: new_br.taxable_slab_income, class: "total-row" },
        { label: "Capital Gains Income (G)", oldVal: (old_br.stcg_equity + old_br.ltcg_equity), newVal: (new_br.stcg_equity + new_br.ltcg_equity) },
        { label: "Slab Tax on progressive rates (H)", oldVal: old_br.slab_tax, newVal: new_br.slab_tax },
        { label: "Capital Gains Tax (I)", oldVal: (old_br.stcg_tax + old_br.ltcg_tax), newVal: (new_br.stcg_tax + new_br.ltcg_tax) },
        { label: "Total Tax before Rebate (J = H+I)", oldVal: old_br.tax_before_rebate, newVal: new_br.tax_before_rebate },
        { label: "Less: Tax Rebate u/s 87A (K)", oldVal: old_br.sec_87a_rebate, newVal: new_br.sec_87a_rebate },
        { label: "Less: Marginal Relief u/s 87A (L)", oldVal: 0, newVal: new_br.sec_87a_marginal_relief },
        { label: "Add: Surcharge (M)", oldVal: old_br.surcharge, newVal: new_br.surcharge },
        { label: "Add: Health & Education Cess @ 4% (N)", oldVal: old_br.cess, newVal: new_br.cess },
        { label: "Total Tax Payable (J - K - L + M + N)", oldVal: old_br.total_tax, newVal: new_br.total_tax, class: "total-row" }
    ];
    
    tableBody.innerHTML = "";
    
    rows.forEach(r => {
        const tr = document.createElement("tr");
        if (r.class) tr.className = r.class;
        if (r.isDisallowed) tr.className = "disallowed-row";
        
        const tdLabel = document.createElement("td");
        tdLabel.innerHTML = r.label;
        tr.appendChild(tdLabel);
        
        const tdOld = document.createElement("td");
        tdOld.innerText = r.oldVal !== null ? r.oldVal.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : "-";
        tr.appendChild(tdOld);
        
        const tdNew = document.createElement("td");
        if (r.newVal !== null) {
            tdNew.innerText = r.newVal.toLocaleString('en-IN', { minimumFractionDigits: 2 });
        } else if (r.isDisallowed) {
            tdNew.innerText = "Not Allowed";
        } else {
            tdNew.innerText = "-";
        }
        tr.appendChild(tdNew);
        
        tableBody.appendChild(tr);
    });
}

/* ==========================================================================
   CHARTS & VISUALIZATIONS GENERATOR
   ========================================================================== */
function renderCharts(res) {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const textColors = isDark ? "#94A3B8" : "#475569";
    const gridColors = isDark ? "rgba(75, 85, 99, 0.15)" : "rgba(226, 232, 240, 0.8)";
    
    // Destroy existing charts to prevent memory leak and visual bugs
    if (comparisonChart) comparisonChart.destroy();
    if (breakupChart) breakupChart.destroy();
    if (projectionChart) projectionChart.destroy();
    
    const old_br = res.old_regime_breakdown;
    const new_br = res.new_regime_breakdown;
    
    // ---------------- CHART 1: Bar Comparison ----------------
    const ctxComp = document.getElementById("taxComparisonChart").getContext("2d");
    comparisonChart = new Chart(ctxComp, {
        type: 'bar',
        data: {
            labels: ['Slab Tax', 'CG Tax', 'Surcharge', 'Cess', 'Total Tax'],
            datasets: [
                {
                    label: 'Old Tax Regime',
                    data: [
                        old_br.slab_tax, 
                        (old_br.stcg_tax + old_br.ltcg_tax), 
                        old_br.surcharge, 
                        old_br.cess, 
                        old_br.total_tax
                    ],
                    backgroundColor: '#1E3A8A',
                    borderRadius: 6
                },
                {
                    label: 'New Tax Regime',
                    data: [
                        new_br.slab_tax, 
                        (new_br.stcg_tax + new_br.ltcg_tax), 
                        new_br.surcharge, 
                        new_br.cess, 
                        new_br.total_tax
                    ],
                    backgroundColor: '#10B981',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: textColors, font: { family: 'Inter', weight: 600 } } }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: textColors } },
                y: { grid: { color: gridColors }, ticks: { color: textColors } }
            }
        }
    });
    
    // ---------------- CHART 2: Doughnut Deductions (Old Regime) ----------------
    const ctxBreakup = document.getElementById("deductionsBreakupChart").getContext("2d");
    
    // Extract deductions that are > 0 to display
    const dedLabelMap = [
        { label: 'HRA Exemption', val: old_br.hra_exemption },
        { label: 'Standard Ded', val: old_br.standard_deduction },
        { label: '80C PF/ELSS/PPF', val: old_br.deductions.sec_80c },
        { label: '80CCD(1B) NPS', val: old_br.deductions.sec_80ccd_1b },
        { label: '80D Medical', val: old_br.deductions.sec_80d },
        { label: 'Interest Ded', val: old_br.deductions.interest_deduction },
        { label: 'Employer NPS 80CCD(2)', val: old_br.deductions.sec_80ccd_2_employer },
        { label: 'Other Exemptions/Deds', val: (old_br.lta_exemption + old_br.reimbursements_exemption + old_br.deductions.sec_80e + old_br.deductions.sec_80g) }
    ];
    
    const activeDeds = dedLabelMap.filter(d => d.val > 0);
    
    breakupChart = new Chart(ctxBreakup, {
        type: 'doughnut',
        data: {
            labels: activeDeds.map(d => d.label),
            datasets: [{
                data: activeDeds.map(d => d.val),
                backgroundColor: [
                    '#1E3A8A', '#3B82F6', '#10B981', '#F59E0B', 
                    '#EF4444', '#8B5CF6', '#EC4899', '#6366F1'
                ],
                borderWidth: isDark ? 2 : 1,
                borderColor: isDark ? '#1F2937' : '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: 'right',
                    labels: { color: textColors, font: { family: 'Inter', size: 10 } } 
                }
            }
        }
    });
    
    // ---------------- CHART 3: Line Area Projection ----------------
    const ctxProj = document.getElementById("taxProjectionChart").getContext("2d");
    
    // Generate projection data points u/s user's parameters
    const projectionPoints = [
        300000, 500000, 750000, 1000000, 1200000, 1500000, 2000000, 2500000, 3000000
    ];
    
    const oldProjTaxes = [];
    const newProjTaxes = [];
    
    // Sum standard variables
    const deductionsTotalOld = old_br.deductions.total_deductions_eligible;
    const exemptionsTotalOld = old_br.hra_exemption + old_br.lta_exemption + old_br.reimbursements_exemption + old_br.professional_tax;
    const otherIncomeOld = old_br.house_property_income + old_br.other_sources_income;
    
    const deductionsTotalNew = new_br.deductions.total_deductions_eligible;
    const otherIncomeNew = new_br.house_property_income + new_br.other_sources_income;
    
    projectionPoints.forEach(gross => {
        // --- Simulate Old ---
        const slabIncomeOld = max(0, gross - exemptionsTotalOld - old_br.standard_deduction) + otherIncomeOld;
        const taxableOld = max(0, slabIncomeOld - deductionsTotalOld);
        const slabTaxOld = calculateClientSlabTax(taxableOld, getClientOldSlabs(res.personal_details.age));
        
        let rebateOld = 0;
        if (taxableOld <= 500000) rebateOld = min(slabTaxOld, 12500);
        
        const finalOld = (slabTaxOld - rebateOld) * 1.04;
        oldProjTaxes.push(max(0, finalOld));
        
        // --- Simulate New ---
        const slabIncomeNew = max(0, gross - 75000) + otherIncomeNew;
        const taxableNew = max(0, slabIncomeNew - deductionsTotalNew);
        const slabTaxNew = calculateClientSlabTax(taxableNew, NEW_SLABS);
        
        let rebateNew = 0;
        if (taxableNew <= 1200000) {
            rebateNew = min(slabTaxNew, 60000);
        } else {
            // Apply marginal relief simulation
            const excess = taxableNew - 1200000;
            if (slabTaxNew > excess) {
                // Slab tax reduces to excess
                const finalNewTax = excess * 1.04;
                newProjTaxes.push(max(0, finalNewTax));
                return;
            }
        }
        
        const finalNew = (slabTaxNew - rebateNew) * 1.04;
        newProjTaxes.push(max(0, finalNew));
    });
    
    projectionChart = new Chart(ctxProj, {
        type: 'line',
        data: {
            labels: projectionPoints.map(p => `Rs. ${(p/100000).toFixed(1)}L`),
            datasets: [
                {
                    label: 'Old Tax Regime',
                    data: oldProjTaxes,
                    borderColor: '#1E3A8A',
                    backgroundColor: 'rgba(30, 58, 138, 0.05)',
                    fill: true,
                    tension: 0.2
                },
                {
                    label: 'New Tax Regime',
                    data: newProjTaxes,
                    borderColor: '#10B981',
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    fill: true,
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: textColors, font: { family: 'Inter', weight: 600 } } }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: textColors } },
                y: { grid: { color: gridColors }, ticks: { color: textColors } }
            }
        }
    });
}

/* ==========================================================================
   OFFLINE CHART CALCULATIONS HELPERS
   ========================================================================== */
function max(a, b) { return a > b ? a : b; }
function min(a, b) { return a < b ? a : b; }

function getClientOldSlabs(age) {
    if (age >= 80) return OLD_SLABS_ABOVE_80;
    if (age >= 60) return OLD_SLABS_60_TO_80;
    return OLD_SLABS_UNDER_60;
}

function calculateClientSlabTax(income, slabs) {
    if (income <= 0) return 0;
    let tax = 0;
    let prevLimit = 0;
    for (let slab of slabs) {
        if (slab.limit === null) {
            tax += (income - prevLimit) * slab.rate;
            break;
        } else if (income > slab.limit) {
            tax += (slab.limit - prevLimit) * slab.rate;
            prevLimit = slab.limit;
        } else {
            tax += (income - prevLimit) * slab.rate;
            break;
        }
    }
    return tax;
}

/* ==========================================================================
   DASHBOARD ACTIONS CONTROLLER
   ========================================================================== */
function setupDashboardActions() {
    const recalculateBtn = document.getElementById("recalculateBtn");
    const downloadPdfBtn = document.getElementById("downloadPdfBtn");
    const printReportBtn = document.getElementById("printReportBtn");
    const loadingOverlay = document.getElementById("loadingOverlay");
    
    // Recalculate
    recalculateBtn.addEventListener("click", () => {
        document.getElementById("resultsSection").classList.add("hidden");
        document.getElementById("calculatorSection").classList.remove("hidden");
        showStep(1);
    });
    
    // Print window
    printReportBtn.addEventListener("click", () => {
        window.print();
    });
    
    // PDF Generation Download
    downloadPdfBtn.addEventListener("click", async () => {
        if (!lastCalculationResult) return;
        
        loadingOverlay.classList.remove("hidden");
        
        try {
            // Re-collect active form parameters
            const form = document.getElementById("taxForm");
            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => {
                const numVal = parseFloat(value);
                if (!isNaN(numVal) && key !== 'name') {
                    data[key] = numVal;
                } else {
                    data[key] = value;
                }
            });
            data['is_parents_senior'] = document.getElementById("is_parents_senior").checked;
            
            const response = await fetch("/api/download-pdf", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errResult = await response.json();
                throw new Error(errResult.error || "Failed to download PDF summary.");
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            // Create download anchor
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            const filenameName = lastCalculationResult.personal_details.name.replace(' ', '_') || "Taxpayer";
            a.download = `Tax_Summary_${filenameName}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            
        } catch (error) {
            showNotification(error.message);
        } finally {
            loadingOverlay.classList.add("hidden");
        }
    });
}

/* ==========================================================================
   TOAST NOTIFICATION MANAGER
   ========================================================================== */
function showNotification(message) {
    const toast = document.getElementById("notificationBanner");
    const msgSpan = document.getElementById("notificationMessage");
    const closeBtn = document.getElementById("closeNotificationBtn");
    
    msgSpan.innerText = message;
    toast.classList.remove("hidden");
    
    // Auto hide after 5 seconds
    const timer = setTimeout(() => {
        toast.classList.add("hidden");
    }, 5000);
    
    closeBtn.onclick = () => {
        clearTimeout(timer);
        toast.classList.add("hidden");
    };
}
