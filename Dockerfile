FROM phusion/baseimage:0.9.16
MAINTAINER Elek, Marton <level2@anzix.net>

# Let the conatiner know that there is no tty
#ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get -y upgrade

# Basic Requirements
RUN apt-get -y install python


RUN mkdir /host
RUN mkdir /host/archive

ADD streamsaver /etc/cron.d/
ADD streamSaver.py /host/


