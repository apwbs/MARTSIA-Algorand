FROM ubuntu:18.04

RUN apt-get update && \
    apt-get -y install sudo && \
    apt-get -y install wget && \
    apt-get -y install python3 && \
    apt-get -y install python3-pip && \
    apt-get -y install curl 
