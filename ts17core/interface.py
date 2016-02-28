import json
import copy
from ts17core import gamemain


class Interface:
    def __init__(self, callback):
        self.game = None
        self.callback = callback

    def setInstruction(self, instruction: str):
        command = json.loads(instruction)
        if command["action"] == "init":
            self.game = gamemain.GameMain(command["seed"],command["player"],self.callback)
        if command["action"] == "move":
            self.game.setVelocity(command["ai_id"], (command["x"], command["y"], command["z"]))
        if command["action"] == "use_skill":
            if command["skill_type"]=="teleport":
                self.game.castSkill(command["ai_id"], "teleport", dst=(command["x"],command["y"],command["z"]))
            elif command["skill_type"]=="longAttack":
                self.game.castSkill(command["ai_id"],"longAttack",player=command["target"])
            else:
                self.game.castSkill(command["ai_id"], command["skill_type"])
        if command["action"] == "upgrade_skill":
            self.game.upgradeSkill(command["ai_id"], command["skill_type"])

    def getInstruction(self, instruction: str):
        command = json.loads(instruction)
        if command["action"] == "query_map":
            return self.game.getFieldJson(command["ai_id"])
        if command["action"] == "query_status":
            return self.game.getStatusJson()

    def nextTick(self):
        self.game.update()

    def getGameObject(self):
        return copy.copy(self.game)

    def setGameObject(self, gameObject):
        self.game=gameObject
        self.game._callback=self.callback