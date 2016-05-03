from ts17core import scene, myrand


class PlayerStatus:
    def __init__(self):
        # 拥有该玩家的AI的ID
        self.aiId = 0
        # 血量
        self.health = 0
        # 速度矢量
        self.speed = (0, 0, 0)
        # 速度上限
        self.speedLimit = 100
        # 能力值，购买技能用
        self.ability = 10
        # 视野半径
        self.vision = 5000
        # 技能列表，应以“技能名:技能等级”形式保存
        self.skillsLV = {}
        # 技能冷却时间，以“技能名：剩余冷却时间”保存,每回合结束后-1
        self.skillsCD = {}
        # 远程攻击的生效倒计时，倒计到0时生效，-1表示不在倒计时中
        self.longAttackCasting = -1
        # 近程攻击的生效倒计时，倒计到0时生效，-1表示不在倒计时中
        self.shortAttackCasting = -1
        # 远程攻击的目标，-1表示没有
        self.longAttackEnemy = -1
        # 冲刺剩余时间，每回合结束后-1
        self.dashTime = 0
        # 护盾剩余时间,每回合结束后-1
        self.shieldTime = 0
        # 护盾等级（考虑到技能特殊效果触发的护盾等级与技能等级不符而设置）
        self.shieldLevel = 0
        # 不可移动时间
        self.stopTime = 0
        # 历史最大血量
        self.maxHealth = self.health
        #因营养源传送获得的一回合不受刺球影响状态
        self.nutrientMove=0
        self.tnutrientMove=0
        #是否死亡
        self.death=False

    def healthChange(self, delta):
        self.health += delta
        if self.health > self.maxHealth:
            self.maxHealth = self.health


# 物体包括：食物（food）、营养源（nutrient）、刺球（spike）、目标生物（target）、远程子弹（bullet）
class ObjectStatus:
    def __init__(self, objType="food"):
        # 物体类型，以小写英文单词字符串表示
        # bullet为远程攻击的点状物体，target目标生物,生命值暂且按10000算
        self.type = objType


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


class CastLongAttackInfo():
    def __init__(self, tPlayer):
        self.name = "longAttack"
        self.player = tPlayer


class GameMain:
    def __init__(self, seed, playerNum, type,callback):
        # 游戏结束标志
        self._gameEnd = False
        #0表示正常比赛，非零数X表示测试赛X
        self._gameType=type
        # 地图大小（地图三维坐标的范围均为[0,_mapSize]）
        self._mapSize = 20000
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
        self._skillPrice = {'longAttack': 1, 'shortAttack': 1, 'shield': 1, 'dash': 1, 'visionUp': 2, 'healthUp': 1}
        # 食物编号
        self._foodCount = 0
        self._foodCountAll = 0
        # 刺球编号
        self._spikeCount = 0
        self._spikeCountAll = 0
        #伤害总量
        self._damage=0;
        # 营养源刷新剩余时间
        self._nutrientFlushTime = 0
        # 营养源刷新位置
        self._nutrientFlushPos = []
        for x in range(8):
            temp = x
            for _ in range(3):
                pos1=tuple(self._rand.randIn(self._mapSize // 2) + ((temp & (1 << y)) >> y) * self._mapSize // 2 for y in range(3))
                pos2=tuple(self._mapSize-y for y in pos1)
                self._nutrientFlushPos.append(pos1)
                self._nutrientFlushPos.append(pos2)

        # 记录变化情况的json的list，每项为一个json object
        self._changeList = []
        # 记录发生变化的玩家集合，在更新结束时发送这些玩家的变化
        self._changedPlayer = set()
        # 增加玩家
        self.addNewPlayer(0, -2, tuple(self._mapSize // 2 for _ in range(3)), 2000)
        pos1 = tuple(self._rand.randIn(self._mapSize-2000)+1000 for _ in range(3))
        while self.dis(pos1,tuple(self._mapSize//2 for _ in range(3)))<2000:
            pos1 = tuple(self._rand.randIn(self._mapSize-2000)+1000 for _ in range(3))
        pos2 = tuple(self._mapSize - pos1[x] for x in range(3))
        self.addNewPlayer(1, 0, pos1, 1000)
        self.addNewPlayer(2, 1, pos2, 1000)

    # player位置获取
    def playerPos(self, playerId):
        return self._scene.getObject(playerId).center

    # 添加新玩家
    def addNewPlayer(self, playerId: int, aiId: int, pos: tuple, radius: int):
        sphere = scene.Sphere(pos, radius)
        self._scene.insert(sphere, playerId)
        newStatus = PlayerStatus()
        newStatus.health = int((radius / 100) ** 3)
        newStatus.maxHealth = newStatus.health
        newStatus.aiId = aiId
        self._players[playerId] = newStatus

    def makeChangeJson(self, playerId: int, aiId: int, pos: tuple, r: int,nutrientMove=0):
        if self._objects.get(playerId) is not None:
            objType = self._objects[playerId].type
        elif self._players.get(playerId) is not None:
            objType = "player"
        else:
            objType = None
        return '{"info":"object","time":%d,"id":%d,"ai_id":%d,"type":"%s","pos":[%.10f,%.10f,%.10f],"r":%.10f,"nutrientmove":%d}' \
               % (self._time, playerId, aiId, objType, pos[0], pos[1], pos[2], r,nutrientMove)

    def makeDeleteJson(self, objId: int):
        return '{"info":"delete","time":%d,"id":%d}' % (self._time, objId)

    # 若target为None则没有目标物体，pos为None则没有目标坐标
    def makeSkillCastJson(self, source: int, skillType: str, target=None):
        if target is not None:
            targetStr = ',"target":%d' % target
        else:
            targetStr = ''
        return '{"info":"skill_cast","time":%d,"source":%d,"type":"%s"%s}' \
               % (self._time, source, skillType, targetStr)

    def makeSkillHitJson(self, skillType: str,player:int, target: int):
        return '{"info":"skill_hit","time":%d,"type":"%s","player":%d,"target":%d}' % (self._time, skillType, player,target)

    def makePlayerJson(self, playerId: int):
        player = self._players[playerId]
        skillList = ",".join(
            '{"name":"%s","level":%d,"cd":%d}' % (skill, player.skillsLV[skill], player.skillsCD[skill]) for skill in
            player.skillsLV.keys())
        speedStr = ",".join('%.10f' % x for x in player.speed)
        sphere = self._scene.getObject(playerId)
        pos = ",".join('%.10f' % x for x in sphere.center)
        return '{"info":"player","time":%d,"id":%d,"ai_id":%d,"health":%d,"max_health":%d,"vision":%d,' \
               '"ability":%d,"pos":[%s],"r":%d,"longattackcasting":%d,"shortattackcasting":%d,"shieldtime":%d,"dashtime":%d,' \
               '"speed":[%s],"skills":[%s]}' \
               % (self._time, playerId, player.aiId, player.health, player.maxHealth, player.vision,
                  player.ability, pos, sphere.radius, player.longAttackCasting,player.shortAttackCasting, player.shieldTime, player.dashTime,
                  speedStr, skillList)

    def newMakePlayerJson(self, playerId: int):
        player = self._players[playerId]
        skillList = ",".join(
            '{"name":"%s","level":%d,"cd":%d}' % (skill, player.skillsLV[skill], player.skillsCD[skill]) for skill in
            player.skillsLV.keys())
        speedStr = ",".join('%.10f' % x for x in player.speed)
        sphere = self._scene.getObject(playerId)
        pos = ",".join('%.10f' % x for x in sphere.center)
        return '{"info":"player","time":%d,"id":%d,"ai_id":%d,"health":%d,"max_health":%d,"vision":%d,' \
               '"ability":%d,"pos":[%s],"r":%d,"longattackcasting":%d,"shortattackcasting":%d,"shieldtime":%d,"dashtime":%d,' \
               '"speed":[%s],"skills":[%s]}' \
               % (self._time, playerId, player.aiId, player.health, player.maxHealth, player.vision,
                  player.ability, pos, sphere.radius, player.longAttackCasting,player.shortAttackCasting, max(player.shieldLevel-4,player.shieldTime), player.dashTime,
                  speedStr, skillList)

    # 每回合调用一次，依次进行如下动作：
    # 相关辅助函数可自行编写
    def update(self):
        # 初始化返回给平台的变化信息的json List
        self._changeList = []
        self._changedPlayer = set()
        if self._time == 5000:
            tempId = 0
            tempMax = 0
            for playerId in self._players:
                if self._players[playerId].aiId == -2:
                    continue
                if self._players[playerId].health > tempMax:
                    tempMax = self._players[playerId].health
                    tempId = self._players[playerId].aiId
            self.gameEnd(tempId,1)

        # 1、结算技能效果
        for playerId in self._rand.shuffle(list(self._castSkills.keys())):
            if self._gameEnd:
                break
            if self._players.get(playerId) is None:
                continue
            if self._players[playerId].death:
                continue
            skillInfo = self._castSkills[playerId]
            skillName = skillInfo.name
            if skillName == 'shortAttack':
                self.shortAttackSet(playerId)
            elif skillName == 'longAttack':
                self.longAttackSet(playerId, skillInfo.player)
            elif skillName == 'dash':
                self.dash(playerId)
            elif skillName == 'shield':
                self.shield(playerId)
            elif skillName == 'visionUp':
                self.visionUp(playerId)
            elif skillName == 'healthUp':
                self.healthUp(playerId)
        for playerId, player in self._players.items():
            if self._gameEnd:
                break
            if player.death:
                continue
            # 远程攻击蓄力到时间后结算远程攻击效果
            if player.longAttackCasting == 0:
                self.longAttackDone(playerId)
            # 近程攻击蓄力到时间后结算远程攻击效果
            if player.shortAttackCasting == 0:
                self.shortAttackDone(playerId)
            # 冲刺状态时间到后恢复原始速度
            if player.dashTime == 0:
                player.speedLimit = 100
        self._castSkills.clear()

        # 2、移动所有物体（包括玩家，远程子弹，目标生物）
        for playerId, player in self._players.items():
            if self._gameEnd:
                break
            if player.death:
                continue
            if playerId == 0:
                player.speed = tuple((self._rand.randIn(20 * 1000000) / 1000000)-10+self._players[1].speed[x]/2+self._players[2].speed[x]/2 for x in range(3))
            if player.stopTime == 0:
                self.playerMove(playerId)

        # 3、判断相交，结算吃、碰撞、被击中等各种效果
        for playerId in self._rand.shuffle(list(self._players.keys())):
            if self._gameEnd:
                break
            player = self._players.get(playerId)
            if player is None:
                continue
            if player.death:
                continue
            sphere = self._scene.getObject(playerId)
            # 玩家（包括目标生物）可食用的物体对其产生效果，包括食用食饵、营养源、目标生物、以及其他玩家AI
            insideList = self._scene.intersect(sphere, True)
            eatableList = [objId for objId in insideList if 1.2 * self._scene._objs[objId].radius < sphere.radius]
            for eatenId in eatableList:
                eatenPlayer = self._players.get(eatenId)
                if eatenPlayer is not None:
                    if (eatenPlayer.shieldTime == 0 or
                                    eatenPlayer.skillsLV["shield"] < 4) and eatenPlayer.shieldLevel < 5:
                        #self.healthChange(playerId, eatenPlayer.health // 2)
                        #self.healthChange(eatenId, -eatenPlayer.health)
                        self._changeList.append(self.makeDeleteJson(eatenId))
                        if player.aiId==-2:
                            self.gameEnd(1-eatenPlayer.aiId,2)
                        else:
                            self.gameEnd(self._players[playerId].aiId,3)
                    continue
                objType = self._objects[eatenId].type
                if objType == "food":
                    self._changeList.append(self.makeDeleteJson(eatenId))
                    self.healthChange(playerId, 40)
                    self.objectDelete(eatenId)
                    self._foodCount -= 1
                elif objType == "nutrient":
                    self._changeList.append(self.makeDeleteJson(eatenId))
                    player.ability += 5
                    self.nutrientMove(playerId)
                    self.objectDelete(eatenId)
            if playerId==0 :
                continue

            # 玩家接触到的物体对其产生效果，包括受到刺球伤害及子弹伤害
            touchList = self._scene.intersect(sphere, False)
            for touchedId in touchList:
                if self._players.get(touchedId) is not None:
                    continue
                objType = self._objects[touchedId].type
                if objType == "spike":
                    if self._players[playerId].tnutrientMove>0:
                        self.objectDelete(touchedId)
                        continue
                    if (self._players[playerId].shieldTime == 0 or
                                    self._players[playerId].skillsLV["shield"] < 5) and self._players[
                                playerId].shieldLevel < 5:
                        damage = self._players[playerId].health // 3
                        if damage>2000:
                            damage=2000
                        self.healthChange(playerId, -damage)
                        self.objectDelete(touchedId)

        # 4、随机产生新的食物等,暂且每回合1个食饵，且上限为1000个。每隔100-110回合刷新一个营养源;
        # 食饵ID为1000000+食物编号， 营养源ID为2000000+营养源位置编号
        if self._time == 0:
            foodPerTick = 150
        else:
            foodPerTick = 10
        for _ in range(foodPerTick):
            if self._gameEnd:
                break
            if self._foodCount > 300:
                break
            center = tuple(self._rand.randIn(self._mapSize) for _ in range(3))
            food = scene.Sphere(center)
            foodId = 1000000 + self._foodCountAll
            self._objects[foodId] = ObjectStatus("food")
            self._scene.insert(food, foodId)
            self._foodCountAll += 1
            self._changeList.append(self.makeChangeJson(foodId, -2, center, 0))
            center2 = tuple(self._mapSize-x for x in center)
            food = scene.Sphere(center2)
            foodId = 1000000 + self._foodCountAll
            self._objects[foodId] = ObjectStatus("food")
            self._scene.insert(food, foodId)
            self._foodCountAll += 1
            self._foodCount += 2
            self._changeList.append(self.makeChangeJson(foodId, -2, center2, 0))


        spikenum=0
        if self._time % 10 == 0:
            spikenum += 1
        for _ in range(spikenum):
            if self._gameEnd:
                break
            if self._spikeCount >= 50:
                break
            center = tuple(self._rand.randIn(self._mapSize) for _ in range(3))
            while self.inplayer(center):
                center = tuple(self._rand.randIn(self._mapSize) for _ in range(3))
            spike = scene.Sphere(center)
            spikeId = 2001000 + self._spikeCountAll
            self._objects[spikeId] = ObjectStatus("spike")
            self._scene.insert(spike, spikeId)
            self._spikeCountAll += 1
            self._spikeCount += 1
            self._changeList.append(self.makeChangeJson(spikeId, -2, center, 0))

        if self._nutrientFlushTime == 0:
            pos = self._rand.randIn(len(self._nutrientFlushPos)>>1)<<1
            nutrientId1 = int(2000000 + pos)
            nutrientId2 = int(2000000 + pos+1)
            time = 0
            while (self._objects.get(nutrientId1) is not None) and (self._objects.get(nutrientId2) is not None):
                pos = self._rand.randIn(len(self._nutrientFlushPos)>>1)<<1
                nutrientId1 = int(2000000 + pos)
                nutrientId2 = int(2000000 + pos+1)
                time += 1
                if time > 10:
                    break
            if time <= 10:
                if self._objects.get(nutrientId1) is  None:
                    nutrient = scene.Sphere(self._nutrientFlushPos[pos])
                    self._objects[nutrientId1] = ObjectStatus("nutrient")
                    self._scene.insert(nutrient, nutrientId1)
                if self._objects.get(nutrientId2) is  None:
                    nutrient = scene.Sphere(self._nutrientFlushPos[pos+1])
                    self._objects[nutrientId2] = ObjectStatus("nutrient")
                    self._scene.insert(nutrient, nutrientId2)
                self._nutrientFlushTime = self._rand.randIn(100) + 10
        else:
            self._nutrientFlushTime -= 1


        # 5、时间+1
        # 所有技能冷却时间 -1, 护盾持续时间 -1， 营养源刷新时间 -1, 瞬移发动后时间 +1
        self._time += 1
        for playerId, player in self._players.items():
            if self._gameEnd:
                break
            if player.death:
                continue
            if player.shieldTime > 0:
                player.shieldTime -= 1
                if player.skillsLV['shield']>2 and player.skillsLV['healthUp']==5:
                    self.healthChange(playerId, 5*player.skillsLV['shield']-5)
            if player.shieldLevel > 0:
                player.shieldLevel -= 1
            if player.stopTime > 0:
                player.stopTime -= 1
            if player.longAttackCasting > 0:
                player.longAttackCasting -= 1
            if player.shortAttackCasting > 0:
                player.shortAttackCasting -= 1
            if player.dashTime > 0:
                player.dashTime -= 1
            if player.nutrientMove>0:
                player.nutrientMove-=1
            if player.tnutrientMove>0:
                player.tnutrientMove-=1
            for skillName in self._players[playerId].skillsCD.keys():
                if player.skillsCD[skillName] > 0:
                    player.skillsCD[skillName] -= 1

        for playerId in self._players:
            if self._players[playerId].death==False:  # 确保只生成未死亡的玩家的变化信息
                self._changeList.append(self.newMakePlayerJson(playerId))

        #判断是否为测试赛
        if self._gameType!=0:
            #测试赛1，如果选手移动则成功
            if (self._gameType==1):
                for playerId in self._players:
                    if (self._players[playerId].aiId!=0):
                        continue
                    if self._players[playerId].speed!=(0,0,0):
                        self.testGameEnd(10)

        # 调用回调函数，向平台传回变化信息
        self._callback("[" + ",".join(self._changeList) + "]")

    # 生命变化，作用于playerId, 变化量delta（受伤害时为负）
    def healthChange(self, playerId: int, delta: int):
        player = self._players.get(playerId)
        if player is None:
            return
        if player.death:
            return
        player.healthChange(delta)
        if delta<0:
            self._damage-=delta
        newHealth = player.health
        if newHealth < player.maxHealth//4:
            self.playerDie(playerId)
        else:
            newRadius = (newHealth ** (1 / 3)) * 100
            newSphere = scene.Sphere(self._scene.getObject(playerId).center, newRadius)
            self._scene.modify(newSphere, playerId)
            self._changedPlayer.add(playerId)

    # 判断玩家生命小于0后即应调用该函数，由该函数负责所有后续处理工作
    def playerDie(self, playerId: int):
        player = self._players.get(playerId)
        if player is None:
            return
        if player.health > player.maxHealth//4:
            return
        #self._players.pop(playerId)
        self._players[playerId].death=True
        self._scene.delete(playerId)
        self._changeList.append(self.makeDeleteJson(playerId))
        # 判断是否只有一个AI有玩家存活，是则游戏结束，该AI获胜
        aliveAI = set()
        for player in self._players.values():
            if player.aiId >= 0 and player.death==False:
                aliveAI.add(player.aiId)
        if len(aliveAI) == 1:
            self.gameEnd(aliveAI.pop(),4)

    # 判断物体应消失后即应调用该函数，由该函数负责所有后续处理工作
    def objectDelete(self, objId: int):
        obj = self._objects.get(objId)
        if obj is None:
            return
        self._objects.pop(objId)
        self._scene.delete(objId)
        self._changeList.append(self.makeDeleteJson(objId))

    # 玩家移动，参数为玩家Id
    def playerMove(self, playerId: int):
        oldPos = self._scene.getObject(playerId).center
        r = self._scene.getObject(playerId).radius
        speed = self._players[playerId].speed
        newPos = tuple(oldPos[i] + speed[i] for i in range(3))
        if self.outsideMap(newPos, r):
            newPos2 = list(newPos)
            for i in range(3):
                if newPos2[i] + r > self._mapSize:
                    newPos2[i]=self._mapSize-r
                elif newPos[i] - r < 0:
                    newPos2[i] = r
            newPos = tuple(newPos2)
        newSphere = scene.Sphere(newPos, r)
        self._scene.modify(newSphere, playerId)
        self._changeList.append(self.makeChangeJson(
            playerId, self._players[playerId].aiId, newSphere.center, newSphere.radius))

    def isBelong(self, playerId: int, aiId: int):
        player = self._players.get(playerId)
        if player is None:
            return False
        return player.aiId == aiId

    # 若aiId为-1则返回所有物体，否则返回该AI控制的所有玩家的视野内物体的并集
    def getFieldJson(self, aiId: int):
        def makeObjectJson(objId, aiId, objType, pos, r, longAttackCasting=-1,shortAttackCasting=-1,shieldTime=-1):
            return '{"id":%d,"ai_id":%d,"type":"%s","pos":[%.10f,%.10f,%.10f],"r":%.10f,"longattackcasting":%d,"shortattackcasting":%d,"shieldtime":%d}' \
                   % (objId, aiId, objType, pos[0], pos[1], pos[2], r, longAttackCasting,shortAttackCasting, shieldTime)

        objectDict = {}
        if aiId == -1:
            for playerId in self._players:
                if self._players[playerId].death:
                    continue
                sphere = self._scene.getObject(playerId)
                objectDict[playerId] = \
                    makeObjectJson(playerId, self._players[playerId].aiId, "player", sphere.center, sphere.radius,
                                   self._players[playerId].longAttackCasting, self._players[playerId].shortAttackCasting,self._players[playerId].shieldTime)
            for objectId in self._objects:
                status = self._objects[objectId]
                sphere = self._scene._objs[objectId]
                objectDict[objectId] = makeObjectJson(objectId, -2, status.type, sphere.center, sphere.radius)
            # 规定营养产生处的ID为4000000+i，该ID暂无意义
            for i, pos in enumerate(self._nutrientFlushPos):
                nutrientId = 4000000 + i
                objectDict[nutrientId] = makeObjectJson(nutrientId, -2, 'source', pos, 0)
        else:
            visionSpheres = [scene.Sphere(self._scene.getObject(playerId).center, self._players[playerId].vision+self._scene.getObject(playerId).radius)
                             for playerId in self._players.keys() if self._players[playerId].aiId == aiId and self._players[playerId].death==False]
            visibleLists = [self._scene.intersect(vs, False) for vs in visionSpheres]
            for objectId in [i for ls in visibleLists for i in ls]:
                if objectDict.get(objectId) is not None:
                    continue
                sphere = self._scene._objs[objectId]
                if self._players.get(objectId) is not None:
                    objectDict[objectId] = \
                        makeObjectJson(objectId, self._players[objectId].aiId, 'player', sphere.center, sphere.radius,
                                       self._players[objectId].longAttackCasting, self._players[objectId].shortAttackCasting,self._players[objectId].shieldTime)
                else:
                    objType = self._objects.get(objectId).type
                    objectDict[objectId] = makeObjectJson(objectId, -2, objType, sphere.center, sphere.radius)
            for i, pos in enumerate(self._nutrientFlushPos):
                if any(sum((vs.center[i] - pos[i]) ** 2 for i in range(3)) < vs.radius ** 2 for vs in visionSpheres):
                    nutrientId = 4000000 + i
                    objectDict[nutrientId] = makeObjectJson(nutrientId, -2, 'source', pos, 0)
        return '{"ai_id":%d,"objects":[%s]}' % (aiId, ','.join(objectDict.values()))

    def getStatusJson(self, aiId: int):
        infoList = []
        for playerId, player in self._players.items():
            if aiId != -1 and player.aiId != aiId:
                continue
            if player.death:
                continue
            infoList.append(self.makePlayerJson(playerId))
        return '{"players":[%s]}' % ','.join(infoList)

    def setSpeed(self, playerId: int, newSpeed: tuple):
        speedLimit = self._players[playerId].speedLimit
        temp=[]
        for x in newSpeed:
            if -2000000<=x<=2000000:
                temp.append(x)
            else:
                temp.append(0)
        newSpeed=tuple(temp)
        newSpeedLength = sum(x ** 2 for x in newSpeed ) ** 0.5
        if newSpeedLength > speedLimit:
            newSpeed = tuple(x * speedLimit / newSpeedLength for x in newSpeed)
        self._players[playerId].speed = newSpeed

    def castSkill(self, playerId: int, skillName: str, **kw):
        if self._players[playerId].longAttackCasting >= 0:
            return
        if self._players[playerId].shortAttackCasting >= 0:
            return
        if self._players[playerId].skillsLV.get(skillName) is not None:
            if self._players[playerId].skillsCD[skillName] == 0:
                if skillName == 'longAttack':
                    self._castSkills[playerId] = CastLongAttackInfo(kw['player'])
                else:
                    self._castSkills[playerId] = CastSkillInfo(skillName)

    # 远程攻击开始蓄力
    def longAttackSet(self, playerId: int, enemyId: int):
        player = self._players.get(playerId)
        if player is None:
            return
        if self._players.get(enemyId) is None:
            return
        if player.death or self._players[enemyId].death:
            return
        self.healthChange(playerId, -10)
        player.skillsCD['longAttack'] = 80
        player.longAttackCasting = 10
        player.longAttackEnemy = enemyId
        self._changeList.append(self.makeSkillCastJson(playerId, 'longAttack', enemyId))

    def shortAttackSet(self, playerId: int):
        player = self._players.get(playerId)
        if player is None:
            return
        if player.death :
            return
        self.healthChange(playerId, -50)
        player.skillsCD['shortAttack'] = 80
        player.shortAttackCasting = 10
        self._changeList.append(self.makeSkillCastJson(playerId, 'shortAttack'))

    # 远程攻击蓄力完成
    def longAttackDone(self, playerId: int):
        player = self._players.get(playerId)
        enemyId = player.longAttackEnemy
        if player is None:
            return
        if self._players[enemyId].death:
            player.longAttackCasting = -1
            player.longAttackEnemy = -1
            return
        if player.death:
            player.longAttackCasting = -1
            player.longAttackEnemy = -1
            return
        enemyObj = self._scene.getObject(enemyId)
        if player.longAttackCasting != 0:
            return
        skillLevel = player.skillsLV['longAttack']
        attackRange = 2000 + 500 * skillLevel
        if self.dis(self._scene.getObject(playerId).center, enemyObj.center) - enemyObj.radius-self._scene.getObject(playerId).radius < attackRange:
            newdamage = 100 * skillLevel
            if player.dashTime!=0:
                newdamage*=(1+(player.skillsLV["dash"]+2)*0.1+0.05)
            if self._players[enemyId].shieldLevel>=5:
                newdamage*=0.7
            elif self._players[enemyId].shieldTime!=0:
                newdamage*=(self._players[enemyId].skillsLV['shield']+2)
                newdamage/=10
            self.healthChange(enemyId, -newdamage)
            if skillLevel == 5:
                self._players[enemyId].stopTime = 30
            self._changeList.append(self.makeSkillHitJson('longAttack', playerId,enemyId))
        player.longAttackCasting = -1
        player.longAttackEnemy = -1

    # 近程攻击，参数为使用者Id
    def shortAttackDone(self, playerId: int):
        player = self._players.get(playerId)
        if player is None:
            return
        if player.death:
            player.shortAttackCasting = -1
            return
        if player.shortAttackCasting != 0:
            return
        skillLevel = self._players[playerId].skillsLV['shortAttack']
        damage = 500 + 200 * (skillLevel - 1)
        if 1<skillLevel<5:
            damage+=100
        attackRange = 1100 + 300 * skillLevel
        if skillLevel==5:
            attackRange-=100
        # 创建虚拟球体，找到所有受到影响的物体。受到影响的判定为：相交
        virtualSphere = scene.Sphere(self.getCenter(playerId), attackRange+self._scene.getObject(playerId).radius)
        for objId in self._scene.intersect(virtualSphere):
            if self._players.get(objId) is not None and objId != playerId :
                newdamage=damage
                if player.dashTime!=0:
                    newdamage*=(1+(player.skillsLV["dash"]+2)*0.1+0.05)
                if self._players[objId].shieldLevel>=5:
                    newdamage*=0.7
                elif self._players[objId].shieldTime!=0:
                    newdamage*=(self._players[objId].skillsLV['shield']+2)
                    newdamage/=10
                self.healthChange(objId, -newdamage)
                self._changeList.append(self.makeSkillHitJson('shortAttack', playerId,objId))
        if skillLevel == 5:
            # self._players[playerId].shieldTime = 30
            self._players[playerId].shieldLevel = 35
            self._changeList.append(self.makeSkillCastJson(playerId, 'shield'))
        player.shortAttackCasting = -1

    # 护盾，参数为使用者Id
    def shield(self, playerId: int):
        skillLevel = self._players[playerId].skillsLV['shield']
        self._players[playerId].shieldTime = 30
        self._players[playerId].skillsCD['shield'] = 80
        self._changeList.append(self.makeSkillCastJson(playerId, 'shield'))

    # 计算两点pos1, pos2距离
    def dis(self, pos1: tuple, pos2: tuple):
        return sum((pos1[i] - pos2[i]) ** 2 for i in range(3)) ** 0.5

    def inplayer(self,pos:tuple):
        for playerId in self._players:
            if self._players[playerId].aiId==-2:
                continue
            if self._players[playerId].death:
                continue
            sphere=self._scene.getObject(playerId)
            if self.dis(pos,sphere.center)<sphere.radius+500:
                return True
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
    def dash(self, playerId: int):
        player = self._players.get(playerId)
        skillLevel = player.skillsLV['dash']
        if player is None:
            return
        player.dashTime = 40
        if skillLevel==5:
            player.dashTime+=40
        player.speedLimit += skillLevel * 20
        player.skillsCD['dash'] = 100
        self._changeList.append(self.makeSkillCastJson(playerId, 'dash'))

    def nutrientMove(self, playerId: int):
        if playerId==0:
            return
        sphere = self._scene.getObject(playerId)
        if self._players[0].death==False:
            bosssphere=self._scene.getObject(0)
        pos = tuple(self._rand.randIn(self._mapSize - 2 * sphere.radius) + sphere.radius for _ in range(3))
        if self._players[0].death==False:
            while self.dis(pos,bosssphere.center)<bosssphere.radius:
                pos = tuple(self._rand.randIn(self._mapSize - 2 * sphere.radius) + sphere.radius for _ in range(3))
        newSphere = scene.Sphere(pos, sphere.radius)
        self._scene.modify(newSphere, playerId)
        self._players[playerId].nutrientMove=2
        self._players[playerId].tnutrientMove=6
        self._changeList.append(self.makeChangeJson(playerId, self._players[playerId].aiId, pos, newSphere.radius,1))

    # 提升视野，参数为使用者Id
    def visionUp(self, playerId: int):
        skillLevel = self._players[playerId].skillsLV['visionUp']
        self._players[playerId].vision = 5000 + 1000 * skillLevel
        self._changedPlayer.add(playerId)
        self._changeList.append(self.makeSkillCastJson(playerId, 'visionUp'))

    # 生命回复，参数为使用者Id
    def healthUp(self, playerId: int):
        self.healthChange(playerId, 500)
        self._changedPlayer.add(playerId)
        self._changeList.append(self.makeSkillCastJson(playerId, 'healthUp'))

    # 获取球心
    def getCenter(self, Id: int):
        return self._scene.getObject(Id).center

    # 购买技能，参数为购买者Id及购买技能名称skillName
    def upgradeSkill(self, playerId: int, skillName: str):
        validSkillName = ['shortAttack', 'longAttack', 'shield', 'dash', 'visionUp', 'healthUp']
        if skillName not in validSkillName:
            return
        if self._players[playerId].skillsLV.get(skillName) is not None:
            price = self._skillPrice[skillName] * 2 ** self._players[playerId].skillsLV[skillName]
            if self._players[playerId].ability >= price and self._players[playerId].skillsLV[skillName] < 5:
                self._changedPlayer.add(playerId)
                self._players[playerId].skillsLV[skillName] += 1
                self._players[playerId].ability -= price
                if (skillName == "visionUp"):
                    self.visionUp(playerId)
                if (skillName == "healthUp"):
                    self.healthUp(playerId)
        else:
            price = self._skillPrice[skillName] * 2 ** len(self._players[playerId].skillsLV)
            if self._players[playerId].ability >= price:
                self._changedPlayer.add(playerId)
                self._players[playerId].skillsLV[skillName] = 1
                self._players[playerId].ability -= price
                self._players[playerId].skillsCD[skillName] = 0
                if (skillName == "visionUp"):
                    self.visionUp(playerId)
                if (skillName == "healthUp"):
                    self.healthUp(playerId)

    def gameEnd(self, winnerId: int,why:int):
        if self._gameEnd:
            return
        if self._gameType!=0:
            return
        self._gameEnd = True
        self._changeList.append('{"info":"end","time":%d,"ai_id":%d,"why":%d,"damage":%d,"maxhealth":%d}' % (self._time, winnerId,why,self._damage,max(self._players[1].health,self._players[2].health)))

    def testGameEnd(self,score:int):
        self._gameEnd=True
        if score>0:
            aiId=0
        else:
            aiId=1
        self._changeList.append('{"info":"end","time":%d,"ai_id":%d,"score":%d}' % (self._time, aiId,score))

