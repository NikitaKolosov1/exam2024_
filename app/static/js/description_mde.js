try {
    document.getElementById('submit_button').addEventListener('click', function (e) {
        var descriptionValue = easymde.value();
        if (document.getElementById('description_area').value == '') {
            alert('Введите поле описание');
            easymde.codemirror.focus();
            e.preventDefault();
            return false;
        }
        document.getElementById('description_area').value = descriptionValue;
    });
} catch (e) {}

var easymde_editor = document.getElementById('description_area');
if (typeof (easymde_editor) != 'undefined' && easymde_editor != null) //редактор
{
    var easymde = new EasyMDE({
        element: document.getElementById("description_area"),
        forceSync: true,
    });

} else { // просмотр
    var easymde = new EasyMDE({
        element: document.getElementById("description_view"),
        toolbar: false,
        status: false,
        shortcuts: [],
        readOnly: true,
        previewImagesInEditor: true,
    });
    easymde.togglePreview();
}