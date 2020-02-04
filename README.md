### Proofpoint platform service dockerized 

This is intended for [proofpoint platform](https://github.com/proofpoint/platform) developers debugging, testing purpose only, production quality support is not developed.

Dockerizing platform service is achieved by using [yelp/dumb-init](https://github.com/Yelp/dumb-init) as base image, with custom python bootstrap script that secures a pid for running after loading proper config files enforced by the platform:
- bootstrap: `bin/config.properties`
- jvm: `etc/jvm.config`
- application: `etc/config.properties`
- log: `etc/log.properties` 
- pid: `var/run/launcher.pid`

Auditing log files locations are set by default:
- app log: `var/log/server.log`
- bootstrap log: `var/log/launcher.log`


#### Get started
- Modify Dockerfile
    - Replace `<LOCATION_OF_YOUR_DISTRIBUTION_PACKAGE>` with your real path: e.g., `target/service-distribution.tar.gz`
    - Replace `<SERVICE_DIR>` with your real service name, this is primarily set by your maven config
- Prepare main class name for bootstrap in `bin/config.properties`
- Prepare process name in `bin/config.properties` if unset it will be java or default string
- Prepare application related config in `etc/`
- Build docker image with command `docker build -t <Image> .`
- Run docker image with command `docker --rm -it <Image>:latest`


