import os
import tempfile
from flask import Flask, request, jsonify, send_file
from src.tax_engine import run_calculation
from src.pdf_generator import generate_tax_report_pdf

app = Flask(__name__, static_folder='public', static_url_path='')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json or {}
        if not data:
            return jsonify({"error": "No input data provided"}), 400
            
        # Basic validation: ensure age is valid if provided
        age_str = data.get('age', 30)
        try:
            age = int(age_str)
            if age <= 0 or age > 120:
                return jsonify({"error": "Please enter a valid age between 1 and 120."}), 400
        except ValueError:
            return jsonify({"error": "Age must be an integer number."}), 400
            
        # Basic validation: check negative salary inputs
        salary_fields = [
            'basic_salary', 'dearness_allowance', 'bonus', 'commission', 'special_allowance', 
            'other_taxable_allowances', 'employer_pf', 'employee_pf', 'gratuity', 
            'leave_encashment', 'pension_income', 'other_salary_income'
        ]
        for field in salary_fields:
            if field in data:
                try:
                    val = float(data[field])
                    if val < 0:
                        return jsonify({"error": f"Value for {field.replace('_', ' ').title()} cannot be negative."}), 400
                except ValueError:
                     return jsonify({"error": f"Value for {field.replace('_', ' ').title()} must be a valid number."}), 400

        result = run_calculation(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download-pdf', methods=['POST'])
def download_pdf():
    try:
        data = request.json or {}
        if not data:
            return jsonify({"error": "No input data provided"}), 400
            
        result = run_calculation(data)
        
        # Ensure temporary directory is inside the workspace
        workspace_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(workspace_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        fd, temp_file_path = tempfile.mkstemp(suffix='.pdf', dir=temp_dir)
        os.close(fd) # Close file descriptor so ReportLab can open and write to it safely
        
        try:
            generate_tax_report_pdf(result, temp_file_path)
            
            # Send file and then delete it
            filename_name = result['personal_details']['name'].replace(' ', '_')
            if not filename_name:
                filename_name = "Taxpayer"
                
            response = send_file(
                temp_file_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"Tax_Summary_{filename_name}.pdf"
            )
            
            # Register a cleanup callback after sending
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                except Exception as e:
                    app.logger.error(f"Error cleaning up temp file: {e}")
                    
            return response
            
        except Exception as e:
            # Clean up if failed during generation
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise e
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("--------------------------------------------------")
    print("India Salary Tax Planner Backend Starting...")
    print("Server running on http://127.0.0.1:5000")
    print("--------------------------------------------------")
    app.run(debug=True, host='127.0.0.1', port=5000)
