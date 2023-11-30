# wp4-solid-liquid-dosing-input
Script to enable calculation of solid and liquid masses from a sample series to be imported into dosing software on a Mettler Toledo XPR automated balance.

This script is intended to work alongside the software: LabX Client from Mettler Toledo, but should still run on machines without this software.
In brief, the script recieves an input file (set template) with some experimental parameter varied across a sample series of variable size.
From this, it calculates the required solid and liquid masses and outputs these values as a .csv file in a format that is readable by LabX Client.
This means that the script can still be used to calculate masses on a machine that does not have LabX Client installed.
Configuration of the LabX software is required for the next step in the process, where these masses are fed into the balance itself.
This script will save the file containing the masses into a directory location as specified in the script.
An import template must then be defined in LabX Client to read input files from this directory, with its format matching that of the input file.
