import http.server
import socketserver
import os
 
# Configuration
PORT = 8000
PDF_PATH = "pdfs/hello.pdf"  # Update this path!
 
class PDFRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Only handle requests for the PDF (e.g., /sample.pdf)
        if self.path == "/sample.pdf":
            self.serve_pdf()
        else:
            # Send 404 for other paths
            self.send_error(404, "File Not Found")
 
    def serve_pdf(self):
        try:
            # Open the PDF in binary read mode
            with open(PDF_PATH, "rb") as f:
                pdf_content = f.read()
                file_size = os.path.getsize(PDF_PATH)
 
            # Send 200 OK response
            self.send_response(200)
            # Set critical headers
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header("Content-Type", "application/pdf")
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        # Allow headers that the Adobe SDK or browser might send
            self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-type, Accept')
            self.send_header("Content-Length", str(file_size))
            self.end_headers()  # Signal end of headers
 
            # Send the PDF content
            self.wfile.write(pdf_content)
 
        except FileNotFoundError:
            self.send_error(404, "PDF File Not Found")
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")
 
# Start the server
with socketserver.TCPServer(("", PORT), PDFRequestHandler) as httpd:
    print(f"Serving PDF at http://localhost:{PORT}/sample.pdf")
    httpd.serve_forever()