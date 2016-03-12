# 自行实现的可控的随机数生成器，方便重现局面
# 采用Xor-shift算法，速度快，随机性一般但作为游戏随机源已足够
# 代码摘抄自https://ja.wikipedia.org/wiki/Xorshift
class MyRand:
    def __init__(self, seed=1234567890):
        if seed != 0:
            self._seed = seed & 0xFFFFFFFF
        else:
            self._seed = 1234567890

    # 产生一个[1,2^32-1]的随机数（Xorshift算法并不会产生0）
    def rand(self) -> int:
        self._seed = (self._seed ^ (self._seed << 13)) & 0xFFFFFFFF
        self._seed = (self._seed ^ (self._seed >> 17)) & 0xFFFFFFFF
        self._seed = (self._seed ^ (self._seed << 5)) & 0xFFFFFFFF
        return self._seed

    # 产生一个[0,maxRand-1]的随机数
    def randIn(self, maxRand: int) -> int:
        lim = 0xFFFFFFFF // maxRand * maxRand
        t = self.rand() - 1
        while t >= lim:
            t = self.rand() - 1
        else:
            return t % maxRand

    # 将一个List随机打乱
    def shuffle(self, ls: list) -> list:
        n = len(ls)
        for i in range(n - 1):
            xchg = self.randIn(n - i) + i
            ls[i], ls[xchg] = ls[xchg], ls[i]
