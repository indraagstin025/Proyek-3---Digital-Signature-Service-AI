import fitz

class PDFAnalyzer:
    def __init__(self):
        self.DEFAULT_SIG_WIDTH = 120
        self.DEFAULT_SIG_HEIGHT = 60
        self.VERTICAL_OFFSET = 10

    def find_signature_locations(self, file_stream, keywoards):
        """
        Mencari koordinat area tanda tangan berdasarkan kata kunci.
        :param file_stream: File PDF (bytes)
        :param keywords: Contoh List kata kuncinya (contoh: ['Hormat Kami', 'Disetujui Oleh'])
        :return: List of dictionaries berisi koordinat
        """
        results = []

        try:
            doc = fitz.open(stream=file_stream.read(), filetype="pdf")
            for page_num, page in enumerate(doc):
                for keyword in keywoards:
                    text_instances = page.search_for(keyword)
                    for rect in text_instances:
                        sig_x = rect.x0
                        sig_y = rect.y0 - self.DEFAULT_SIG_HEIGHT - self.VERTICAL_OFFSET

                        if sig_y < 0:
                            sign_y = 0
                        found_item = {
                            "page_number": page_num + 1,
                            "keyword_found": keyword,
                            "coordinates": {
                                "x": float(sig_x),
                                "y": float(sig_y),
                                "width": self.DEFAULT_SIG_WIDTH,
                                "height": self.DEFAULT_SIG_HEIGHT,
                            },
                            "context_text_rect": {
                                "x": float(rect.x0),
                                "y": float(rect.y0),
                                "w": float(rect.width),
                                "h": float(rect.height),
                            },
                        }
                        results.append(found_item)
            doc.close()
            return results
        except Exception as e:
            print(f"Error analyzing PDF: {e}")
            return []

analyzer = PDFAnalyzer()
