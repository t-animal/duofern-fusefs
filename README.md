# Duofernstick Fileystem

## Quickstart

1. Copy the udev rule from etc to your udev folder
2. Plug in your rademacher stick (see https://github.com/gluap/pyduofern/issues/7 )
3. Run:

```
python -m venv venv
source venv/bin/activate
pip install -r freeze
```
4. Initialize your stick as explained [here](https://pypi.org/project/pyduofern/)
5. Run: 
```
python main.py -d mnt/ &
sleep 5;
ls mnt
```

Note the `-d` flag? That indicates that fuse should run in the fore-
ground. No idea why it doesn't work witout that.

## Supported HW
Currently only rademacher rollotrons are supported, because I own no
other rademacher hardware. The whole software is also heavily geared
towards those because I don't intend to add more. I'll happily merge
pull requests, though.

## The filesystem
You'll find a folder for each of your rademacher devices. In it you'll find
files that can only be read (e.g. `cat mnt/56d4d/state`). Those report info
about your device.

There's also files that can only be written (e.g. `echo 1 >> mnt/546da/up`).
When you write anything into them, you'll execute the corresponding command.
Note that these files don't support truncating. I.e. in bash 
`echo 1 > mnt/5323d/up` will throw an error (but still execute the command).

There's also files that can be written to and read from. For those, both
the upper remarks apply. If you write a value to it, though, the corresponding
command is executed with the value as parameter. This also means that you
must provide viable parameters. If you write -5 into position, for example,
it will throw.
