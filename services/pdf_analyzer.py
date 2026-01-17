import fitz  # PyMuPDF
from google import genai
from google.genai import types
import json
import os
import time
import re
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("⚠️ PERINGATAN: GOOGLE_API_KEY belum diset.")

if api_key:
    # Client initialized later in class
    pass

class PDFAnalyzer:
    def __init__(self):
        # [UPDATED] Menggunakan model pilihan user
        self.model_name = "gemini-2.5-flash" 
        
        # Inisialisasi Client
        try:
            print(f"🔌 Menghubungkan ke model: {self.model_name}...")
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            print(f"⚠️ Gagal inisialisasi client: {e}")
            self.client = None

    def _clean_text(self, text):
        """Membersihkan noise dari teks PDF"""
        clean = re.sub(r'\\', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean


    def analyze_document_content(self, file_stream, user_doc_type="General"):
        print(f"🔍 [AI] Request Analisis Cerdas. Konteks User: '{user_doc_type}'")

        try:
            # 1. Baca File PDF
            file_stream.seek(0)
            pdf_bytes = file_stream.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            raw_text = ""
            for i in range(min(20, len(doc))): # Baca max 20 halaman cukup
                raw_text += doc[i].get_text()
            doc.close()

            full_text = self._clean_text(raw_text)

            if len(full_text) < 50:
                return {"status": "fail", "error": "Dokumen kosong atau tidak terbaca."}

            # 2. PROMPT BARU (ANTI-MARKDOWN & RINGKAS)
            prompt = f"""
            Anda adalah Legal Auditor.
            Tugas: Analisis dokumen berlabel "{user_doc_type}".
            
            INSTRUKSI KHUSUS:
            1. JANGAN gunakan format Markdown (seperti bintang **, pagar #, atau bullet point). Gunakan teks biasa paragraf pendek.
            2. Buat SINGKAT dan PADAT. Maksimal 3 kalimat per poin.
            3. Fokus pada risiko utama saja.

            TEKS DOKUMEN:
            {full_text[:20000]} 

            OUTPUT JSON MURNI:
            {{
                "summary": "Ringkasan dokumen dalam 2 kalimat saja.",
                "key_entities": ["Nama 1", "Nama 2", "Tanggal"],
                "critical_points": ["Poin penting 1", "Poin penting 2"],
                "risk_analysis": "Jelaskan risiko hukum utama secara singkat tanpa format bold/italic."
            }}
            """

            # 3. Eksekusi Request
            max_retries = 3
            response = None
            
            # Konfigurasi Safety Settings
            # Note: google-genai uses types.SafetySetting
            # But defaults are usually fine. If blocked, we can add them back.
            
            for attempt in range(max_retries):
                try:
                    if not self.client:
                        raise Exception("Client AI belum terinisialisasi.")
                        
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt
                    )
                    break 
                except Exception as e:
                    print(f"⚠️ Retrying AI request... ({attempt+1}/{max_retries}) Error: {e}")
                    time.sleep(2)

            if not response:
                return {"error": "Gagal terhubung ke AI."}

            # 4. Parsing JSON
            text_resp = response.text.replace("```json", "").replace("```", "").strip()
            
            start = text_resp.find("{")
            end = text_resp.rfind("}") + 1
            if start != -1 and end != -1:
                text_resp = text_resp[start:end]

            result_json = json.loads(text_resp)
            
            # Hapus document_type agar frontend pakai data DB
            if "document_type" in result_json:
                del result_json["document_type"]
            
            print(f"✨ [AI] Sukses. Ringkasan: {result_json.get('summary')[:30]}...")
            return result_json

        except Exception as e:
            print(f"❌ Error Analysis: {e}")
            return {"error": f"Internal Error: {str(e)}"}

analyzer = PDFAnalyzer()