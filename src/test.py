import unittest
import myrand
import scene
import time
import gamemain



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
        number= 100
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


class GameMaintest(unittest.TestCase):
    def setUp(self):
        self.game=gamemain.GameMain(0)
        self.player1=gamemain.PlayerStatus()
        self.player0=gamemain.PlayerStatus()
        self.player0.health=1000
        self.player1.health=1331
        self.game._players={0:self.player0,1:self.player1}
        self.game._scene.insert((scene.Sphere((10000,10000,10000),10)),0)
        self.game._scene.insert((scene.Sphere((10100,10100,10100),11)),1)

    """def testMove(self):
        self.player0.speed=(1,0,0)
        self.game.update()
        self.assertEqual(self.game._scene.getObject(0).center,(100100,10000,10000))"""

    def testSkillShop(self):
        self.game.upgradeSkill(0,"longAttack")
        self.assertEqual(self.player0.ability,0,"money is not enough")
        self.assertEqual(self.player0.skills,{})
        self.player0.ability=1;
        self.game.upgradeSkill(0,"shield")
        self.assertEqual(self.player0.ability,1,"money is not enough")
        self.assertEqual(self.player0.skills,{})
        self.player0.ability=10000;
        self.game.upgradeSkill(0,"longAttack")
        self.assertEqual(self.player0.ability,9999,"ability is wrong")
        self.assertEqual(self.player0.skills,{"longAttack":1})
        self.game.upgradeSkill(0,"shortAttack")
        self.assertEqual(self.player0.ability,9997,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":1,"longAttack":1})
        self.game.upgradeSkill(0,"shield")
        self.assertEqual(self.player0.ability,9989,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":1,"longAttack":1,"shield":1})
        self.game.upgradeSkill(0,"teleport")
        self.assertEqual(self.player0.ability,9973,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":1,"longAttack":1,"shield":1,"teleport":1})
        self.game.upgradeSkill(0,"visionUp")
        self.assertEqual(self.player0.ability,9941,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":1,"longAttack":1,"shield":1,"teleport":1,"visionUp":1})
        self.assertEqual(self.player0.vision,1000)
        self.game.upgradeSkill(0,"healthUp")
        self.assertEqual(self.player0.ability,9909,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":1,"longAttack":1,"shield":1,"teleport":1,"visionUp":1,"healthUp":1})
        self.assertEqual(self.player0.health,3500)
        self.game.upgradeSkill(0,"longAttack")
        self.assertEqual(self.player0.ability,9907,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":1,"longAttack":2,"shield":1,"teleport":1,"visionUp":1,"healthUp":1})
        self.game.upgradeSkill(0,"shortAttack")
        self.assertEqual(self.player0.ability,9905,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":2,"longAttack":2,"shield":1,"teleport":1,"visionUp":1,"healthUp":1})
        self.game.upgradeSkill(0,"shield")
        self.assertEqual(self.player0.ability,9901,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":2,"longAttack":2,"shield":2,"teleport":1,"visionUp":1,"healthUp":1})
        self.game.upgradeSkill(0,"teleport")
        self.assertEqual(self.player0.ability,9897,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":2,"longAttack":2,"shield":2,"teleport":2,"visionUp":1,"healthUp":1})
        self.game.upgradeSkill(0,"visionUp")
        self.assertEqual(self.player0.ability,9893,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":2,"longAttack":2,"shield":2,"teleport":2,"visionUp":2,"healthUp":1})
        self.assertEqual(self.player0.vision,1500)
        self.game.upgradeSkill(0,"healthUp")
        self.assertEqual(self.player0.ability,9891,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":2,"longAttack":2,"shield":2,"teleport":2,"visionUp":2,"healthUp":2})
        self.assertEqual(self.player0.health,5500)
        self.game.upgradeSkill(0,"longAttack")
        self.assertEqual(self.player0.ability,9887,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":2,"longAttack":3,"shield":2,"teleport":2,"visionUp":2,"healthUp":2})
        self.game.upgradeSkill(0,"shortAttack")
        self.assertEqual(self.player0.ability,9883,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":3,"longAttack":3,"shield":2,"teleport":2,"visionUp":2,"healthUp":2})
        self.game.upgradeSkill(0,"shield")
        self.assertEqual(self.player0.ability,9875,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":3,"longAttack":3,"shield":3,"teleport":2,"visionUp":2,"healthUp":2})
        self.game.upgradeSkill(0,"teleport")
        self.assertEqual(self.player0.ability,9867,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":3,"longAttack":3,"shield":3,"teleport":3,"visionUp":2,"healthUp":2})
        self.game.upgradeSkill(0,"visionUp")
        self.assertEqual(self.player0.ability,9859,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":3,"longAttack":3,"shield":3,"teleport":3,"visionUp":3,"healthUp":2})
        self.assertEqual(self.player0.vision,2000)
        self.game.upgradeSkill(0,"healthUp")
        self.assertEqual(self.player0.ability,9855,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":3,"longAttack":3,"shield":3,"teleport":3,"visionUp":3,"healthUp":3})
        self.assertEqual(self.player0.health,7500)
        self.game.upgradeSkill(0,"longAttack")
        self.assertEqual(self.player0.ability,9847,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":3,"longAttack":4,"shield":3,"teleport":3,"visionUp":3,"healthUp":3})
        self.game.upgradeSkill(0,"shortAttack")
        self.assertEqual(self.player0.ability,9839,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":4,"longAttack":4,"shield":3,"teleport":3,"visionUp":3,"healthUp":3})
        self.game.upgradeSkill(0,"shield")
        self.assertEqual(self.player0.ability,9823,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":4,"longAttack":4,"shield":4,"teleport":3,"visionUp":3,"healthUp":3})
        self.game.upgradeSkill(0,"teleport")
        self.assertEqual(self.player0.ability,9807,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":4,"longAttack":4,"shield":4,"teleport":4,"visionUp":3,"healthUp":3})
        self.game.upgradeSkill(0,"visionUp")
        self.assertEqual(self.player0.ability,9791,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":4,"longAttack":4,"shield":4,"teleport":4,"visionUp":4,"healthUp":3})
        self.assertEqual(self.player0.vision,2500)
        self.game.upgradeSkill(0,"healthUp")
        self.assertEqual(self.player0.ability,9783,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":4,"longAttack":4,"shield":4,"teleport":4,"visionUp":4,"healthUp":4})
        self.assertEqual(self.player0.health,9500)
        self.game.upgradeSkill(0,"longAttack")
        self.assertEqual(self.player0.ability,9767,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":4,"longAttack":5,"shield":4,"teleport":4,"visionUp":4,"healthUp":4})
        self.game.upgradeSkill(0,"shortAttack")
        self.assertEqual(self.player0.ability,9751,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":4,"teleport":4,"visionUp":4,"healthUp":4})
        self.game.upgradeSkill(0,"shield")
        self.assertEqual(self.player0.ability,9719,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":5,"teleport":4,"visionUp":4,"healthUp":4})
        self.game.upgradeSkill(0,"teleport")
        self.assertEqual(self.player0.ability,9687,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":5,"teleport":5,"visionUp":4,"healthUp":4})
        self.game.upgradeSkill(0,"visionUp")
        self.assertEqual(self.player0.ability,9655,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":5,"teleport":5,"visionUp":5,"healthUp":4})
        self.assertEqual(self.player0.vision,3000)
        self.game.upgradeSkill(0,"healthUp")
        self.assertEqual(self.player0.ability,9639,"ability is wrong")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":5,"teleport":5,"visionUp":5,"healthUp":5})
        self.assertEqual(self.player0.health,11500)
        self.game.upgradeSkill(0,"longAttack")
        self.assertEqual(self.player0.ability,9639,"skill can't be improved")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":5,"teleport":5,"visionUp":5,"healthUp":5})
        self.game.upgradeSkill(0,"shortAttack")
        self.assertEqual(self.player0.ability,9639,"skill can't be improved")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":5,"teleport":5,"visionUp":5,"healthUp":5})
        self.game.upgradeSkill(0,"shield")
        self.assertEqual(self.player0.ability,9639,"skill can't be improved")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":5,"teleport":5,"visionUp":5,"healthUp":5})
        self.game.upgradeSkill(0,"teleport")
        self.assertEqual(self.player0.ability,9639,"skill can't be improved")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":5,"teleport":5,"visionUp":5,"healthUp":5})
        self.game.upgradeSkill(0,"visionUp")
        self.assertEqual(self.player0.ability,9639,"skill can't be improved")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":5,"teleport":5,"visionUp":5,"healthUp":5})
        self.assertEqual(self.player0.vision,3000)
        self.game.upgradeSkill(0,"healthUp")
        self.assertEqual(self.player0.ability,9639,"skill can't be improved")
        self.assertEqual(self.player0.skills,{"shortAttack":5,"longAttack":5,"shield":5,"teleport":5,"visionUp":5,"healthUp":5})
        self.assertEqual(self.player0.health,11500)

    def testEat(self):
        self.now=self.player1.health
        self.player0.speed=(47,47,47)
        self.game.update()
        self.assertTrue(self.player1.health<now+100)
        self.now=self.player1.health
        self.game.update()
        self.assertTrue(self.player1.health<now+1100)
        self.assertTrue(self.player1.health>=now+1000)
        self.assertNotIn(0,self._scene.intersect(self._scene.getObject(1)))

    def testshield_level4(self):
        self.player0.ability=100
        for x in range(4):
            self.game.upgradeSkill(0,"shield")
        self.game._castSkills[0]="shield"
        self.player0.speed=(47,47,47)
        self.now=self.player1.health
        self.game.update()
        self.assertTrue(self.game._castSkills=={},"castSkills is not empty")
        self.assertTrue(self.player1.health<now+100)
        self.assertEqual(self.player0.shieldTime,160)
        self.now=self.player1.health
        self.game.update()
        self.assertTrue(self.player1.health<now+100)
        self.assertTrue(0 in self._scene.intersect(self._scene.getObject(1)))
        self.assertEqual(self.player0.shieldTime,159)
        self.player0.speed=(0,0,0)
        self.now=self.player1.health
        for x in range(158)
            self.game.update()
            self.assertTrue(self.player1.health<now+100)
            self.assertTrue(0 in self._scene.intersect(self._scene.getObject(1)))
            self.assertEqual(self.player0.shieldTime,158-x)
            self.now=self.player1.health
        self.now1=self.player0.health
        self.game.update()
        self.assertTrue(self.player1.health<now+1100)
        self.assertTrue(self.player1.health>=now+now1)
        self.assertTrue(0 not in self._scene.intersect(self._scene.getObject(1)))






if __name__ == "__main__":
    unittest.main()
