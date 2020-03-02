CSVInspector - A graphical interactive tool to inspect and process CSV files.

Copyright (C) 2020 J. Férard <https://github.com/jferard>

License: GPLv3

# What it looks like

![alt text](https://raw.githubusercontent.com/wiki/jferard/CSVInspector/images/CSVInspector_capture.png)

# Use case
CSVInspector main goal is to help user performing repetitive one shot tasks on small data sets. Those tasks may be data aggregation, table join, column selection or creation, ...
CSVInspector provides the `show` method that displays the current stat of a data set.

(If you work on stable data or if the data sets are big, you should consider using SQL.)

Typical use case is:
* load one or two light csv files (< 10 k lines);
* aggregate some columns in both tables;
* add some columns;
* join files;
* save the result.



# Overview
CSVInspector is a very basic client/server application:
* The server is a Python module that wraps some features of Pandas to handle CSV data.
* The client is a Kotlin/JavaFX GUI that sends Python scripts to the server and displays the results.

# Install & run
Python (won't work for now in a virtual env): 

    $ pushd lang/python
    $ pip install --user -r requirements.txt
    $ popd
    
Kotlin:
    
    $ mvn clean install
    $ /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java -jar target/csv_inspector-1.0-SNAPSHOT.jar

# Usage 
## Code sample

    #!/usr/bin/env python3.7
    
    from csv_inspector import *
    
    info = inspect("fixtures/datasets-2020-02-22-12-33.csv")
    info.show()
    
    data = info.open()
    # do whatever you want here
    data.show()
    # do whatever you want here
    data.show()
    data.save("fixtures/datasets-2020-02-22-12-33-new.csv")
 
## Main commands
The wrapper provides the following instructions:

`inspect(path)`
> finds the encoding, csv format and column types of a file. Returns an `Inspection` object. 

`info.show()`
> Shows the result of `inspect` in a window.
> `info` is an `Inspection` object. 
    
`info.open()`
> Opens the CSV file and returns a `Data` object.

`data.show()`
> Shows the `Data` object in a window.

`data.save(path)`
> Saves the `Data` object to a file.

The `Data` class is just a wrapper around a Pandas DataFrame. Hence, you can do:

    df = data.df
    # work with df
    data = Data(df)

## Other Commands
Note the square brackets.

`data.swap[x][y]`
> `x` and `y` are indices, slices or tuples of slices/indices

`data.add[func, name, index]`
> `func` is a function of `Data` (use numeric indices)
> `name` is the name of the new column
> `index` (opt) is the index of the new column 

`data.merge[x][func, name]`
> Same as `add`, but removes the merged columns and place the new column at the first merged index.

`data.groupby[w][x, func_x, y, func_y, ..., last_func]`
> `w`, `x`, `y`, ... are indices, slices or tuples of slices/indices
> `func_x`, `func_y`, ... are functions of `Data` (use numeric indices)
> `last_func` (opt) is a function for the remaining cols

`data1.ljoin[data2][x][y]`
`data1.rjoin[data2][x][y]`
`data1.ojoin[data2][x][y]`
`data1.ijoin[data2][x][y]`
> `x` and `y` are indices, slices or tuples of slices/indices
> `data1` and `data2` are `Data` instances

`data.filter[func1, func2]`
> `func1` and `func1` are functions of `Data` (use numeric indices)

`data.move_before[idx][x]`
`data.move_after[idx][x]`
> `idx` is an index
> `x` is an index, slice or tuple of slices/indices

`data.select[x]`
> Select some of the columns.
> `x` is an index, slice or tuple of slices/indices

`data.drop[x]`
> Drop some of the columns.
> `x` is an index, slice or tuple of slices/indices

`data.map[x][func]`
> Map some columns using a function.
> `x` is an index, slice or tuple of slices/indices
> `func` is a function of `Data` (use numeric indices)

`data.sort[x]`
`data.rsort[x]`
> Sort the rows.
> `x` is the index, slice or tuple of slices/indices of the key
