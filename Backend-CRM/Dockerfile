FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for WeasyPrint and LibreOffice
# Note: WeasyPrint requires these system libraries (cannot be installed via pip/requirements.txt)
# requirements.txt handles Python packages, Dockerfile handles system libraries
# LibreOffice is required for DOCX to PDF conversion
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libglib2.0-0 \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Verify LibreOffice installation
RUN soffice --version || (echo "LibreOffice installation failed" && exit 1)

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
