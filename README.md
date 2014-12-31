alfred-hunterdouglas
====================

Alfred Workflow for Hunter Douglas Platinum Gateway

README for Hunter Douglas Platinum Control

Firstly, I would like to thank the folks at SmartThings and tannewt on github for their work on showing me how to build a alfred workflow and for sample dump of the tcp dialog with the Platinum gateway respectively. Their appropriate license files are included in this distribution.

To use:

Step 1:
Install the Platinum Control Alfred workflow

Step 2:
open Alfred and pl_update *gateway-ip*

if you have a really large installation, sometimes some of the windows and rooms were getting missed - I was unable to debug the python socket behavior to see why some of the data was missing. So I used an exec of nc (netcat) to get the data for larger networks. To activate this alternative method:

pl_update *gateway-ip* alt

If someone can figure out the bug in my code, please do let me know.

pls *scene-name*

plw *up|down|n* *window-name*    where n is numeric %age up you want the window - 100=up, 0=down

plr *up|down|n* *room-name*

pl *scene-name*                  as that is the common usage
