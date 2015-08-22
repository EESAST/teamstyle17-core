from enum import Enum

Skill=Enum("Skill",("DistantAttack","CloseAttack","Shield","VisionUp","HealthUp"))
SkillAction=Enum("SkillAction",("Cast","Buy"))
SphereType=Enum("SphereType",("Player","Prey","Treasure","Target","Stingball"))

class Instruction(object):

    def __init__(self,player,sphere):
        self.player=player
        self.sphere=sphere

    def getInfo(self):
        return (self.player,self.sphere)

class MoveInstruction(Instruction):

    def __init__(self,player,sphere):
        super().__init__(player,sphere)
        self.velocity=[0,0,0]

class SkillInstruction(Instruction):

    def __init__(self,player,sphere,skill,action):
        super().__init__(player,sphere)
        self.skill=skill
        self.action=action

class Sphere(object):

    def __init__(self,pos,radius,type):
        self.pos=pos
        self.radius=radius
        self.type=type #SphereType

class Field(object):

    def __init__(self,center,size):
        self.objectList=[] #List of Sphere
        self.center=center
        self.size=size

class SphereStatus(object):

    def __init__(self,sphere,hp=0):
        self.sphere=sphere
        self.hp=hp
        self.skillLevelList={}

class PlayerStatus(object):

    def __init__(self):
        self.sphereList=[] #List of SphereStatus

class GameInterface(object):

    def __init__(self,gameServer=None):
        self.__server=gameServer

    def setInstruction(self,instruction:Instruction):
        pass

    def getVisionField(self,player,sphere):
        pass

    def getPlayerStatus(self,player):
        pass
