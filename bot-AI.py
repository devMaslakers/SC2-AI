from ctypes.wintypes import POINT
import math
from multiprocessing.connection import wait
from pickle import TRUE
from random import random
from re import A
from tkinter import UNITS
from turtle import distance
from typing import List
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
    pointOfWait: any

    nonAttackCounter = 0
    lastTimeWhenAttacked = 0

    lastEnemySupply = 0
    actualEnemySupply = 0
    
    timeOfEnemyBaseAwait = 0
    attackNumber = 0


    async def on_start(self):

        if self.townhalls.first.position[0] < self.townhalls.first.position[1]:
                self.maslakCorner = 1
        else:
            self.maslakCorner = -1

        self.mainNexus = self.townhalls.first
        self.pointOfWait = self.main_base_ramp.top_center
        await self.stateOfAI.setPointOfDefence(self.main_base_ramp.top_center)



    async def on_building_construction_complete(self, unit: Unit):
        if unit.type_id == UnitTypeId.ASSIMILATOR or unit.type_id == UnitTypeId.NEXUS:
            await self.distribute_workers()

            if unit.type_id == UnitTypeId.NEXUS:

                if self.townhalls.amount == 2:
                    ramps = self.game_info.map_ramps
                    closestRamp = self.main_base_ramp
                    closestRampDistance = 400

                    for ramp in ramps:
                        if ramp != self.main_base_ramp:
                            distance = unit.distance_to(ramp.top_center)  
                            if distance < closestRampDistance:

                                closestRampDistance = distance                   
                                closestRamp = ramp
                    pos = closestRamp.top_center.towards(self.start_location, random.randrange(1,2))

                    self.pointOfWait = pos


    async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float):
        async def countSupply(attackedUnit: Unit):
            closestEnemies = self.enemy_units.in_distance_of_group([attackedUnit], 15)
            enemySupply = 0

            for enemy in closestEnemies:
                enemySupply += self.calculate_supply_cost(enemy.type_id)
            
            return enemySupply

        if not unit.is_structure:
            if unit.distance_to(self.enemy_start_locations[0]) < 16:
                self.timeOfEnemyBaseAwait = 0


        if self.enemy_units:
            isInRange = False

            for nexus in self.townhalls:
                if nexus.distance_to(unit) < 25:
                    isInRange = True

            if not isInRange:
                if unit.is_structure:
                    isInRange = True


            if isInRange:
                await self.updateNonAttackCounter()

                closestEnemy = self.enemy_units.closest_to(unit)

                enemySupply = await countSupply(unit)
        
                if enemySupply > 0:

                    if enemySupply <= 10:
                        await self.stateOfAI.setPointOfDefence(closestEnemy)
                        await self.stateOfAI.stalkerDefend()
                        

                    elif enemySupply > 10 and enemySupply <= 30:
                        await self.stateOfAI.setPointOfDefence(closestEnemy)
                        await self.stateOfAI.defend()
                

    async def on_enemy_unit_entered_vision(self, unit: Unit):
        await self.calculateSupplyInVision()

        self.lastEnemySupply = self.actualEnemySupply


    async def on_enemy_unit_left_vision(self, unit_tag: int):
        await self.calculateSupplyInVision()


    async def on_unit_destroyed(self, unit_tag: int):
        if unit_tag == UnitTypeId.NEXUS:
            await self.distribute_workers()

        supply = 0

        enemies = self.enemy_units.exclude_type({UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV})
        for enemy in enemies:
            supply += self.calculate_supply_cost(enemy.type_id)

        diffrence = self.actualEnemySupply - supply

        if diffrence > 0:
            self.actualEnemySupply = supply
            self.lastEnemySupply -= diffrence
        



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
        async def attackCommand():
            async def searchEnemyCommand():
                randomNumber = random.randrange(0, ( self.expansion_locations.length ) - 1)

                return randomNumber


            targetLocation:any

            if self.supply_army > self.lastEnemySupply:

                if not self.enemy_units and self.enemy_structures:
                    targetLocation = self.enemy_structures.in_closest_distance_to_group(army).position

                elif self.enemy_units and not self.enemy_structures:
                    targetLocation = self.enemy_units.in_closest_distance_to_group(army).position

                else:
                    if self.attackNumber == 0:
                        targetLocation = self.enemy_start_locations[0]
                    else:
                        targetLocation = self.expansion_locations[self.attackNumber]


                if army.in_distance_between(self.enemy_start_locations[0], 0, 15):
                    if self.timeOfEnemyBaseAwait > 400:
                        self.attackNumber = await searchEnemyCommand()

                if targetLocation:
                    for unit in army:
                        unit.attack(targetLocation)


            elif self.nonAttackCounter > 100:
                await self.updateNonAttackCounter()
                await self.stateOfAI.retreat()


        state = await self.stateOfAI.getState()


        if self.units.exclude_type({UnitTypeId.PROBE}).amount > 0:
            army = self.units.exclude_type({UnitTypeId.PROBE})


            if state == "attack" or state == "fullAttack":
                await attackCommand()


            if state == "defend" or state == "fullDefend":
                for unit in army:
                    await self.defendThePoint(unit)


            if state == "wait":
                for unit in army:
                    await self.waitAtThePoint(unit)


            if state == "stalkerDefend":
                stalkerArmy = army(UnitTypeId.STALKER)

                for stalker in stalkerArmy:
                    await self.defendThePoint(stalker)
            

            if state == "retreat":

                targetArmy = army.in_distance_between(self.mainNexus, 30, 300)

                if targetArmy.amount != 0:
            
                    for retreatingUnit in targetArmy:
                        targetNexus = self.townhalls.closest_to(self.enemy_start_locations[0])
                        pos = targetNexus.position.towards(self.enemy_start_locations[0], random.randrange(8,10))

                        retreatingUnit.move(pos)


        if self.nonAttackCounter > 100:
            if self.supply_army >= self.lastEnemySupply and self.supply_army > 30:
                await self.stateOfAI.attack()
                await self.updateNonAttackCounter()
                
            else:
                await self.stateOfAI.wait()
                await self.updateNonAttackCounter()



    async def calculateSupplyInVision(self):
        supply = 0

        enemies = self.enemy_units.exclude_type({UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV})
        for enemy in enemies:
            supply += self.calculate_supply_cost(enemy.type_id)

        self.actualEnemySupply = supply

        
    async def defendThePoint(self, unit: Unit):
        unit.attack(self.stateOfAI.pointOfDefence)

    async def waitAtThePoint(self, unit: Unit):
        unit.move(self.pointOfWait)


    async def checkNonAttackCounter(self):
        self.nonAttackCounter = self.state.game_loop - self.lastTimeWhenAttacked

    async def updateNonAttackCounter(self):
        self.nonAttackCounter = 0
        self.lastTimeWhenAttacked = self.state.game_loop


    async def checkEnemyWaitingCounter(self):
        self.timeOfEnemyBaseAwait = self.state.game_loop - self.nonAttackCounter


    async def on_step(self, iteration:int):

        await self.maintainMicro()
        await self.checkNonAttackCounter()
        await self.checkEnemyWaitingCounter()


        async def _trainingProbes():
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
            if self.already_pending(UnitTypeId.NEXUS) == 0:
                if (self.supply_workers / self.structures(UnitTypeId.NEXUS).amount) > 16:     
                    await self.expand_now()
                elif self.supply_cap > 180 and self.minerals > 800:
                    await self.expand_now()


        async def _placingAssimilator():
            async def getPossibleGeysers():
                geysers = self.vespene_geyser

                for nexus in self.townhalls:
                    if nexus.is_ready:
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
                if self.structures(UnitTypeId.CYBERNETICSCORE).amount < 2 and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0:
                    targetPylon = self.structures(UnitTypeId.PYLON).closest_to(self.mainNexus)
                    
                    if self.structures(UnitTypeId.CYBERNETICSCORE).amount == 0 or self.structures(UnitTypeId.FLEETBEACON):
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
                    if stargate.is_idle and self.can_afford(UnitTypeId.VOIDRAY):
                        stargate.train(UnitTypeId.VOIDRAY)

        
        async def _trainingCarrier():
            if self.structures(UnitTypeId.STARGATE).ready and self.structures(UnitTypeId.FLEETBEACON).ready:
                stargates = self.structures(UnitTypeId.STARGATE)
                for stargate in stargates:
                    if stargate.is_idle and self.can_afford(UnitTypeId.CARRIER):
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

            #FLEET_BEACON
            if self.can_afford(UnitTypeId.FLEETBEACON) and self.structures(UnitTypeId.STARGATE).amount >= 2:
                await _placingFleetBeacon()


            #CARRIER
            if self.structures(UnitTypeId.STARGATE) and self.can_afford(UnitTypeId.CARRIER):
                await _trainingCarrier()
            
            #VOID_RAY
            elif self.structures(UnitTypeId.STARGATE) and self.can_afford(UnitTypeId.VOIDRAY):
                await _trainingVoidRay()
            
            #STARGATE
            elif self.structures(UnitTypeId.CYBERNETICSCORE) and self.structures(UnitTypeId.PYLON) and self.can_afford(UnitTypeId.STARGATE):
                await _placingStargate()

            #SOME_STALKERS
            elif self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(UnitTypeId.STALKER):
                await _trainingStalker()

                     

            #UPGRADES
            if self.structures(UnitTypeId.CYBERNETICSCORE).ready:
                for cyberneticsCore in self.structures(UnitTypeId.CYBERNETICSCORE):
                    if not cyberneticsCore.is_idle:
                        if self.can_afford(UpgradeId.PROTOSSAIRWEAPONSLEVEL1) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL1) == 0:
                            self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL1)

                        elif self.can_afford(UpgradeId.PROTOSSAIRWEAPONSLEVEL2) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL2) == 0:
                            if self.tech_requirement_progress(UpgradeId.PROTOSSAIRWEAPONSLEVEL2) == 1:
                                self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL2)

                        elif self.can_afford(UpgradeId.PROTOSSAIRWEAPONSLEVEL3) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL3) == 0:
                            if self.tech_requirement_progress(UpgradeId.PROTOSSAIRWEAPONSLEVEL3) == 1:
                                self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL3)


                        if self.can_afford(UpgradeId.PROTOSSAIRARMORSLEVEL1) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL1) == 0:
                            self.research(UpgradeId.PROTOSSAIRARMORSLEVEL1)

                        elif self.can_afford(UpgradeId.PROTOSSAIRARMORSLEVEL2) and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL2) == 0:
                            if self.tech_requirement_progress(UpgradeId.PROTOSSAIRARMORSLEVEL2) == 1:
                                self.research(UpgradeId.PROTOSSAIRARMORSLEVEL2)

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