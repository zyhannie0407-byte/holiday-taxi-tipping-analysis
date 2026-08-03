FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/java && \
    ln -s "$(dirname "$(dirname "$(readlink -f "$(which java)")")")" /opt/java/openjdk

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "holiday_tipping_dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]