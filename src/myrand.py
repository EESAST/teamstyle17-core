# ����ʵ�ֵĿɿص���������������������־���
# ����Xor-shift�㷨���ٶȿ죬�����һ�㵫��Ϊ��Ϸ���Դ���㹻
# ����ժ����https://ja.wikipedia.org/wiki/Xorshift
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
