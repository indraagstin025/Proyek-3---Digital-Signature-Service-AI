from flask import Flask, request, jsonify
from flask_cors import CORS
from services.pdf_analyzer import analyzer
import os

app = Flask(__name__)
CORS(app) 

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "AI Service Online", 
        "version": "1.0.0",
        "backend": "PyMuPDF (Fitz)"
    })

@app.route('/analyze-layout', methods=['POST'])
def analyze_pdf():
    
    if 'file' not in request.files:
        return jsonify({"error": "No PDF file uploaded"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    default_keywords = ["Tanda Tangan", "Signature", "Hormat Kami", "Disetujui Oleh", "Approved By"]
    client_keywords = request.form.getlist('keywords')
    keywords_to_search = client_keywords if client_keywords else default_keywords

    try:
        file.seek(0)
        locations = analyzer.find_signature_locations(file, keywords_to_search)
        return jsonify({
            "status": "success",
            "filename": file.filename,
            "total_matches": len(locations),
            "locations": locations
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)