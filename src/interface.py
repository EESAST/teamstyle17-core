import json,gamemain,queue

class Interface:

    def __init__(self):
        self.game=None
        self.queue=queue.Queue

    def newGame(self):
        self.game=gamemain.GameMain()

    def setInstruction(self,instruction:str):
        command=json.loads(instruction)

    def getField(self,instruction:str):
        command=json.loads(instruction)

    def nextTick(self):
        self.game.update()