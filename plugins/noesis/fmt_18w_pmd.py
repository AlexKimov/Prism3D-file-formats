from inc_noesis import *
import os.path
import os


def registerNoesisTypes():
    handle = noesis.register( "18 Wheels of Steel 3D model", ".pmd")

    noesis.setHandlerTypeCheck(handle, steelWheelsModelCheckType)
    noesis.setHandlerLoadModel(handle, steelWheelsModelLoadModel)
        
    return 1 
    
    
class Vector3F:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        
    def read(self, reader):
        self.x, self.y, self.z = noeUnpack('3f', reader.readBytes(12)) 
        
    def getStorage(self):
        return (self.x, self.y, self.z)     


class Vector4F:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.w = 0  
        
    def read(self, reader):
        self.x, self.y, self.z, self.w = noeUnpack('4f', reader.readBytes(16))
        
    def getStorage(self):
        return (self.x, self.y, self.z, self.w)      
    

class Vector2F:
    def __init__(self):
        self.x = 0
        self.y = 0
        
    def read(self, reader):
        self.x, self.y = noeUnpack('2f', reader.readBytes(8))
 
    def getStorage(self):
        return (self.x, self.y) 
  

class Vector3UI16:
    def read(self, reader):
        self.x = reader.readShort()
        self.y = reader.readShort()
        self.z = reader.readShort()
        
    def getStorage(self):
        return (self.x, self.y, self.z)  
  
        
class SteelWheelsModelHeader:
    def __init__(self):
        self.faceCount = 0
        self.vertexCount = 0
        self.name = ""
        
    def read(self, reader):
        reader.seek(4, NOESEEK_REL)
        self.name = reader.readBytes(16).decode("ascii").rstrip('\0')
        self.faceCount = reader.readUInt()                  
        self.vertexCount = reader.readUInt()                  
        reader.seek(16, NOESEEK_REL)


class SteelWheelsModelObject:
    def __init__(self, header):
        self.header = header
        self.vertexCoordinates = []      
        self.uvCoordinates = []        
        self.faceIndexes = [] 
        
    def read(self, reader):
        for i in range(self.header.faceCount):                
            indexes = Vector3UI16()
            indexes.read(reader)
            
            self.faceIndexes.append(indexes) 
        
        reader.seek(self.header.faceCount * 2, NOESEEK_REL)
        
        for i in range(self.header.vertexCount):                
            coords = Vector3F()
            coords.read(reader)
            
            self.vertexCoordinates.append(coords)
        
        for i in range(self.header.vertexCount):             
            uv = Vector2F()
            uv.read(reader)
            self.uvCoordinates.append(uv)                                   
        
        
class SteelWheelsModel:
    def __init__(self, reader):
        self.reader = reader
        self.objectCount = 0
        self.omCount = 0
        self.headers = []
        self.objects = []
           
    def readHeader(self, reader):
        reader.seek(4, NOESEEK_REL)
        self.objHeaderCount = reader.readUInt()    
        self.objectCount = reader.readUInt()
        reader.seek(4, NOESEEK_REL)
        
    def readObjectTable(self, reader):
        for i in range(self.objHeaderCount):            
            header = SteelWheelsModelHeader()
            header.read(reader)
            
            self.headers.append(locator)             
            
    def readObjectData(self, reader):
        for i in range(self.objectCount):
            obj = SteelWheelsModelObject(self.headers[i])
            obj.read(reader)

            self.objects.append(obj)            
            
    def read(self):
        self.readHeader(self.reader)
        reader.seek(36, NOESEEK_REL)
        self.readObjectTable(self.reader)
        reader.seek(12 + 32, NOESEEK_REL)              
        self.readObjectData(self.reader)

    
def steelWheelsModelCheckType(data):     
    
    return 1     
    

def steelWheelsModelLoadModel(data, mdlList):
    #noesis.logPopup()

    model = SteelWheelsModel(NoeBitStream(data))
    model.read()
 
    ctx = rapi.rpgCreateContext()
       
    #transMatrix = NoeMat43( ((-1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, 0)) ) 
    #rapi.rpgSetTransform(transMatrix)      
    
    materials = []
    textures = [] 
    
    textureName = "worker.png" 
    texture = rapi.loadExternalTex(textureName)

    if texture == None:
        texture = NoeTexture(textureName, 0, 0, bytearray())

    textures.append(texture)            
    material = NoeMaterial(textureName, textureName)
    material.setFlags(noesis.NMATFLAG_TWOSIDED, 1)
    materials.append(material)    
     
    for obj in model.objects:   
        rapi.rpgSetMaterial(textureName)        
        rapi.rpgSetName(obj.headers[model.objects.index(obj)].name)

        for indexes in obj.faceIndexes:               
            rapi.immBegin(noesis.RPGEO_TRIANGLE)
        
            for index in indexes.getStorage():         
                rapi.immUV2(obj.uvCoordinates[index].getStorage())         
                rapi.immVertex3(obj.vertexCoordinates[index].getStorage()) 
                   
            rapi.immEnd()                

    mdl = rapi.rpgConstructModelSlim()
    mdl.setModelMaterials(NoeModelMaterials(textures, materials)) 
        
    mdlList.append(mdl)        
            
    return 1
 