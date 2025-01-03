To configure this module, you need to:

1.  Go to *Inventory -\> Configuration -\> Settings* and check "Storage
    Locations" option.

2.  Go to *Inventory -\> Configuration -\> Operation types*.

3.  Create a new operation type with the following options:  
    - \`Operation type\`: Task material
    - \`Code\`: TM
    - \`Type of operation\`: Delivery
    - \`Default Source Location\`: WH/Stock
    - \`Default Destination Location\`: WH/Stock/Shelf 1

4.  Go to *Project -\> Configuration -\> Projects*.

5.  Create a new project with the following options:  
    - \`Name\`: Task material
    - \`Operation type\`: Task material

6.  Go to *Project -\> Configuration -\> Task Stages* and edit some records.  
    - \`In progress\`: Check Use Stock Moves option and add the created
      project.
    - \`Done\`: Check Use Stock Moves option + Done Stock Moves and add
      the created project.
