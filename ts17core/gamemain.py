from ts17core import scene, myrand
import json
import math


class PlayerStatus:
    def __init__(self):
        # 拥有该物体的AI的ID
        self.aiId = 0
        # 血量
        self.health = 0
        # 速度矢量
        self.speed = (0, 0, 0)
        # 能力值，购买技能用
        self.ability = 0
        # 视野半径
        self.vision = 0
        # 技能列表，应以“技能名:技能等级”形式保存
        self.skills = {}
        # 技能冷却时间，以“技能名：剩余冷却时间”保存,每回合结束后-1
        self.skillsCD = {}
        # 护盾剩余时间,每回合结束后-1
        self.shieldTime = 0
        # 护盾等级（考虑到技能特殊效果触发的护盾等级与技能等级不符而设置）
        self.shieldLevel = 0
        # 最近一次使用瞬间移动后经过的时间（为瞬移满级效果设定）
        self.teleportTime = 0
        # 不可移动时间
        self.stopTime = 0
        # 历史最大血量
        self.maxHealth = self.health

    def max_health(self):
        if self.health > self.maxHealth:
            self.maxHealth = self.health


# 物体包括：食物（food）、营养源（nutrient）、刺球（spike）、目标生物（target）、远程子弹（bullet）
class ObjectStatus:
    def __init__(self, objtype="food"):
        # 物体类型，以小写英文单词字符串表示
        # bullet为远程攻击的点状物体，target目标生物,生命值暂且按10000算
        self.type = objtype


class BulletStatus():
    def __init__(self, damage: int, enemy: int, speed: int, owner: int, stop: bool):
        self.type = "bullet"
        self.damage = damage
        self.enemy = enemy
        self.owner = owner
        self.stop = stop
        self.speed = speed


class CastSkillInfo():
    def __init__(self, name):
        self.name = name


class CastTeleportInfo():
    def __init__(self, tdst):
        self.name = "teleport"
        self.dst = tdst


class CastLongAttackInfo():
    def __init__(self, tplayer):
        self.name = "longAttack"
        self.player = tplayer


class GameMain:
    def __init__(self, seed, player_num, callback):
        # 游戏结束标志
        self._gameEnd = False
        # 地图大小（地图三维坐标的范围均为[0,_mapSize]）
        self._mapSize = 100000
        # 当前时刻，以tick为单位，是非负整数
        self._time = 0
        # 保存玩家信息，应以“玩家ID:PlayerStatus”形式保存
        self._players = {}
        # 保存其他物体（不含玩家）的信息，应以“物体ID:物体信息”形式保存，物体信息的类型和格式可自行规定
        self._objects = {}
        # 用于自动向平台发回变化信息的回调函数，调用时以一个json字符串为参数
        self._callback = callback
        # 场景管理器，物体和玩家的位置、大小的信息记录在这里面。详情参考scene.py中的注释
        self._scene = scene.Octree(self._mapSize)
        # 存储该回合内施放了但未结算的技能，以“玩家ID:技能名”形式保存，每回合应清空一次
        self._castSkills = {}
        # 随机数生成器，所有随机事件必须从这里获取随机数
        self._rand = myrand.MyRand(seed)
        # 技能基础价格
        self._skillPrice = {'longAttack': 1, 'shortAttack': 1, 'shield': 2, 'teleport': 2, 'visionUp': 2, 'healthUp': 1}
        # 食物编号
        self._foodCount = 0
        # 营养源刷新剩余时间
        self._nutrientFlushTime = 0
        # 营养源刷新位置
        self._nutrientFlushPos = [tuple(self._mapSize // 2 for _ in range(3))]
        # 记录变化情况的json的list，每项为一个json object
        self._changeList = []
        # 记录发生变化的玩家集合，在更新结束时发送这些玩家的变化
        self._changedPlayer = set()
        # 增加玩家
        self.addNewPlayer(0, tuple(self._mapSize // 2 for _ in range(3)), 20)
        pos1 = tuple(self._rand.randIn(self._mapSize) for _ in range(3))
        pos2 = tuple(self._mapSize - pos1[x] for x in range(3))
        self.addNewPlayer(1, pos1, 10)
        self.addNewPlayer(2, pos2, 10)

    # player位置获取
    def playerPos(self, ID):
        return self._scene.getObject(ID).center

    # 添加新玩家
    def addNewPlayer(self, playerID: int, pos: tuple, radius: int):
        player = scene.Sphere(pos, radius)
        self._scene.insert(player, playerID)
        newStatus = PlayerStatus()
        newStatus.health = radius ** 3
        self._players[playerID] = newStatus

    def makeChangeJson(self, id: int, ai_id: int, pos: tuple, r: int):
        if self._objects.get(id) is not None:
            objType = self._objects[id].type
        elif self._players.get(id) is not None:
            objType = "player"
        else:
            objType = None
        return '{"info":"object","time":%d,"id":%d,"ai_id":%d,"type":%s,"pos":[%d,%d,%d],"r":%d}' \
               % (self._time, id, ai_id, objType, pos[0], pos[1], pos[2], r)

    def makeDeleteJson(self, id: int):
        return '{"info":"delete","time":%d,"id":%d}' % (self._time, id)

    # 若target为None则没有目标物体，pos为None则没有目标坐标
    def makeSkillCastJson(self, source: int, skillType: str, target, pos):
        if target is not None:
            targetStr = ',"target":%d' % target
        else:
            targetStr = ''
        if pos is not None:
            posStr = ',"x":%d,"y":%d,"z":%d' % pos
        else:
            posStr = ''
        return '{"info":"skill_cast","time":%d,"source":%d,"type":%s%s%s}' \
               % (self._time, source, skillType, targetStr, posStr)

    def makeSkillHitJson(self, skillType: str, target: int):
        return '{"info":"skill_hit","time":%d,"type":%s,"target":%d}' % (self._time, skillType, target)

    def makePlayerJson(self, playerId: int):
        status = self._players[playerId]
        skillList = ",".join('{"name":%s,"level":%d}' % pair for pair in status.skills.items())
        return '{"info":"player","time":%d,"id":%d,"ai_id":%d,"health":%d,"vision":%d,"ability":%d,"skills":[%s]}' \
               % (self._time, playerId, status.aiId, status.health, status.vision, status.ability, skillList)

    # 每回合调用一次，依次进行如下动作：
    # 相关辅助函数可自行编写
    def update(self):
        # 初始化返回给平台的变化信息的json List
        self._changeList = []
        self._changedPlayer = set()

        # 1、结算技能效果
        # TODO 远程攻击和瞬间移动的满级效果没有写
        for playerId in self._castSkills:
            skillInfo = self._castSkills[playerId]
            skillName = skillInfo.name
            if skillName == 'shortAttack':
                self.shortAttack(playerId)
            elif skillName == 'longAttack':
                self.longAttack(playerId, skillInfo.player)
            elif skillName == 'teleport':
                self.teleport(playerId, skillInfo.dst)
            elif skillName == 'shield':
                self.shield(playerId)

        self._castSkills.clear()

        # 2、移动所有物体（包括玩家，远程子弹，目标生物）
        # TODO 关于物体触碰边界可以作更为细致的处理
        for playerId in self._players.keys():
            if playerId == 0:
                x = self._rand.randIn(10)
                y = self._rand.randIn(10)
                z = self._rand.randIn(10)
                self.move(playerId, (x, y, z), self._scene.getObject(playerId).radius)
                continue
            if self._players[playerId].stopTime == 0:
                self.move(playerId, self._players[playerId].speed, self._scene.getObject(playerId).radius)
        for objId in self._objects.keys():
            if self._objects[objId].type == "bullet":
                if self.longAttackbullet(objId) == False:
                    self.move(objId, (0, 0, 0), 0, True)

        # 3、判断相交，结算吃、碰撞、被击中等各种效果
        for playerId in self._players.keys():
            if playerId == 0:
                continue
            sphere = self._scene.getObject(playerId)
            # 玩家AI可食用的物体对其产生效果，包括食用食饵、营养源、目标生物、以及其他玩家AI
            insideList = self._scene.intersect(sphere, True)
            eatableList = [objId for objId in insideList if 1.2 * self._scene.getObject(objId).radius < sphere.radius]
            for objId in eatableList:
                self._changeList.append(self.makeDeleteJson(objId))
                if self._players.get(objId) is not None:
                    if self._players[objId].shieldTime == 0 or (
                            self._players[objId].skills["shield"] < 4 and self._players[objId].shiledLevel < 4):
                        self.healthUp(playerId, self._players[objId].health)
                        self.gameEnd()
                    continue
                objType = self._objects[objId].type
                if objType == "food":
                    self.healthUp(playerId, 10)
                    self._scene.delete(objId)
                    self._objects.pop(objId)
                    self._foodCount -= 1
                elif objType == "nutrient":
                    self.healthUp(playerId, self._rand.rand() % 301 + 200)
                    self._players[playerId].ability += self._rand.rand() % 5 + 1
                    self._objects.pop(objId)
                    self._scene.delete(objId)
            # 玩家AI接触到的物体对其产生效果，包括受到刺球伤害及子弹伤害
            touchList = self._scene.intersect(sphere, False)
            for objId in touchList:
                if self._players.get(objId) is not None:
                    continue
                objType = self._objects[objId].type
                if objType == "spike":
                    if self._players[playerId].shieldTime == 0 or (
                            self._players[playerId].skills["shield"] < 5 and self._players[playerId].shieldLevel < 5):
                        damage = self._players[playerId].health // 3
                        self.healthDown(playerId, damage)
                        self._objects.pop(objId)
                        self._scene.delete(objId)
        # 认为目标生物ID为0，其只可能受到子弹伤害或被玩家食用
        target = self._scene.getObject(0)
        insideList = self._scene.intersect(target, True)
        eatableList = [objId for objId in insideList if 1.2 * self._scene.getObject(objId).radius < target.radius]
        for objId in eatableList:
            if self._objects[objId].type == "bullet":
                continue
            elif self._players.get(objId) is not None:
                self.healthUp(0, self._players[objId].health)
                self._scene.delete(objId)
                self._players.pop(objId)
                self.gameEnd()

        # 判断是否有球体生命值小于历史最大值四分之一，有则死亡
        for playerId in self._players:
            if playerId == 0:
                continue
            if self._players[playerId].health * 4 < self._players[playerId].maxHealth:
                self.gameEnd()

        # 4、随机产生新的食物等,暂且每回合10个食饵，且上限为1000个。每隔10-20回合刷新一个营养源;
        # 食饵ID为1000000+食物编号， 营养源ID为2000000+营养源位置编号
        foodPerTick = 10
        for _ in range(foodPerTick):
            center = tuple(self._rand.randIn(self._mapSize) for _ in range(3))
            food = scene.Sphere(center)
            foodId = 1000000 + self._foodCount
            self._objects[foodId] = ObjectStatus("food")
            self._scene.insert(food, foodId)
            self._foodCount += 1
            self._changeList.append(self.makeChangeJson(foodId, -2, center, 0))
            if self._foodCount > 1000:
                break

        if self._nutrientFlushTime == 0:
            pos = self._rand.randIn(len(self._nutrientFlushPos))
            nutrientId = int(2000000 + pos)
            time = 0
            while self._objects.get(nutrientId) is not None:
                pos = self._rand.randIn(len(self._nutrientFlushPos))
                nutrientId = int(2000000 + pos)
                time += 1
                if time > 10:
                    break
            if time <= 10:
                nutrient = scene.Sphere(self._nutrientFlushPos[pos])
                self._objects[nutrientId] = ObjectStatus("nutrient")
                self._scene.insert(nutrient, nutrientId)
                self._nutrientFlushTime = self._rand.randIn(11) + 10
        else:
            self._nutrientFlushTime -= 1

        # 5、时间+1
        # 所有技能冷却时间 -1, 护盾持续时间 -1， 营养源刷新时间 -1, 瞬移发动后时间 +1
        self._time += 1
        for playerId in self._players.keys():
            if self._players[playerId].shieldTime > 0:
                self._players[playerId].shieldTime -= 1
            if self._players[playerId].shieldLevel > 0:
                self._players[playerId].shieldLevel -= 1
            if self._players[playerId].stopTime > 0:
                self._players[playerId].stopTime -= 1
            for skillName in self._players[playerId].skillsCD.keys():
                if self._players[playerId].skillsCD[skillName] > 0:
                    self._players[playerId].skillsCD[skillName] -= 1

        for playerId in self._changedPlayer:
            self._changeList.append(self.makePlayerJson(playerId))
        # 调用回调函数，向平台传回变化信息
        self._callback("[" + ",".join(self._changeList) + "]")

    # 生命下降，作用物体Id为objId, 受到伤害damage
    def healthDown(self, objId: int, damage):
        if self._players.get(objId) is not None:
            self._changedPlayer.add(objId)
        if objId == 0:
            oldHealth = self._players[0].health
            newHealth = oldHealth - damage
            # TODO 如果目标生物被远程攻击消灭怎么办？
            # 目标生物死就死了，这局就没有目标生物吧，这可以作为一种战术 -- cai_lw 16/2/27
            if newHealth <= 0:
                self._objects.pop(0)
                self._scene.delete(0)
                return
            newRadius = self._scene.getObject(0).radius * (newHealth / oldHealth) ** (1 / 3)
            newSphere = scene.Sphere(self._scene.getObject(0).center, newRadius)
            self._scene.modify(newSphere, 0)
            self._players[0].health = newHealth
        else:
            oldHealth = self._players[objId].health
            newHealth = oldHealth - damage
            if newHealth <= 0:
                self._players.pop(objId)
                self._scene.delete(objId)
                return
            newRadius = self._scene.getObject(objId).radius * (newHealth / oldHealth) ** (1 / 3)
            newSphere = scene.Sphere(self._scene.getObject(objId).center, newRadius)
            self._scene.modify(newSphere, objId)
            self._players[objId].health = newHealth

    # 物体移动，参数为物体Id, 物体速度speed，物体半径radius（用以判断移动是否合法）,是否为子弹isbullet（若子弹移动出界，则删除）
    def move(self, Id: int, tspeed: tuple, radius=0, isbullet=False):
        if (isbullet):
            enemy = self._scene.getObject(self._objects[Id].enemy).center
            bullet = self._scene.getObject(Id).center
            length = self._objects[Id].speed / math.sqrt(bullet[0] ** 2 + bullet[1] ** 2 + bullet[2] ** 2)
            speed = tuple(length * enemy[x] for x in range(3))
        else:
            speed = tspeed
        x = self._scene.getObject(Id).center[0] + speed[0]
        y = self._scene.getObject(Id).center[1] + speed[1]
        z = self._scene.getObject(Id).center[2] + speed[2]
        pos = (x, y, z)
        if self.outsideMap(pos, radius):
            if isbullet:
                self._objects.pop(Id)
                self._scene.delete(Id)
            else:
                vx = self._players[Id].speed[0]
                vy = self._players[Id].speed[1]
                vz = self._players[Id].speed[2]
                if x + radius > self._mapSize or x - radius < 0:
                    vx = 0
                if y + radius > self._mapSize or y - radius < 0:
                    vy = 0
                if z + radius > self._mapSize or z - radius < 0:
                    vz = 0
                self._players[Id].speed = (vx, vy, vz)
            return
        else:
            newSphere = scene.Sphere(pos, radius)
            self._scene.modify(newSphere, Id)
        if self._players.get(Id) is None:
            aiId = -2
        else:
            aiId = self._players[Id].aiId
        self._changeList.append(self.makeChangeJson(Id, -2, newSphere.center, newSphere.radius))

    # 若playerId为-1则返回全局所有物体，否则只返回该ID玩家视野内物体
    def getFieldJson(self, aiId: int):
        objectList = []
        changelist = []
        if aiId == -1:
            '''for info in self._lastObjectist:
                if info["type"] == "player":
                    sphere = self._scene.getObject(info["id"])
                    objectList.append({"id": info["id"], "type": "player", "pos": sphere.center, "r": sphere.radius})
                    if sphere.center != info["pos"] or sphere.radius != info["r"]:
                        changelist.append({"id": info["id"], "type": "player", "pos1": info["pos"], "r1": info["r"],
                                           "pos2": sphere.center, "r2": sphere.radius})
                elif info["type"] == "spike" or info["type"] == "food" or info["type"] == "nutrient":
                    if info["id"] in self._objects:
                        objectList.append(info)
                    else:
                        changelist.append({"id": info["id"], "type": info["type"], "pos1": info["pos"], "r1": info["r"],
                                           "pos2": (-1, -1, -1), "r2": -1})
                else:
                    if info["id"] in self._objects:
                        sphere = self._scene.getObject(info["id"])
                        objectList.append(
                            {"id": info["id"], "type": info["type"], "pos": sphere.center, "r": sphere.radius})
                        if sphere.center != info["pos"] or sphere.radius != info["r"]:
                            changelist.append(
                                {"id": info["id"], "type": info["type"], "pos1": info["pos"], "r1": info["r"],
                                 "pos2": sphere.center, "r2": sphere.radius})
                    else:
                        changelist.append({"id": info["id"], "type": info["type"], "pos1": info["pos"], "r1": info["r"],
                                           "pos2": (-1, -1, -1), "r2": -1})
            for objectId in self._objects:
                status = self._objects[objectId]
                if objectId not in self._lastobjects:
                    sphere = self._scene.getObject(objectId)
                    objectList.append({"id": objectId, "type": status.type, "pos": sphere.center, "r": sphere.radius})
                    changelist.append(
                        {"id": objectId, "type": status.type, "pos1": (-1, -1, -1), "r1": -1, "pos2": sphere.center,
                         "r2": sphere.radius})
            self._lastObjectist = objectList
            self._lastobjects = self._objects
            return json.dumps({"ai_id": aiId, "objects": changelist})'''
			pass
        else:
            visionSphere = scene.Sphere(self._scene.getObject(aiId).center, self._players[aiId].vision)
            visibleList = self._scene.intersect(visionSphere, False)
            for objectId in visibleList:
                sphere = self._scene.getObject(objectId)
                if self._players.get(objectId) is not None:
                    objType = "player"
                else:
                    objType = self._objects.get(objectId).type
                objectList.append({"id": objectId, "type": objType, "pos": sphere.center, "r": sphere.radius})
            return json.dumps({"ai_id": aiId, "objects": objectList})

    def getStatusJson(self):
        infoList = []
        for playerId, status in self._players.items():
            info = {"id": playerId, "health": status.health, "vision": status.vision, "ability": status.ability}
            skillList = []
            for name, level in status.skills.items():
                skillList.append({"name": name, "level": level})
            info["skills"] = skillList
            infoList.append(info)
        return json.dumps({"players": infoList})

    def setVelocity(self, playerId: int, newSpeed: tuple):
        speedLimit = 10000
        newSpeedLength = sum(x ** 2 for x in newSpeed) ** 0.5
        if newSpeedLength > speedLimit:
            newSpeed = tuple(x * speedLimit / newSpeedLength for x in newSpeed)
        self._players[playerId].speed = newSpeed

    # TODO 此处应添加处理技能附加参数（如施放位置、对象等）
    def castSkill(self, playerId: int, skillName: str, **kw):
        if self._players[playerId].skills.get(skillName) is not None:
            if self._players[playerId].skillsCD[skillName] == 0:
                if skillName == 'teleport':
                    self._castSkills[playerId] = CastTeleportInfo(kw['dst'])
                elif skillName == 'longAttack':
                    self._castSkills[playerId] = CastLongAttackInfo(kw['player'])
                else:
                    self._castSkills[playerId] = CastSkillInfo(skillName)

    # 获取单位速度矢量
    def getUnitSpeed(self, playerId: int):
        velocity = sum(x ** 2 for x in self._players[playerId].speed) ** 0.5
        return tuple(x / velocity for x in self._players[playerId].speed)

    # 远程攻击，参数为使用者Id
    def longAttack(self, playerId: int, enemy: int):
        skillLevel = self._players[playerId].skills['longAttack']
        damage = 100 * skillLevel
        stop = False
        speed = 50 + 50 * skillLevel
        if (skillLevel == 5):
            stop = True
        # 发射速度是否这样处理？
        self.healthDown(playerId, 10)
        self._players[playerId].skillsCD['longAttack'] = 80
        bullet = scene.Sphere(self.getCenter(playerId))
        i = 0
        # 发射物体的ID命名方式为：playerId + i
        while self._scene.getObject(int(str(playerId) + str(i))) is not None:
            i += 1
        bulletID = int(str(playerId) + str(i))
        self._scene.insert(bullet, bulletID)
        self._objects[bulletID] = BulletStatus(damage, enemy, speed, playerId, stop)
        self._changeList.append(self.makeSkillCastJson(playerId, 'longAttack', enemy, None))

    # 近程攻击，参数为使用者Id
    def shortAttack(self, playerId: int):
        skillLevel = self._players[playerId].skills['shortAttack']
        damage = 1000 + 200 * (skillLevel - 1)
        Range = 100 + 10 * (skillLevel - 1)
        self.healthDown(playerId, 50)
        self._players[playerId].skillsCD['shortAttack'] = 80
        self._changeList.append(self.makeSkillCastJson(playerId, 'shortAttack', None, None))
        # 创建虚拟球体，找到所有受到影响的物体。受到影响的判定为：相交
        virtualSphere = scene.Sphere(self.getCenter(playerId), Range)
        for objId in self._scene.intersect(virtualSphere):
            if self._players.get(objId) is not None and objId != playerId and self._players[playerId].shieldTime == 0:
                self.healthDown(objId, damage)
                self._changeList.append(self.makeSkillHitJson('shortAttack', objId))
        if skillLevel == 5:
            # self._players[playerId].shieldTime = 30
            self._players[playerId].shieldLevel = 34

    # 护盾，参数为使用者Id
    def shield(self, playerId: int):
        skillLevel = self._players[playerId].skills['shield']
        self._players[playerId].shieldTime = 81 + 20 * skillLevel
        self._players[playerId].skillsCD['shield'] = 100
        self._changeList.append(self.makeSkillCastJson(playerId, 'shield', None, None))

    # 计算两点pos1, pos2距离
    def dis(self, pos1: tuple, pos2: tuple):
        return sum((pos1[i] - pos2[i]) ** 2 for i in range(3)) ** 0.5

    # 判断远程攻击是否可以命中
    def longAttackbullet(self, bulletId: int):
        if (self.dis(self._scene.getObject(bulletId).center,
                     self._scene.getObject(self._objects[bulletId].enemy).center) <
                    self._scene.getObject(self._objects[bulletId].enemy).radius + self._objects[bulletId].speed):
            if self._players[self._objects[bulletId].enemy].shieldTime == 0 and self._players[
                self._objects[bulletId].enemy].shieldLevel < 5:
                self.healthDown(self._objects[bulletId].enemy, self._objects[bulletId].damage)
            if (self._objects[bulletId].stop == True):
                self._players[self._objects[bulletId].enemy].stopTime = 30
            self._scene.delete(bulletId)
            self._objects[bulletId].type = "None"
            # self._objects.pop(bulletId)
            return True
        else:
            return False

    # 判断某物体是否越界，参数为物体球心及半径
    def outsideMap(self, pos: tuple, radius):
        if pos[0] - radius < 0 or pos[0] + radius > self._mapSize \
                or pos[1] - radius < 0 or pos[1] + radius > self._mapSize \
                or pos[2] - radius < 0 or pos[2] + radius > self._mapSize:
            return True
        else:
            return False

    # 瞬移，参数为使用者Id， 目标位置pos2
    def teleport(self, playerId: int, pos2: tuple):
        skillLevel = self._players[playerId].skills['teleport']
        if self._players[playerId].skillsCD['teleport'] != 0:
            return
        sphere = self._scene.getObject(playerId)
        if self.outsideMap(pos2, sphere.radius):
            return
        if skillLevel != 5:
            if self.dis(sphere.center, pos2) > 9000 + 1000 * skillLevel:
                return
        self._players[playerId].skillsCD['teleport'] = 100
        newSphere = scene.Sphere(pos2, sphere.radius)
        self._scene.modify(newSphere, playerId)
        self._changeList.append(self.makeChangeJson(playerId, self._players[playerId].aiId, pos2, newSphere.radius))

    # 提升视野，参数为使用者Id
    def visionUp(self, playerId: int):
        skillLevel = self._players[playerId].skills['visionUp']
        self._players[playerId].vision = 1000 + 500 * skillLevel
        self._changedPlayer.add(playerId)
        self._changeList.append(self.makeSkillCastJson(playerId, 'visionUp', None, None))

    # 生命回复，参数为使用者Id
    def healthUp(self, playerId: int, num: int):
        self.healthDown(playerId, -num)
        self._changedPlayer.add(playerId)
        self._changeList.append(self.makeSkillCastJson(playerId, 'healthUp', None, None))

    # 获取球心
    def getCenter(self, Id: int):
        return self._scene.getObject(Id).center

    # 获取半径
    def getRadius(self, Id: int):
        return self._scene.getObject(Id).radius

    # 购买技能，参数为购买者Id及购买技能名称skillName
    def upgradeSkill(self, playerId: int, skillName: str):
        if self._players[playerId].skills.get(skillName) is not None:
            price = self._skillPrice[skillName] * 2 ** self._players[playerId].skills[skillName]
            if self._players[playerId].ability >= price and self._players[playerId].skills[skillName] < 5:
                self._changedPlayer.add(playerId)
                self._players[playerId].skills[skillName] += 1
                self._players[playerId].ability -= price
                if (skillName == "visionUp"):
                    self.visionUp(playerId)
                if (skillName == "healthUp"):
                    self.healthUp(playerId, 2000)
        elif self._players[playerId].skills.get(skillName) is None:
            price = self._skillPrice[skillName] * 2 ** len(self._players[playerId].skills)
            if self._players[playerId].ability >= price:
                self._changedPlayer.add(playerId)
                self._players[playerId].skills[skillName] = 1
                self._players[playerId].ability -= price
                self._players[playerId].skillsCD[skillName] = 0
                if (skillName == "visionUp"):
                    self.visionUp(playerId)
                if (skillName == "healthUp"):
                    self.healthUp(playerId, 2000)

    def gameEnd(self):
        self._gameEnd = True
        self._changeList.append('{"info":"end","time":%d,"ai_id":%d}' % (self._time, -2))
