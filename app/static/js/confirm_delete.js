document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.delete-button').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            let bookTitle = this.getAttribute('data-book-title');
            let confirmDelete = confirm(`Вы уверены, что хотите удалить книгу "${bookTitle}"?`);
            if (confirmDelete) {
                this.closest('form').submit();
            }
        });
    });
});