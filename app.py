from flask import Flask, request, jsonify
from flask_cors import CORS
from services.pdf_analyzer import analyzer
import os

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "AI Legal Assistant Online", "version": "3.0.0"})

# Endpoint Baru untuk Analisis Konten
@app.route('/analyze-content', methods=['POST'])
def analyze_content_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    
    try:
        file.seek(0) # Reset pointer
        result = analyzer.analyze_document_content(file)
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)