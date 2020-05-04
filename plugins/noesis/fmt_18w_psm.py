from inc_noesis import *
import os.path
import os


def registerNoesisTypes():
    handle = noesis.register( "Prism engine (18 Wheels of Steel / Hunting Unlimited) 3D model", ".psm")

    noesis.setHandlerTypeCheck(handle, prism3DModelCheckType)
    noesis.setHandlerLoadModel(handle, prism3DModelLoadModel)
        
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


class Prism3DModelMatrix:
    def __init__(self):
        self.rot1 = Vector4F()
        self.pos1 = Vector3F()
        self.pos2 = Vector3F()
        self.rot2 = Vector4F()
        self.transMatrix = None
        
    def read(self, reader):       
        self.rot1.read(reader) 
        self.pos1.read(reader)   
        self.pos2.read(reader)
        self.rot2.read(reader)  
            
    def getTransMat(self, rot, pos):
        rotQuat = NoeQuat(rot.getStorage())
        transMatrix = rotQuat.toMat43()
        transMatrix[3] = pos.getStorage()

        return transMatrix 

    def getMat1(self):        
        return self.getTransMat(self.rot1, self.pos1)
        
    def getMat2(self):        
        return self.getTransMat(self.rot2, self.pos2)
        
        
class Prism3DModelLocator:
    def __init__(self):
        self.matrixes = []
        self.indexes = []
        self.weights = [] 
        self.names = None        
        
    def read(self, reader):
        count = reader.readUInt()
        for i in range(count):
            matrix = Prism3DModelMatrix()
            matrix.read(reader)            
            self.matrixes.append(matrix)

        self.indexes.extend(noeUnpack('{}b'.format(count), reader.readBytes(count)))
        self.weights.extend(noeUnpack('{}f'.format(count), reader.readBytes(4 * count)))  
        buffer = [reader.readBytes(16) for i in range(count)]
        self.names = [name.decode("ascii").rstrip('\0') for name in buffer]


class Prism3DModelObject:
    def __init__(self, version=6):
        self.version = version
        self.name = ""
        self.faceCount = 0        
        self.vertexCount = 0        
        self.matrixIndex = 0        
        self.vertexCount = 0
        self.vertexCoordinates = []      
        self.uvCoordinates = []      
        self.normals = []   
        self.faceIndexes = [] 
        self.faceIndexes2 = [] 
        
    def read(self, reader):
        self.name = reader.readBytes(16).decode("ascii").rstrip('\0')
        self.faceCount = reader.readUInt()                  
        self.vertexCount = reader.readUInt()                  
        self.matrixIndex = reader.readUInt() 
        
        self.unkn1 = reader.readUInt() 
        self.unkn2 = reader.readUInt() 
        
        reader.seek(16, NOESEEK_REL)
        
        for i in range(self.vertexCount):                
            coords = Vector3F()
            coords.read(reader)
            self.vertexCoordinates.append(coords)
        
        reader.seek(self.vertexCount * self.unkn2, NOESEEK_REL)       
        reader.seek(4 * self.vertexCount  * self.unkn2, NOESEEK_REL)
        
        for i in range(self.vertexCount):    
            normal = Vector3F()
            normal.read(reader)
            self.normals.append(normal) 
            
        if self.unkn1 == 3:  
            reader.seek(4 * self.vertexCount, NOESEEK_REL)
            
        for i in range(self.vertexCount):             
            uv = Vector2F()
            uv.read(reader)
            self.uvCoordinates.append(uv)                            
            
        for i in range(self.faceCount):                
            indexes = Vector3UI16()
            indexes.read(reader)
            
            self.faceIndexes.append(indexes)            
        
        if self.version > 3:        
            for i in range(self.faceCount):                
                index = reader.readUShort()
            
                self.faceIndexes2.append(index)         
        
        
class Prism3DModel:
    def __init__(self, reader):
        self.reader = reader
        self.version = 0
        self.objectCount = 0
        self.omCount = 0
        self.locators = []
        self.objects = []
           
    def readHeader(self, reader):
        self.version = reader.readUInt()
        self.omCount = reader.readUInt()    
        self.objectCount = reader.readUInt()
        if self.version > 3:
            reader.seek(4, NOESEEK_REL)
        
    def readLocators(self, reader):
        for i in range(self.omCount):            
            locator = Prism3DModelLocator()
            locator.read(reader)
            
            self.locators.append(locator)             
            
    def readObjects(self, reader):
        for i in range(self.objectCount):
            obj = Prism3DModelObject(self.version)
            obj.read(reader)

            self.objects.append(obj)            
            
    def read(self):
        self.readHeader(self.reader)
        self.readLocators(self.reader) 
        self.readObjects(self.reader)

    
def prism3DModelCheckType(data):     
    
    return 1     
    

def prism3DModelLoadModel(data, mdlList):
    #noesis.logPopup()

    model = Prism3DModel(NoeBitStream(data))
    model.read()
 
    ctx = rapi.rpgCreateContext()
       
    transMatrix = NoeMat43( ((-1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, 0)) ) 
    rapi.rpgSetTransform(transMatrix)      
    
    materials = []
    textures = [] 
    
    textureName = "rocketcar.jpg" 
    texture = rapi.loadExternalTex(textureName)

    if texture == None:
        texture = NoeTexture(textureName, 0, 0, bytearray())

    textures.append(texture)            
    material = NoeMaterial(textureName, textureName)
    material.setFlags(noesis.NMATFLAG_TWOSIDED, 1)
    materials.append(material)    
     
    for obj in model.objects:   
        if obj.name.startswith('glass'): 
            rapi.rpgSetMaterial('glass')
        elif obj.name.startswith('rpm'):
            rapi.rpgSetMaterial('rpm') 
        elif obj.name.startswith('mph'):
            rapi.rpgSetMaterial('mph')         
        else: 
            rapi.rpgSetMaterial(textureName)        
        rapi.rpgSetName(obj.name)

        for indexes in obj.faceIndexes:               
            rapi.immBegin(noesis.RPGEO_TRIANGLE)
        
            for index in indexes.getStorage():
                rapi.immNormal3(obj.normals[index].getStorage())          
                rapi.immUV2(obj.uvCoordinates[index].getStorage())         
                rapi.immVertex3(obj.vertexCoordinates[index].getStorage()) 
                   
            rapi.immEnd() 

    bones = []
    
    # skeleton    
    for locator in model.locators:
        if locator.names[0].startswith('Bip01'):
            index = 0

            for matrix in locator.matrixes:        
                if locator.indexes[index] >= 0:
                    matrix.transMatrix = matrix.getMat1() * locator.matrixes[locator.indexes[index]].transMatrix                      
                else:         
                    matrix.transMatrix = matrix.getMat1()

                boneName = locator.names[index]
                boneParentName = locator.names[locator.indexes[index]]
                if locator.indexes[index] < 0:
                    boneParentName = ""
                
                bones.append(NoeBone(index, boneName, matrix.transMatrix, boneParentName))
                     
                index += 1                

    mdl = rapi.rpgConstructModelSlim()
    mdl.setBones(bones)
    mdl.setModelMaterials(NoeModelMaterials(textures, materials)) 
        
    mdlList.append(mdl)        
            
    return 1
 