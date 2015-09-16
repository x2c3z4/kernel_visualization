Kernel Visualization Tool
=========================
This tool used to analysize Linux or Solaris kernel.
It can  draw callgraphs of your specific function, and help you understand the code.


Quick Start
===========
1. Debian

	```
	apt-get install -y systemtap linux-image-`uname -r`-dbg linux-headers-`uname -r` graphvize
	```

2. Solaris

	```
	pkg install graphvize
	```

Example
=======
Debian
------
1. Run using stap

	```
	bash stap_base.stp 'module("scsi_mod").function("scsi_request_fn")' 'module("scsi_mod").function("*")' | tee scsi_request_fn.log
	```

	```
	python callee.py scsi_request_fn.log
	```

	![callgraph of scsi_request_fn](/examples/images/scsi_request_fn.cg.png)
	![backtrace of scsi_request_fn](/examples/images/scsi_request_fn.bt.png)


Solaris
-------
1. Run using Dtrace(use `-d` option that stands for dtrace log)

	```
	./dtrace_base.d sdioctl | tee sdioctl.dtrace.log
	```

	```
	python callee.py sdioctl.dtrace.log -d
	```

	![callgraph of sdioctl](/examples/images/sdioctl.cg.png)

	![callgraph of sdioctl](/examples/images/sdioctl.bt.png)

Details
=======
1. In callgraph, from left to right, it presents the throughout program flow which begins from the most left function. It's only **one program call path** that currently your kernel is running. So this tool is dynamic, not like Doxygen. Doxgen is static analysis. It couldn't give me the whole path.

2. In the same list box of callgraph, it presents its parent call them **step by step**, one and one. If it enters and calls other functions, you will 
see that it points to his children.

3. There exists these paths that they have the same root parent, because we are **dynamic**. The same function could have different path in different context. So I have to add some random number in the output name.

Usage
======

```
 $ callee.py -h
Usage: callee.py [options] log_file

Generate pngs from Dtrace or Systemtap log

Options:
  -h, --help            show this help message and exit
  -k, --keep-dot        keep dot file, default delect it
  -o OUTPUT_FORMAT, --output-format=OUTPUT_FORMAT
                        output file format, could be ["png", "jpg", "svg"],
                        default is png
  -d, --is_dtrace_log   default is systemtap log, -d stand for dtrace log
  -c THRESHOLD_CG, --threshold_cg=THRESHOLD_CG
                        only generate call graph when the call link extend to
                        threshold_cg
  -b THRESHOLD_BT, --threshold_bt=THRESHOLD_BT
                        only generate backtrace graph when the call link
                        extend to threshold_bt

```

You can go to `example/log/` and play.

Contact
=======
Alex Feng
lifeng1519@gmail.com