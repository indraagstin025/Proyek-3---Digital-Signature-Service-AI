from google import genai
import os
from dotenv import load_dotenv
from pathlib import Path

def test_api_key_v2():
    print("="*60)
    print("🕵️  DIAGNOSTIK PATH & KEY (VERSI 2)")
    print("="*60)

    # 1. TENTUKAN LOKASI SCRIPT INI BERADA
    base_dir = Path(__file__).resolve().parent
    print(f"📂 Script berjalan di folder:\n   {base_dir}")

    # 2. CARI .ENV SECARA MANUAL DI BEBERAPA KEMUNGKINAN
    possible_paths = [
        base_dir / ".env",              # Di folder yang sama
        base_dir.parent / ".env",       # Di satu folder luarnya
        base_dir.parent.parent / ".env" # Di dua folder luarnya
    ]

    target_env = None
    
    print("\n🔍 Mencari file .env...")
    for path in possible_paths:
        if path.exists():
            print(f"   ✅ DITEMUKAN di: {path}")
            target_env = path
            break
        else:
            print(f"   ❌ Tidak ada di: {path}")

    # 3. LOAD ENV JIKA KETEMU
    if target_env:
        load_dotenv(dotenv_path=target_env)
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if api_key:
            masked = f"{api_key[:6]}......{api_key[-4:]}"
            print(f"\n🔑 Key berhasil dibaca: {masked}")
            
            # Tes koneksi singkat
            try:
                genai.configure(api_key=api_key)
                m = genai.GenerativeModel('gemini-1.5-flash')
                print("📡 Tes Koneksi ke Google...")
                response = m.generate_content("Hi")
                print("✅ KONEKSI SUKSES! API Key valid.")
            except Exception as e:
                print(f"❌ Key terbaca tapi Error: {e}")
        else:
            print("\n⚠️ File .env ketemu, tapi isinya KOSONG atau format salah.")
            print("   Pastikan isinya: GOOGLE_API_KEY=AIzaSy...")
    else:
        print("\n🚫 FATAL: File .env benar-benar tidak ditemukan di folder manapun.")
        print("   Coba cek apakah nama filenya '.env.txt'?")
        
        # DEBUG: List semua file di folder ini untuk melihat nama asli
        print("\nDaftar file di folder ini:")
        for f in os.listdir(base_dir):
            print(f" - {f}")

if __name__ == "__main__":
    test_api_key_v2()