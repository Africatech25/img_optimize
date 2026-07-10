#!/usr/bin/env python3
"""Create a test PDF file for testing PDF repair functionality"""
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from io import BytesIO
import os

# Créer un PDF simple avec reportlab
packet = BytesIO()
can = canvas.Canvas(packet)
can.drawString(50, 700, "Test PDF Document - Curriculum Vitae")
can.save()

# Lire le PDF créé
packet.seek(0)
pdf = PdfReader(packet)

# Créer un writer et ajouter la page
writer = PdfWriter()
writer.add_page(pdf.pages[0])
writer.add_metadata({
    '/Title': 'Test CV Document',
    '/Author': 'Test User',
    '/Subject': 'Curriculum Vitae'
})

# Sauvegarder
with open('test.pdf', 'wb') as output:
    writer.write(output)

print("✓ Test PDF created: test.pdf")
