from ctypes.wintypes import POINT
from multiprocessing.connection import wait
from pickle import TRUE
from random import random
from re import A
from turtle import distance
from grpc import protos
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race, AIBuild
from sc2.main import run_game
from sc2.player import Bot, Computer, Human, Observer
from sc2 import maps

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit

import random



gameMap = "ThunderbirdLE"

class stateOfAI_Mind():
    def __init__(self):
        self.state = [False, False, False, False, False, True, False]
        self.stateString = ["stalkerDefend", "defend", "fullDefend", "attack", "fullAttack", "wait", "retreat"]

        self.pointOfDefence: any 

    async def setPointOfDefence(self, point):
        self.pointOfDefence = point

    async def stalkerDefend(self):
        await self.setState(0) 

    async def defend(self):
        await self.setState(1)
    
    async def fullDefend(self):
        await self.setState(2)

    async def attack(self):
        await self.setState(3)

    async def fullAttack(self):
        await self.setState(4)

    async def wait(self):
        await self.setState(5)

    async def retreat(self):
        await self.setState(6)



    async def setState(self, index):
        for x in range(len(self.state)):
            self.state[x] = False
        
        self.state[index] = True


    async def getState(self):
        index = 0

        for s in self.state:
            if s:
                return self.stateString[index]

            index += 1
            
    


class MaslakBot(BotAI):
    stateOfAI = stateOfAI_Mind()

    maslakAmountOfNexuses = 1
    maslakCorner = 1
    maslakCorner_PylonXY = POINT(10, -6)

    lastEnemySupply = 0

    nonAttackCounter = 0
    lastTimeWhenAttacked = 0
    


    async def on_start(self):

        if self.townhalls.first.position[0] < self.townhalls.first.position[1]:
                self.maslakCorner = 1
        else:
            self.maslakCorner = -1

        self.mainNexus = self.townhalls.first
        self.stateOfAI.setPointOfDefence(self.mainNexus)



    async def on_building_construction_complete(self, unit: Unit):
        if unit.type_id == UnitTypeId.ASSIMILATOR or unit.type_id == UnitTypeId.NEXUS:
            await self.distribute_workers()



    async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float):
        async def countSupply(attackedUnit: Unit):
            closestEnemies = self.enemy_units.in_distance_of_group([attackedUnit], 15)
            enemySupply = 0

            for enemy in closestEnemies:
                enemySupply += self.calculate_supply_cost(enemy.type_id)
            
            return enemySupply


        if self.enemy_units:
            isInRange = False

            for nexus in self.townhalls:
                if nexus.distance_to(unit) < 25:
                    isInRange = True

            if isInRange:
                self.nonAttackCounter = 0
                self.lastTimeWhenAttacked = self.state.game_loop

                closestEnemy = self.enemy_units.closest_to(unit)

                enemySupply = await countSupply(unit)
        
                if enemySupply > 0:
                    self.lastEnemySupply = enemySupply

                    if enemySupply <= 10:
                        await self.stateOfAI.setPointOfDefence(closestEnemy)
                        await self.stateOfAI.stalkerDefend()
                        

                    elif enemySupply > 10 and enemySupply <= 30:
                        await self.stateOfAI.setPointOfDefence(closestEnemy)
                        await self.stateOfAI.defend()
                
            else:
                enemySupply = await countSupply(unit)
                
                if self.supply_army > enemySupply:
                    await self.stateOfAI.attack()
                else:
                    await self.stateOfAI.retreat()




    async def on_unit_destroyed(self, unit_tag: int):
        if unit_tag == UnitTypeId.NEXUS:
            await self.distribute_workers()
        



    async def on_unit_created(self, unit: Unit):
        if unit.type_id == UnitTypeId.PROBE:
            probe = unit
            foundIdealNexus = False

            for nexus in self.townhalls:
                if not nexus.surplus_harvesters and nexus.is_ready:
                    targetMineralField = self.mineral_field.closest_to(nexus)

                    probe.gather(targetMineralField)
                    foundIdealNexus = True

            if not foundIdealNexus:
                nearestNexus = self.townhalls.closest_to(probe)
                targetMineralField = self.mineral_field.closest_to(nearestNexus)

                probe.gather(targetMineralField)




    async def maintainMicro(self):
        state = await self.stateOfAI.getState()

        if self.nonAttackCounter > 100 and self.nonAttackCounter < 120 and self.supply_army > self.lastEnemySupply:
            self.stateOfAI.attack()
        else:
            self.stateOfAI.wait()


        if self.units.exclude_type({UnitTypeId.PROBE, UnitTypeId.STALKER}).amount > 0:
            army = self.units.exclude_type({UnitTypeId.PROBE, UnitTypeId.STALKER})

            #enemyArmy = self.enemy_units.exclude_type({UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV})


            if state == "attack" or state == "fullAttack":
                targetLocation:any

                if self.lastEnemySupply > self.supply_army:
                    if not self.enemy_structures and not self.enemy_units:
                        targetLocation = self.enemy_start_locations[0]
                    elif not self.enemy_units:
                        targetLocation = self.enemy_structures.in_closest_distance_to_group(army).position
                    else:
                        targetLocation = self.enemy_units.in_closest_distance_to_group(army).position

                    for unit in army:
                        unit.attack(targetLocation)
                else:
                    self.stateOfAI.retreat()



            elif state == "defend" or state == "fullDefend":
                for unit in army:
                    self.defendThePoint(unit)


            elif state == "wait" or state == "stalkerDefend":
                targetNexus = self.structures(UnitTypeId.NEXUS).closest_to(self.enemy_start_locations[0])
                pos = targetNexus.position.towards(self.enemy_start_locations[0], random.randrange(10, 15))

                for unit in army:
                    unit.move(pos)

            
            elif state == "retreat":
                targetArmy = army.in_distance_of_group([self.mainNexus], 30)
                restOfArmy = army.in_distance_between(self.mainNexus, 30, 300)
                avgPos = 0

                for defenceUnit in targetArmy:
                    avgPos += defenceUnit.position

                avgPos = avgPos / targetArmy.amount

                for retreatingUnit in restOfArmy:
                    retreatingUnit.move(avgPos)


        if self.units(UnitTypeId.STALKER).amount > 0:
            stalkerGuard = self.units(UnitTypeId.STALKER)
            #.closest_n_units(self.stateOfAI.pointOfDefence, 4)

            if self.townhalls:

                if state == "stalkerDefend" or state == "defend" or state == "fullDefend" or state == "attack":
                    for stalker in stalkerGuard:
                        await self.defendThePoint(stalker)

                elif state == "wait":
                    targetNexus = self.townhalls.closest_to(self.enemy_start_locations[0])
                    pos = targetNexus.position.towards(self.enemy_start_locations[0], random.randrange(10, 15))

                    for stalker in stalkerGuard:
                        stalker.move(pos)

            else:
                targetLocation = self.structures.in_closest_distance_to_group(stalkerGuard).position

                for stalker in stalkerGuard:
                    stalker.move(pos)


        
    async def defendThePoint(self, unit: Unit):
        unit.attack(self.stateOfAI.pointOfDefence)


    async def checkNonAttackCounter(self):
        self.nonAttackCounter = self.state.game_loop - self.lastTimeWhenAttacked


    async def on_step(self, iteration:int):
        await self.maintainMicro()
        await self.checkNonAttackCounter()


        async def _trainingProbes():
            if self.supply_left > 0: 
                nexus.train(UnitTypeId.PROBE)


        async def _placingPylon():
            if self.already_pending(UnitTypeId.PYLON) == 0:
                if not self.structures(UnitTypeId.PYLON):
                    await self.build(UnitTypeId.PYLON, near=self.main_base_ramp.top_center, max_distance=3)
                
                elif self.structures(UnitTypeId.PYLON).amount == 1:
                    targetNexus = self.mainNexus
                    await self.build(UnitTypeId.PYLON, near=targetNexus)

                elif self.supply_cap != 200:
                    target_pylon = self.structures(UnitTypeId.NEXUS).closest_to(self.enemy_start_locations[0])
                    pos = target_pylon.position.towards(self.enemy_start_locations[0], random.randrange(8, 15))

                    await self.build(UnitTypeId.PYLON, near=pos)


            if self.state.game_loop > 16 * 120:
                structures = self.structures

                for building in structures:
                    if not building.is_powered and self.worker_en_route_to_build(UnitTypeId.PYLON) == 0:
                        closestPylon = self.structures(UnitTypeId.PYLON).closest_to(building)

                        if closestPylon.distance_to(building) > 6.5:
                            await self.build(UnitTypeId.PYLON, near=building)




        async def _expanding():
            if (self.supply_workers / self.structures(UnitTypeId.NEXUS).amount) > 16:
                    if self.already_pending(UnitTypeId.NEXUS) == 0:
                        await self.expand_now()



        async def _placingAssimilator():
            async def getPossibleGeysers():
                geysers = self.vespene_geyser

                for nexus in self.townhalls:
                    baseGeysers = geysers.closest_n_units(nexus, 2)

                    for vespeneGeyser in baseGeysers:
                        if await self.can_place(UnitTypeId.ASSIMILATOR, vespeneGeyser.position):
                            return vespeneGeyser

                return None


            if self.already_pending(UnitTypeId.ASSIMILATOR) == 0 and self.structures(UnitTypeId.ASSIMILATOR).amount / self.townhalls.amount < 2:
                finalVespeneGeyser = await getPossibleGeysers()
                
                if not finalVespeneGeyser == None:
                    await self.build(UnitTypeId.ASSIMILATOR, near=finalVespeneGeyser)
                                

                
        async def _placingGateway():
            if self.structures(UnitTypeId.PYLON).ready:
                targetPylon = self.structures(UnitTypeId.PYLON).closest_to(self.mainNexus)

                if self.structures(UnitTypeId.GATEWAY).amount < 1 and self.already_pending(UnitTypeId.GATEWAY) == 0:
                    await self.build(UnitTypeId.GATEWAY, near=targetPylon)

                elif self.already_pending(UnitTypeId.GATEWAY) == 0 and self.structures(UnitTypeId.CYBERNETICSCORE) and self.structures(UnitTypeId.GATEWAY).amount < 3:
                   await self.build(UnitTypeId.GATEWAY, near=targetPylon)



        async def _placingCyberneticCore():
            if self.structures(UnitTypeId.GATEWAY).ready:
                if not self.structures(UnitTypeId.CYBERNETICSCORE) and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0:
                    targetPylon = self.structures(UnitTypeId.PYLON).closest_to(self.mainNexus)
                    
                    await self.build(UnitTypeId.CYBERNETICSCORE, near=targetPylon)


        async def _placingStargate():
            if self.structures(UnitTypeId.CYBERNETICSCORE).ready:
                if self.already_pending(UnitTypeId.STARGATE) == 0 and self.structures(UnitTypeId.STARGATE).amount < 5:
                    targetPylon = self.structures(UnitTypeId.PYLON).closest_to(self.mainNexus)

                    await self.build(UnitTypeId.STARGATE, near=targetPylon)


        async def _placingFleetBeacon():
            if self.already_pending(UnitTypeId.FLEETBEACON) == 0 and self.structures(UnitTypeId.FLEETBEACON).amount == 0:
                targetNexus = self.structures(UnitTypeId.NEXUS).closest_to(self.start_location)
                targetPylon = self.structures(UnitTypeId.PYLON).closest_to(targetNexus)

                await self.build(UnitTypeId.FLEETBEACON, targetPylon)



        async def _trainingStalker():
            if self.structures(UnitTypeId.GATEWAY).ready:
                gates = self.structures(UnitTypeId.GATEWAY)
                
                for gate in gates:
                    if self.units(UnitTypeId.STALKER).amount < (self.supply_cap / 10):
                        if gate.is_idle:
                            gate.train(UnitTypeId.STALKER)                  



        async def _trainingVoidRay():
            if self.structures(UnitTypeId.STARGATE).ready:
                stargates = self.structures(UnitTypeId.STARGATE)
                for stargate in stargates:
                    if self.supply_left >= self.calculate_supply_cost(UnitTypeId.VOIDRAY) and stargate.is_idle:
                        stargate.train(UnitTypeId.VOIDRAY)

        
        async def _trainingCarrier():
            if self.structures(UnitTypeId.STARGATE).ready and self.structures(UnitTypeId.FLEETBEACON).ready:
                stargates = self.structures(UnitTypeId.STARGATE)
                for stargate in stargates:
                    if self.supply_left >= self.calculate_supply_cost(UnitTypeId.CARRIER) and stargate.is_idle:
                        stargate.train(UnitTypeId.CARRIER)




        if self.townhalls:
            nexus = self.townhalls.random

            #PROBE
            if nexus.is_idle and self.can_afford(UnitTypeId.PROBE) and self.workers.amount < 68:
                await _trainingProbes()

            #PYLON
            if self.supply_left < self.structures(UnitTypeId.NEXUS).amount * 8 and self.can_afford(UnitTypeId.PYLON):
                await _placingPylon()

            #EXPO
            if self.structures(UnitTypeId.NEXUS).amount > 0 and self.can_afford(UnitTypeId.NEXUS):
                await _expanding()

            #ASSIMILATOR
            if self.structures(UnitTypeId.GATEWAY) and self.supply_left > 3 and self.can_afford(UnitTypeId.ASSIMILATOR):
                await _placingAssimilator()

            #GATEWAY
            if self.structures(UnitTypeId.PYLON) and self.can_afford(UnitTypeId.GATEWAY):
                await _placingGateway()

            #CYBERNETIC_CORE
            if self.structures(UnitTypeId.GATEWAY) and self.structures(UnitTypeId.PYLON) and self.can_afford(UnitTypeId.CYBERNETICSCORE):
                await _placingCyberneticCore()
            
            #STARGATE
            if self.structures(UnitTypeId.CYBERNETICSCORE) and self.structures(UnitTypeId.PYLON) and self.can_afford(UnitTypeId.STARGATE):
                await _placingStargate()

            #FLEET_BEACON
            if self.can_afford(UnitTypeId.FLEETBEACON) and self.structures(UnitTypeId.STARGATE).amount >= 2:
                await _placingFleetBeacon()


            #SOME_STALKERS
            if self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(UnitTypeId.STALKER):
                await _trainingStalker()


            #VOID_RAY
            if self.structures(UnitTypeId.STARGATE) and self.can_afford(UnitTypeId.VOIDRAY):
                await _trainingVoidRay()

            #CARRIER
            if self.structures(UnitTypeId.STARGATE) and self.can_afford(UnitTypeId.CARRIER):
                await _trainingCarrier()

            

            #UPGRADES
            if self.structures(UnitTypeId.CYBERNETICSCORE).ready:
                if self.can_afford(UpgradeId.PROTOSSAIRWEAPONSLEVEL1) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL1) == 0:
                    self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL1)

                elif self.can_afford(UpgradeId.PROTOSSAIRARMORSLEVEL1) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL1) == 0:
                    self.research(UpgradeId.PROTOSSAIRARMORSLEVEL1)

                elif self.can_afford(UpgradeId.PROTOSSAIRWEAPONSLEVEL2) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL2) == 0:
                    if self.tech_requirement_progress(UpgradeId.PROTOSSAIRWEAPONSLEVEL2) == 1:
                        self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL2)

                elif self.can_afford(UpgradeId.PROTOSSAIRARMORSLEVEL2) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL2) == 0:
                    if self.tech_requirement_progress(UpgradeId.PROTOSSAIRARMORSLEVEL2) == 1:
                        self.research(UpgradeId.PROTOSSAIRARMORSLEVEL2)

                elif self.can_afford(UpgradeId.PROTOSSAIRWEAPONSLEVEL3) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL3) == 0:
                    if self.tech_requirement_progress(UpgradeId.PROTOSSAIRWEAPONSLEVEL3) == 1:
                        self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL3)

                elif self.can_afford(UpgradeId.PROTOSSAIRARMORSLEVEL3) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL3) == 0:
                    if self.tech_requirement_progress(UpgradeId.PROTOSSAIRARMORSLEVEL3) == 1:
                        self.research(UpgradeId.PROTOSSAIRARMORSLEVEL3)


        else:
            if self.can_afford(UnitTypeId.NEXUS):
                await self.expand_now()


        

run_game(
    maps.get(gameMap),
    [Bot(Race.Protoss, MaslakBot()),
     Computer(Race.Protoss, Difficulty.Hard, AIBuild.Rush)
     #Computer(Race.Zerg, Difficulty.Hard)
    ],
     
     realtime=False
)