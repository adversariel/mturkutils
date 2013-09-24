TMPDIR=tmp
WEBDIR=web
TSPREP=timestamp_prep.log
TSTEST=timestamp_test.log
TSUPLOAD=timestamp_upload.log

all: prep test upload
	
$(TMPDIR)/$(TSPREP): $(WEBDIR)/adjectives_slider.html
	DRIVER_TMPDIR=$(TMPDIR) DRIVER_TSTAMP=$(TSPREP) python driver.py prep
prep: $(TMPDIR)/$(TSPREP)
	
$(TMPDIR)/$(TSTEST): $(TMPDIR)/$(TSPREP)
	DRIVER_TMPDIR=$(TMPDIR) DRIVER_TSTAMP=$(TSTEST) python driver.py test
test: $(TMPDIR)/$(TSTEST)
	
$(TMPDIR)/$(TSUPLOAD): $(TMPDIR)/$(TSTEST)
	DRIVER_TMPDIR=$(TMPDIR) DRIVER_TSTAMP=$(TSUPLOAD) python driver.py upload
upload: $(TMPDIR)/$(TSUPLOAD)
	
clean:
	rm -rf tmp/
