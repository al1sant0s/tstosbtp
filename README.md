# Convert TSTO textpool files

This tool allows you to convert sbtp (textpool) files to xml files back and forth from
the game 'The Simpsons: Tapped Out'.

## Installation

First, make sure you have [**python**](https://www.python.org/downloads/)
and [**git**](https://git-scm.com/downloads) installed on your system.

With those requirements satisfied, run either of the following commands in the command-line interface to install tstosbtp, according to your OS:

* Windows installation command.

```shell
python -m pip install tstosbtp@git+https://github.com/al1sant0s/tstosbtp
```

* Linux installation command.

```shell
python3 -m pip install tstosbtp@git+https://github.com/al1sant0s/tstosbtp
```

If you use windows I recommend you to get the modern [windows terminal from microsoft store](https://apps.microsoft.com/detail/9n0dx20hk701?hl).

## Basic usage

To get the full help execute the following command:

```shell
tstosbtp --help
```

The tool will receive a list of directories and will convert the files from these directories on the spot.
That means the converted files will replace their correspondent original files.

## Converting files

To convert from sbtp to xml use the following command:

```shell
tstosbtp /path/to/textpools/
```

You can now edit the contents of the xml files. Once you are done and wants to
convert files back from xml to sbtp, perform the following command:

```shell
tstosbtp -r /path/to/textpools/
```

Both commands work with multiple directories at once.

```shell
tstosbtp /path/to/textpools-en/ /path/to/textpools-pt/ /path/to/textpools-fr/
```

```shell
tstosbtp -r /path/to/textpools-en/ /path/to/textpools-pt/ /path/to/textpools-fr/
```

## Keeping original files

By default the tool will delete the original files after conversion. For example, if you are converting from
sbtp to xml, after the xml files get created, the original sbtp files are removed. To prevent this behaviour
you can use -k argument.

```shell
tstosbtp -k /path/to/textpools/
```

To preserve the xml files:

```shell
tstosbtp -k -r /path/to/textpools/
```

## Xml indentation level

Choose the indentation level to be used to produce the xml files. The default value is 2, if you
wish to use an indentation level of 4 for example:

```shell
tstosbtp -i 4 /path/to/textpools/
```
