==========
 nui skin
==========

The skin is very similar to the concept of the cmf skin, except it is
derived from a z3 view rather than a ZODB object or object proxy.

Macros
======

#@@ note: currently we are just using the default skin

The most important piece of the skin is perhaps the
*main_template*. This view (derived from magic.pt), is an overlay of the
general structure needed by an openplans page. Within in it, named
slots allow template using this über macro to inject css, javascript
and content into this structures using commands from the metal
namespace.


How To
======

To invoke the master macro, add this line to your template's html::

<html
   metal:use-macro="here/@@main_template/macro/master">

To add custom behavior for your view, you will need to fill the
slots. Here is an example of how to inject extra css into the header
of your page::

<metal:link fill-slot="link">
  <link rel="stylesheet" href="/++resource++css/custom.css"
        type="text/css" media="all" />
</metal:link>


Slots
=====

The following slots are defined for the nui main_template::

* link -- for css and other link attributes

* script -- for ecmascript 

* content -- for content
