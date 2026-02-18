# Parts used
* Regular cheap refractometer, one or two pieces, about $10.
* 3D printed camera mount for the refractometer.
* 3D printed IR thermal sensor holder.
* Transparent tube of PMMA or polycarbonate (better), 20mm inner diameter, $7.
* 6mm hose barb elbow, 2 pcs, $1 each.

# Refractometer
One refractometer coupled with camera module is enough. It is good idea to add second refractometer opposed to the first one. 
So the refractions can be also observed visually at the same time when camera is measuring the liquid. 
Anyway, the camera mounted refractometer should be positioned vertically with camera module underneath. That's becuase the heat from the test tube and from LEDs is raising up. And the ambient air temperature should not be affected of what appens in the test tube.
If second refractometer is not used, it's recommended to close the open side of the test tube with diagonal insert. This minimizes the volume of measured liquid. Keeping the volume minimal is important to read the concentration changes as soon as they happen.

# 3D printed camera mount
The camera mount has 2 parts:
1. Part that mounts on the refractometer ocular. It has 7 knurled nuts M3x4. They are inserted with heat into dedicated holes in the plastic. 3 nuts to mount on the oculat and 4 nuts for camera module adjustments in 3 possible axes.
2. Part that hold the camera module. It has 4 slots which allow to adjust the camera position and tilt and also the camera focus on the Z-axis.

The first part has also Raspberry Pi Zero pad. It is good idea to use VHB double sided tape to stick to it the ambient temperature sensor holder.
The holder is not printed with the mount becuase the printed parts are fragile and might break wile mounting the temperature sensor.

# The illumination
4 white light LEDs are glued into dedicated blind holes on the test tube with transparent silicone.

# Test tube temperature measurement
The test tube temperature measurement is required to compensate the visible refraction to real concentration of the solution. 
However, plastic test tube is not a great conductor of heat. This creates a lag in temperature measurement. To compensate the lag:
* Flat test pad is made on the round test tube. This makes IR radiation uniform and also reduces the plastic wall thickness, increasing the heat trasmission speed.
* The test pad is painted with black matte paint.
* The IR temperature sensor is used because it takes the temperature value almost immediately from radiation. The contact temperature sensors need an extra time to be heated.
* The temperature sensor is mounted on the test tube with special holder. It isolates the IR radiation and reflections from ambient and protects the sensord from damage and dust.

# The hose barbs
2 holes to be made in the test tube for the hose barbs. It is recommended to use elbow barbs to have more convenient tubing. 
However, straight barbs are also OK. 

IMPORTANT NOTES:
1. The input barb should be at lowest possible position and the output barb is at the highest.
2. Make air gap (space) between the upper barb and further tubing. That's to avoid Bell syphon effect. if your liquid flows in horizontal or upward directions then no air gap needed.

