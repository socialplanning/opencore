// function to open the popup window
function referencebrowser_openBrowser(path, fieldName, at_url, fieldRealName)
{
    atrefpopup = window.open(path + '/referencebrowser_popup?fieldName=' + fieldName + '&fieldRealName=' + fieldRealName +'&at_url=' + at_url,'referencebrowser_popup','toolbar=no,location=no,status=no,menubar=no,scrollbars=yes,resizable=yes,width=500,height=550');
}

// function to return a reference from the popup window back into the widget
function referencebrowser_setReference(widget_id, uid, label, url, portal_type, multi)
{
    parent_div=document.getElementById(widget_id+'_wrapper');
    children=parent_div.childNodes;

    // check if the item isn't already in the list
    for (var x=0; x < children.length; x++) {
        if (children[x].nodeName != 'DIV') {
            continue;
        }
        subchildren=children[x].childNodes;
        for (var y=0; y < subchildren.length; y++) {
            if (subchildren[y].nodeName != 'INPUT') {
                continue;
            }
            if (subchildren[y].value == uid) {
                return false;
            }
        }
    }

    // now add the new item
    newdiv=document.createElement('div');
    newdiv.setAttribute('id', uid);
    newdiv.innerHTML='<input type="hidden" id="hid_'+uid+'" name="'+widget_id+':list" value="'+uid+'" /><input type="checkbox" id="cb_'+uid+'" value="'+uid+'" name="'+widget_id+'_del:list" />'+label+' <a href="'+url+'">(manage membership)</a>';
    parent_div.appendChild(newdiv);
    changed_field=document.getElementById(widget_id+'_changed');
    changed_field.setAttribute('value', 'yes');
}

// function to clear the reference field or remove items
function referencebrowser_removeReference(widget_id)
{
    parent_div=document.getElementById(widget_id+'_wrapper');
    children=parent_div.childNodes;

    // get the set of selected items; must step through
    // backwards or it will stop after the first removal
    for (var x=children.length-1; x >= 0; x--) {
        if (children[x].nodeName != 'DIV') {
            continue;
        }
        subchildren=children[x].childNodes
        for (var y=0; y < subchildren.length; y++) {
            if (subchildren[y].nodeName != 'INPUT' ||
                subchildren[y].type != 'checkbox') {
                continue;
            }
            if (subchildren[y].checked) {
                parent_div.removeChild(children[x]);
                changed_field=document.getElementById(widget_id+'_changed');
                changed_field.setAttribute('value', 'yes');
                break;
            }
        }
    }
}
