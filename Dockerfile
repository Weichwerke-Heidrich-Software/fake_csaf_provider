FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential libssl-dev libffi-dev python3-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ./fake_csaf_provider /app/fake_csaf_provider

EXPOSE 34443

CMD ["python","-m","fake_csaf_provider.main"]
