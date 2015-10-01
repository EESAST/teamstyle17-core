# 自行实现的可控的随机数生成器，方便重现局面
# 采用Xor-shift算法，速度快，随机性一般但作为游戏随机源已足够
# 代码摘抄自https://ja.wikipedia.org/wiki/Xorshift
class MyRand:
    def __init__(self, seed=1234567890):
        if seed != 0:
            self._seed = seed & (1 << 32 - 1)
        else:
            self._seed = 1234567890

    def rand(self):
        self._seed = (self._seed ^ (self._seed << 13)) & (1 << 32 - 1)
        self._seed = (self._seed ^ (self._seed >> 17)) & (1 << 32 - 1)
        self._seed = (self._seed ^ (self._seed << 5)) & (1 << 32 - 1)
        return self._seed
