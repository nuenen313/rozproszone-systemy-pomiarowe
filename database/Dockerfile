FROM postgres:18-alpine

ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=admin_pass1234
ENV POSTGRES_DB=abcd_db

WORKDIR /docker-entrypoint-initdb.d

COPY 01-init_database.sql /docker-entrypoint-initdb.d/

EXPOSE 5432

CMD ["postgres"]