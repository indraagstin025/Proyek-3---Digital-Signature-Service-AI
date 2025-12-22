from flask import Flask, request, jsonify
from flask_cors import CORS
from services.pdf_analyzer import analyzer
import os

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "AI Legal Assistant Online", "version": "3.1.0"})

@app.route('/analyze-content', methods=['POST'])
def analyze_content_route():
    # 1. Cek File
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    # 2. [UPDATE PENTING] Ambil parameter 'document_type' dari form-data
    # Jika tidak ada dikirim (saat upload pertama), default-nya 'General' (untuk Auto-Labeling)
    doc_type = request.form.get('document_type', 'General')
    
    print(f"📥 Menerima Request Analisis. Tipe: {doc_type} | File: {file.filename}")

    try:
        file.seek(0) # Reset pointer file agar terbaca dari awal
        
        # 3. Kirim file + tipe dokumen ke Analyzer
        result = analyzer.analyze_document_content(file, doc_type)
        
        return jsonify({"status": "success", "data": result})
        
    except Exception as e:
        print(f"❌ Error Route: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)