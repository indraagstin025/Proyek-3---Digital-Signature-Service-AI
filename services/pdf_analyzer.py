import fitz  # PyMuPDF
import google.generativeai as genai
import json
import os
import time
import re
from dotenv import load_dotenv
from pathlib import Path

# Load Environment Variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY tidak ditemukan.")

genai.configure(api_key=api_key)

class PDFAnalyzer:
    def __init__(self):
        # Gunakan model Flash Lite agar cepat
        self.model_name = "models/gemini-flash-lite-latest"
        
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception:
            print(f"⚠️ Fallback model ke 2.0-flash-lite...")
            self.model = genai.GenerativeModel("models/gemini-2.0-flash-lite")

    def _clean_text(self, text):
        """Membersihkan noise dari teks PDF"""
        clean = re.sub(r'\\', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def analyze_document_content(self, file_stream, doc_type="General"):
        print(f"🔍 [AI] Menerima request analisis. Hint awal: '{doc_type}'")

        try:
            # 1. Baca File PDF
            doc = fitz.open(stream=file_stream.read(), filetype="pdf")
            raw_text = ""
            # Baca lebih banyak halaman agar konteks lebih dapat (misal 15 halaman)
            for i in range(min(15, len(doc))):
                raw_text += doc[i].get_text()
            doc.close()

            # 2. BERSIHKAN TEKS
            full_text = self._clean_text(raw_text)

            if len(full_text) < 50:
                return {"error": "Dokumen kosong/tidak terbaca.", "document_type": "Unknown"}

            # ==================================================================
            # PERUBAHAN UTAMA: Hapus Logika Manual (If-Else)
            # Kita serahkan klasifikasi sepenuhnya ke Prompt AI agar lebih cerdas.
            # ==================================================================

            # 3. MEMBUAT PROMPT CERDAS
            # Kita minta AI melakukan 2 hal: KLASIFIKASI & EKSTRAKSI
            
            prompt = f"""
            Anda adalah Senior Legal Auditor AI. Tugas Anda ada dua:
            1. KLASIFIKASIKAN jenis dokumen ini secara spesifik.
            2. EKSTRAK poin-poin pentingnya.

            TEKS DOKUMEN:
            {full_text[:20000]}

            ---------------------------------------------------------
            DAFTAR KATEGORI DOKUMEN (Pilih satu yang paling cocok):
            - "Memorandum of Understanding (MoU)"
            - "Perjanjian Kerjasama (PKS)"
            - "Non-Disclosure Agreement (NDA)"
            - "Kontrak Kerja Karyawan"
            - "Surat Keputusan (SK)"
            - "Surat Kuasa"
            - "Perjanjian Sewa Menyewa"
            - "Berita Acara"
            - "Invoice / Tagihan"
            - "Dokumen Umum" (Jika tidak masuk kategori di atas)
            ---------------------------------------------------------

            INSTRUKSI JSON OUTPUT (Wajib JSON murni):
            {{
                "document_type": "TULIS_KATEGORI_HASIL_ANALISIS_DISINI",
                "summary": "Ringkasan profesional 2-3 kalimat mengenai isi dokumen.",
                "key_entities": ["Nama Pihak 1", "Nama Pihak 2", "Tanggal Surat", "Nomor Surat"],
                "critical_points": [
                    "Sebutkan Nilai Uang (Rp/USD) jika ada",
                    "Sebutkan Durasi/Tenggat Waktu jika ada",
                    "Kewajiban Utama Para Pihak",
                    "Sanksi atau Denda"
                ],
                "risk_analysis": "Analisis risiko hukum singkat (Rendah/Sedang/Tinggi) beserta alasannya."
            }}
            """

            # 4. KIRIM KE AI
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
                    if "429" in str(e) or "Quota" in str(e):
                        time.sleep(5)
                        continue
                    raise e 

            # 5. PARSING HASIL
            if not response:
                return {"error": "AI tidak merespons.", "document_type": doc_type}

            text_resp = response.text.replace("```json", "").replace("```", "").strip()
            
            # Bersihkan JSON string
            start_idx = text_resp.find("{")
            end_idx = text_resp.rfind("}") + 1
            if start_idx != -1 and end_idx != -1:
                text_resp = text_resp[start_idx:end_idx]

            try:
                # Parse ke Python Dict
                result_json = json.loads(text_resp)
                
                # [LOG DEBUG]
                detected_type = result_json.get("document_type", "General")
                print(f"✨ [AI] Klasifikasi Selesai: Terdeteksi sebagai '{detected_type}'")

                # Pastikan key 'document_type' ada (jika AI lupa, pakai default/hint)
                if not result_json.get("document_type"):
                     result_json["document_type"] = doc_type

                return result_json

            except json.JSONDecodeError:
                return {
                    "summary": "Gagal parsing hasil AI, namun teks terbaca.", 
                    "document_type": doc_type, # Fallback ke hint awal
                    "risk_analysis": "Tidak dapat dianalisis otomatis."
                }

        except Exception as e:
            print(f"❌ Error Analysis: {e}")
            return {"error": str(e), "document_type": doc_type}

analyzer = PDFAnalyzer()