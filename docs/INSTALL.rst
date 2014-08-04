lmu.contenttypes.blog Installation
----------------------------------

To install lmu.contenttypes.blog using zc.buildout and the plone.recipe.zope2instance
recipe to manage your project, you can do this:

* Add ``lmu.contenttypes.blog`` to the list of eggs to install, e.g.:

    [buildout]
    ...
    eggs =
        ...
        lmu.contenttypes.blog
       
* Re-run buildout, e.g. with:

    $ ./bin/buildout
