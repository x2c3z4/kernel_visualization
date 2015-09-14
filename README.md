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

	![callgraph of scsi_request_fn](/examples/images/scsi_request_fn.cg.png)
	![backtrace of scsi_request_fn](/examples/images/scsi_request_fn.bt.png)


Solaris
-------
1. Run using Dtrace

	```
	./dtrace_base.d sdioctl | tee sdioctl.log
	```

	![callgraph of sdioctl](/examples/images/sdioctl.cg.png)

	![callgraph of sdioctl](/examples/images/sdioctl.bt.png)


Usage
======

```
 $ callee.py -h
Usage: callee.py [options] log_file

Generate pngs from Dtrace or Systemtap log


Options:
  -h, --help            show this help message and exit
  -k, --keep-dot        keep dot file, default delect it
  -d, --is_dtrace_log   default is systemtap log, -d stand for dtrace log
  -c THRESHOLD_CG, --threshold_cg=THRESHOLD_CG
                        only generate call graph when the call link extend to
                        threshold_cg
  -b THRESHOLD_BT, --threshold_bt=THRESHOLD_BT
                        only generate backtrace graph when the call link
                        extend to threshold_bt
```

You can go to `example/log/` and run: 

```
python callee.py scsi_request_fn.log
```

```
python callee.py sdioctl.dtrace.log -d
```

Contact
=======
Alex Feng
lifeng1519@gmail.com