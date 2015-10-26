import unittest
import myrand


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


class OctreeTest(unittest.TestCase):
    def setUp(self):
        import scene
        self.scene = scene
        self.tree = scene.Octree()

    def testBasic(self):
        sp1 = self.scene.Sphere((123456, 123456, 123456), 90000)
        sp2 = self.scene.Sphere((234567, 234567, 234567), 90000)
        self.tree.insert(sp1, 0)
        self.tree.insert(sp2, 1)
        sp3 = self.scene.Sphere((179011, 179011, 179011), 10000)
        self.assertEqual(self.tree.intersect(sp3, True), [])
        tmpResult = self.tree.intersect(sp3, False)
        tmpResult.sort()
        self.assertEqual(tmpResult, [0, 1])
        self.tree.delete(0)
        self.assertEqual(self.tree.intersect(sp3, False), [1])

    def testAgain(self):
        number = 100
        sqr = lambda x: x * x
        rand = myrand.MyRand()
        sp = []
        for i in range(number):
            sp.append(self.scene.Sphere(
                (rand.rand() % 800000 + 100000, rand.rand() % 800000 + 100000, rand.rand() % 800000 + 100000),
                rand.rand() % 100000))
            self.tree.insert(sp[i], i)
        for i in range(number):
            temp = []
            for j in range(number):
                if sqr(sp[i].center[0] - sp[j].center[0]) + sqr(sp[i].center[1] - sp[j].center[1]) + sqr(
                                sp[i].center[2] - sp[j].center[2]) < sqr(sp[i].radius):
                    temp.append(j)
            treeResult = self.tree.intersect(sp[i], True)
            treeResult.sort()
            self.assertEqual(treeResult, temp)
            temp = []
            for j in range(number):
                if sqr(sp[i].center[0] - sp[j].center[0]) + sqr(sp[i].center[1] - sp[j].center[1]) + sqr(
                                sp[i].center[2] - sp[j].center[2]) < sqr(sp[i].radius + sp[j].radius):
                    temp.append(j)
            treeResult = self.tree.intersect(sp[i], False)
            treeResult.sort()
            self.assertEqual(treeResult, temp)


if __name__ == "__main__":
    unittest.main()
