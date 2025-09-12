FROM php:8.2-cli

# Herramientas para compilar extensiones PECL
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc make autoconf pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Instalar IBM MQ Client desde los .deb locales
COPY Client/ibmmq-runtime_9.3.0.0_amd64.deb Client/ibmmq-client_9.3.0.0_amd64.deb Client/ibmmq-gskit_9.3.0.0_amd64.deb Client/ibmmq-sdk_9.3.0.0_amd64.deb /tmp/
RUN apt-get update \
    && apt-get install -y /tmp/ibmmq-runtime_9.3.0.0_amd64.deb \
                          /tmp/ibmmq-gskit_9.3.0.0_amd64.deb \
                          /tmp/ibmmq-client_9.3.0.0_amd64.deb \
                          /tmp/ibmmq-sdk_9.3.0.0_amd64.deb \
    && rm -rf /var/lib/apt/lists/* /tmp/*.deb

ENV LD_LIBRARY_PATH=/opt/mqm/lib64:/opt/mqm/lib

# Instalar y habilitar extensión mqseries (requiere red durante build)
RUN pecl install mqseries \
    && docker-php-ext-enable mqseries

WORKDIR /app
COPY mq_consumer.php /app/

CMD ["php", "mq_consumer.php"]

