import unittest
import myrand
import scene
import time
import gamemain

sp=[]
temp=[]
tree=scene.Octree()
class MyRandTest(unittest.TestCase):
    def setUp(self):
        import myrand, time
        self.myrand = myrand
        self.time = time

    def testRange(self):
        rand = self.myrand.MyRand()
        for _ in range(0, 1000):
            num = rand.rand()
            self.assertTrue(0 <= num < 1 << 32)

    def testReproduce(self):
        rand = self.myrand.MyRand(int(self.time.time()))
        seed = rand.rand()
        rand._seed = seed
        randList1 = [rand.rand() for _ in range(0, 1000)]
        rand._seed = seed
        randList2 = [rand.rand() for _ in range(0, 1000)]
        self.assertEqual(randList1, randList2)
def sqr(x):
    return x*x

class OctreeTest(unittest.TestCase):
    def setUp(self):
        import scene
        self.scene = scene
        self.tree = scene.Octree()

    def testBasic(self):
        sp1 = self.scene.Sphere((123456, 123456, 123456), 100000)
        sp2 = self.scene.Sphere((234567, 234567, 234567), 100000)
        self.tree.insert(sp1, 0)
        self.tree.insert(sp2, 1)
        sp3 = self.scene.Sphere((166666, 166666, 166666), 10000)
        self.assertEqual(self.tree.intersect(sp3, True), [])
        self.assertEqual(set(self.tree.intersect(sp3, False)), {0, 1})
        self.tree.delete(0)
        self.assertEqual(self.tree.intersect(sp3, False), [1])

    def testAgain(self):
        number=5
        self.rand=myrand.MyRand(int(time.time()))
        sp=[]
        for i in range(number):
            sp.append(self.scene.Sphere((self.rand.rand(),self.rand.rand(),self.rand.rand()),self.rand.rand()))
            tree.insert(sp[i],i)
        for i in range(number):
            temp=[]
            for j in range(number):
                if sqr(sp[i].center[0]-sp[j].center[0])+sqr(sp[i].center[1]-sp[j].center[1])+sqr(sp[i].center[2]-sp[j].center[2])<sqr(sp[i].radius):
                    temp.append(j)
            print(temp)
            self.assertEqual(tree.intersect(sp[i],True),temp)
            temp=[]
            for j in range(number):
                if sqr(sp[i].center[0]-sp[j].center[0])+sqr(sp[i].center[1]-sp[j].center[1])+sqr(sp[i].center[2]-sp[j].center[2])<sqr(sp[i].radius+sp[j].radius):
                    temp.append(j)
            self.assertEqual(tree.intersect(sp[i],False),temp)

class GameMaintest(unittest.TestCase):
    def setUp(self):
        self.game=gamemain.GameMain()
        self.player1=gamemain.PlayerStatus()
        self.player2=gamemain.PlayerStatus()

    def test




if __name__ == "__main__":
    unittest.main()
