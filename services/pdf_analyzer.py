import fitz
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
from pathlib import Path


env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY tidak ditemukan.")

genai.configure(api_key=api_key)


class PDFAnalyzer:
    def __init__(self):

        try:
            self.model = genai.GenerativeModel("gemini-2.0-flash")
        except:
            self.model = genai.GenerativeModel("gemini-flash-latest")

    def analyze_document_content(self, file_stream):
        print(f"🔍 [AI LEGAL] Membaca & Menganalisis Dokumen (Bahasa Indonesia)...")

        try:
            doc = fitz.open(stream=file_stream.read(), filetype="pdf")
            full_text = ""

            page_limit = min(5, len(doc))
            for i in range(page_limit):
                full_text += doc[i].get_text()

            doc.close()

            if len(full_text) < 50:
                return {"error": "Dokumen terlalu pendek atau tidak terbaca."}

            prompt = f"""
            Bertindaklah sebagai Asisten Legal/Hukum AI yang ahli. Analisis teks dokumen berikut ini.
            
            TEKS DOKUMEN:
            {full_text[:8000]} ... (terpotong)

            TUGAS:
            Berikan analisis terstruktur dalam format JSON saja. Gunakan Bahasa Indonesia yang formal dan profesional.
            
            FORMAT JSON:
            {{
                "summary": "Ringkasan dokumen dalam 2-3 kalimat yang padat dan jelas.",
                "document_type": "Jenis Dokumen (Misal: Perjanjian Kerja, Surat Kuasa, Invoice, dsb)",
                "parties": ["Nama Pihak Pertama", "Nama Pihak Kedua", ...],
                "risk_level": "Tingkat Risiko (Pilih satu: 'Tinggi', 'Sedang', atau 'Rendah')",
                "key_points": [
                    "Poin penting 1 (Kewajiban/Denda/Tanggal)",
                    "Poin penting 2",
                    "Poin penting 3"
                ]
            }}
            
            PENTING:
            - Output WAJIB JSON valid. Jangan gunakan markdown block.
            - risk_level harus salah satu dari: "Tinggi", "Sedang", "Rendah".
            - Jika dokumen berbahasa Inggris, TERJEMAHKAN analisisnya ke Bahasa Indonesia.
            """

            response = self.model.generate_content(prompt)

            text_resp = response.text.replace("```json", "").replace("```", "").strip()

            return json.loads(text_resp)

        except Exception as e:
            print(f"❌ Error Analysis: {e}")
            return {"error": f"Gagal menganalisis: {str(e)}"}


analyzer = PDFAnalyzer()
