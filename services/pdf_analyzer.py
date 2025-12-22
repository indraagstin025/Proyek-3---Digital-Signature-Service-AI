import fitz  # PyMuPDF
import google.generativeai as genai
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
    genai.configure(api_key=api_key)

class PDFAnalyzer:
    def __init__(self):
        # [UPDATE] Menggunakan model terbaru dari daftar yang tersedia (Dec 2025)
        # Kita pilih 'gemini-3-flash-preview' untuk performa cepat & cerdas.
        self.model_name = "models/gemini-3-flash-preview"
        
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        try:
            print(f"🔌 Menghubungkan ke model: {self.model_name}...")
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            print(f"⚠️ Gagal inisialisasi model utama: {e}")
            # Fallback jika model 3 error, coba versi 2.5 lite
            print(f"⚠️ Mencoba fallback ke models/gemini-2.5-flash-lite-preview-09-2025...")
            self.model = genai.GenerativeModel("models/gemini-2.5-flash-lite-preview-09-2025")

    def _clean_text(self, text):
        """Membersihkan noise dari teks PDF"""
        clean = re.sub(r'\\', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def analyze_document_content(self, file_stream, doc_type="General"):
        print(f"🔍 [AI] Menerima request analisis. Context: '{doc_type}'")

        try:
            # Reset pointer stream
            file_stream.seek(0)
            pdf_bytes = file_stream.read()

            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            raw_text = ""
            # Baca max 20 halaman
            for i in range(min(20, len(doc))):
                raw_text += doc[i].get_text()
            doc.close()

            full_text = self._clean_text(raw_text)

            if len(full_text) < 50:
                return {
                    "status": "fail", 
                    "error": "Dokumen kosong/tidak terbaca.", 
                    "document_type": "Unknown"
                }

            prompt = f"""
            Anda adalah Senior Legal Auditor AI.
            Tugas:
            1. KLASIFIKASIKAN jenis dokumen ini (Pilih dari daftar).
            2. EKSTRAK poin penting.

            TEKS DOKUMEN:
            {full_text[:25000]} 

            DAFTAR KATEGORI:
            - Memorandum of Understanding (MoU)
            - Perjanjian Kerjasama (PKS)
            - Non-Disclosure Agreement (NDA)
            - Kontrak Kerja
            - Surat Keputusan (SK)
            - Invoice
            - Dokumen Umum

            HINT: {doc_type}

            OUTPUT HARUS JSON MURNI:
            {{
                "document_type": "KATEGORI_YANG_DIPILIH",
                "summary": "Ringkasan 2 paragraf.",
                "key_entities": ["Pihak A", "Pihak B", "Nomor Surat"],
                "critical_points": ["Poin 1", "Poin 2"],
                "risk_analysis": "Analisis risiko (Rendah/Sedang/Tinggi)."
            }}
            """

            max_retries = 3
            response = None
            
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        prompt, 
                        safety_settings=self.safety_settings
                    )
                    break 
                except Exception as e:
                    print(f"⚠️ Retry AI {attempt+1}/{max_retries}: {e}")
                    time.sleep(2)

            if not response:
                return {"error": "AI Timeout/No Response", "document_type": doc_type}

            text_resp = response.text.replace("```json", "").replace("```", "").strip()
            
            start = text_resp.find("{")
            end = text_resp.rfind("}") + 1
            if start != -1 and end != -1:
                text_resp = text_resp[start:end]

            result_json = json.loads(text_resp)
            
            if not result_json.get("document_type"):
                result_json["document_type"] = doc_type

            print(f"✨ [AI] Sukses. Tipe: {result_json.get('document_type')}")
            return result_json

        except Exception as e:
            print(f"❌ Error Analysis: {e}")
            return {"error": str(e), "document_type": doc_type}

analyzer = PDFAnalyzer()