/** xinha - Internal Link plugin, based on James Fork / James Sleeman - Linker Plugin **/
InternalLink._pluginInfo =
{
  name     : "InternalLink",
  version  : "1.0",
  developer: "David Turner",
  developer_url: "http://topp.openplans.org",
  c_owner      : "The Open Planning Project",
  license      : "htmlArea",
  sponsor      : "The Open Planning Project",
  sponsor_url  : "http://topp.openplans.org"
};

Xinha.loadStyle('dTree/dtree.css', 'InternalLink');

Xinha.Config.prototype.InternalLink = 
{
  'treeCaption' : document.location.host,
  'backend' : 'internal-link',
  'backend_data' : null,
  'files' : null
};


function InternalLink(editor, args)
{
  this.editor  = editor;
  this.lConfig = editor.config.InternalLink;

  var linker = this;
  editor.config.registerButton(
			       'createinternallink', 'Link to Internal Page', [_editor_url + "images/ed_buttons_main.gif",7,1], false,
			       function(e, objname, obj) { linker._createLink(linker._getSelectedAnchor()); }
			       );

  // See if we can find 'createlink'
 editor.config.addToolbarElement("createinternallink", "createlink", 1);
}

InternalLink.prototype._lc = function(string)
{
  return Xinha._lc(string, 'InternalLink');
};

InternalLink.prototype._createLink = function(a)
{
  if(!a && this.editor.selectionEmpty(this.editor.getSelection()))
  {       
    alert(this._lc("You must select some text before making a new link."));
    return false;
  }

  var inputs =
  {
    type:     'url',
    href:     'http://www.example.com/',
    target:   '',
    p_width:  '',
    p_height: '',
    p_options: ['menubar=no','toolbar=yes','location=no','status=no','scrollbars=yes','resizeable=yes']
  };

  if(a && a.tagName.toLowerCase() == 'a')
  {
    var href =this.editor.fixRelativeLinks(a.getAttribute('href'));
    if(a.getAttribute('onclick'))
      {
        var m = a.getAttribute('onclick').match(/window\.open\(\s*this\.href\s*,\s*'([a-z0-9_]*)'\s*,\s*'([a-z0-9_=,]*)'\s*\)/i);

        // Popup Window
        inputs.href   = href ? href : '';
        inputs.target = 'popup';
        inputs.p_name = m[1];
        inputs.p_options = [ ];


        var args = m[2].split(',');
        for(var x = 0; x < args.length; x++)
        {
          var i = args[x].match(/(width|height)=([0-9]+)/);
          if(i)
          {
            inputs['p_' + i[1]] = parseInt(i[2]);
          }
          else
          {
            inputs.p_options.push(args[x]);
          }
        }
      }
    else 
      {
        // Normal
        inputs.href   = href;
        inputs.target = a.target;
      }
    }


  var linker = this;

  // If we are not editing a link, then we need to insert links now using execCommand
  // because for some reason IE is losing the selection between now and when doOK is
  // complete.  I guess because we are defocusing the iframe when we click stuff in the
  // linker dialog.

  this.a = a; // Why doesn't a get into the closure below, but if I set it as a property then it's fine?

  var doOK = function()
  {
    //if(linker.a) alert(linker.a.tagName);
    var a = linker.a;

    var values = linker._dialog.hide();
    var atr =
    {
      href: '',
      target:'',
      title:'',
      onclick:''
    };

    if(values.href)
     {
       atr.href = values.href;
       atr.target = values.target;
       if(values.target == 'popup')
       {

         if(values.p_width)
         {
           values.p_options.push('width=' + values.p_width);
         }
         if(values.p_height)
         {
           values.p_options.push('height=' + values.p_height);
         }
         atr.onclick = 'try{if(document.designMode && document.designMode == \'on\') return false;}catch(e){} window.open(this.href, \'' + (values.p_name.replace(/[^a-z0-9_]/i, '_')) + '\', \'' + values.p_options.join(',') + '\');return false;';
       }
     }

    if(a && a.tagName.toLowerCase() == 'a')
    {
      if(!atr.href)
      {
        if(confirm(linker._dialog._lc('Are you sure you wish to remove this link?')))
        {
          var p = a.parentNode;
          while(a.hasChildNodes())
          {
            p.insertBefore(a.removeChild(a.childNodes[0]), a);
          }
          p.removeChild(a);
          linker.editor.updateToolbar();
          return;
        }
      }
      else
      {
        // Update the link
        for(var i in atr)
        {
          a.setAttribute(i, atr[i]);
        }
        
      }
    }
    else
    {
      if(!atr.href) return true;

      // Insert a link, we let the browser do this, we figure it knows best
      var tmp = Xinha.uniq('http://www.example.com/Link');
      linker.editor._doc.execCommand('createlink', false, tmp);

      // Fix them up
      var anchors = linker.editor._doc.getElementsByTagName('a');
      for(var i = 0; i < anchors.length; i++)
      {
        var anchor = anchors[i];
        if(anchor.href == tmp)
        {
          // Found one.
          if (!a) a = anchor;
          for(var j in atr)
          {
            anchor.setAttribute(j, atr[j]);
          }
        }
      }
    }
    linker.editor.selectNodeContents(a);
    linker.editor.updateToolbar();
  };

  this._dialog.show(inputs, doOK);

};

InternalLink.prototype._getSelectedAnchor = function()
{
  var sel  = this.editor.getSelection();
  var rng  = this.editor.createRange(sel);
  var a    = this.editor.activeElement(sel);
  if(a != null && a.tagName.toLowerCase() == 'a')
  {
    return a;
  }
  else
  {
    a = this.editor._getFirstAncestor(sel, 'a');
    if(a != null)
    {
      return a;
    }
  }
  return null;
};

InternalLink.prototype.onGenerateOnce = function()
{
  this._dialog = new InternalLink.Dialog(this);
};
// Inline Dialog for InternalLink

InternalLink.Dialog_dTrees = [ ];


InternalLink.Dialog = function (linker)
{
  var  lDialog = this;
  this.Dialog_nxtid = 0;
  this.linker = linker;
  this.id = { }; // This will be filled below with a replace, nifty

  this.ready = false;
  this.files  = false;
  this.html   = false;
  this.dialog = false;

  // load the dTree script
  this._prepareDialog();

};

InternalLink.Dialog.prototype._prepareDialog = function()
{
  var lDialog = this;
  var linker = this.linker;

  // We load some stuff up int he background, recalling this function
  // when they have loaded.  This is to keep the editor responsive while
  // we prepare the dialog.
  if(typeof dTree == 'undefined')
  {
    Xinha._loadback(_editor_url + 'plugins/InternalLink/dTree/dtree.js',
                       function() {lDialog._prepareDialog(); }
                      );
    return;
  }

  if(this.files == false)
  {
    if(linker.lConfig.backend)
    {
        //get files from backend
        Xinha._postback(linker.lConfig.backend,
                          linker.lConfig.backend_data,
                          function(txt) {
                            try {
                                lDialog.files = eval(txt);
                            } catch(Error) {
                                lDialog.files = [ {url:'',title:Error.toString()} ];
                            }
                            lDialog._prepareDialog(); });
    }
    else if(linker.lConfig.files != null)
    {
        //get files from plugin-config
        lDialog.files = linker.lConfig.files;
        lDialog._prepareDialog();
    }
    return;
  }
  var files = this.files;

  if(this.html == false)
  {
    Xinha._getback(_editor_url + 'plugins/InternalLink/dialog.html', function(txt) { lDialog.html = txt; lDialog._prepareDialog(); });
    return;
  }
  var html = this.html;

  // Now we have everything we need, so we can build the dialog.
  this.dialog = new Xinha.Dialog(linker.editor, this.html, 'InternalLink');
  var dialog = this.dialog;
  var dTreeName = Xinha.uniq('dTree_');

  this.dTree = new dTree(dTreeName, _editor_url + 'plugins/InternalLink/dTree/');
  eval(dTreeName + ' = this.dTree');

  this.dTree.add(this.Dialog_nxtid++, -1, linker.lConfig.treeCaption , null, linker.lConfig.treeCaption);
  this.makeNodes(files, 0);

  // Put it in
  var ddTree = this.dialog.getElementById('dTree');
  //ddTree.innerHTML = this.dTree.toString();
  ddTree.innerHTML = '';
  ddTree.style.position = 'absolute';
  ddTree.style.left = 1 + 'px';
  ddTree.style.top =  0 + 'px';
  ddTree.style.overflow = 'auto';
  ddTree.style.backgroundColor = 'white';
  this.ddTree = ddTree;
  this.dTree._linker_premade = this.dTree.toString();

  var options = this.dialog.getElementById('options');
  options.style.position = 'absolute';
  options.style.top      = 0   + 'px';
  options.style.right    = 0   + 'px';
  options.style.width    = 320 + 'px';
  options.style.overflow = 'auto';

  // Hookup the resizer
  this.dialog.onresize = function()
    {
      var h = parseInt(dialog.height) - dialog.getElementById('h1').offsetHeight;
      var w = parseInt(dialog.width)  - 322 ;
      // An error is thrown with IE when trying to set a negative width or a negative height
      // But perhaps a width / height of 0 is not the minimum required we need to set
      if (w<0) w = 0;
      if (h<0) h = 0;
      options.style.height = ddTree.style.height = h + 'px';
      ddTree.style.width  = w + 'px';
    };

  this.ready = true;
};

InternalLink.Dialog.prototype.makeNodes = function(files, parent)
{
  var id;
  var link;
  var title;
  for(var i = 0; i < files.length; i++)
  {
    if(typeof files[i] == 'string')
    {
      this.dTree.add(InternalLink.nxtid++, parent,
                     files[i].replace(/^.*\//, ''),
                     'javascript:document.getElementsByName(\'' + this.dialog.id.href + '\')[0].value=decodeURIComponent(\'' + encodeURIComponent(files[i]) + '\');document.getElementsByName(\'' + this.dialog.id.href + '\')[0].focus();void(0);',
                     files[i]);
    }
    else if(files[i].length)
    {
      id = this.Dialog_nxtid++;
      this.dTree.add(id, parent, files[i][0].replace(/^.*\//, ''), null, files[i][0]);
      this.makeNodes(files[i][1], id);
    }
    else if(typeof files[i] == 'object')
    {
      if(files[i].children) {
        id = this.Dialog_nxtid++;
      } else {
        id = InternalLink.nxtid++;
      }

      if(files[i].title) title = files[i].title;
      else if(files[i].url) title = files[i].url.replace(/^.*\//, '');
      else title = "no title defined";

      if(files[i].url) link = 'javascript:document.getElementsByName(\'' + this.dialog.id.href + '\')[0].value=decodeURIComponent(\'' + encodeURIComponent(files[i].url) + '\');document.getElementsByName(\'' + this.dialog.id.href + '\')[0].focus();void(0);';
      else link = '';
      
      this.dTree.add(id, parent, title, link, title);
      if(files[i].children) {
        this.makeNodes(files[i].children, id);
      }
    }
  }
};

InternalLink.Dialog.prototype._lc = InternalLink.prototype._lc;

InternalLink.Dialog.prototype.show = function(inputs, ok, cancel)
{
  if(!this.ready)
  {
    var lDialog = this;
    window.setTimeout(function() {lDialog.show(inputs,ok,cancel);},100);
    return;
  }

  if(this.ddTree.innerHTML == '')
  {
    this.ddTree.innerHTML = this.dTree._linker_premade;
  }
  if(inputs.target=='popup')
  {
    this.dialog.getElementById('popuptable').style.display = '';
  }
  else
  {
    this.dialog.getElementById('popuptable').style.display = 'none';
  }
  
  var html = this.linker.editor.getHTML();  
  
  // if we're not editing an existing link, hide the remove link button
  if (inputs.href == 'http://www.example.com/' && inputs.to == 'alice@example.com') { 
    this.dialog.getElementById('clear').style.display = "none";
  }
  else {
    this.dialog.getElementById('clear').style.display = "";
  }
  // Connect the OK and Cancel buttons
  var dialog = this.dialog;
  var lDialog = this;
  if(ok)
  {
    this.dialog.getElementById('ok').onclick = ok;
  }
  else
  {
    this.dialog.getElementById('ok').onclick = function() {lDialog.hide();};
  }

  if(cancel)
  {
    this.dialog.getElementById('cancel').onclick = cancel;
  }
  else
  {
    this.dialog.getElementById('cancel').onclick = function() { lDialog.hide();};
  }

  // Show the dialog
  this.linker.editor.disableToolbar(['fullscreen','internal-link']);

  this.dialog.show(inputs);

  // Init the sizes
  this.dialog.onresize();
};

InternalLink.Dialog.prototype.hide = function()
{
  this.linker.editor.enableToolbar();
  return this.dialog.hide();
};
