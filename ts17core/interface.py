import json
import copy
from ts17core import gamemain


class Interface:
    def __init__(self, callback):
        self.game = None
        self.callback = callback

    def setInstruction(self, instruction: str):
        command = json.loads(instruction)
        if command["action"] != "init" and not self.game.isBelong(command["id"], command["ai_id"]):
            raise ValueError('Player %d does not belong to AI %d' % (command["id"], command["ai_id"]))
        if command["action"] == "init":
            self.game = gamemain.GameMain(command["seed"], command["player"], self.callback)
        elif command["action"] == "move":
            self.game.setSpeed(command["id"], (command["x"], command["y"], command["z"]))
        elif command["action"] == "use_skill":
            if command["skill_type"] == "longAttack":
                self.game.castSkill(command["id"], "longAttack", player=command["target"])
            else:
                self.game.castSkill(command["id"], command["skill_type"])
        elif command["action"] == "upgrade_skill":
            self.game.upgradeSkill(command["id"], command["skill_type"])
        else:
            raise ValueError('No such action: %s' % command["action"])

    def getInstruction(self, instruction: str):
        command = json.loads(instruction)
        if command["action"] == "query_map":
            return self.game.getFieldJson(command["ai_id"])
        elif command["action"] == "query_status":
            return self.game.getStatusJson(command["ai_id"])
        else:
            raise ValueError('No such action: %s' % command["action"])

    def nextTick(self):
        self.game.update()

    def getGameObject(self):
        return copy.deepcopy(self.game)

    def setGameObject(self, gameObject):
        self.game = gameObject
        self.game._callback = self.callback
