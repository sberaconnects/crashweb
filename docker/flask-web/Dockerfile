FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron curl ca-certificates xz-utils locales file \
    && sed -i 's/# en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen && locale-gen \
    && rm -rf /var/lib/apt/lists/*

ENV LC_ALL=en_US.UTF-8

COPY web/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY web/ /app/
COPY docker/shared/bt_utils.py /app/
COPY docker/flask-web/auto-install-sdk.sh /usr/local/bin/auto-install-sdk.sh
COPY docker/flask-web/docker-entrypoint-flask.sh /usr/local/bin/docker-entrypoint-flask.sh
RUN chmod +x /usr/local/bin/auto-install-sdk.sh /usr/local/bin/docker-entrypoint-flask.sh

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/docker-entrypoint-flask.sh"]
