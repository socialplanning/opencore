function toggle_editor(fieldname) {
    editor_elem = document.getElementById('wysiwygEditorBox');
    text_format = document.getElementById(fieldname+'_text_format');
    if (text_format.value == 'text/html') {
        editor_elem.style.display = 'block';
        window.kupu._setDesignMode()
    } else {
        editor_elem.style.display = 'none';
    }
}
