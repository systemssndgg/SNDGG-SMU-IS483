# ngsi-ld-deployment
This repository contains docker-compose files for various deployment setups of NGSI-LD context brokers for SNDGO.

## Orion-LD
- [orion.aio.yml](./orion.aio.yml): Contains services for the Orion-LD context broker, Mintaka, JSON IOT agent and the Mosquitto MQTT broker
- [orion.yml](./orion.yml): Contains services for the Orion-LD context broker and Mintaka.

## Scorpio
- [scorpio.aio.yml](./scorpio.aio.yml): Contains services for the Scorpio context broker, JSON IOT agent and the Mosquitto MQTT broker
- [scorpio.aio.nokafka.yml](./scorpio.aio.nokafka.yml): Similar to `scorpio.aio.yml`, but without Kafka integration
- [scorpio.yml](./scorpio.yml): Contains services for the Scorpio context broker.
- [scorpio.nokafka.yml](./scorpio.nokafka.yml): Similar to `scorpio.yml`, but without Kafka integration

## IOT Agent only
- [agent.json.yml](./agent.json.yml): Contains the JSON IOT agent and the Mosquitto MQTT broker
- [agent.opcua.yml](./agent.opcua.yml): Contains the OPCUA IOT agent.

## API Gateway
As different context brokers have different endpoints or ports for services (i.e., temporal API), there will be multiple dockerfiles and `nginx.conf` files for each broker. Edit the `.conf` files in [`/nginx`](./nginx) to modify the URLs.
- [orion.gateway.yml](./orion.gateway.yml): Contain setup for an NGINX reverse proxy serving as an API gateway for the Orion-LD context broker with Mintaka and IOTAgent-JSON support. 
- [scorpio.gateway.yml](./scorpio.gateway.yml): Contain setup for an NGINX reverse proxy serving as an API gateway for the Scorpio context broker with IOTAgent-JSON support. 

## Context Server
- [context.yml](./context.yml): Acts as a context server, hosting files from the `datamodels` folder.


# Requirements
1. Docker

# How to run
1. Clone this repository
2. Run `cd ngsi-ld-deployment`
3. Create a copy of the `.env.sample` file and rename it to `.env`. Edit the variables as needed.
4. Run `docker-compose -f <filename> up --build`
5. To stop the services, run `docker-compose -f <filename> stop`.

# Quickstart Run (Orion Broker):
1. Clone this repository
2. Run `cd ngsi-ld-deployment`
3. Run `docker compose -f orion.aio.yml up --build`
