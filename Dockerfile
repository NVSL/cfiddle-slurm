FROM jupyter/scipy-notebook

LABEL org.opencontainers.image.source="https://github.com/NVSL/cfiddle-slurm" \
      org.opencontainers.image.title="cfiddle-slurm-cluster" \
      org.opencontainers.image.description="CFiddle + Slurm Docker cluster on Ubuntu" \
      org.label-schema.docker.cmd="docker-compose up -d" \
      maintainer="Steven Swanson"


USER root
RUN mkdir /slurm
WORKDIR /slurm

ARG GOSU_VERSION=1.11

COPY SLURM_TAG ./
COPY IMAGE_TAG ./
COPY slurm.conf ./
COPY slurmdbd.conf ./

COPY ./install_slurm.sh ./
RUN ./install_slurm.sh

COPY ./install_cfiddle.sh ./
RUN ./install_cfiddle.sh 

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["slurmdbd"]
