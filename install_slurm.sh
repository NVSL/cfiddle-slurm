#!/usr/bin/env bash
set -ex

SLURM_TAG=$(cat SLURM_TAG)
IMAGE_TAG=$(cat IMAGE_TAG)
GOSU_VERSION=1.11

groupadd -r --gid=990 slurm || true
useradd -r -g slurm --uid=990 slurm|| true

groupadd -r --gid=995 munge || true
useradd -r -g munge --uid=998 munge || true

apt-get update --fix-missing --allow-releaseinfo-change
apt-get install -y \
       docker-compose \
       gnupg \
       munge \
       mariadb-server \
       psmisc \
       bash-completion \
       slurmd slurm slurm-client slurmdbd slurmctld \
       munge

apt-get clean -y

#docker build --build-arg SLURM_TAG=$SLURM_TAG -t slurm-docker-cluster:$IMAGE_TAG .


mkdir -p /etc/sysconfig/slurm \
        /var/spool/slurmd \
        /var/run/slurmd \
        /var/run/slurmdbd \
        /var/lib/slurmd \
        /var/log/slurm \
        /data

#mkdir -p /etc/slurm
mkdir -p /etc/slurm/
cp slurm.conf /etc/slurm/slurm.conf
cp slurmdbd.conf /etc/slurm/slurmdbd.conf

touch /var/lib/slurmd/node_state \
        /var/lib/slurmd/front_end_state \
        /var/lib/slurmd/job_state \
        /var/lib/slurmd/resv_state \
        /var/lib/slurmd/trigger_state \
        /var/lib/slurmd/assoc_mgr_state \
        /var/lib/slurmd/assoc_usage \
        /var/lib/slurmd/qos_usage \
        /var/lib/slurmd/fed_mgr_state \

#/sbin/create-munge-key

chown -R slurm:slurm /var/*/slurm*
chown slurm:slurm /etc/slurm/slurmdbd.conf
chmod 600 /etc/slurm/slurmdbd.conf

#echo "NodeName=$(hostname) RealMemory=1000 State=UNKNOWN" >> /etc/slurm/slurm.conf
