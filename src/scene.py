import copy

class Sphere:
    def __init__(self, center=(0, 0, 0), r=0):
        self.center = center
        self.radius = r


class Octree:
    class OctreeNode:
        _nodeSizeLimit = 4

        def __init__(self):
            # smallCorner和bigCorner分别为x,y,z均最小和均最大的那个角的坐标
            # 盒子的范围是inclusive的，即边界所在角、边、面均属于盒子范围内
            self.smallCorner = (0, 0, 0)
            self.bigCorner = (0, 0, 0)
            # 两个List分别为：由于压在边界上所以只能放在本结点的obj，可以放到下一层结点但出于效率考虑暂不往下放的obj
            self.fixedObjList = []
            self.pushableObjList = []
            # children格式：下标范围为0-7，二进制低起第1,2,3位分别代表x,y,z坐标是否大于中心（是为1否为0）
            self.children = []

        def center(self):
            return tuple((self.smallCorner[i] + self.bigCorner[i]) / 2 for i in range(3))

        def _makeChildren(self):
            center = self.center()
            self.children = []
            for i in range(0, 8):
                newCorner = tuple(self.smallCorner[j] if i & (2 ** j) == 0 else self.bigCorner[j] for j in range(3))
                newNode = Octree.OctreeNode()
                newNode.smallCorner = tuple((min(center[j], newCorner[j]) for j in range(3)))
                newNode.bigCorner = tuple((max(center[j], newCorner[j]) for j in range(3)))
                self.children.append(newNode)

        def _pushCode(self, obj: Sphere):
            center = self.center()
            if any((obj.center[i] - obj.radius < center[i]) ^ (obj.center[i] + obj.radius < center[i])
                   for i in range(3)):
                return -1
            else:
                return sum((obj.center[i] >= center[i]) * 2 ** i for i in range(3))

        def insert(self, objId: int, tree):
            obj = tree._objs.get(objId)
            code = self._pushCode(obj)
            if code == -1:
                self.fixedObjList.append(objId)
            else:
                self.pushableObjList.append(objId)
            self._pushIfNecessary(tree)

        def _pushIfNecessary(self, tree):
            if len(self.pushableObjList) == 0 or len(self.fixedObjList) + len(
                    self.pushableObjList) <= self._nodeSizeLimit:
                return
            else:
                if len(self.children) == 0:
                    self._makeChildren()
                for objId in self.pushableObjList:
                    code = self._pushCode(tree._objs[objId])
                    tree._paths[objId] += str(code)
                    self.children[code].insert(objId, tree)
                self.pushableObjList = []

        def delete(self, objId: int, route: str):
            if route == "":
                try:
                    self.fixedObjList.remove(objId)
                except:
                    pass
                try:
                    self.pushableObjList.remove(objId)
                except:
                    pass
            else:
                self.children[int(route[0])].delete(objId, route[1:])

        def intersect(self, obj: Sphere, tree, centerOnly: bool) -> list:
            def norm(p: tuple) -> float:
                return sum(p[i] ** 2 for i in range(3)) ** 0.5

            def vec(p1: tuple, p2: tuple) -> tuple:
                return tuple(p2[i] - p1[i] for i in range(3))

            def dot(p1: tuple, p2: tuple) -> int:
                return sum(p1[i] * p2[i] for i in range(3))

            def cross(p1: tuple, p2: tuple) -> tuple:
                return (p1[1] * p2[2] - p1[2] * p2[1], p1[2] * p2[0] - p1[0] * p2[2], p1[0] * p2[1] - p1[1] * p2[0])

            def insideSphere(obj: Sphere, point: tuple) -> bool:
                return norm(vec(obj.center, point)) < obj.radius

            def intersectWithSphere(obj1: Sphere, obj2: Sphere) -> bool:
                return norm(vec(obj1.center, obj2.center)) < obj1.radius + obj2.radius

            # 非常蛋疼，没有信心，求计算几何高手帮忙debug
            def intersectWithBox(obj: Sphere, small: tuple, big: tuple) -> bool:
                # 球心在正方体内显然可直接返回True
                if all(small[i] < obj.center[i] < big[i] for i in range(3)):
                    return True
                # 先判断正方体8个顶点是否有在球内的
                for i in range(0, 8):
                    corner = tuple(small[j] if i & (2 ** j) == 0 else big[j] for j in range(3))
                    if insideSphere(obj, corner):
                        return True
                # 若没有，则检查正方体的12条边是否有和球相交的
                for i1, i2 in [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
                               (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)]:
                    endpoint1 = tuple(small[j] if i1 & (2 ** j) == 0 else big[j] for j in range(3))
                    endpoint2 = tuple(small[j] if i2 & (2 ** j) == 0 else big[j] for j in range(3))
                    # 判断条件的含义为：圆心到线段所在直线的距离小于半径，且圆心与线段两端点连线与线段的有向角一锐一钝
                    # 按照计算几何惯例，全部用空间向量运算
                    if norm(cross(vec(obj.center, endpoint1), vec(obj.center, endpoint2))) \
                            / norm(vec(endpoint1, endpoint2)) < obj.radius \
                            and ((dot(vec(endpoint1, obj.center), vec(endpoint1, endpoint2)) > 0)
                                     ^ (dot(vec(endpoint2, obj.center), vec(endpoint2, endpoint1)) > 0)):
                        return True
                # 若没有，则检查正方体的6个面是否有和球相交的
                for i in range(0, 6):
                    upper = [1e10 if i // 2 == j else big[j] for j in range(3)]
                    lower = [-1e10 if i // 2 == j else small[j] for j in range(3)]
                    unitNorm = tuple(1 if i // 2 == j else 0 for j in range(3))
                    corner = small if i % 2 == 0 else big
                    # 判断条件的含义为：圆心到面的投影在面内，且圆心到面的距离小于圆的半径
                    if sum(lower[j] < obj.center[j] < upper[j] for j in range(3)) == 3 \
                            and abs(dot(unitNorm, vec(obj.center, corner))) < obj.radius:
                        return True
                return False

            ans = list(
                filter((lambda objId: insideSphere(obj, tree._objs[objId].center)) if centerOnly \
                           else (lambda objId: intersectWithSphere(obj, tree._objs[objId])),
                       self.fixedObjList + self.pushableObjList))
            if len(self.children) > 0:
                for ch in self.children:
                    if intersectWithBox(obj, ch.smallCorner, ch.bigCorner):
                        ans.extend(ch.intersect(obj, tree, centerOnly))
            return ans

    def __init__(self, mapSize=1000000):
        self._root = self.OctreeNode()
        self._root.bigCorner = (mapSize, mapSize, mapSize)
        self._objs = {}
        self._paths = {}

    # 添加ID为objId的球体obj
    def insert(self, obj: Sphere, objId: int):
        if self._objs.get(objId) is not None:
            raise ValueError
        self._objs[objId] = copy.copy(obj)
        self._paths[objId] = ""
        self._root.insert(objId, self)

    def getObject(self, objId: int):
        return copy.copy(self._objs.get(objId))

    # 将ID为objId的球体换成obj
    def modify(self, obj: Sphere, objId: int):
        if self._objs.get(objId) is None:
            raise ValueError
        self._root.delete(objId, self._paths[objId])
        self._objs[objId]=copy.copy(obj)
        self._paths[objId]=""
        self._root.insert(objId, self)

    # 删除ID为objId的物体
    def delete(self, objId: int):
        self._root.delete(objId, self._paths[objId])
        self._objs.pop(objId)
        self._paths.pop(objId)

    # 若centerOnly为True则返回所有球心在obj内的物体，否则返回所有与obj相交的物体
    # 提示：既可用于判断相交，也可用于获取视野内物体
    # 注意：若obj恰为树中某个物体，是会返回该物体本身的
    def intersect(self, obj: Sphere, centerOnly=False) -> list:
        return self._root.intersect(obj, self, centerOnly)
