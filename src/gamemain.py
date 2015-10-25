import scene,myrand

class PlayerStatus:

    def __init__(self):
        #Ѫ��
        self.health=0
        #�ٶ�ʸ��
        self.speed=(0,0,0)
        #����ֵ����������
        self.ability=0
        #��Ұ�뾶
        self.vision=0
        #�����б�Ӧ�ԡ�������:���ܵȼ�����ʽ����
        self.skills={}


class GameMain:

    def __init__(self):
        # ��ǰʱ�̣���tickΪ��λ���Ǹ�����
        self._time=0
        # ���������Ϣ��Ӧ�ԡ����ID:PlayerStatus����ʽ����
        self._players={}
        # ���������������Ϣ��Ӧ�ԡ�����ID:������Ϣ����ʽ���棬������Ϣ�����ͺ͸�ʽ�����й涨
        self._objects={}
        # �������������������ҵ�λ�á���С����Ϣ��¼�������档����ο�scene.py�е�ע��
        self._scene=scene.Octree()
        # �洢�ûغ���ʩ���˵�δ����ļ��ܣ��ԡ����ID:����������ʽ���棬ÿ�غ�Ӧ���һ��
        self._castSkills={}
        # ���������������������¼�����������ȡ�����
        self._rand=myrand.MyRand()

    # ÿ�غϵ���һ�Σ����ν������¶�����
    # ��ظ������������б�д
    def update(self):
        # 1�����㼼��Ч��
        for playerId,skillName in self._castSkills:
            pass
        self._castSkills={}
        # 2���ƶ��������壨�ƺ�ֻ��������ƶ�����
        for playerId in self._players.keys():
            pass
        # 3���ж��ཻ������ԡ���ײ�������еȸ���Ч��
        for playerId in self._players.keys():
            pass
        # 4����������µ�ʳ���
        pass
        # 5��ʱ��+1
        self._time+=1

    # ��playerIdΪ-1�򷵻�ȫ���������壬����ֻ���ظ�ID�����Ұ������
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