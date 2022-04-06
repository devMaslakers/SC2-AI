
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