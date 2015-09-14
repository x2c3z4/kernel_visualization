#!/usr/sbin/dtrace -s

#pragma D option flowindent

::$1:entry
{
  stack();
  /*ustack();*/
  self->in = 1;
}

:*scsi*::entry,
:*scsi*::return
/self->in/
{
}

::$1:return
{
  self->in = 0;
  /*printf("return 0x%x\n", arg1);*/
  printf("----------------------------------------------------\n")
}
