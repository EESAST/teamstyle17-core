import scene,myrand

class PlayerStatus:

    def __init__(self):
        #血量
        self.health=0
        #速度矢量
        self.speed=(0,0,0)
        #能力值，购买技能用
        self.ability=0
        #视野半径
        self.vision=0
        #技能列表，应以“技能名:技能等级”形式保存
        self.skills={}


class GameMain:

    def __init__(self):
        # 当前时刻，以tick为单位，是负整数
        self._time=0
        # 保存玩家信息，应以“玩家ID:PlayerStatus”形式保存
        self._players={}
        # 保存其他物体的信息，应以“物体ID:物体信息”形式保存，物体信息的类型和格式可自行规定
        self._objects={}
        # 场景管理器，物体和玩家的位置、大小的信息记录在这里面。详情参考scene.py中的注释
        self._scene=scene.Octree()
        # 存储该回合内施放了但未结算的技能，以“玩家ID:技能名”形式保存，每回合应清空一次
        self._castSkills={}
        # 随机数生成器，所有随机事件必须从这里获取随机数
        self._rand=myrand.MyRand()

    # 每回合调用一次，依次进行如下动作：
    # 相关辅助函数可自行编写
    def update(self):
        # 1、结算技能效果
        for playerId,skillName in self._castSkills:
            pass
        self._castSkills={}
        # 2、移动所有物体（似乎只有玩家能移动？）
        for playerId in self._players.keys():
            pass
        # 3、判断相交，结算吃、碰撞、被击中等各种效果
        for playerId in self._players.keys():
            pass
        # 4、随机产生新的食物等
        pass
        # 5、时间+1
        self._time+=1

    # 若playerId为-1则返回全局所有物体，否则只返回该ID玩家视野内物体
    def getFieldJson(self,playerId:int):
        pass

    def setVelocity(self,playerId:int,newSpeed:tuple):
        speedLimit=10000
        newSpeedLength=sum(x**2 for x in newSpeed)
        if newSpeedLength>speedLimit:
            newSpeed=tuple(x*speedLimit/newSpeedLength for x in newSpeed)
        self._players[playerId].speed=newSpeed

    def castSkill(self,playerId:int,skillName:str):
        if self._players[playerId].skills.get(skillName)!=None:
            self._castSkills[playerId]=skillName