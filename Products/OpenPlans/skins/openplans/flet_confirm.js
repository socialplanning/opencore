function uncheckflet_confirmation(flet_id, flet_title)
{
    flet_box = document.getElementById(flet_id+'_checkbox');
    checked = flet_box.checked
    if (checked == false) {
        conf_msg = "Are you sure you want to unselect the '"+flet_title+"' " +
            "featurelet?  If you unselect this featurelet and then save " +
            "your changes, you will be removing features from your project " +
            "and (in some cases) irretrievably deleting archives and /or " +
            "content. To continue, please press the 'OK' button, otherwise " +
            "please press 'Cancel' to reselect the featurelet.";
        response = confirm(conf_msg);
        if (response != true) {
            flet_box.checked = true;
        }
    }
}
