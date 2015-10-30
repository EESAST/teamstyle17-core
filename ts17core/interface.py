import json
from ts17core import gamemain


class Interface:
    def __init__(self):
        self.game = None

    def setInstruction(self, instruction: str):
        command = json.loads(instruction)
        if command["action"] == "init":
            self.game = gamemain.GameMain(command["seed"])
        if command["action"] == "move":
            self.game.setVelocity(command["ai_id"], (command["x"], command["y"], command["z"]))
        if command["action"] == "use_skill":
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
