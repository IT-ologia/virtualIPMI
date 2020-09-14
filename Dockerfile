FROM centos:8

WORKDIR /root
ENV LC_ALL C.UTF-8

RUN echo "assumeyes=1" >> /etc/dnf/dnf.conf
RUN dnf update -y && dnf install -y epel-release

RUN dnf install python38 python38-devel 

RUN dnf install -y \
		sqlite \
		sqlite-devel \
		vim \
		openssh-clients \
		tzdata \
	&& dnf clean all

RUN python3 -m venv --system-site-packages myenv
RUN source myenv/bin/activate

RUN pip3 install tox 

COPY requirements.txt /root/requirements.txt
RUN pip3 install -r requirements.txt

COPY scripts /root/scripts
RUN mkdir /root/log

COPY virtualIPMI.py /root/virtualIPMI.py
CMD python3 /root/virtualIPMI.py
