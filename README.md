## MANAGE KERNEL CONFIG ##

This program allows to try to recover a kernel configuration by parsing the
sources and the list of exported symbols, obtained from /proc/kallsyms.

Of course, this is not a trivial task, and a lot of info is missed, so it can
only return the bare minimum to ensure that the exported symbols are available.

The idea is to be able to compile new modules for a running kernel, when there
is no .config file available.

### Usage ###

First obtain the list of exported symbols with

        cat /proc/kallsyms > kallsyms.txt

Then, call Manage Kernel Config:

        ./manage_kernel ARCHITECTURE PATH_TO_KERNEL_SOURCE PATH_TO_KALLSYMS.TXT

The architecture is the processor architecture used by the kernel (e.g. arm)

The path to the kernel source is the path to the folder where the kernel source
files are (uncompressed). This kernel source must be the same version that is
running in the device.

Finally, the path to kallsyms.txt must point to where the kallsyms.txt created
in the previous step is now.

The program first outputs a list with all the not-found symbols, and after it,
a list of the kernel options to enable, showing not only the option itself, but
also where in the configuration tree it is. This allow to easily mark them from
make menuconfig.
