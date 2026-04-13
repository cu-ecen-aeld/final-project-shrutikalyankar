# Default to no debug, can be overridden with DEBUG=y
# DEBUG = y

ifeq ($(DEBUG),y)
  DEBFLAGS = -O -g -DBIRD_DEBUG
else
  DEBFLAGS = -O2
endif

# Add the flags to the kernel build process
ccflags-y += $(DEBFLAGS)

ifneq ($(KERNELRELEASE),)
# Part 1: Executed by the Kernel Build System
# This tells the kernel to create birdclassifier.ko from birdclassifier.o
obj-m := birdclassifier.o

else
# Part 2: Executed when you run 'make' from the command line
# KERNELDIR should point to the kernel source (Buildroot handles this automatically)
KERNELDIR ?= /lib/modules/$(shell uname -r)/build
PWD       := $(shell pwd)

modules:
	$(MAKE) -C $(KERNELDIR) M=$(PWD) modules

clean:
	rm -rf *.o *~ core .depend .*.cmd *.ko *.mod.c .tmp_versions modules.order Module.symvers
endif
