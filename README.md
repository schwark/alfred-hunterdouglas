alfred-hunterdouglas
====================

Alfred Workflow for Hunter Douglas Platinum Gateway

README for Hunter Douglas Platinum Control

Firstly, I would like to thank the folks at SmartThings and tannewt on github for their work on showing me how to build a alfred workflow and for sample dump of the tcp dialog and initial python code with the Platinum gateway respectively. Their appropriate license files are included in this distribution.

To use:

Step 1:
Install the Platinum Control Alfred workflow

Step 2:
open Alfred and 

```bash
w_update <gateway-ip>
```

```bash
w <scene-name>
```
runs a scene

```bash
wi <up|down|n> <window-name>
```
rolls a specific window to a specified position - can be up/down or a number n where n is numeric %age up you want the window - 100=up, 0=down

```bash
wr <up|down|n> <room-name>
```
rolls all windows in a room to specified position


