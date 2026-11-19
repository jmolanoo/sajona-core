FROM postgres:16.6-alpine
RUN mkdir -p /backups && chown -R postgres:postgres /backups
COPY docker/backup/backup.sh /usr/local/bin/backup.sh
COPY docker/backup/restore_test.sh /usr/local/bin/restore_test.sh
RUN chmod +x /usr/local/bin/backup.sh /usr/local/bin/restore_test.sh
USER postgres
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["while true; do /usr/local/bin/backup.sh; sleep 86400; done"]
