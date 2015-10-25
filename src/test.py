import unittest


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
        sp1 = self.scene.Sphere((123456, 123456, 123456), 100000)
        sp2 = self.scene.Sphere((234567, 234567, 234567), 100000)
        self.tree.insert(sp1, 0)
        self.tree.insert(sp2, 1)
        sp3 = self.scene.Sphere((166666, 166666, 166666), 10000)
        self.assertEqual(self.tree.intersect(sp3, True), [])
        self.assertEqual(set(self.tree.intersect(sp3, False)), {0, 1})
        self.tree.delete(0)
        self.assertEqual(self.tree.intersect(sp3, False), [1])


if __name__ == "__main__":
    unittest.main()
