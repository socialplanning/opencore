/*
Copyright 2007 Open Planning Project

Limits the number of selections of a particular set of checkboxes.
When more than the limit has been selected, all the checkboxes are
deselected (except the checkbox that caused it to go over limit).

To indicate the limit, place a limit-select="NUMBER" attribute on
every checkbox input element, like:

  <input type="checkbox" name="group-name" limit-select="2">

Then make sure OC.activateLimitSelect() is called on load.
Transitionally, simply including this file will cause this to be
bound.

*/

/* Disabling to use oc-behaviors.js

if (typeof OC == 'undefined') {
   OC = {};
}

OC.activateLimitSelect = function () {
   var els = document.getElementsByTagName('input');
   for (var i=0; i<els.length; i++) {
      if (els[i].getAttribute('type') == 'checkbox'
	  && els[i].getAttribute('limit-select')) {
	 els[i].setAttribute('onchange', 'OC._checkLimitSelect(this)');
      }
   }
};

OC.addOnLoad = function (callback) {
   if (window.onload) {
      var oldOnLoad = window.onload;
      window.onload = function () {
	 callback();
	 oldOnload();
      }
   } else {
      window.onload = callback;
   }
};

OC.addOnLoad(OC.activateLimitSelect);

OC._checkLimitSelect = function (input) {
   var limit = parseInt(input.getAttribute('limit-select'));
   if (! input.checked || ! limit) {
      return;
   }
   var name = input.name;
   var total = OC._countAllChecks(name);
   if (total > limit) {
      OC.deselectAllCheckboxes(name);
      input.checked = true;
   }
};

OC._countAllChecks = function (name) {
   var els = document.getElementsByTagName('input');
   var total = 0;
   for (var i=0; i<els.length; i++) {
      if (els[i].getAttribute('type') == 'checkbox'
	  && els[i].name == name
	  && els[i].checked) {
	 total ++;
      }
   }
   return total;
};

OC.deselectAllCheckboxes = function (name) {
   var els = document.getElementsByTagName('input');
   for (var i=0; i<els.length; i++) {
      if (els[i].getAttribute('type') == 'checkbox'
	  && els[i].name == name
	  && els[i].checked) {
	 els[i].checked = false;
      }
   }
};

*/