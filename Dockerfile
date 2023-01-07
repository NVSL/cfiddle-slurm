FROM stevenjswanson/cse142l-swanson-dev:latest

LABEL org.opencontainers.image.source="https://github.com/NVSL/cfiddle-slurm" \
      org.opencontainers.image.title="cfiddle-slurm-cluster" \
      org.opencontainers.image.description="CFiddle + Slurm Docker cluster on Ubuntu" \
      org.label-schema.docker.cmd="docker-compose up -d" \
      maintainer="Steven Swanson"

USER root
RUN mkdir /slurm
WORKDIR /slurm


COPY SLURM_TAG ./
COPY IMAGE_TAG ./
COPY slurm.conf ./
COPY slurmdbd.conf ./

COPY ./install_slurm.sh ./
RUN ./install_slurm.sh

COPY . /cse142L/cfiddle-slurm
RUN (cd /cse142L/cfiddle-slurm; /opt/conda/bin/pip install -e .)
RUN ls /opt/conda/lib/python3.10/site-packages/cfiddle*
#COPY ./install_cfiddle.sh ./
#RUN ./install_cfiddle.sh 

RUN groupadd cfiddlers
RUN useradd -g cfiddlers -p fiddle -s /usr/bin/bash test_fiddler
RUN useradd -r -s /usr/sbin/nologin -u 7000 cfiddle 
COPY cfiddle_sudoers /etc/sudoers.d

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/opt/conda/bin/cfiddle_with_env.sh", "/usr/local/bin/docker-entrypoint.sh"]
CMD ["slurmdbd"]
