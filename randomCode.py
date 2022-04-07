
# SOME RANDOM PYLON CODE, TRYING TO CENTER MAIN BASE 
# marginXY = self.maslakCorner_PylonXY
# direction = self.maslakCorner

# pos = (targetNexus.position[0] + direction * marginXY[0], targetNexus.position[1] + direction * marginXY[1])  
# print(type(pos))


#Konstrukcja XY
#(self.townhalls.first.position[0] + 12, self.townhalls.first.position[1] - 6)

#Po kazdym wybudowaniu assimilator, przetasowac robotnikow

#CANNON
# async def _placingPhotonCannon():
        #     if self.structures(UnitTypeId.FORGE).ready and self.structures(UnitTypeId.PYLON).ready:
        #         targetPylon = self.structures(UnitTypeId.PYLON).closest_to(self.main_base_ramp.top_center)

        #         if self.structures(UnitTypeId.PHOTONCANNON).amount < 1 and self.already_pending(UnitTypeId.PHOTONCANNON) < 1:
        #             await self.build(UnitTypeId.PHOTONCANNON, near=targetPylon, max_distance=3)

#FORGE
# async def _placingForge():
#             if self.already_pending(UnitTypeId.FORGE) == 0:
#                 targetNexus = self.mainNexus
#                 targetPylon = self.structures(UnitTypeId.PYLON).closest_to(targetNexus.position)

#                 await self.build(UnitTypeId.FORGE, near=targetPylon, max_distance=8)


# #FORGE
# if not self.structures(UnitTypeId.FORGE) and self.can_afford(UnitTypeId.FORGE):
#     await _placingForge()

# #CANNONS
# if self.structures(UnitTypeId.FORGE) and self.can_afford(UnitTypeId.PHOTONCANNON):
#     await _placingPhotonCannon()

# lastEnemySupply = 0
#     biggestSeenSuply = 0
#     suplyTimer = 0
#     lastTimeWhenChangedSuply = 0


# if self.units(UnitTypeId.STALKER).amount > 0:
#             amountOfStalkers = math.floor(self.units(UnitTypeId.STALKER).amount / 3)

#             if not self.structures(UnitTypeId.FLEETBEACON):
#                 amountOfStalkers = 0
  

#             stalkerGuard = self.units(UnitTypeId.STALKER).closest_n_units(self.stateOfAI.pointOfDefence, amountOfStalkers)

#             if self.townhalls and stalkerGuard:

#                 if state == "stalkerDefend" or state == "defend" or state == "fullDefend":
#                     for stalker in stalkerGuard:
#                         await self.defendThePoint(stalker)


#                 elif state == "wait" or state == "retreat":
#                     targetNexus = self.townhalls.closest_to(self.enemy_start_locations[0])
#                     pos = targetNexus.position.towards(self.enemy_start_locations[0], random.randrange(10, 15))

#                     for stalker in stalkerGuard:
#                         if state == "wait":
#                             stalker.attack(pos)
#                         else:
#                             stalker.move(pos)


#             elif stalkerGuard:
#                 targetLocation = self.structures.in_closest_distance_to_group(stalkerGuard).position

#                 for stalker in stalkerGuard:
#                     stalker.move(targetLocation)