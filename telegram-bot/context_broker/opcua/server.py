import asyncio
import logging
from asyncua import Server, ua

# init_variables = [{
#     # "temperature": {
#     #     "value": 0,
#     #     "unitSymbol": "°C",
#     #     "unitCode": "CEL"
#     # },
#     "temperature": 15.0,
#     "locatedIn": "urn:ngsi-ld:Room:Room001",
#     "deviceType": "TemperatureSensor",
#     },
#     {
#     "locatedIn": "urn:ngsi-ld:Room:Room001",
#     "deviceType": "Buzzer",
#     "command": "Off",
#     "status": "Off"
#     }
# ]

init_variables = {
    # "temperature": {
    #     "value": 0,
    #     "unitSymbol": "°C",
    #     "unitCode": "CEL"
    # },
    "temperature": 15.0,
    "locatedIn": "urn:ngsi-ld:Room:Room001",
    "deviceType": "TemperatureSensor",
}

async def main():
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger('asyncua')

    # Setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # Populating address space with variables
    sensor = await server.nodes.objects.add_object(idx, "")
    for key, value in init_variables.items():
        variable = await sensor.add_variable(idx, key, value)
        await variable.set_writable()

    _logger.info("Starting server!")

    async with server:
        while True:
            await asyncio.sleep(2)
            # Future logic for updating and logging variable values

if __name__ == "__main__":
    asyncio.run(main())
