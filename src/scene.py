class Sphere:
    def __init__(self):
        self.center = (0, 0, 0)
        self.radius = 0


class OctreeNode:
    _nodeSizeLimit = 4

    def __init__(self):
        # smallCorner和bigCorner分别为x,y,z均最小和均最大的那个角的坐标
        # 盒子的范围是inclusive的，即边界所在角、边、面均属于盒子范围内
        self.smallCorner = (0, 0, 0)
        self.bigCorner = (0, 0, 0)
        # 两者分别为：由于压在边界上所以只能放在本结点的obj，可以放到下一层结点但出于效率考虑暂不往下放的obj
        self.fixedObjList = []
        self.pushableObjList = []
        # children格式：下标范围为0-7，二进制低起第1,2,3位分别代表x,y,z坐标是否大于中心（是为1否为0）
        self.children = []

    def center(self):
        return tuple((self.smallCorner[i] + self.bigCorner[i]) // 2 for i in range(0, 3))

    def _deleteChildren(self):
        self.children = []

    def _makeChildren(self):
        center = self.center()
        self._deleteChildren()
        for i in range(0, 8):
            newCorner = tuple(self.smallCorner[j] if i & (2 ** j) == 0 else self.bigCorner[j] for j in range(0, 3))
            newNode = OctreeNode()
            # 中心坐标本身统一归到坐标较大的那半
            newNode.smallCorner = tuple((min(center[j], newCorner[j]) for j in range(0, 3)))
            newNode.bigCorner = tuple((max(center[j] - 1, newCorner[j]) for j in range(0, 3)))
            self.children.append(newNode)

    def _pushCode(self, obj: Sphere):
        center = self.center()
        if sum(obj.center[i] - obj.radius < center[i] ^ obj.center[i] - obj.radius < center[i] for i in
               range(0, 3)) != 0:
            return -1
        else:
            return sum((obj.center[i] >= center[i]) * 2 ** i for i in range(0, 3))

    def insert(self, objId: int, tree: Octree):
        obj = tree._objs.get(objId)
        code = self._pushCode(obj)
        if code == -1:
            self.fixedObjList.append(obj)
        else:
            self.pushableObjList.append(obj)
            self._pushIfNecessary(tree)

    def _pushIfNecessary(self, tree: Octree):
        if len(self.pushableObjList) == 0 or len(self.fixedObjList) + len(self.pushableObjList) <= self._nodeSizeLimit:
            return
        else:
            if len(self.children) == 0:
                self._makeChildren()
            for objId in self.pushableObjList:
                code = self._pushCode(tree._objs.get(objId))
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

    def insideList(self, obj: Sphere, tree: Octree):
        def norm(p: tuple) -> float:
            return sum(p[i] ** 2 for i in range(0, 3)) ** 0.5

        def vec(p1: tuple, p2: tuple) -> tuple:
            return tuple(p2[i] - p1[i] for i in range(0, 3))

        def dot(p1: tuple, p2: tuple) -> int:
            return sum(p1[i] * p2[i] for i in range(0, 3))

        def cross(p1: tuple, p2: tuple) -> tuple:
            return (p1[1] * p2[2] - p1[2] * p2[1], p1[2] * p2[0] - p1[0] * p2[2], p1[0] * p2[1] - p1[1] * p2[0])

        def insideSphere(obj: Sphere, point: tuple):
            return norm(vec(obj.center, point)) < obj.radius

        def intersectWithBox(obj: Sphere, small: tuple, big: tuple) -> bool:
            for i in range(0, 8):
                corner = tuple(small[j] if i & (2 ** j) == 0 else big[j] for j in range(0, 3))
                if insideSphere(obj, corner):
                    return True
            for i1, i2 in [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3), (2, 6), (3, 7), (4, 5), (4, 6), (5, 7),
                           (6, 7)]:
                endpoint1 = tuple(small[j] if i1 & (2 ** j) == 0 else big[j] for j in range(0, 3))
                endpoint2 = tuple(small[j] if i2 & (2 ** j) == 0 else big[j] for j in range(0, 3))
                if norm(cross(vec(obj.center, endpoint1), vec(obj.center, endpoint2))) / norm(
                        vec(endpoint1, endpoint2)) < obj.radius \
                        and (dot(vec(endpoint1, obj.center), vec(endpoint1, endpoint2)) > 0 ^ dot(
                            vec(endpoint2, obj.center), vec(endpoint2, endpoint1)) > 0):
                    return True
            for i in range(0, 6):
                upper = [1e10 if i // 2 == j else big[j] for j in range(0, 3)]
                lower = [-1e10 if i // 2 == j else small[j] for j in range(0, 3)]
                unitNorm = tuple(1 if i // 2 == j else 0 for j in range(0, 3))
                corner = small if i % 2 == 0 else big
                if sum(lower[j] < obj.center[j] < upper[j] for j in range(0, 3)) == 3 \
                        and abs(dot(unitNorm, vec(obj.center, corner))) < obj.radius:
                    return True
            return False

        ans = list(
            filter(lambda objId: insideSphere(obj, tree._objs[objId].center), self.fixedObjList + self.pushableObjList))
        if len(self.children) > 0:
            for ch in self.children:
                if intersectWithBox(obj, ch.smallCorner, ch.bigCorner):
                    ans.extend(ch.insideList(obj, tree))
        return ans


class Octree:
    _mapSize = 1000000

    def __init__(self):
        self._root = OctreeNode()
        self._root.bigCorner = (self._mapSize, self._mapSize, self._mapSize)
        self._objs = {}
        self._paths = {}

    def insert(self, obj: Sphere, objId: int):
        self._objs[objId] = obj
        self._paths[objId] = ""
        self._root.insert(objId, self)

    def delete(self, objId: int):
        self._root.delete(objId, self._paths[objId])
        self._objs.pop(objId)
        self._paths.pop(objId)

    def move(self, objId: int, delta: tuple):
        pass

    def insideList(self, obj: Sphere, centerOnly=True) -> list:
        return self._root.insideList(obj, self)
