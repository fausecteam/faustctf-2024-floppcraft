SERVICE := floppcraft
DESTDIR ?= dist_root
SERVICEDIR ?= /srv/$(SERVICE)

.PHONY: build install

build:
	echo nothing to build

install: build
	mkdir -p $(DESTDIR)$(SERVICEDIR)
	# Remove dependency image from docker-compose
	yq -y 'del(.services."floppcraft-deps")' docker-compose.yml > $(DESTDIR)$(SERVICEDIR)/docker-compose.yml
	mkdir -p $(DESTDIR)$(SERVICEDIR)/floppcraft
	cp floppcraft/* $(DESTDIR)$(SERVICEDIR)/floppcraft -r
	mkdir -p dist_root/srv/floppcraft/deps
	cp deps/* $(DESTDIR)$(SERVICEDIR)/deps -r
	cp data $(DESTDIR)$(SERVICEDIR) -r
	mkdir -p $(DESTDIR)/etc/systemd/system/faustctf.target.wants/
	ln -s /etc/systemd/system/docker-compose@.service $(DESTDIR)/etc/systemd/system/faustctf.target.wants/docker-compose@$(SERVICE).service

