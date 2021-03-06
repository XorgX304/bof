"""Byte conversion and management functions. Available functions:

- Resize byte arrays to bigger, or truncate to smaller
- Byte conversion to and from integers
- Byte conversion to and from IPv4 strings

.. note:: The default byteorder used is big endian but it can be changed using
          function ``set_byteorder()`` with either ``"little"`` or ``"big"``
          as first parameter.
"""

from re import match

from .base import BOFProgrammingError
from ipaddress import IPv4Address

__DEFAULT_BYTEORDER = 'big'
_BYTEORDER = __DEFAULT_BYTEORDER

def set_byteorder(byteorder:str) -> None:
    """Changes default byte order to use is byte conversion functions.
    
    :param byteorder: Accepts two values: ``big`` for big endian (default) or
                      ``little`` for little endian
    :raises BOFProgrammingError: If ``byteorder`` is invalid.

    Example::

        set_byteorder(byteorder:str) -> None
    """
    if byteorder not in ["big", "little"]:
        raise BOFProgrammingError("Byte order is either 'big' or 'little'")
    global _BYTEORDER
    _BYTEORDER = byteorder


def get_size(array) -> int:
    """Gives the number of bytes the parameter ``array`` fits into.

    :param array: Object tested for size. Can have type int or bytes.
    :raises BOFProgrammingError: If ``array`` is not an int or a bytearray.
    """
    if isinstance(array, bytes):
        return len(array)
    if isinstance(array, int):
        return ((array.bit_length() + 7) // 8)
    raise BOFProgrammingError("get_size expects bytes or int")

def resize(array:bytes, size:int, byteorder:str=None) -> bytes:
    """Resize a byte array to the expected ``size``.

    If `size` is bigger than ``array``'s actual size, ``array`` is padded. If
    ``size`` is smaller, the value of ``array`` is truncated. Padding or
    truncation outcomes change according to ``byteorder``. If ``byteorder`` is
    not set, the global ``byteorder`` value will be used (set with
    ``set_byteorder()``).

    :param array: Byte array to resize.
    :param size: The expected size of the byte array after padding/truncation.
    :param byteorder: If set, the resizing will rely on the specified
                      byteorder. Otherwise, global ``byteorder`` will be used
                      (set with ``set_byteorder()``).
    :returns: The resized byte array.

    Example::

        >>> x = bof.byte.from_int(1234)
        >>> x = bof.byte.resize(x, 1)
        >>> x
        b'\xd2'
        >>> x = bof.byte.resize(x, 4)
        >>> x
        b'\x00\x00\x00\xd2'
    """
    global _BYTEORDER
    byteorder = byteorder if byteorder else _BYTEORDER
    if size < len(array):
        return array[len(array)-size:] if byteorder == 'big' else array[:size]
    if size > len(array):
        padding = []
        for _ in range(size - len(array)):
            padding += [b'\x00']
        padding = b''.join(padding)
        return padding + array if byteorder == 'big' else array + padding
    return array

def from_int(value:int, size:int=0, byteorder:str=None) -> bytes:
    """Converts an integer to a bytearray.

    :param value: The integer value to convert to a byte or a byte array.
    :param size: If set, the bytearray will be of the specified size.
    :param byteorder: If set, the conversion will rely on the specified
                      byteorder. Otherwise, global ``byteorder`` will be used
                      (set with ``set_byteorder()``).
    :returns: The value resized as a bytearray.
    :raises BOFProgrammingError: If ``value`` is not int or ``byteorder`` is
                                 invalid.

    Example::

        >>> bof.byte.from_int(65980)
        b'\x01\x01\xbc'
        >>> bof.byte.from_int(65980, size=8, byteorder='big')
        b'\x00\x00\x00\x00\x00\x01\x01\xbc'
    """
    global _BYTEORDER
    byteorder = byteorder if byteorder else _BYTEORDER
    if byteorder not in ["big", "little"]:
        raise BOFProgrammingError("Byte order is either 'big' or 'little'")
    if not isinstance(value, int) or not isinstance(size, int):
        raise BOFProgrammingError("Int to bytes expects an int")
    value = value.to_bytes((value.bit_length() + 7) // 8, byteorder)
    if len(value) == 0:
        size = 1 if not size else size
    return resize(value, len(value) if not size else size, byteorder)

def to_int(array:bytes, byteorder:str=None) -> int:
    """Converts a byte array to an integer.

    :param array: Byte array to convert to an integer.
    :param byteorder: Byte order to use. If not set, global ``byteorder`` will
                      be used (set with ``set_byteorder()``).
    :returns: The value of the bytearray converted to an integer.
    :raises BOFProgrammingError: If ``array`` is not bytes or ``byteorder`` is
                                 invalid.

    Example::

        >>> bof.byte.to_int(b'\x01\x01\xbc')
        65980
    """
    global _BYTEORDER
    byteorder = byteorder if byteorder else _BYTEORDER
    if byteorder not in ["big", "little"]:
        raise BOFProgrammingError("Byte order is either 'big' or 'little'")
    if not isinstance(array, bytes):
        raise BOFProgrammingError("Bytes to int expects bytes")
    return int.from_bytes(array, byteorder)

def from_ipv4(ip:str, size:int=0, byteorder:str=None) -> bytes:
    """Converts a IPv4 string to a bytearray.

    :param ip: IPv4 string with format with format ``"A.B.C.D"``
    :param size: If set, the byte aray will be of the specified size.
    :param byteorder: If not set, global ``byteorder`` will be used (set with
                      ``set_byteorder()``).
    :returns: The IPv4 address as a bytearray (should be on 4 bytes).

    Example::

        value = byte.from_ipv4("127.0.0.1")
    """
    return bytes(map(int, ip.split('.')))

def to_ipv4(array:bytes) -> str:
    """Converts a byte array representing an IPv4 address to a string with
    format "A.B.C.D" (IPv4) using Python's builtin ``ipaddress`` module.

    :param array: Byte array to convert to an IPv4 address (usually 4 bytes :)).
    :returns: The IP address as a string with format ``"A.B.C.D"``
    """
    return str(IPv4Address(array))

def to_mac(array:bytes) -> str:
    """Converts a MAC address as a byte array to a MAC address as a string
    with format AA:BB:CC:DD:EE:FF.

    :param array: Byte array to convert to a MAC address (usually 6 bytes)
    :returns: The MAC address as a string.
    """
    return ':'.join(("%02x" % b) for b in array)

def from_mac(mac:str):
    """Converts a MAC address as a string with format AA:BB:CC:DD:EE:FF
    to a byte array (6 bytes).

    :param mac: String with MAC address
    :returns: A byte array of the corresponding MAC address.
    """
    array = bytes.fromhex(mac.replace(":", ""))
    return array

def to_knx(value:bytes, group=False) -> str:
    """Converts a 2-bytes array to a KNX individual (X.Y.Z) or group 
    address (X/Y/Z).

    :Individual address ``X.Y.Z``: X and Y are 4 bits (1st byte) and
                                   Z is 8 bits (2nd byte).
    :Group address ``X/Y/Z``: X is 6 bits, Y is 3 bits (1st byte) and
                              Z is 8 bits (2nd byte).

    :param value: Byte array (2 bytes) to convert
    :param group: Boolean stating if the KNX address is a group address
                  (default is False: the final string will have a the
                  format of an individual KNX address.
    """
    if not len(value):
        return None
    first_chunk_size = 5 if group else 4
    string_format = "{0}/{1}/{2}" if group else "{0}.{1}.{2}"
    bitlist = to_bit_list(value[:1])
    x = int("".join([str(x) for x in bitlist[:first_chunk_size]]), 2)
    y = int("".join([str(x) for x in bitlist[first_chunk_size:]]), 2)
    z = to_int(value[1:])
    return string_format.format(x, y, z)

def from_knx(address:str) -> bytes:
    """Converts a KNX individual address (X.Y.Z) or group address
    (X/Y/Z) to a byte array (2 bytes, X Y being one byte, and Z the
    other).

    :param address: KNX address as a string with format X.Y.Z or
                    X/Y/Z.
    """
    addr = match("(\d{1,2})\.(\d{1,2})\.(\d{1,3})", address)
    first_chunk_size = 4 # individual address
    if not addr:
        addr = match("(\d{1,2})/(\d{1,2})/(\d{1,3})", address)
        first_chunk_size = 5 # group address
    if not addr:
        return None
    x, y, z = (int(addr.group(a+1)) for a in range(3))
    x = int_to_bit_list(x)[8-first_chunk_size:]
    y = int_to_bit_list(y)[first_chunk_size:]
    b1 = from_int(bit_list_to_int(x + y))
    b2 = from_int(z)
    return b''.join([b1, b2])

def int_to_bit_list(n:int, size:int=8, byteorder:str=None) -> list:
    """Representation of n as a list of bits (0 or 1).
    
    
    :param n: Integer to convert to a list of bits (0 or 1).
    :param size: If set, the list will be of the specified size.
    :param byteorder: If not set, global ``byteorder`` will be used (set with
                      ``set_byteorder()``).
    :returns: The value of the integer ``n`` as a list of bits (0 or 1).
    :raises BOFProgrammingError: If ``byteorder`` is invalid.
    """
    global _BYTEORDER
    byteorder = byteorder if byteorder else _BYTEORDER
    if byteorder not in ["big", "little"]:
        raise BOFProgrammingError("Byte order is either 'big' or 'little'")
    t = []
    for i in range(size):
        b = n & 1
        t.append(b)
        n >>= 1
    if byteorder == 'big':
        t.reverse()
    return t

def bit_list_to_int(t:list, byteorder:str=None) -> int:
    """Integer represented by the bit list t. t is a list of 0 or 1 values.

    :param t: List of bit to convert to an integer.
    :param byteorder: If not set, global ``byteorder`` will be used (set with
                      ``set_byteorder()``).
    :returns: The integer represented by the list of bits ``t``.
    :raises BOFProgrammingError: If ``byteorder`` is invalid.

    """
    global _BYTEORDER
    byteorder = byteorder if byteorder else _BYTEORDER
    if byteorder not in ["big", "little"]:
        raise BOFProgrammingError("Byte order is either 'big' or 'little'")
    n = 0
    if byteorder != 'big':
        t = reversed(t)
    for b in t:
        n <<= 1
        n += b
    return n

def to_bit_list(value:bytes, size=None, byteorder:str=None) -> list:
    """List of bits represented by the bytes-like object value.

    :param value: Bytes to convert to a list of bits.
    :param size: If set, the list will be of the specified size.
    :param byteorder: If not set, global ``byteorder`` will be used (set with
                      ``set_byteorder()``).
    :returns: The bytes ``value`` represented as a list of bits.
    :raises BOFProgrammingError: If ``byteorder`` is invalid.

    """
    global _BYTEORDER
    byteorder = byteorder if byteorder else _BYTEORDER
    if byteorder not in ["big", "little"]:
        raise BOFProgrammingError("Byte order is either 'big' or 'little'")
    n = int.from_bytes(value, byteorder=byteorder)
    size = size if size else 8 * len(value)
    return int_to_bit_list(n, size=8*len(value))

def from_bit_list(bits:list, byteorder:str=None) -> bytes:
    """Array of bytes representing the list of bits t.

    :param bits: List of bits to convert to bytes.
    :param byteorder: If not set, global ``byteorder`` will be used (set with
                      ``set_byteorder()``).
    :returns: The list of bits represented as a bytes-like object.
    :raises BOFProgrammingError: If ``byteorder`` is invalid.
    """
    global _BYTEORDER
    byteorder = byteorder if byteorder else _BYTEORDER
    if byteorder not in ["big", "little"]:
        raise BOFProgrammingError("Byte order is either 'big' or 'little'")
    assert len(bits) % 8 == 0
    n = bit_list_to_int(bits, byteorder=byteorder)
    return n.to_bytes(len(bits) // 8, byteorder=byteorder)
