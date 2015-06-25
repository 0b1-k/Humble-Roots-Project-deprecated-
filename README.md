# The Humble Roots Project (v0.4)
**Home Automation Applied To Medical Cannabis Cultivation**

The *Humble Roots Project* is a grow room automation system designed to meet indoor cannabis horticulture
challenges using open software, open hardware and readily available consumer appliances. The project
blends these elements together into an inexpensive, reliable, automated system, with a focus
on sustainability.

The application of the concepts and technology used as part of the Humble Roots Project is not limited
to indoor growing or horticulture; it has far-reaching applications to many other automation scenarios
where sensors, actuators, rules and data visualization are combined to solve a problem.

For in-depth details about the project, check out the [project documentation](./docs/HumbleRootsProject.pdf).

![Humble Roots Lab](./docs/humbleroots.png "Humble Roots Lab")

**Plant Growth Timelapse**

<a href="http://www.youtube.com/watch?feature=player_embedded&v=OL0RneAysnU
" target="_blank"><img src="http://img.youtube.com/vi/OL0RneAysnU/0.jpg" 
alt="Enigma Girls 2 Growth Timelapse" width="240" height="180" border="10" /></a>

## Getting Started

1. Install the *Humble Roots Project* files

	```
	git clone https://github.com/fabienroyer/Humble-Roots-Project.git
	```
2. Assemble the wireless [sensor nodes](./arduino/README.md) and the [actuator nodes](./hardware/README.md).
3. Upload the [Arduino sketches](./arduino/README.md) to the wireless nodes.
4. Install the [project dependencies](./dependencies.md).
5. [Configure](./config/README.md) the ['bootstrap'](./config/bootstrap.json.template) and ['config'](./config/config.json.template) files.
6. Start the project processes.

