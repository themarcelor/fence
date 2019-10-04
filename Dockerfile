# To run: docker run -d -v /path/to/fence-config.yaml:/var/www/fence/fence-config.yaml --name=fence -p 80:80 fence
# To check running container: docker exec -it fence /bin/bash

FROM python:3.7-buster

LABEL maintainer="Sebastian Ramirez <tiangolo@gmail.com>"

# Standard set up Nginx
ENV NGINX_VERSION 1.17.4-1~buster
ENV NJS_VERSION   1.17.4.0.3.5-1~buster

RUN set -x \
	&& apt-get update \
	&& apt-get install --no-install-recommends --no-install-suggests -y gnupg1 apt-transport-https ca-certificates \
	&& \
	NGINX_GPGKEY=573BFD6B3D8FBC641079A6ABABF5BD827BD9BF62; \
	found=''; \
	for server in \
		ha.pool.sks-keyservers.net \
		hkp://keyserver.ubuntu.com:80 \
		hkp://p80.pool.sks-keyservers.net:80 \
		pgp.mit.edu \
	; do \
		echo "Fetching GPG key $NGINX_GPGKEY from $server"; \
		apt-key adv --no-tty --keyserver "$server" --keyserver-options timeout=10 --recv-keys "$NGINX_GPGKEY" && found=yes && break; \
	done; \
	test -z "$found" && echo >&2 "error: failed to fetch GPG key $NGINX_GPGKEY" && exit 1; \
	apt-get remove --purge --auto-remove -y gnupg1 && rm -rf /var/lib/apt/lists/* \
	&& dpkgArch="$(dpkg --print-architecture)" \
	&& nginxPackages=" \
		nginx=${NGINX_VERSION} \
		nginx-module-xslt=${NGINX_VERSION} \
		nginx-module-geoip=${NGINX_VERSION} \
		nginx-module-image-filter=${NGINX_VERSION} \
		nginx-module-njs=${NJS_VERSION} \
	" \
	&& case "$dpkgArch" in \
		amd64|i386) \
# arches officialy built by upstream
			echo "deb https://nginx.org/packages/mainline/debian/ buster nginx" >> /etc/apt/sources.list.d/nginx.list \
			&& apt-get update \
			;; \
		*) \
# we're on an architecture upstream doesn't officially build for
# let's build binaries from the published source packages
			echo "deb-src https://nginx.org/packages/mainline/debian/ buster nginx" >> /etc/apt/sources.list.d/nginx.list \
			\
# new directory for storing sources and .deb files
			&& tempDir="$(mktemp -d)" \
			&& chmod 777 "$tempDir" \
# (777 to ensure APT's "_apt" user can access it too)
			\
# save list of currently-installed packages so build dependencies can be cleanly removed later
			&& savedAptMark="$(apt-mark showmanual)" \
			\
# build .deb files from upstream's source packages (which are verified by apt-get)
			&& apt-get update \
			&& apt-get build-dep -y $nginxPackages \
			&& ( \
				cd "$tempDir" \
				&& DEB_BUILD_OPTIONS="nocheck parallel=$(nproc)" \
					apt-get source --compile $nginxPackages \
			) \
# we don't remove APT lists here because they get re-downloaded and removed later
			\
# reset apt-mark's "manual" list so that "purge --auto-remove" will remove all build dependencies
# (which is done after we install the built packages so we don't have to redownload any overlapping dependencies)
			&& apt-mark showmanual | xargs apt-mark auto > /dev/null \
			&& { [ -z "$savedAptMark" ] || apt-mark manual $savedAptMark; } \
			\
# create a temporary local APT repo to install from (so that dependency resolution can be handled by APT, as it should be)
			&& ls -lAFh "$tempDir" \
			&& ( cd "$tempDir" && dpkg-scanpackages . > Packages ) \
			&& grep '^Package: ' "$tempDir/Packages" \
			&& echo "deb [ trusted=yes ] file://$tempDir ./" > /etc/apt/sources.list.d/temp.list \
# work around the following APT issue by using "Acquire::GzipIndexes=false" (overriding "/etc/apt/apt.conf.d/docker-gzip-indexes")
#   Could not open file /var/lib/apt/lists/partial/_tmp_tmp.ODWljpQfkE_._Packages - open (13: Permission denied)
#   ...
#   E: Failed to fetch store:/var/lib/apt/lists/partial/_tmp_tmp.ODWljpQfkE_._Packages  Could not open file /var/lib/apt/lists/partial/_tmp_tmp.ODWljpQfkE_._Packages - open (13: Permission denied)
			&& apt-get -o Acquire::GzipIndexes=false update \
			;; \
	esac \
	\
	&& apt-get install --no-install-recommends --no-install-suggests -y \
						$nginxPackages \
						gettext-base \
	&& rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/nginx.list \
	\
# if we have leftovers from building, let's purge them (including extra, unnecessary build deps)
	&& if [ -n "$tempDir" ]; then \
		apt-get purge -y --auto-remove \
		&& rm -rf "$tempDir" /etc/apt/sources.list.d/temp.list; \
	fi

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log
EXPOSE 80
# Removed the section that breaks pip installations
# && apt-get remove --purge --auto-remove -y apt-transport-https ca-certificates
# added --no-tty to apt-key adv as without it it breaks (even though it works in official Nginx)
# apt-key adv --no-tty
# Standard set up Nginx finished

# Expose 443, in case of LTS / HTTPS
EXPOSE 443

# Install uWSGI
RUN pip install uwsgi

# RUN uwsgi --build-plugin "/usr/src/uwsgi/plugins/python python37" \
# 	&& mv python37_plugin.so /usr/lib/uwsgi/plugins/python37_plugin.so \
# 	&& chmod 644 /usr/lib/uwsgi/plugins/python37_plugin.so
# RUN apt-get update \
#     && apt-get -y install uwsgi uwsgi-plugin-python3

# Remove default configuration from Nginx
RUN rm /etc/nginx/conf.d/default.conf
# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
# COPY uwsgi.ini /etc/uwsgi/

COPY nginx.conf /etc/nginx/nginx.conf
COPY uwsgi.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/uwsgi.conf /etc/nginx/conf.d/uwsgi.conf


# Which uWSGI .ini file should be used, to make it customizable
ENV UWSGI_INI /etc/uwsgi/uwsgi.ini

# By default, run 2 processes
ENV UWSGI_CHEAPER 2

# By default, when on demand, run up to 16 processes
ENV UWSGI_PROCESSES 16

# By default, allow unlimited file sizes, modify it to limit the file sizes
# To have a maximum of 1 MB (Nginx's default) change the line to:
# ENV NGINX_MAX_UPLOAD 1m
ENV NGINX_MAX_UPLOAD 0

# By default, Nginx will run a single worker process, setting it to auto
# will create a worker for each CPU core
ENV NGINX_WORKER_PROCESSES 1

# By default, Nginx listens on port 80.
# To modify this, change LISTEN_PORT environment variable.
# (in a Dockerfile or with an option for `docker run`)
ENV LISTEN_PORT 80

# Copy the entrypoint that will generate Nginx additional configs
# COPY entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh

COPY dockerrun.sh /dockerrun.sh
RUN chmod +x /dockerrun.sh

# ENTRYPOINT ["/entrypoint.sh"]

ENV appname=fence

# RUN apk update \
#     && apk add postgresql-libs postgresql-dev libffi-dev libressl-dev \
#     && apk add linux-headers musl-dev gcc \
#     && apk add curl bash git vim make

COPY . /$appname
COPY ./deployment/uwsgi/uwsgi.ini /etc/uwsgi/uwsgi.ini
COPY ./deployment/uwsgi/wsgi.py /$appname/wsgi.py
WORKDIR /$appname

RUN python -m pip install --upgrade pip \
    && python -m pip install --upgrade setuptools \
    && pip install -r requirements.txt

RUN mkdir -p /var/www/$appname \
    && mkdir -p /var/www/.cache/Python-Eggs/ \
    && mkdir /run/nginx/ \
    && ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log \
    && chown nginx -R /var/www/.cache/Python-Eggs/ \
    && chown nginx /var/www/$appname

# RUN apk update && apk add openssh && apk add libmcrypt-dev

#
# libmhash is required by mcrypt - below - no apk package available
#
# RUN (cd /tmp \
#   && wget -O mhash.tar.gz https://sourceforge.net/projects/mhash/files/mhash/0.9.9.9/mhash-0.9.9.9.tar.gz/download \
#   && tar xvfz mhash.tar.gz \
#   && cd mhash-0.9.9.9 \
#   && ./configure && make && make install \
#   && /bin/rm -rf /tmp/*)

# #
# # mcrypt is required to decrypt dbgap user files - see fence/sync/sync_users.py
# #
# RUN (cd /tmp \
#   && wget -O mcrypt.tar.gz https://sourceforge.net/projects/mcrypt/files/MCrypt/Production/mcrypt-2.6.4.tar.gz/download \
#   && tar xvfz mcrypt.tar.gz \
#   && cd mcrypt-2.6.4 \
#   && ./configure && make && make install \
#   && /bin/rm -rf /tmp/*)
# EXPOSE 80

RUN COMMIT=`git rev-parse HEAD` && echo "COMMIT=\"${COMMIT}\"" >$appname/version_data.py \
    && VERSION=`git describe --always --tags` && echo "VERSION=\"${VERSION}\"" >>$appname/version_data.py \
    && python setup.py develop

# RUN apt-get update \
#     && apt-get install
# RUN pip uninstall -y cffi && pip install pycrypto cffi

# RUN pip install --upgrade authutils

WORKDIR /var/www/$appname

CMD ["sh","-c","bash /fence/dockerrun.bash && /dockerrun.sh"]
