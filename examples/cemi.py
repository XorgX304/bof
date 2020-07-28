from sys import path, argv
path.append('../')

from bof import knx, BOFNetworkError, byte

def connect_request(knxnet, connection_type):
    ip, port = knxnet.source
    connectreq = knx.KnxFrame(type="CONNECT REQUEST")
    connectreq.body.connection_request_information.connection_type_code.value = knx.KnxSpec().get_code_id("connection type code", connection_type)
    connectreq.body.control_endpoint.ip_address.value = ip
    connectreq.body.control_endpoint.port.value = port
    connectreq.body.data_endpoint.ip_address.value = ip
    connectreq.body.data_endpoint.port.value = port
    if connection_type == "Tunneling Connection":
        connectreq.body.connection_request_information.append(knx.KnxField(name="link layer", size=1, value=b"\x02"))
        connectreq.body.connection_request_information.append(knx.KnxField(name="reserved", size=1, value=b"\x00"))
    connectresp = knxnet.send_receive(connectreq)
    knxnet.channel = connectresp.body.communication_channel_id.value
    return connectresp

def disconnect_request(knxnet):
    discoreq = knx.KnxFrame(type="DISCONNECT REQUEST")
    discoreq.body.communication_channel_id = knxnet.channel
    discoreq.body.control_endpoint.ip_address.value = byte.from_ipv4(knxnet.source[0])
    discoreq.body.control_endpoint.port.value = byte.from_int(knxnet.source[1])
    knxnet.send_receive(discoreq)

def read_property(knxnet, sequence_counter, object_type, property_id):
    request = knx.KnxFrame(type="CONFIGURATION REQUEST", cemi="PropRead.req")
    request.body.communication_channel_id.value = knxnet.channel
    request.body.sequence_counter.value = sequence_counter
    propread = request.body.cemi.cemi_data.propread_req
    propread.number_of_elements.value = 1
    propread.object_type.value = knxspecs.object_types[object_type]
    propread.object_instance.value = 1
    propread.property_id.value = knxspecs.properties[object_type][property_id]
    try:
        response = knxnet.send_receive(request) # ACK
        while (1):
            response = knxnet.receive() # PropRead.con
            if response.sid == "CONFIGURATION REQUEST":
                # We tell the boiboite we received it
                ack = knx.KnxFrame(type="CONFIGURATION ACK")
                ack.body.communication_channel_id.value = knxnet.channel
                ack.body.sequence_counter.value = sequence_counter
                knxnet.send(ack)
                return response
    except BOFNetworkError:
        pass #Timeout

if len(argv) < 2:
    print("Usage: python {0} IP_ADDRESS".format(argv[0]))
    quit()

knxspecs = knx.KnxSpec()
knxnet = knx.KnxNet()
knxnet.connect(argv[1], 3671)

# Gather device information
connectresp = connect_request(knxnet, "Device Management Connection")
read_property(knxnet, 0, "IP PARAMETER OBJECTS", "PID_ADDITIONAL_INDIVIDUAL_ADDRESSES")
disconnect_request(knxnet)

# Establish tunneling connection to read and write objects
connectresp = connect_request(knxnet, "Tunneling Connection")
print("Device individual address: {0}".format(connectresp.body.connection_response_data_block.connection_data.knx_address.value))
# TODO
disconnect_request(knxnet)
