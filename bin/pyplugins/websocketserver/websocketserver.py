import math
import random
import json
import socket #just for exception handling for restarts here

import sys
sys.path.append('/usr/lib/pymodules/python2.7/') #wtf
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/gevent-0.13.6-py2.7-linux-x86_64.egg') #dum-di-dum..
sys.path.append('/usr/local/lib/python2.7/dist-packages/greenlet-0.3.1-py2.7-linux-i686.egg')
sys.path.append('/usr/local/lib/python2.7/dist-packages/ws4py-0.1.6-py2.7.egg')
import ws4py.server.geventserver


from PythonQt.QtGui import QVector3D as Vec3
from PythonQt.QtGui import QQuaternion as Quat

import tundra

clients = set()
connections = dict()

scene = None

def log(s):
    print "WebsocketServer:", s

def newclient(connectionid):
    if scene is not None:
        tundra.Server().UserConnected(connectionid, 0, 0)
        avent = scene.GetEntityByNameRaw("Avatar" + str(connectionid))
        return avent.id

    else:
        tundra.LogWarning("Websocket server got a client connection, but has no scene - what to do?")

def removeclient(connectionid):
    tundra.Server().UserDisconnected(connectionid, 0)

def on_sceneadded(name):
    '''Connects to various signal when scene is added'''
    global scene
    sceneapi = tundra.Scene()
    scene = sceneapi.GetScene(name).get() #*Raw
    print "Using scene:", scene.name, scene

    assert scene.connect("AttributeChanged(IComponent*, IAttribute*, AttributeChange::Type)", onAttributeChanged)
    assert scene.connect("EntityCreated(Entity*, AttributeChange::Type)", onNewEntity)

    assert scene.connect("ComponentAdded(Entity*, IComponent*, AttributeChange::Type)", onComponentAdded)

    assert scene.connect("EntityRemoved(Entity*, AttributeChange::Type)", onEntityRemoved)

    
def update(t):
    if server is not None:
        #server.next()
        server._stopped_event.wait(timeout=0.001)
        #print '.',

#def on_exit(self):
        # Need to figure something out what to do and how

def sendAll(data):
    for client in clients:
        try:
            client.send(json.dumps(data))
        except socket.error:
            pass #client has been disconnected, will be noted later & disconnected by another part

def onAttributeChanged(component, attribute, changeType):
    #FIXME Only syncs hard coded ec_placeable
    #Maybe get attribute or something
    
    #FIXME Find a better way to get component name
    component_name = str(component).split()[0]

    #Let's only sync EC_Placeable
    if component_name != "EC_Placeable":
        return

    entity = component.ParentEntity()
    
    # Don't sync local stuff
    if entity.IsLocal():
        return

    ent_id = entity.id

    data = component.GetAttributeQVariant('Transform')
    transform = list()

    transform.extend([data.position().x(), data.position().y(), data.position().z()])
    transform.extend([data.rotation().x(), data.rotation().y(), data.rotation().z()])
    transform.extend([data.scale().x(), data.scale().y(), data.scale().z()])

    sendAll(['setAttr', {'id': ent_id, 
                         'component': component_name,
                         'Transform': transform}])

def onNewEntity(entity, changeType):
    sendAll(['addEntity', {'id': entity.id}])
    print entity

def onComponentAdded(entity, component, changeType):
    #FIXME Find a better way to get component name
    component_name = str(component).split()[0]

    # Just sync EC_Placeable and EC_Mesh since they are currently the
    # only ones that are used in the client
    if component_name not in ["EC_Placeable", "EC_Mesh"]:
        return

    if component_name == "EC_Mesh":
        sendAll(['addComponent', {'id': entity.id, 'component': component_name, 'url': 'ankka.dae'}])

    else: #must be pleaceable
        data = component.transform
        transform = list()

        transform.extend([data.position().x(), data.position().y(), data.position().z()])
        transform.extend([data.rotation().x(), data.rotation().y(), data.rotation().z()])
        transform.extend([data.scale().x(), data.scale().y(), data.scale().z()])

        sendAll(['addComponent', {'id': entity.id, 
                             'component': component_name,
                             'Transform': transform}])

    print entity.id, component

def onEntityRemoved(entity, changeType):
    print "Removing", entity
    sendAll(['removeEntity', {'id': entity.id}])

def handle_clients(ws, env):
    print 'START', ws
    clients.add(ws)
    
    # Don't do this! Figure out a way to fake a kNet connection or
    # something.
    connectionid = random.randint(1000, 10000)
    
    while True:
        # "main loop" for the server. When your done with the
        # connection break from the loop. It is important to remove
        # the socket from clients set

        try:
            msg = ws.receive(msg_obj=True)
        except socket.error, e:
            #if there is an error we simply quit by exiting the
            #handler. Eventlet should close the socket etc.
            print "Socket error:", e
            break

        if msg is None:
            # if there is no message the client will Quit
            log("msg is None - client has disconnected.")
            break

        try:
            function, params = json.loads(str(msg.data))
        except ValueError, error:
            print "JSON parse error:", error
            continue

        if function == 'CONNECTED':
            ws.send(json.dumps(['initGraffa', {}]))

            myid = newclient(connectionid)
            connections[myid] = connectionid
            ws.send(json.dumps(['setId', {'id': myid}]))
            
            if scene is not None:
                xml = scene.GetSceneXML(True, False) #temporary yes, locals no
                ws.send(json.dumps(['loadScene', {'xml': str(xml)}]))
            else:
                tundra.LogWarning("Websocket Server: handling a client, but doesn't have scene :o")

        elif function == 'Action':
            action = params.get('action')
            args = params.get('params')
            id = params.get('id')

            if scene is not None:
                av = scene.GetEntityByNameRaw("Avatar%s" % connections[id])
                av.Exec(1, action, args)
            else:
                tundra.LogError("Websocket Server: received entity action, but doesn't have scene :o")
                
        elif function == 'reboot':
            break

    # Remove connection
    clients.remove(ws)
    removeclient(connectionid)

    print 'END', ws

if tundra.Server().IsAboutToStart():
    server = ws4py.server.geventserver.WebSocketServer(('0.0.0.0', 9999), handle_clients)
    server.start()
    print "websocket server started."

    assert tundra.Frame().connect("Updated(float)", update)

    sceneapi = tundra.Scene()
    print "Websocket Server connecting to OnSceneAdded:", sceneapi.connect("SceneAdded(QString)", on_sceneadded)
    #on_sceneadded("TundraServer")
