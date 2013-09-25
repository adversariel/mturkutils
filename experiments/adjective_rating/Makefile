PYTHON=python
TMPDIR=tmp
WEBDIR=web
SCRIPT=driver.py
TSPREP=timestamp_prep.log
TSTEST=timestamp_test.log
TSUPLOAD=timestamp_upload.log
TSSANDBOX=timestamp_sandbox.log
TSPRODUCT=timestamp_production.log
DEPSCRIPT=

ifeq ($(CHKSCRIPT), 1)
	DEPSCRIPT=$(SCRIPT)
endif

all: prep test upload
	@echo Finished all preliminary steps (or everything is up to date).
	@echo 'Type "make sandbox" to publish to the sandbox.'
	@echo 'Type "make production" to publish to the actual MTurk worker space.'
$(TMPDIR)/$(TSPREP): $(DEPSCRIPT) $(WEBDIR)/adjectives_slider.html
	DRIVER_TMPDIR=$(TMPDIR) DRIVER_TSTAMP=$(TSPREP) $(PYTHON) $(SCRIPT) prep
prep: $(TMPDIR)/$(TSPREP)
	
$(TMPDIR)/$(TSTEST): $(DEPSCRIPT) $(TMPDIR)/$(TSPREP)
	DRIVER_TMPDIR=$(TMPDIR) DRIVER_TSTAMP=$(TSTEST) $(PYTHON) $(SCRIPT) test
test: $(TMPDIR)/$(TSTEST)
	
$(TMPDIR)/$(TSUPLOAD): $(DEPSCRIPT) $(TMPDIR)/$(TSTEST)
	DRIVER_TMPDIR=$(TMPDIR) DRIVER_TSTAMP=$(TSUPLOAD) $(PYTHON) $(SCRIPT) upload
upload: $(TMPDIR)/$(TSUPLOAD)
	
$(TMPDIR)/$(TSSANDBOX): $(DEPSCRIPT) $(TMPDIR)/$(TSUPLOAD)
	DRIVER_TMPDIR=$(TMPDIR) DRIVER_TSTAMP=$(TSSANDBOX) $(PYTHON) $(SCRIPT) sandbox
sandbox: $(TMPDIR)/$(TSSANDBOX)
	
$(TMPDIR)/$(TSPRODUCT): $(DEPSCRIPT) $(TMPDIR)/$(TSUPLOAD)
	DRIVER_TMPDIR=$(TMPDIR) DRIVER_TSTAMP=$(TSPRODUCT) $(PYTHON) $(SCRIPT) production
production: $(TMPDIR)/$(TSPRODUCT)
	
clean:
	rm -rf tmp/
