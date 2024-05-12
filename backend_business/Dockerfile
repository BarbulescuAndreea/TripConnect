FROM python:3.11.3-slim-buster

WORKDIR /usr/src/idp

ENV LIBRARY_PATH="${LIBRARY_PATH}:/usr/local/opt/openssl/lib/"
ENV C_INCLUDE_PATH="${C_INCLUDE_PATH}:/usr/local/opt/openssl/include/"

RUN apt-get update && \
    apt-get install -y netcat openssl libpq-dev gcc && \
    apt-get clean

RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/idp/requirements.txt
RUN pip install -r requirements.txt

COPY . /usr/src/idp/
RUN chmod +x app2.sh
CMD ["./app2.sh"]