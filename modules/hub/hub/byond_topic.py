import sys
import socket
import struct
import urllib.parse

TOPIC_PACKET_ID = b'\x83'
TOPIC_RESPONSE_STRING = b'\x06'
TOPIC_RESPONSE_FLOAT = b'\x2a'

def export(address, port, args):
    try:
        send(address, port, urllib.parse.urlencode(args))
    except socket.timeout:
        pass

def send(address, port, query):
    """Send a Topic() packet to the specified server. Returns the response from the server.

    :param address: address (IP or DNS) of the DreamDaemon instance to send the Topic() to.
    :param port:    port that the DreamDaemon instance is serving the world on
    :param query:   query string to be sent

    :returns: a tuple of response type, and dict of key-value pairs, parsed from
    the url query string returned from the server. The actual data returned
    depends on the codebase the server is running.

    """

    if(len(query) == 0 or query[0] != '?'):
        queryString = '?' + query
    else:
        queryString = query

    # Header:
    # - pad byte
    # - packetId (0x83)
    # - big-endian uint16_t packet-size
    # - pad byte
    packetSize = len(queryString) + 6
    if(packetSize >= (2**16-1)):
        raise Exception('query string too big, max packet size exceeded.')
    packet = struct.pack('>xcH5x', TOPIC_PACKET_ID, packetSize) + bytes(queryString, encoding='utf8') + b'\x00'
    sock = socket.create_connection((address, port))
    sock.settimeout(2)
    sock.send(packet)

    # Response has a 5-byte header, which has a length attribute inside it to
    # tell us how big the response actually is. (Allegedly)

    recv_header = sock.recv(5)
    recvPacketId, content_len, response_type = struct.unpack('>xcHc', recv_header)
    if(recvPacketId != TOPIC_PACKET_ID):
        # How strange. Are we perhaps talking to something that isn't a BYOND server?
        sock.close()
        raise Exception('Incorrect packet-ID received in response. Expecting 0x83, received {}'.format(recvPacketId))

    data = ""
    if(response_type == TOPIC_RESPONSE_STRING):
        content_len -= 2
    if(response_type == TOPIC_RESPONSE_FLOAT):
        content_len -= 1

    response = sock.recv(content_len)
    if(len(response) < content_len):
        raise Exception('Truncated response: (' + str(len(response)) + 'of' + str(content_len) + ')')

    sock.close()
    if(response_type == TOPIC_RESPONSE_STRING):
        data = urllib.parse.parse_qs(str(response, encoding='utf8'), keep_blank_values=True)

    elif(response_type == TOPIC_RESPONSE_FLOAT):
        # Float type response, where the data returned is a floating point value.
        data = struct.unpack('<f', response)[0]

    else:
        # No idea what response *this* is, but maybe it's something
        # specific to a codebase we're not used to.
        data = response

    return (response_type, data)

def queryStatus(address, port):
    try:
        responseType, responseData = send(address, port, '?status')
        if(responseType == TOPIC_RESPONSE_STRING):
            return responseData
        else:
            return None
    except socket.timeout:
        return None

def queryPlayerCount(address, port):
    try:
        responseType, responseData = send(address, port, '?playing')
        if(responseType == TOPIC_RESPONSE_FLOAT):
            return str(int(responseData))
        else:
            return None
    except socket.timeout:
        return None
