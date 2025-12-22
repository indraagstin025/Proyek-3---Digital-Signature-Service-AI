from flask import Flask, request, jsonify
from flask_cors import CORS
from services.pdf_analyzer import analyzer
import os
import requests  # Wajib install: pip install requests
import io        # Bawaan python

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "AI Legal Assistant Online", "version": "3.2.0 (URL Support)"})

# Pastikan route ini sama dengan yang dipanggil di Node.js (aiService.js)
@app.route('/analyze-content', methods=['POST'])
def analyze_content_route():
    try:
        # 1. Cek apakah Request berbentuk JSON (Metode Baru)
        if request.is_json:
            data = request.get_json()
            
            # Ambil URL dan Tipe
            file_url = data.get('file_url')
            doc_type = data.get('document_type', 'General')
            
            if not file_url:
                return jsonify({"error": "Parameter 'file_url' wajib ada."}), 400
            
            print(f"📥 https://en.wikipedia.org/wiki/Mode_%28statistics%29 Mendownload file dari: {file_url}")
            
            # 2. Download File dari URL (Supabase/S3)
            # Python server yang melakukan download, bukan dikirim mentah dari Node.js
            download_resp = requests.get(file_url, timeout=30)
            
            if download_resp.status_code != 200:
                return jsonify({"error": f"Gagal mendownload file dari URL. Status: {download_resp.status_code}"}), 400
                
            # 3. Ubah bytes hasil download menjadi File Object (agar kompatibel dengan analyzer lama)
            file_stream = io.BytesIO(download_resp.content)
            
        # 4. Fallback: Cek jika masih ada yang upload File Fisik (Metode Lama/Direct Upload)
        elif 'file' in request.files:
            print("📥 [FILE MODE] Menerima file fisik langsung.")
            file_stream = request.files['file']
            doc_type = request.form.get('document_type', 'General')
            file_stream.seek(0)
            
        else:
            return jsonify({"error": "Harap kirim JSON {'file_url': ...} atau Upload File Form-Data"}), 400

        print(f"🤖 Menganalisis dokumen tipe: {doc_type}...")

        # 5. Kirim ke Analyzer
        # Analyzer tidak perlu diubah, karena dia menerima 'file-like object'
        # Baik itu dari request.files atau io.BytesIO, cara bacanya sama.
        result = analyzer.analyze_document_content(file_stream, doc_type)
        
        return jsonify({"status": "success", "data": result})
        
    except Exception as e:
        print(f"❌ Error Route: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)