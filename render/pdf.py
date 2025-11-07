# compose/render/pdf.py
def render_pdf(nodes, config, output_path):
    with open(output_path, 'wb') as f:
        content = "BT\n/F1 12 Tf\n"
        y = 800
        for n in nodes:
            if n.type == 'heading':
                content += f"1 0 0 1 50 {y} Tm ({n.text}) Tj\n"
                y -= 30
            elif n.type == 'paragraph':
                content += f"1 0 0 1 60 {y} Tm ({n.text}) Tj\n"
                y -= 20
        content += "ET"
        pdf = f"""%PDF-1.1
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800]
/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length {len(content)} >> stream
{content}
endstream endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000115 00000 n 
0000000310 00000 n 
0000000500 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
600
%%EOF"""
        f.write(pdf.encode("utf-8"))
