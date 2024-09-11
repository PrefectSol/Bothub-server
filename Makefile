build: build-platform

build-platform:
	@docker build -t bothub-platform .

clear:
	@python scripts/clear.py

rmdb:
	@sudo rm -rf platform/database/*
	
start:
	@python platform/control/start.py $(filter-out $@,$(MAKECMDGOALS))

stop:
	@python platform/control/stop.py $(filter-out $@,$(MAKECMDGOALS))

status:
	@python platform/control/status.py $(filter-out $@,$(MAKECMDGOALS))

enable-net:
	@python platform/control/enable_net.py $(filter-out $@,$(MAKECMDGOALS))

disable-net:
	@python platform/control/disable_net.py $(filter-out $@,$(MAKECMDGOALS))

force-restart:
	@make stop
	@make rmdb
	@make clear
	@make build
	@make enable_net
	
