## compile dumb-init
FROM gcc:9.2.0 as dumb-init-builder

RUN git clone -b v1.2.1 --depth 1 --single-branch https://github.com/proofpoint/dumb-init.git
RUN cd dumb-init && make

FROM docker.io/azul/zulu-openjdk-debian:11.0.5
COPY --from=dumb-init-builder /dumb-init/dumb-init /usr/local/bin/dumb-init

#RUN apt-get update && \
#    DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes \
                     # These packages are security updates
RUN apt-get update \
  && apt-get install -y python3-pip python3-dev curl \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip \

RUN set -ex; \
    adduser --disabled-password --gecos /service -u 1005 service

ADD <LOCATION_OF_YOUR_DISTRIBUTION_PACKAGE> /service
RUN mv /service/<SERVICE_DIR> /service/<SERVICE_DIR> \
  && bash -c 'mkdir -p /service/<SERVICE_DIR>/etc'

# ${project.build.directory}/${project.artifactId}-${project.version}-distribution.tar.gz
WORKDIR /service/<SERVICE_DIR>

COPY dev/etc etc/
COPY dev/bin/main.py bin/
COPY dev/bin/config.properties bin/
COPY docker-entrypoint.sh bin/


RUN set -ex; \
    chmod +x bin/docker-entrypoint.sh; \
    chown -R service /service

EXPOSE 9443 8443 8079

USER service

ENTRYPOINT ["/usr/local/bin/dumb-init", "bin/docker-entrypoint.sh"]
