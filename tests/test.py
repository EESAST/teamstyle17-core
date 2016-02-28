import unittest, time
from ts17core import myrand, scene, gamemain


class MyRandTest(unittest.TestCase):
    def testRange(self):
        rand = myrand.MyRand()
        for _ in range(0, 1000):
            num = rand.rand()
            self.assertTrue(0 <= num < 1 << 32)

    def testReproduce(self):
        rand = myrand.MyRand(int(time.time()))
        seed = rand.rand()
        rand._seed = seed
        randList1 = [rand.rand() for _ in range(0, 1000)]
        rand._seed = seed
        randList2 = [rand.rand() for _ in range(0, 1000)]
        self.assertEqual(randList1, randList2)


class OctreeTest(unittest.TestCase):
    def setUp(self):
        self.tree = scene.Octree()

    def testBasic(self):
        sp1 = scene.Sphere((123456, 123456, 123456), 90000)
        sp2 = scene.Sphere((234567, 234567, 234567), 90000)
        self.tree.insert(sp1, 0)
        self.tree.insert(sp2, 1)
        sp3 = scene.Sphere((179011, 179011, 179011), 10000)
        self.assertEqual(self.tree.intersect(sp3, True), [])
        tmpResult = self.tree.intersect(sp3, False)
        tmpResult.sort()
        self.assertEqual(tmpResult, [0, 1])
        self.tree.delete(0)
        self.assertEqual(self.tree.intersect(sp3, False), [1])

    def testAgainstNaiveImpl(self):
        number = 100
        sqr = lambda x: x * x
        rand = myrand.MyRand()
        sp = []
        for i in range(number):
            sp.append(scene.Sphere(
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


class GameMainTest(unittest.TestCase):
    def setUp(self):
        self.game = gamemain.GameMain(0, 2, lambda _: None)
        self.game.addNewPlayer(0, (100, 100, 100), 20)
        self.game.addNewPlayer(1, (10100, 10100, 10100), 30)
        self.game.addNewPlayer(2, (10000, 10000, 10000), 10)
        self.player1 = self.game._players[1]
        self.player2 = self.game._players[2]

    def testMove(self):
        self.player2.speed = (10, 0, 0)
        self.game.update()
        self.assertEqual(self.game._scene.getObject(2).center, (10010, 10000, 10000))

    def testSkillShop(self):
        self.game.upgradeSkill(2, "longAttack")
        self.assertEqual(self.player2.ability, 0, "money is not enough")
        self.assertEqual(self.player2.skills, {})
        self.player2.ability = 1
        self.game.upgradeSkill(2, "shield")
        self.assertEqual(self.player2.ability, 1, "money is not enough")
        self.assertEqual(self.player2.skills, {})
        self.player2.ability = 10000
        for x in range(5):
            self.game.upgradeSkill(2, "longAttack")
            self.assertEqual(self.player2.ability, 10000 - 2 ** (x + 1) + 1, "ability is wrong")
            self.assertEqual(self.player2.skills, {"longAttack": x + 1})
        for x in range(5):
            self.game.upgradeSkill(2, "shortAttack")
            self.assertEqual(self.player2.ability, 9969 - 2 ** (x + 1), "ability is wrong")
            self.assertEqual(self.player2.skills, {"shortAttack": x + 1, "longAttack": 5})
        for x in range(5):
            self.game.upgradeSkill(2, "shield")
            self.assertEqual(self.player2.ability, 9937 - 2 ** (x + 2) - 4, "ability is wrong")
            self.assertEqual(self.player2.skills, {"shortAttack": 5, "longAttack": 5, "shield": x + 1})
        for x in range(5):
            self.game.upgradeSkill(2, "teleport")
            self.assertEqual(self.player2.ability, 9869 - 2 ** (x + 2) - 12, "ability is wrong")
            self.assertEqual(self.player2.skills, {"shortAttack": 5, "longAttack": 5, "shield": 5, "teleport": x + 1})
        for x in range(5):
            self.game.upgradeSkill(2, "visionUp")
            self.assertEqual(self.player2.ability, 9793 - 2 ** (x + 2) - 28, "ability is wrong")
            self.assertEqual(self.player2.skills,
                             {"shortAttack": 5, "longAttack": 5, "shield": 5, "teleport": 5, "visionUp": x + 1})
            self.assertEqual(self.player2.vision, 1000 + 500 * (x + 1))
        for x in range(5):
            self.game.upgradeSkill(2, "healthUp")
            self.assertEqual(self.player2.ability, 9701 - 2 ** (x + 1) - 30, "ability is wrong")
            self.assertEqual(self.player2.skills,
                             {"shortAttack": 5, "longAttack": 5, "shield": 5, "teleport": 5, "visionUp": 5,
                              "healthUp": x + 1})
            self.assertEqual(self.player2.health, 3000 + 2000 * x)
        self.game.upgradeSkill(2, "longAttack")
        self.assertEqual(self.player2.ability, 9639, "skill can't be improved")
        self.assertEqual(self.player2.skills,
                         {"shortAttack": 5, "longAttack": 5, "shield": 5, "teleport": 5, "visionUp": 5, "healthUp": 5})
        self.game.upgradeSkill(2, "shortAttack")
        self.assertEqual(self.player2.ability, 9639, "skill can't be improved")
        self.assertEqual(self.player2.skills,
                         {"shortAttack": 5, "longAttack": 5, "shield": 5, "teleport": 5, "visionUp": 5, "healthUp": 5})
        self.game.upgradeSkill(2, "shield")
        self.assertEqual(self.player2.ability, 9639, "skill can't be improved")
        self.assertEqual(self.player2.skills,
                         {"shortAttack": 5, "longAttack": 5, "shield": 5, "teleport": 5, "visionUp": 5, "healthUp": 5})
        self.game.upgradeSkill(2, "teleport")
        self.assertEqual(self.player2.ability, 9639, "skill can't be improved")
        self.assertEqual(self.player2.skills,
                         {"shortAttack": 5, "longAttack": 5, "shield": 5, "teleport": 5, "visionUp": 5, "healthUp": 5})
        self.game.upgradeSkill(2, "visionUp")
        self.assertEqual(self.player2.ability, 9639, "skill can't be improved")
        self.assertEqual(self.player2.skills,
                         {"shortAttack": 5, "longAttack": 5, "shield": 5, "teleport": 5, "visionUp": 5, "healthUp": 5})
        self.assertEqual(self.player2.vision, 3500)
        self.game.upgradeSkill(2, "healthUp")
        self.assertEqual(self.player2.ability, 9639, "skill can't be improved")
        self.assertEqual(self.player2.skills,
                         {"shortAttack": 5, "longAttack": 5, "shield": 5, "teleport": 5, "visionUp": 5, "healthUp": 5})
        self.assertEqual(self.player2.health, 11000)

    def testEat(self):
        now = self.player1.health
        self.player2.speed = (47, 47, 47)
        self.game.update()
        self.assertTrue(self.player1.health < now + 100)
        now = self.player1.health
        self.game.update()
        self.assertTrue(self.player1.health < now + 1100)
        self.assertTrue(self.player1.health >= now + 1000)
        self.assertTrue(self.game._gameEnd)

    def testshield_level4(self):
        self.player2.ability = 100
        for x in range(4):
            self.game.upgradeSkill(2, "shield")
        self.game.castSkill(2, "shield")
        self.player2.speed = (47, 47, 47)
        now = self.player1.health
        self.game.update()
        self.assertTrue(self.game._castSkills == {}, "castSkills is not empty")
        self.assertTrue(self.player1.health < now + 100)
        self.assertEqual(self.player2.shieldTime, 160)
        now = self.player1.health
        self.game.update()
        self.assertTrue(self.player1.health < now + 100)
        self.assertEqual(self.player2.shieldTime, 159)
        self.player2.speed = (0, 0, 0)
        now = self.player1.health
        for x in range(159):
            self.game.update()
            self.assertTrue(self.player1.health < now + 100)
            self.assertEqual(self.player2.shieldTime, 158 - x)
            self.now = self.player1.health
        now1 = self.player2.health
        self.game.update()
        self.assertTrue(self.player1.health < now + 1100)
        self.assertTrue(self.player1.health >= now + now1)
        self.assertTrue(self.game._gameEnd)

    def tsetshortattack(self):
        self.player2.speed = (50, 50, 50)
        self.game.update()
        self.player2.speed = (0, 0, 0)
        self.game.upgradeSkill(2, "shortAttack")
        self.game.castSkill(2, "shortAttack")
        self.assertTrue(self.player2.health >= 1000, "shortAttack to fast")
        self.game.update()
        self.assertTrue(self.player1.health < 331 + 100, "shortAttack is wrong")
        self.assertTrue(self.player2.health < 1000, "shortAtack without cost")

    def testteleport(self):
        self.player2.ability = 100
        self.game.upgradeSkill(2, "teleport")
        self.temp = self.game.playerPos(2)
        self.game.castSkill(2, "teleport", dst=(10010, 10010, 10010))
        self.assertTrue(self.game.playerPos(2) == self.temp, "move too fast")
        self.game.update()
        self.assertEqual(self.game.playerPos(2), (10010, 10010, 10010), "teleport wrong")

    def testlongAttack(self):
        self.player2.ability = 100
        self.game.upgradeSkill(2, "longAttack")
        self.game.castSkill(2, "longAttack", player=1)
        self.assertTrue(self.player2.health == 1000, "longAttack to fast")
        self.game.update()
        self.assertEqual(self.player2.health, 990, "no longAttack")
        self.assertTrue(self.player1.health >= 2197, "longAttack speed is wrong")
        temp = self.player1.health
        self.assertTrue(20 in self.game._objects)
        self.game.update()
        self.assertTrue(self.game._objects[20].type == "None")
        self.assertTrue(self.player1.health == temp - 100, "longAttack is wrong")
