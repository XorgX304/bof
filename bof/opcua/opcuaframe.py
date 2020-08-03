"""
OPC UA frame handling
------------------

OPC UA frames handling implementation, implementing ``bof.frame``'s
``BOFSpec``, ``BOFFrame``, ``BOFBlock`` and ``BOFField`` classes.
See `bof/frame.py`.

BOF should not contain code that is bound to a specific version of a protocol's
specifications. Therefore OPC UA frame structure and its content is described in
:file:`opcua.json`.
"""

from os import path

from ..base import BOFProgrammingError, to_property, log
from ..frame import BOFFrame, BOFBlock, BOFField
from ..spec import BOFSpec

###############################################################################
# OPCUA SPECIFICATION CONTENT                                                 #
###############################################################################

OPCUASPECFILE = "opcua.json"

class OpcuaSpec(BOFSpec):
    """Singleton class for OPC UA specification content usage.
    Inherits ``BOFSpec``, see `bof/frame.py`.

    The default specification is ``opcua.json`` however the end user is free
    to modify this file (add categories, contents and attributes) or create a
    new file following this format.

    Usage example::

        spec = opcua.OpcuaSpec()
        block_template = spec.get_block_template(block_name="HEL_BODY")
        item_template = spec.get_item_template("HEL_BODY", "protocol version")
        message_structure = spec.get_code_name("message_type", "HEL")
    """

    def __init__(self):
        """Initialize the specification object with a JSON file.
        If `filepath` is not specified, we use a default one specified in 
        `OPCUASPECFILE`.
        """
        #TODO: add support for custom file path (depends on BOFSpec)
        filepath = path.join(path.dirname(path.realpath(__file__)), OPCUASPECFILE)
        super().__init__(filepath)

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def get_item_template(self, block_name:str, item_name:str) -> dict:
        """Returns an item template (dict of values) from a `block_name` and
        a `field_name`.
        
        Note that an item template can represent either a field or a block,
        depending on the "type" key of the item.

        :param block_name: Name of the block containing the item.
        :param item_name: Name of the item to look for in the block.
        """
        if block_name in self.blocks:
            for item in self.blocks[block_name]:
                if item['name'] == item_name:
                    return item
        return None

    def get_block_template(self, block_name:str) -> list:
        """Returns a block template (list of item templates) from a block name.

        :param block_name: Name of the block we want the template from.
        """
        return self._get_dict_value(self.blocks, block_name) if block_name else None
    
    def get_code_name(self, code_name:str, identifier) -> str:
        """Returns the value associated to an `identifier` inside a `code_name`
        association table. See `opcua.json` + usage example to better 
        understand the association table concept.
        
        :param identifier: Key we want the value from, as str or byte.
        :param code_name: Association table name we want to look into for identifier
                    match.
        """
        code_name = self._get_dict_key(self.codes, code_name)
        if isinstance(identifier, bytes):
            for key in self.codes[code_name]:
                if identifier == str.encode(key):
                    return self.codes[code_name][key]
        if isinstance(identifier, str):
            for key in self.codes[code_name]:
                if identifier == key:
                    return self.codes[code_name][key]
        return None

###############################################################################
# OPC UA FRAME CONTENT                                                        #
###############################################################################

#-----------------------------------------------------------------------------#
# OPC UA fields (byte or byte array) representation                           #
#-----------------------------------------------------------------------------#

class OpcuaField(BOFField):
    """An ``OpcuaField`` is a set of raw bytes with a name, a size and a
    content (``value``). Inherits ``BOFField``. See `frame.py`.

    Usage example::

        # creating a field from raw parameters
        field = opcua.OpcuaField(name="protocol version", value=b"1", size=4)
        field.value = field.value = b'\x00\x00\x00\x02'

        # creating a field from a template
        item_template_field = spec.get_item_template("HEL_BODY", "protocol version")
        field = opcua.OpcuaField(**item_template_field)
    """

    # For now there is no need to redefine getter and setter property from
    # BOFField (base class attributes are compatible with OPC UA field spec)

#-----------------------------------------------------------------------------#
# OPC UA blocks (set of fields) representation                                #
#-----------------------------------------------------------------------------#

class OpcuaBlock(BOFBlock):
    """Object representation of an OPC UA block. Inherits ``BOFBlock``. 
    See `frame.py`.

    An OpcuaBlock (as well as a BOFBlock) contains a set of items.
    Those items can be fields as well as blocks, therefore creating
    "nested blocks" or "sub-block".

    It is usually built from a template which gives its structure.
    Values can also be specified to "fill" the block stucture.
    If no structure is specified the block remains empty.

    Some block field's value (typically a sub-block type) may depend on the
    value of another field. In that case the keyword "depends:" is used to
    associate the variable to its value, based on given parameters to another
    field. The process can be looked in details `__init__` method, and
    understood from examples.

    Usage example:: 

        # block creation with direct parameters
        block = opcua.OpcuaBlock(name="header", type="HEADER")

        # block creation from an item template (as found in json spec file)
        item_template_block = {"name": "header", "type": "HEADER"}
        block = opcua.OpcuaBlock(item_template_block=item_template_block)

        # block creation from an item template with dependency specified in defaults
        # parameters
        item_template_block = {"name": "body", "type": "depends:message_type"}
        block = opcua.OpcuaBlock(
                item_template_block={"name": "body", "type": "depends:message_type"},
                defaults={"message_type": "HEL"})

        # fills block with byte value at creation (note that a type is still mandatory)
        block = opcua.OpcuaBlock(type="STRING", value=14*b"\x01")

        # a block with dependency can be created from raw bytes too (no default parameter)
        data1 = b'HEL\x00...'
        data2 = b'\x00...'
        block = opcua.OpcuaBlock()
        block.append(opcua.OpcuaBlock(value=data1, parent=block, 
                        **{"name": "header", "type": "HEADER"}))
        block.append(opcua.OpcuaBlock(alue=data2, parent=block, 
                        **{"name": "body", "type": "depends:message_type"}))

        # we can access list block `fields` using
        block.attributes

        # and access on of those `fields` with
        block.protocol_version
    """
    
    @classmethod
    def factory(cls, item_template:dict, **kwargs) -> object:
        """Returns either an `OpcuaBlock` or an `OpcuaField` depending on the
        template specified item type. That's why it's a factory as a class method.

        :param item_template: item template representing sub-block or field.
        
        Keyword arguments:
        
        :param defaults: defaults values to assign a field as dictionnary
                         (can therefore be used to construct blocks with
                         dependencies if not found in raw bytes, see example
                         above)
        :param value: bytes value to fill the block with
                         (can create dependencies on its own, see example
                         above)
        """
        # case where item template represents a field (non-recursive)
        if "type" in item_template and item_template["type"] == "field":
            value = b''
            if "defaults" in kwargs and item_template["name"] in kwargs["defaults"]:
                value = kwargs["defaults"][template["name"]]
            elif "value" in kwargs and kwargs["value"]:
                value = kwargs["value"][:item_template["size"]]
            return OpcuaField(**item_template, value=value)
        # case where item template represents a sub-block (nested/recursive block)
        else:
            return OpcuaBlock(item_template_block=item_template, **kwargs)
    
    def __init__(self, **kwargs):
        """Initialize the ``OpcuaBlock``.

            Keyword arguments:

            :param type: a string specifying block type (as found in json
                         specifications) to construct the block on.
            :param item_template_block: item template dict corresponding to a 
                         block (which is described in item_block_template['type']),
                         giving its structure to the OpcuaBlock. If a block type
                         is already specified this parameter won't be taken into
                         account.
            :param defaults: defaults values to assign a field as dictionnary
                         (can therefore be used to construct blocks with
                         dependencies if not found in raw bytes, see example
                         above)
            :param value: bytes value to fill the block with
                         (can create dependencies on its own, see example
                         above). If defaults parameter is found it overcomes
                         the value passed as bytes.

            See example in class docstring to understand dependency creation
            either with defaults or with value parameter.
            
        """
        self._spec = OpcuaSpec()
        super().__init__(**kwargs)

        # we gather args values and set some default values first
        defaults = kwargs["defaults"] if "defaults" in kwargs else {}
        value = kwargs["value"] if "value" in kwargs else {}
        block_type = None
        block_template = None

        # there are several way to get a block type, either by its name 
        # or by specifying a template
        if "type" in kwargs:
            block_type = kwargs["type"]
        elif "item_template_block" in kwargs and "type" in kwargs["item_template_block"]:
            item_template_block = kwargs["item_template_block"]
            block_type = item_template_block["type"]
        else:
            log("No type or item_template_block specified, creating empty block")
            return

        # if a dependency is found in block type
        # looks for needed information in default arg
        if block_type.startswith("depends:"):
            dependency = block_type.split(":")[1]

            # checks first for dependency defaults parameter
            if dependency in defaults:
                block_type = self._spec.get_code_name(dependency, defaults[dependency])
                if dependency == None:
                    raise BOFProgrammingError("No valid association found for dependency '{0}' with '{1}'.".format(dependency, defaults[dependency]))
            # if not found in defaults, check in parent block
            else:
                block_type = self._get_depends_block(dependency)
                if block_type == None:
                    raise BOFProgrammingError("No valid association found in parents for dependency '{0}'.".format(dependency))
           
            log("Creating OpcuaBlock of type '{0}' from dependency '{1}'.".format(block_type, dependency))
        else:
            log("Creating OpcuaBlock of type '{0}'.".format(block_type))
        
        # for the moment, we set the block name to its type
        self._name = block_type

        # if block template has not been found we extract the block template according to the type found in item template
        block_template = self._spec.get_block_template(block_type)

        if not block_template:
            raise BOFProgrammingError("Block type '{0}' not found in specifications.".format(block_type))

        for item_template in block_template:
            new_item = self.factory(item_template, defaults=defaults, value=value, parent=self)
            self.append(new_item)

            # Cut value to fill byte by byte
            if value:
                if len(new_item) >= len(value):
                    break
                value = value[len(new_item):]

        return