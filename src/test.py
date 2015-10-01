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


if __name__ == "__main__":
    unittest.main()
