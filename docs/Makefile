# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = levelorm
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile gh-pages

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

gh-pages:
	# check for clean working tree and index
	git diff --quiet --exit-code
	git diff --quiet --cached --exit-code
	# build
	make html
	tar cf ../docs.tar _build/html
	# prepare
	cd ..
	git checkout gh-pages
	rm -r *.html *.inv _sources _static
	tar xf docs.tar --strip-components=2
	rm docs.tar
	git add .
