/* =============================================================================
* xinhaconfig.js
*
* Simplified interface for use of the Xinha WYSIWYG editor, providing a method
* by which multiple editors can be defined on a single page, each potentially
* using a different configuration
*
* All configuration data is stored in attributes of the textarea itself, using
* callbacks to perform post-processing. In order to make a textarea a WYSIWYG
* editor, simply add an "editor-type" attribute, and set its value to "wysiwyg".
* The Xinha JS and this file must also be included in the HEAD of the document.
*
* EXAMPLE:
*   This textarea will create a WYSIWYG editor based on the "simple"
*   configuration of XinhaConfig. It overrides the statusBar, toolbar,
*   formatblock, pageStyle, and pageStyleSheets settings in that base. However,
*   the height and plugins remain as in the base. By including the cols and rows
*   attributes, the textarea is sure to display in a desired manner if Xinha
*   does not load for any reason. Other attributes that can be
*
* <textarea cols="80" rows="15"
            width="600px" editor-type="wysiwyg" base="simple" statusBar="false"
*           toolbar="formatblock,separator,justifyleft,justifyright"
*           formatblock="{'Page Heading':'h2','Section Heading':'h3','Item Heading':'h4','Normal':'p'}"
*           pageStyle="body{background:#ccc none;color:#fc9;margin:0;padding:0.5em"
*           pageStyleSheets="/etc/css/stylesheet.css,/etc/css/template.css"></textarea>
*
* Compatible with all toolbar buttons and plugins.
*
* The following XinhaConfig compatible plugins load CSS into the Iframe:
*   Abbreviation
*   DefinitionList
*   Forms
*   InsertAnchor
*   LangMarks
*   SetId
*   Template
* ____________________________________________________________________________ *
*
* // additional customized bases can be created and added by addressing the new
* // property of XinhaConfig directly
* XinhaConfig.book = {
*   flowToolbars : true,
*   formatblock : {
*     'Book Title' : 'h1',
*     'Chapter Title' : 'h2',
*     'Section Heading' : 'h3',
*     'Subsection Heading' : 'h4',
*     'Normal' : 'p'
*   },
*   height : '400px',
*   pageStyle : '',
*   pageStyleSheets : [],
*   plugins : [
*     'FindReplace',
*     'FullScreen',
*     'SpellChecker',
*     'Stylist',
*     'TableOperations'
*   ],
*   showLoading : false,
*   statusBar : true,
*   toolbar : [
*     ['about'],
*     ['separator', 'popupeditor'],
*     ['separator', 'formatblock', 'bold', 'italic', 'underline'],
*     ['separator', 'justifyleft', 'justifycenter'],
*     ['linebreak', 'insertorderedlist', 'insertunorderedlist', 'outdent', 'indent'],
*     ['separator', 'inserthorizontalrule', 'insertimage']
*   ],
*   width : '99%'
* };
* ____________________________________________________________________________ *
*
* Developed by Jake Kronika <jkronika@imagescape.com>
* For Imaginary Landscape, LLC <www.imagescape.com>
* Copyright (c) 2006
*
* Last updated 2006.06.06
*
* Copyright (c) 2006 Imaginary Landscape LLC and Contributors.
*
* Permission is hereby granted, free of charge, to any person obtaining
* a copy of this software and associated documentation files (the
* "Software"), to deal in the Software without restriction, including
* without limitation the rights to use, copy, modify, merge, publish,
* distribute, sublicense, and/or sell copies of the Software, and to
* permit persons to whom the Software is furnished to do so, subject to
* the following conditions:
*
* The above copyright notice and this permission notice shall be
* included in all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
* NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
* LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
* OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
* WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*
* =========================================================================== */

var _XC_plugins = [
      'Abbreviation',
      'BackgroundImage',
      'CharacterMap',
      'CharCounter',
      'ClientsideSpellcheck',
      'ContextMenu',
      'CSS',
      'DefinitionList',
      'DoubleClick',
      'DynamicCSS',
      'EditTag',
      'EnterParagraphs',
      'Equation',
      'Filter',
      'FindReplace',
      'FormOperations',
      'Forms',
      'FullPage',
      'FullScreen',
      'GetHtml',
      'HorizontalRule',
      'HtmlTidy',
      'ImageManager',
      'InsertAnchor',
      'InsertMarquee',
      'InsertPagebreak',
      'InsertPicture',
      'InsertSmiley',
      'InsertWords',
      'InternalLink',
      'LangMarks',
      'Linker',
      'ListType',
      'NoteServer',
      'PasteText',
      'QuickTag',
      'SetId',
      'SpellChecker',
      'Stylist',
      'SuperClean',
      'TableOperations',
      'Template',
      'UnFormat'
    ], ls_url;

function _XC_init() {
  // initialize all plugins associated with Xinha

  alert(typeof _XC_plugins);
  if (typeof(_XC_plugins) != 'object') {
    // there are no appropriate plugins

    // halt processing
    return;
  }

  if (!HTMLArea.loadPlugins(_XC_plugins, function() { _XC_init(editor); })) {
    // the plugins couldn't be loaded on this pass, but the initialization will
    // automatically be called again after a timeout

    // halt processing of this pass
    return;
  }

  // the plugins were properly initialized

  // load the plugins
  HTMLArea.loadPlugins(_XC_plugins);

  _XC_parse();
}

var getAttributes = function(ar, el) {
  // get multiple attributes from an element and return those attributes as a
  // new object instance

  // empty object variable
  var obj = {};

  if (ar.constructor == Array) {
    // if the argument ar is an array

    for (var i = 0; i < ar.length; i++) {
      // traverse all property names in ar

      if (el.getAttribute && el.getAttribute(ar[i])) {
        // if this element has a getAttribute function that finds the attribute

        // add the attribute to the object to be returned
        obj[ar[i]] = el.getAttribute(ar[i]);
      } else if (el[ar[i]]) {
        // if there is no getAttribute or getAttribute doesn't find the
        // attribute, but this element has an object property as named

        // add the property to the object to be returned
        obj[ar[i]] = el[ar[i]];
      } else {
        // if getAttribute and object property methods fail

        // ensure a value by setting the value as an empty string
        obj[ar[i]] = '';
      }
    }
  } else if (ar.constructor == String) {
    // if the argument ar is a string

    if (el.getAttribute && el.getAttribute(ar)) {
      // if this element has a getAttribute function that finds the attribute

      // add the attribute to the object to be returned
      obj[ar] = el.getAttribute(ar);
    } else if (el[ar]) {
      // if there is no getAttribute or getAttribute doesn't find the
      // attribute, but this element has an object property as named

      // add the property to the object to be returned
      obj[ar] = el[ar];
    }
  }

  // return the object comprised of properties built from element attributes
  return obj;
};

function merge(base, merger, deep, no_repeat) {
  // merge items from one object into another object, overriding the original
  // values beyond the depth indicated by deep
  // - if deep > 0, merge sub-objects to the deep-th level
  //   - NOTE: if an object property is an array and that array contains an
  //     object, that object will not be merged, as arrays are extended to
  //     become one larger array when merging sublevels
  // - if deep = 0, all values will be overridden
  // - if deep < 0, all levels will be merged
  //   - CAUTION: this will cause an infinite loop if there are any circular
  //     references!

  if (typeof(merger) == 'object' && typeof(base) == 'object' && !merger.isEmpty()) {
    // make sure we are working with another object

    for (var i in merger) {
      // traverse all object properties

      if (typeof(base[i]) == 'undefined' || base[i] === null) {
        // if the merger's property does not exist on the base

        // create the new property
        base[i] = merger[i];
      } else if (deep !== 0) {
        // if we should merge any sublevels of the objects

        if (typeof(merger[i]) == 'undefined') {
          continue;
        }

        if (base[i].constructor == Array && merger[i].constructor == Array) {
          // if this property of both objects is an array

          // extend the base's array with the merger's array
          if (!merger[i].isEmpty()) {
            if (no_repeat) {
              base[i].pushOrExtendIfNew(merger[i]);
            } else {
              base[i].pushOrExtend(merger[i]);
            }
          }
        } else if (base[i].constructor == Boolean && merger[i].constructor == Boolean) {
          // if this property of both objects is a boolean

          // set the property to true if either objects' property is true
          base[i] = (base[i] || merger[i]);
        } else if (typeof(base[i]) == 'object' && typeof(merger[i]) == 'object' && !merger[i].isEmpty()) {
          // if this property of both objects is an object as well

          // merge the sub-objects, to one level lesser depth
          merge(base[i], merger[i], parseInt(deep, 10) - 1, no_repeat);
        } else {
          // any other types

          // create or overwrite the property
          base[i] = merger[i];
        }
      } else {
        // do not merge any sublevels of the objects

        // create or overwrite the property
        base[i] = merger[i];
      }
    }
  }

  // return the merged object
  return base;
}

var removeItemFromArray = function(ar, val) {
  // if an element with the given val exists in the ar, remove it and return the
  // new array

  // create an empty array to store all non-removed values, preserving order
  var newAr = [];

  for (var i = 0; i < ar.length; i++) {
    // traverse the original array

    if (ar[i] != val) {
      // this element is not the value to be removed

      // add this element to the new array
      newAr[i] = ar[i];
    }
  }

  // return the revised array, with the element of the given val removed
  return newAr;
};

var removeItemFromObject = function(obj, name) {
  // if a property with the given name exists in the obj, remove it and return
  // the new object

  // create an empty object to store all non-removed values, preserving keys
  var newObj = {};

  for (var x in obj) {
    // traverse the original object

    if (x != name) {
      // this property is not the one to be removed

      // add this property to the new object
      newObj[x] = obj[x];
    }
  }

  // return the revised object, with the property of the given name removed
  return newObj;
};

Array.prototype.contains = function(val) {
  // search for a value in the current array

  for (var i = 0; val && i < this.length; i++) {
    // traverse the elements in this array

    if (val == this[i]) {
      // an identical item was found

      // affirmative response
      return true;
    } else if (val.constructor == Array) {
      // the val is an array

      // flag for all sub-items found
      var allFound = true;

      for (var j = 0; j < val.length; j++) {
        // traverse the elements in val

        if (!this.contains(val[j])) {
          // the current item in val isn't in this array

          // change flag to negative
          allFound = false;

          // stop processing this loop
          break;
        }
      }

      if (allFound) {
        // every item in val is in this array

        // affirmative response
        return true;
      }
    }
  }

  // no identical item was found

  // negative response
  return false;
};

Array.prototype.flatten = function(deep) {
  // create a one dimensional array from a multi-dimensional array, stopping at
  // the depth indicated by deep (as an integer)
  // - if deep = 0, leave the array as is
  // - if deep > 0, create a new array consisting of flattened  elements to the
  //   deep-th level
  // - if deep < 0 or is not defined, flatten all elements at all depths

  if (typeof(deep) == 'undefined') {
    // if deep is not defined

    // set deep to -1 to flatten all elements
    deep = -1;
  } else if (deep === 0) {
    // if deep is defined as 0 (zero)

    // no change will be made to the array, so return to save time
    return;
  }

  // flattened array variable
  var lin = [];

  for (var i = 0; i < this.length; i++) {
    // traverse elements in this array

    if (deep !== 0 && this[i] && this[i].constructor == Array) {
      // if flattening sub-arrays and the current element is an array

      // flatten this sub-array
      this[i].flatten(deep - 1);

      for (var j = 0; j < this[i].length; j++) {
        // traverse elements in the flattened sub-array

        // push this element onto the flattened array
        lin.pushOrExtend(this[i][j]);
      }
    } else {
      // if not linearizing sub-arrays or the current element is not an array

      // push this element onto the flattened array
      lin.pushOrExtend(this[i]);
    }
  }

  // empty the array
  this.length = 0;

  // reset this array to the flattened version
  this.pushOrExtend(lin);

  // return the flattened array
  return this;
};

Array.prototype.isEmpty = function() {
  // check to see if this array contains any non-empty values

  if (!this.length) {
    // this array contains no elements

    // positive response
    return true;
  }

  for (var i = 0; i < this.length; i++) {
    // traverse array elements

    if (this[i] &&
        ( !( this[i].constructor != String
            && this[i].constructor != Array
            && this[i].constructor != Object )
          // if this element is not a String, Array, or Object
          && !this[i].isEmpty())) {
          // or this element is non-empty

      // negative response
      return false;
    }
  }

  // this array is empty of all values

  // positive response
  return true;
};

Array.prototype.pushOrExtend = function() {
  // push items of any type onto the end of this array
  //
  // if an argument is an array, extend this array with the argument array
  // - example: [1,2,3].pushOrExtend([4,5,6]) = [1,2,3,4,5,6]

  for (var i = 0; i < arguments.length; i++) {
    // traverse all arguments provided

    if (typeof(arguments[i]) == 'undefined' || arguments[i] === null) {
      continue;
    }

    // simplified naming of the current argument being looked at
    var ar = arguments[i];

    if (ar.constructor == Array) {
      // if the argument is an array

      for (var i = 0; i < ar.length; i++) {
        // traverse the elements in ar

        // pushOrExtend this array with the current element in ar
          this.pushOrExtend(ar[i]);
      }
    } else {
      // if the argument is not an array

      // create a new element on the end of this array equal to ar
      this[this.length] = ar;
    }
  }

  // return the extended array
  return this;
};

Array.prototype.pushOrExtendIfNew = function() {
  // push items of any type onto the end of this array, only if the item (or all
  // items in a flattened array) is not already in the flattened array
  //
  // - example: [1,2,3].pushOrExtendIfNew([2,3,4]) = [1,2,3,4]

  for (var i = 0; i < arguments.length; i++) {
    // traverse all arguments provided to be added to the array

    // set a simple reference to the current item
    var ar = arguments[i];

    if (typeof(ar) == 'undefined' || ar === null) {
      // invalid value

      // skip to the next argument
      continue;
    }

    if (ar.constructor == Array) {
      // current argument is an array

      // make sure the array is one dimensional
      ar.flatten();

      for (var j = 0; j < ar.length; j++) {
        // traverse all items in this argument array

        // create a copy of the current array, so we don't modify it
        var self = this;

        // make the copy one dimensional
        self.flatten();

        if (!self.contains(ar[j])) {
          // if the current item of the argument array isn't in this array

          // add the new item to this array
          this.pushOrExtend(ar[j]);
        }
      }
    } else {
      // the argument is not an array

      // create a copy of the current array, so we don't modify it
      var self = this;

      // make the copy one dimensional
      self.flatten();

      if (!self.contains(ar)) {
        // if the argument isn't in this array

        // add the new item to this array
        this.pushOrExtend(ar);
      }
    }
  }

  // return the extended array
  return this;
};

Array.prototype.toString = function() {
  // extract a string representation from an array

  // initialize the string
  var str = '\n[';

  for (var i = 0; i < this.length; i++) {
    // traverse array elements

    if (i > 0) {
      // if this is not the first element in the array

      // append a comma
      str += ',';
    }

    // append the string representation of this element to the array string
    str += '\n  ' + i + ' : ' + this[i];
  }

  // return the extracted string representation and closing bracket
  return str + '\n]';
};

Object.prototype.isEmpty = function() {
  // check to see if this object contains any non-empty values

  var base = {};

  if (this == base) {
    // this object contains no keys

    // positive response
    return true;
  }

  for (var p in this) {
    // traverse object properties

    if (this[p] &&
        // this property exists
        ( ( this[p].constructor != String && this[p].constructor != Array && this[p].constructor != Object )
          // if this property is not a String, Array, or Object
          || !this[p].isEmpty())) {
          // or this property is non-empty
      var inBase = false;
      for (var x in base) {
        // traverse elements in the base object) {
        if (p == x && this[p] == base[x]) {
          inBase = true;
          break;
        }
      }

      if (inBase) {
        // this is a base object property, so ignore it

        // continue with the next object property
        continue;
      }

      // this is a non-empty property

      // negative response
      return false;
    }
  }

  // this object is empty of all values

  // positive response
  return true;
};

/* used during development/debugging */
Object.prototype.toString = function(deep) {
  //
  var str = '\n{';

  for (var i in this) {
    if (i != 'isEmpty' && i != 'toString') {
      str += '\n  ' + i + ' : '
          + (typeof this[i] == 'object' && !deep ? '[object]' : this[i])
          + ',';
    }
  }

  // return
  return str.substring(0, (str.lastIndexOf(',') >= 0 ? str.lastIndexOf(',') : str.length)) + '\n}';
};
// */

String.prototype.isEmpty = function() {
  // check to see if this string contains any non-empty values

  if (this !== '') {
    // this is not an empty string

    // negative response
    return false;
  }

  // this string is empty

  // positive response
  return true;
};

var XinhaConfig = {
  // XinhaConfig object that creates a Xinha configuration using three standard
  // bases or any additional bases added to the object using the XinhaConfig
  // prototype

  empty : {
    charSet : 'ISO-8859-1',
    flowToolbars : false,
    height : '300px',
    pageStyle : '',
    pageStyleSheets : [],
    plugins : [
 'CharacterMap',
 'ContextMenu',
 'FullPage',
 'ImageManager',
 'ListType',
 'SpellChecker',
 'Stylist',
 'SuperClean',
 'TableOperations'
    ],
    showLoading : false,
    statusBar : false,
    toolbar : [
      ['about'],
      ['separator', 'popupeditor']
    ],
    width : '99%'
  },

  simple : {
    charSet : 'ISO-8859-1',
    flowToolbars : false,
    formatblock : {
      'Header 1' : 'h1',
      'Header 2' : 'h2',
      'Header 3' : 'h3',
      'Header 4' : 'h4',
      'Header 5' : 'h5',
      'Header 6' : 'h6',
      'Normal' : 'p'
    },
    height : '300px',
    pageStyle : '',
    pageStyleSheets : [],
    plugins : [
      'FindReplace',
      'FullPage',
      'HtmlEntities'
    ],
    showLoading : false,
    statusBar : true,
    toolbar : [
      ['about'],
      ['separator', 'popupeditor'],
      ['separator', 'formatblock', 'bold', 'italic'],
      ['separator', 'justifyleft', 'justifycenter', 'justifyright']
    ],
    width : '99%'
  },

  advanced : {
    charSet : 'utf8',
    flowToolbars : false,
    formatblock : {
      'Normal' : {tag: 'p',
                  invoker: function (xinha) {
                    var blockquote = xinha.getParentElement();
                    while (blockquote !== null && blockquote.tagName != 'BLOCKQUOTE')
                    {
                      blockquote = blockquote.parentNode;
                    }
                    if (blockquote)
                    {
                      var blockParent = blockquote.parentNode;
                      var firstChild = null;
                      while (blockquote.childNodes.length) {
                        if (firstChild === null)
                        {
                          firstChild = blockquote.childNodes[0];
                        }
                        blockParent.insertBefore(blockquote.childNodes[0], blockquote);
                      }
                      blockParent.removeChild(blockquote);
                      if (firstChild !== null)
                      {
                        // FIXME: this selects the entire first node, instead of just placing the
                        // cursor at the beginning (or at the previous location where the cursor was).
                        // Without this, the cursor hangs off to the side of the screen, where the
                        // blockquote once had been.
                        xinha.selectNodeContents(firstChild);
                      }
                    }
                    else
                    {
                      if( !Xinha.is_gecko)
                      {
                        xinha.execCommand('formatblock', false, '<p>');
                      }
                      else
                      {
                        xinha.execCommand('formatblock', false, 'p');
                      }                        
                    }
                  },
                  // always return false, to give others a chance to override
                  // if nobody else thinks they should be selected, then it will default
                  // to normal because it comes first
                  detect: function(xinha, el) { return false; }
                 },
      'Heading' : 'h2',
      'Subheading' : 'h3',
      'Pull-quote' : {tag: 'blockquote',
                      invoker: function (xinha) {
                        xinha.execCommand("formatblock", false, "blockquote");
                        var blockquote = xinha.getParentElement();
                        while (blockquote !== null && blockquote.tagName != 'BLOCKQUOTE') {
                          blockquote = blockquote.parentNode;
                        } 
                        if (blockquote)
                        {
                          Xinha.addClass(blockquote, "pullquote");
                        }
                        xinha.updateToolbar()
                      },
                      detect: function (xinha, el) {
                        while (el !== null) {
                          if (el.nodeType == 1 && el.tagName.toUpperCase() == 'BLOCKQUOTE') {
                            return /\bpullquote\b/.test(el.className);
                          }
                          el = el.parentNode;
                        }
                        return false;
                      }
                     }
    },
    filters : {
	'tidy_handler' : null
    },
    height : '600',
    ImageManager : { 
	'backend' : 'backend?'
    },
    pageStyle : '',
    pageStyleSheets : ['/++resource++css/themes/openplans.css', '/++resource++css/opencore.css'],
    plugins : [
      'ImageManager',
      'InternalLink',
      'GetHtml',
      'FullScreen'
      //'TableOperations'
      // remove spellchecker (don't have backend yet)
      //'SpellChecker'
    ],
    showLoading : false,
    statusBar : true,
    SuperClean : {
	'filters' : { 'tidy' : true },
	'show_dialog' : false
    },
    toolbar : [
        ["formatblock"],
        ["fontsize"],
        ["bold","italic","strikethrough"],
        ["forecolor","hilitecolor"],
        ["justifyleft","justifycenter","justifyright","justifyfull"],
        ["insertorderedlist","insertunorderedlist"],
        ["outdent","indent"],
        ["createinternallink"],
        ["inserttable"],
        ["toggleborders"],
        ["insertimage"],
        ["htmlmode"]
    ],
    width : '800'
  },

  advform : {
    charSet : 'ISO-8859-1',
    flowToolbars : false,
    formatblock : {
      'Header 1' : 'h1',
      'Header 2' : 'h2',
      'Header 3' : 'h3',
      'Header 4' : 'h4',
      'Header 5' : 'h5',
      'Header 6' : 'h6',
      'Normal' : 'p'
    },
    height : '300px',
    pageStyle : '',
    pageStyleSheets : [],
    plugins : [
      'FindReplace',
      'FullPage',
      'HtmlEntities',
      'Stylist',
      'TableOperations',
      'Forms'
    ],
    showLoading : false,
    statusBar : true,
    toolbar : [
      ['about'],
      ['separator', 'popupeditor'],
      ['separator', 'formatblock', 'bold', 'italic'],
      ['separator', 'justifyleft', 'justifycenter', 'justifyright'],
      ['linebreak', 'insertorderedlist', 'insertunorderedlist', 'outdent', 'indent'],
      ['separator', 'inserthorizontalrule', 'createlink'],
      ['separator', 'killword'],
      ['separator', 'htmlmode'],
      ['separator', 'insert_image', 'insertimage']
    ],
    width : '99%'
  },

  landscaper : {
    charSet : 'ISO-8859-1',
    flowToolbars : false,
    formatblock : {
      '&mdash; format &mdash;' : '',
      'Page Headline' : 'h2',
      'Subhead 1' : 'h3',
      'Subhead 2' : 'h4',
      'Subhead 3' : 'h5',
      'Subhead 4' : 'h6',
      'Normal':'p'
    },
    height : '400px',
    pageStyle : '',
    pageStyleSheets : [],
    plugins : [
      'CharacterMap',
      'FindReplace',
      'FullPage',
      'HtmlEntities',
      'ImageManager',
      'ListType',
      'HorizontalRule',
      'SpellChecker',
      'Stylist',
      'SuperClean',
      'TableOperations'
    ],
    showLoading : false,
    statusBar : true,
    toolbar : [
      ['about', 'showhelp'],
      ['separator', 'popupeditor'],
      ['separator', 'formatblock', 'bold', 'italic'],
      ['separator', 'cut', 'copy', 'paste'],
      ['separator', 'undo', 'redo'],
      ['separator', 'selectall'],
      ['separator', 'justifyleft', 'justifyright', 'justifycenter'],
      ['linebreak', 'insertorderedlist', 'insertunorderedlist'],
      ['separator', 'superscript', 'subscript'],
      ['separator', 'indent', 'outdent'],
      ['separator', 'inserthorizontalrule', 'createlink'],
      ['separator', 'killword'],
      ['separator', 'htmlmode'],
      ['separator', 'insert_image', 'insertimage']
    ],
    width : '99%'
  },

  create : function(obj) {
    return merge(new HTMLArea.Config(), obj, 0, true);
  }
};

function Editor(textarea) {
  // Editor: instantiable class for WYSIWYGs using Xinha

  // INITIAL VALIDATION CHECK

  if (textarea.constructor == String) {
    // if the textarea argument is a string

    if (!document.getElementById || !document.getElementById(textarea)) {
      // if the document object has no getElementById method, or there is no
      // element with an id as stored in the textarea argument

      // cannot proceed, so return a null object
      return null;
    }

    // get the textarea by the provided id string
    textarea = document.getElementById(textarea);
  }

  // OBJECT VARIABLE INITIALIZATION

  this.type = 'wysiwyg';
  this.element = textarea;
  this.element.editor = this;
  this.id = getAttributes('id', this.element).id;
  this.config = {};
  this.callbacks = getAttributes('callbacks', this.element).callbacks;
  this.started = false;
  this.pluginsReady = false;

  // PUBLIC METHODS

  this.performCallbacks = function() {
    // execute callback functions for this editor

    if (this.callbacks) {
      // if the callbacks property is a valid value

      if (typeof(this.callbacks) == 'function') {
        // if the callbacks property is a function

        // execute the callbacks
        this.callbacks();
      } else if (typeof(this.callbacks) == 'string') {
        // if the callbacks property is a string

        // evaluate the callbacks for execution
        this.callbackResult = eval(this.callbacks);

        if (this.callbackResult && typeof(this.callbackResult) == 'function') {
          // if the callbacks evaluation resulted in a function

          // execute the evaluated function
          this.callbackResult();
        }
      }
    }
  };

  this.pluginLoad = function(self) {
    if (!this && !self) {
      OC.debug("Editor object was not passed propertly");
      return;
    } else if (!self) {
      self = this;
    }

    if (!self.config || typeof(self.config.plugins) != 'object') {
      // there are no appropriate plugins
      OC.debug("There are no appropriate plugins");
      // halt processing
      return;
    }

    if (!HTMLArea.loadPlugins(self.config.plugins, function() { self.pluginLoad(self); })) {
      // the plugins couldn't be loaded on this pass, but the initialization will
      // automatically be called again after a timeout
         
      // halt processing of this pass
      return;
    }

    // the plugins were properly initialized

    // load the plugins
    HTMLArea.loadPlugins(self.config.plugins);

    self.editorInit();
  };

  this.editorInit = function() {
    this.config.editor = HTMLArea.makeEditors(
      [this.id],
      this.config,
      this.config.plugins
    );

    this.pluginsReady = true;
  };

  this.makeObject = function(src) {
    // create an object from a string

    // object base
    var obj = {};

    if (src && src.constructor && src.constructor == String) {
      // if the src provided is a string

      // remove wrapping curly brackets if they exist
      src = src.match(/^\{?([^{}]*)\}?$/)[1];

      if (!src) {
        // if no match was found, the src isn't a valid string
        // this should never be the case, because any string should match, but
        // just in case...
        return {};
      }

      // create an array of property:value pairs by splitting the src at commas
      var ar = src.split(',');

      for (var i = 0; i < ar.length; i++) {
        // traverse the array of property:value pair strings

        // split the property and value at the ':' separator;
        var tmp = ar[i].split(":");

        if (tmp.length != 2) {
          // if this string does not have both a property and a value

          continue;
        }

        // remove any extra single quotes from the values' start/end
        tmp[0] = tmp[0].match(/^'?([^']*)'?$/)[1];
        tmp[1] = tmp[1].match(/^'?([^']*)'?$/)[1];

        // set the object value
        if (tmp[0] && tmp[1] !== null) {
          obj[tmp[0]] = tmp[1];
        }
      }
    }

    return obj;
  };

  this.getArray = function(ar) {
    if (!ar || ar.constructor != Array || ar.isEmpty()) {
      // non-existent, not an array, or empty of values

      // return an empty array
      return [];
    }

    // array containing some value(s)

    // return original
    return ar;
  };

  this.getBoolean = function(val) {
    if (val == 'false') {
      return false;
    } else {
      return Boolean(val);
    }
  };

  // PROCESSING

  // attributes of the textarea to grab for configuration
  var attrs = [
    'base',
    'height',
    'width',
    'debug',
    'toolbar',
    'toolbarRemove',
    'plugins',
    'pluginsRemove',
    'pageStyle',
    'pageStyleSheets',
    'statusBar',
    'flowToolbars',
    'showLoading',
    'formatblock'
  ];

  // grab the attributes from the textarea
  var obj = getAttributes(attrs, this.element);

  // make sure the boolean values are in Boolean form
  obj.debug = this.getBoolean(obj.debug);
  obj.statusBar = this.getBoolean(obj.statusBar);
  obj.flowToolbars = this.getBoolean(obj.flowToolbars);
  obj.showLoading = this.getBoolean(obj.showLoading);

  // make sure the array values are in array form, separating individual items
  // at commas
  // BE CAREFUL WHEN CREATING FILES, BECAUSE SPACES AND INVALID CHARACTERS ARE
  // NOT STRIPPED IN THIS PROCESS!
  obj.toolbar = [obj.toolbar.split(',')];
  obj.toolbarRemove = obj.toolbarRemove.split(',');
  obj.plugins = obj.plugins.split(',');
  obj.pluginsRemove = obj.pluginsRemove.split(',');
  obj.pageStyleSheets = obj.pageStyleSheets.split(',');

  // make sure the object values are in object form, using the method of the
  // Editor class
  obj.formatblock = this.makeObject(obj.formatblock);

  // join configuration with that of the base

  merge(this.config, XinhaConfig[obj.base], -1, true);

  // join configuration with that from the textarea
  merge(this.config, obj, -1, true);

  // create a Xinha configuration using the method of the XinhaConfig class
  this.config = XinhaConfig.create(this.config);

  if (!this.config.formatblock || this.config.formatblock.isEmpty()) {
    // there is no valid formatblock configuration

    if (XinhaConfig[obj.base]
        && XinhaConfig[obj.base].formatblock
        && !XinhaConfig[obj.base].formatblock.isEmpty()) {
      // one is attached to the base, but was not merged
      // this is a special case, as merge() is intended to overwrite existing
      // items with empty ones, but we do not want that action for formatblock

      // copy the XinhaConfig base formatblock to this.config
      this.config.formatblock = XinhaConfig[obj.base].formatblock;

      // make sure formatblock is in the toolbar
      this.config.toolbar.pushOrExtendIfNew(['formatblock']);
    } else {
      // no formatblock should be added to the editor

      // remove the formatblock from the configuration, if it exists
      this.config = removeItemFromObject(this.config, 'formatblock');

      // remove the formatblock from the toolbar, if it exists
      this.config.toolbar = removeItemFromArray(this.config.toolbar, 'formatblock');
    }
  } else {
    // there is a valid formatblock configuration

    if (obj.formatblock && !obj.formatblock.isEmpty()) {
      // if the obj formatblock is non-empty

      // use the obj formatblock instead of merging with a XinhaConfig base
      this.config.formatblock = obj.formatblock;
    } else if (XinhaConfig[obj.base]
               && XinhaConfig[obj.base].formatblock
               && !XinhaConfig[obj.base].formatblock.isEmpty()) {
      // the obj formatblock is empty but the XinhaConfig base is non-empty

      // use the XinhaConfig base formatblock instead of merging with anything
      // this should be automatic in this case
      this.config.formatblock = XinhaConfig[obj.base].formatblock;
    }

    // make sure formatblock is in the toolbar
    this.config.toolbar.pushOrExtendIfNew(['formatblock']);
  }

  // make sure the plugins, toolbar, and pageStylesheets are an array, even if
  // it is empty []
  this.config.plugins = this.getArray(this.config.plugins);
  this.config.toolbar = [this.getArray(this.config.toolbar).flatten()];
  this.config.pageStyleSheets = this.getArray(this.config.pageStyleSheets);

  // remove omitted toolbar items
  var tmp = [], toolbar = this.config.toolbar[0];
  for (var i = 0; i < toolbar.length; i++) {
    if (!obj.toolbarRemove.contains(toolbar[i])) {
      if (toolbar[i] != 'separator') {
        tmp.pushOrExtendIfNew(toolbar[i]);
      } else {
        tmp.pushOrExtend(toolbar[i]);
      }
    }
  }
  this.config.toolbar = [tmp];

  // remove omitted plugin items
  tmp = [];
  for (var i = 0; i < this.config.plugins.length; i++) {
    if (!obj.pluginsRemove.contains(this.config.plugins[i])) {
      tmp.pushOrExtendIfNew(this.config.plugins[i]);
    }
  }
  this.config.plugins = tmp;

  addIscapeHelp(this);

  this.pluginLoad();

  // return the new Editor object
  return this;
}

function __get_wysiwygs() {
  var w = [];

  if (document.getElementsByTagName) {
    var ta = document.getElementsByTagName('textarea');

    for (var i = 0; i < ta.length; i++) {
      if (typeof(ta[i].editor_type) != 'string') {
        if (!ta[i].getAttribute
            || typeof(ta[i].getAttribute('editor-type')) != 'string'
            || ta[i].getAttribute('editor-type') != 'wysiwyg') {
          continue;
        } else {
          w[w.length] = ta[i];
        }
      } else {
        if (ta[i]['editor-type'] == 'wysiwyg') {
          w[w.length] = ta[i];
        }
      }
    }
  }

  return w;
}

function addIscapeImageInsert(editor) {
  editor.config.btnList.insert_image = [
    'Insert image from library',
    (typeof(ls_url) == 'string' && ls_url !== ''
      ? ls_url : '/admin/') + 'images/page_icons/image.gif',
    false,
    function (e) {
      MainEditor = e;
      var loc = window.location.href.match(/\/([^\/]*)\/page_edit/);
      var popup_url = '/'
        + (loc && loc[1] ? loc[1] : 'admin')
        + '/page_edit_library_popup?inctype=image'
        + '&callback_function=insertImageIntoTextarea'
        + '&section_id='+section_id;
      window.open(popup_url, '_blank');
    }
  ];

  editor.config.btnList.insertimage[0] = 'Modify Image';
}

function addIscapeHelp(editor) {
  if (typeof(xinha_help_url) == 'string' && xinha_help_url !== '') {
    editor.config.btnList.showhelp = [
      'Help using the Editor',
      ['/common/js/xinha-trunk/images/ed_buttons_main.gif', 9, 2],
      true,
      function (e) {
        window.open(xinha_help_url, 'support_full');
      }
    ];
  }
}

var _XC_delay_startup = true;
function _XC_startEditors(editors) {
  if (!editors || !editors.length) {
    // editor list not passed correctly,
    // or there are no editors to start

    // halt processing
    OC.debug("editor list not passed correctly");
    return;
  }

  var loaders = {};
  for (var i = 0; i < editors.length; i++) {
    if (editors[i].started) {
      continue;
    } else if (editors[i] && !editors[i].pluginsReady) {
      setTimeout(function() { _XC_startEditors(editors); }, 150);
      return;
    } else if (editors[i]) {
      if (_XC_delay_startup) {
        _XC_delay_startup = false;

        setTimeout(function() { _XC_startEditors(editors); }, 500);
        return;
      }

      merge(loaders, editors[i].config.editor, 0, true);

      editors[i].performCallbacks();

      editors[i].started = true;
    }
  }

  HTMLArea.startEditors(loaders);
}

var pre_wysiwyg_onload = window.onload;
window.onload = function() {
  if (pre_wysiwyg_onload) {
    pre_wysiwyg_onload();
  }

  var w = __get_wysiwygs();

  var editors = [];
  for (var i = 0; i < w.length; i++) {
    editors.pushOrExtendIfNew(new Editor(w[i]));
  }

  _XC_startEditors(editors);
};
