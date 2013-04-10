"""

Devices controled my the ISY are representd at "nodes" on the ISY device and
with Node Objects in the API

There are three types of Node Object:

    * IsyNode - Node Object 
	Represent lights, switches, motion sensors 
    * IsyScene - Scene Object
	Represents Scenes contains Nodes that comprise a "Scene"
    * IsyNodeFolder - Can hold Scene's or Nodes
	a organizational obj for Scene's and Nodes

Only IsyNode Objects maintain "state" 

    What states are maintined depend on the physical node device itself
    but they can include
	- on, off of dim level
	- temperature
	- wattage

    Nodes can have "members" or subnodes

IsyScene Objects can take commands but do not maintin a queryable state

    A Scene is predefined state for one or more nodes
    scenes can only be comprised of nodes which are call "members"

    only nodes can be members of a scene 

IsyNodeFolders are just for organizing  

    Nodes, Scenes and Folders can be members of a Folder 



"""
from ISY.IsyUtilClass import IsyUtil, IsySubClass, val2bool
from ISY.IsyExceptionClass import *
# from IsyClass import *
# from IsyNodeClass import *
#from IsyProgramClass import *
# from IsyVarClass import *

__all__ = ['IsyNode', 'IsyNodeFolder', 'IsyScene']





class _IsyNodeBase(IsySubClass):

    def on(self, val=255) :
        """ Send On command to a node

            args: 
                take optional value for on level

        """
	if not str(val).isdigit :       
	    TypeError("On Command : Bad Value : node=%s val=%s" %
		    self._mydict["address"], str(val))

        self.isy._node_comm(self._mydict["address"], "DON", val)
        #if "property" in self._mydict :
        #    self._mydict["property"]["time"] = 0
        # self.update()

    def off(self) :
        """ Send Off command to a node

            args: None

        """
        self.isy._node_comm(self._mydict["address"], "DOF")
        if "property" in self._mydict :
            self._mydict["property"]["time"] = 0
            if "ST" in  self._mydict["property"] :
                self._mydict["property"]["ST"]["value"] = 0
                self._mydict["property"]["ST"]["formatted"] = "off"

    def beep(self) :
        self.isy._node_comm(self._mydict["address"], "BEEP")


    def member_iter(self):
        return self.members_list()

    def member_list(self):
        if 'members' in self._mydict :
            # print("mydict['members'] : ", type(self._mydict['members']) )
            if type(self._mydict['members']) == 'dict' :
                return self._mydict['members'].keys()
            # if type(self._mydict['members']) == 'list' :
            return self._mydict['members'][:]
        return [ ]

    def is_member(self, obj) :
        if "members" in self._mydict :
            if isinstance(obj, str)  :
                return obj in self._mydict["members"]
            elif isinstance(obj, IsyBaseClass)  :
                return obj._get_prop("address") in self._mydict["members"]
        return False

    # check if scene _contains_ node
    def __contains__(self, other):
            return self.is_member(other)

    # check if obj _contains_  attib
#    def __contains__(self, other):
#       if isinstance(other, str)  :
#           return other in self._getlist
#       else :
#           return False



#
# convers a node Id  to a int
# eg: "9 4A 5F 2" => 00001001010010100101111100000010 => 155868930
#
def node_id_to_int(h) :
    a = h.split(' ')
    return  ( int(a[0], 16) << 24 ) | ( int(a[1], 16) << 16 ) | \
		    ( int(a[2], 16) << 8 ) | int(a[3], 16)



# def rate
# def onlevel
class IsyNode(_IsyNodeBase):
    """ Node Class for ISY

        Attributes :
            status / ST
            ramprate / RR
            onlevel / OL

        Readonly Attributes :
            address
            formatted
            enabled
            pnode
            type
            name
            ELK_ID
            flag

        funtions:
	    get_rr:
	    set_rr:
    """
    _getlist = ['address', 'enabled', 'formatted',
            'ELK_ID',
            'name', 'pnode', 'flag',
            'OL', 'RR', 'ST', 'type']
    _setlist = ['RR', 'OL', 'status', 'ramprate', 'onlevel']
    _propalias = {'status': 'ST', 'value': 'ST', 'val': 'ST',
            'id': 'address', 'addr': 'address',
            'ramprate': 'RR', 'onlevel': 'OL',
            "node-flag": "flag"}
    #_boollist = [ "enabled" ]

    def __init__(self, isy, ndict) :
        if isinstance(ndict, dict):
            self._mydict = ndict
        else :
            print("error : class IsyNode called without ndict")
            raise TypeError("IsyNode: called without ndict")

        if isinstance(isy, IsyUtil):
            self.isy = isy
            self.debug = isy.debug
        else :
            print("error : class IsyNode called without isyUtilClass")
            raise TypeError("IsyNode: isy is wrong class")
        # only update if not a scene

        if not self.isy.eventupdates :
            #update only nodes
            if "node-flag" in self._mydict :
                self.update()

	self._hash = node_id_to_int(self._mydict["address"])

        if self.debug & 0x01 :
            print("Init Node : \"" + self._mydict["address"] + \
                "\" : \"" + self._mydict["name"] + "\"")
            # self.isy._printdict(self.__dict__)


    # Special case from BaseClass due to ST/RR/OL props
    def _get_prop(self, prop):

        # print "IN get_prop ", prop

        if prop == "formatted" :
            prop = "ST"
            value = "formatted"
        else :
            value = "value"

        if prop in self._propalias :
            prop = self._propalias[prop]

        if not prop in self._getlist :
            raise IsyPropertyError("no property Attribute " + prop)

        # check if we have a property

        if prop in ['ST', 'OL', 'RR'] :
            # Scene's do not have property values

            if prop in self._mydict["property"] :
                # print self._mydict["property"]
                # print "prop value", prop, value
                return self._mydict["property"][prop][value]
            else :
                return None

#            if self._mydict["property"]["time"] == 0 :
#                    self.update()
#            elif self.isy.cachetime :
#                if time.gmtime() < (self.cachetime + self._mydict["property"]["time"] ) :
#                    self.update()

        else :

            if prop in self._mydict :
		if prop in self._boollist :
		    return(val2bool(self._mydict[prop])) 
		else :
		    return self._mydict[prop]
            else :
                return None

    def _set_prop(self, prop, new_value):
        """  generic property set """
        # print "IN set_prop ", prop, new_value
        if self.debug & 0x04 :
            print("_set_prop ", prop, " : ", new_value)

        if prop in self._propalias :
            prop = self._propalias[prop]

        if not prop in self._setlist :
	    if prop == "ST" :
		self.on(new_value)
		return
	    else :
		raise IsyPropertyError("_set_prop : " \
		    "Invalid property Attribute " + prop)

        if prop in ['OL', 'RR'] :
            if not str(new_value).isdigit :
                TypeError("Set Property : Bad Value : node=%s prop=%s val=%s" %
                            self._mydict["address"], prop, str(new_value))


	    self.isy._node_set_prop(self._mydict["address"], prop, str(new_value))

            self._mydict["property"]["time"] = 0

            if prop in self._mydict["property"] :
                # if isinstance(new_value, (int, float))  : # already checked with isdigit
		self._mydict["property"][prop]["value"] = new_value

        # we need to tie this to some action
        elif prop in self._mydict :
            # self._mydict[prop] = new_value
            pass
        else :
            #print "_set_prop AttributeError"
            raise AttributeError("no Attribute " + prop)

    # ramprate property
    # obj mathod for getting/setting a Node's value
    # sets how fast a light fades on.
    def get_rr(self):
        """ Get/Set RampRate property of Node """
        return self._get_prop("RR")

    def set_rr(self, new_value):
        """ Get/Set RampRate property of Node """
        return self._set_prop("RR", new_value)

    ramprate = property(get_rr, set_rr)

    # On Level property
    # obj mathod for getting/setting a Node's value
    # where in most cases light is how bright the light is
    # when turned on
    def get_ol(self):
        """ Get/Set On Level property of Node """
        return self._get_prop("OL")

    def set_ol(self, new_value):
        """ Get/Set On Level property of Node """
        return self._set_prop("OL", new_value)
    onlevel = property(get_ol, set_ol)


#    def get_fm(self):
#       """ property On Level Value of Node """
#        return self._get_prop("formatted")
#    formatted = property(get_fm)

    # status property
    # obj mathod for getting/setting a Node's value
    # where in most cases light is how bright the light is
    def get_status(self):
        """ Get/Set Status property of Node """
        return self._get_prop("ST")
    def set_status(self, new_value):
        """ Get/Set Status property of Node """
        return self.on(new_value)
    status = property(get_status, set_status)


    #
    # readonly to node attribute
    #


#    def on(self) :
#        self.isy._node_comm(self._mydict["address"], "DON")
#       #if "property" in self._mydict :
#        #    self._mydict["property"]["time"] = 0
#        # self.update()
#
#    def off(self) :
#        self.isy._node_comm(self._mydict["address"], "DOF")
#       if "property" in self._mydict :
#            self._mydict["property"]["time"] = 0
#           if "ST" in  self._mydict["property"] :
#               self._mydict["property"]["ST"]["value"] = 0
#               self._mydict["property"]["ST"]["formatted"] = "off"
#
#    def beep(self) :
#        self.isy._node_comm(self._mydict["address"], "BEEP")

    #
    #
    #
    def update(self) :
        """ force object to manualy update it's propertys """
        xurl = "/rest/nodes/" + self._mydict["address"]
        if self.debug & 0x01 :
            print("_updatenode pre _getXML")
        _nodestat = self.isy._getXMLetree(xurl)
        # del self._mydict["property"]["ST"]
        for prop in _nodestat.iter('property'):
            tprop = dict()
            for k, v in list(prop.items()) :
                tprop[k] = v
            if "id" in tprop :
                self._mydict["property"][tprop["id"]] = tprop
        # self._mydict["property"]["time"] = time.gmtime()

    # experimental
    def __bool__(self) :
        #print "__nonzero__ call", self._mydict["property"]["ST"]["value"], \
        #        " :: ", int(self._mydict["property"]["ST"]["value"])
        return(bool(self._mydict["property"]["ST"]["value"]) > 0)

    # use the node address as the hash value
    def __hash__(self) :
	return( self._hash )


#    def __str__(self):
#       print "__str__ call"
#       return("my str : " + self._mydict["name"])

    def __float__(self):
        # print "__float__ call"
        return float(int(self._mydict["property"]["ST"]["value"]) / float(255))

class IsyScene(_IsyNodeBase):
    """ Node Folder Class for ISY

        writeonly attributes :
            status

        readonly attributes :
            address
            name
            flag
            deviceGroup
            parent
            parent-type
            ELK_ID
    """
    _getlist = ['address', 'name', "ELK_ID", "deviceGroup",
                'flag', 'parent', 'parent-type']
    _setlist = []
    _propalias = {'id': 'address', 'addr': 'address',
                    "group-flag": "flag"}

    # status property
    # obj mathod for getting/setting a  Scene's value
    # where in most cases light is how bright the light is
    def set_status(self, new_value):
        """ set status value of Scene """
        return self._set_prop("ST", new_value)

    status = property(None, set_status)

    def _gettype(self):
        return "scene"
    type = property(_gettype)

    def _getmembers(self) :
        """ List members of a scene or group """
        if "members" in self._mydict :
            return self._mydict["members"].keys()
        else :
            return None
    members = property(_getmembers)

    def member_list(self) :
        return self._getmembers()

    def is_member(self, obj) :
        if "members" in self._mydict :
            if isinstance(obj, str)  :
                return obj in self._mydict["members"]
            elif isinstance(obj, _IsyNodeBase)  :
                return obj._get_prop("address") in self._mydict["members"]
        return False

    def member_iter(self, flag=0):
        if "members" in self._mydict :
            for k in list(self._mydict["members"].keys()) :
                if flag and not(flag & self._mydict["members"][k]) :
                    continue
                else :
                    yield k

    def __iter__(self):
        return self.member_iter()

    # check if scene _contains_ node
    def __contains__(self, other):
            return self.is_member(other)



class IsyNodeFolder(_IsyNodeBase):
    """ Node Folder Class for ISY

        readonly attributes :
            address
            name
            flag
    """
    _getlist = ['address', 'name', 'flag']
    _setlist = []
    _propalias = {'id': 'address', 'addr': 'address', "folder-flag": "flag"}

    def _gettype(self):
        return "folder"
    type = property(_gettype)

    def __iter__(self):
        return self.member_iter()

    def __contains__(self, other):
        pass

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")
    exit(0)
