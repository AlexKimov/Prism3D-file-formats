from inc_noesis import *
import os.path
import os


def registerNoesisTypes():
    handle = noesis.register( "18 Wheels of Steel 3D model", ".gdt")

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


class SteelWheelsModelPolygon:
    def __init__(self):
        self.type = 0        
        self.faceCount = 0        
        self.vertexCount = 0        
        self.vertexCoordinates = []      
        self.uvCoordinates = []      
        self.faceIndexes = [] 
        
    def read(self, reader):
        self.type = reader.readUInt()  
        
        reader.seek(24, NOESEEK_REL)  
                        
        self.vertexCount = reader.readUShort()                  
        self.faceCount = reader.readUShort()          
        
        for i in range(self.faceCount // 3):                
            indexes = Vector3UI16()
            indexes.read(reader)
            
            self.faceIndexes.append(indexes)        
        
        for i in range(self.vertexCount):                
            coords = Vector3F()
            coords.read(reader)
            
            self.vertexCoordinates.append(coords) 
          
        reader.seek(self.vertexCount * 4, NOESEEK_REL) 
          
        if self.type == 349:  
            for i in range(self.vertexCount):             
                uv = Vector2F()
                uv.read(reader)
            
                self.uvCoordinates.append(uv)
                
            reader.seek(16, NOESEEK_REL) 
        else:
            for i in range(self.vertexCount):
                reader.seek(12, NOESEEK_REL) 
            
                uv = Vector2F()
                uv.read(reader)     
                
                self.uvCoordinates.append(uv)      
        reader.seek(2, NOESEEK_REL)   
        
        
class SteelWheelsModel:
    def __init__(self, reader):
        self.reader = reader
        self.polygons = []
           
    def readHeader(self, reader):
        reader.seek(8, NOESEEK_REL)
        self.polygonCount = reader.readUInt()        
            
    def readObjects(self, reader):
        for i in range(self.polygonCount):
            poly = SteelWheelsModelPolygon()
            poly.read(reader)

            self.polygons.append(poly)            
            
    def read(self):
        self.readHeader(self.reader)
        self.readObjects(self.reader)

    
def steelWheelsModelCheckType(data):     
    
    return 1     
    

def steelWheelsModelLoadModel(data, mdlList):
    #noesis.logPopup()

    model = SteelWheelsModel(NoeBitStream(data))
    model.read()
 
    ctx = rapi.rpgCreateContext()

    for polygon in model.polygons:   
        for indexes in polygon.faceIndexes:               
            rapi.immBegin(noesis.RPGEO_TRIANGLE)
        
            for index in indexes.getStorage():       
                rapi.immUV2(polygon.uvCoordinates[index].getStorage())         
                rapi.immVertex3(polygon.vertexCoordinates[index].getStorage()) 
                   
            rapi.immEnd() 


    mdl = rapi.rpgConstructModelSlim()
        
    mdlList.append(mdl)        
            
    return 1
 