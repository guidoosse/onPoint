FROM postgres:16-alpine

COPY init-databases.sh /usr/local/bin/init-databases
RUN chmod 0755 /usr/local/bin/init-databases

ENTRYPOINT ["/usr/local/bin/init-databases"]