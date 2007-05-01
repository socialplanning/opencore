// function to open the popup window
function deletelist_openConfirmation(path, list_id)
{
    conf_msg = "Are you sure you want to delete the '"+list_id+"' " +
        "mailing list?  Doing so will cause the mailing list address to " +
        "quit working, and will irretrievably delete all list archives.  " +
        "To delete, please press the 'OK' button, otherwise please press " +
        "'Cancel'.";
    response = confirm(conf_msg);
    if (response==true) {
        confirm_input = document.getElementById(list_id+'_confirm_delete');
        confirm_input.setAttribute('value', 'true');
    }
}
