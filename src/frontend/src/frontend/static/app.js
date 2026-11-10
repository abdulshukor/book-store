(() => {
  'use strict';
  const bookDialog = document.getElementById('book-dialog');
  const deleteDialog = document.getElementById('delete-dialog');
  const bookForm = document.getElementById('book-form');
  const deleteForm = document.getElementById('delete-form');
  if (!bookDialog || !bookForm || !deleteDialog || !deleteForm) return;

  const addUrl = bookForm.action;
  const setField = (name, value) => {
    const input = bookForm.elements.namedItem(name);
    if (input) input.value = value ?? '';
  };

  function openAdd() {
    bookForm.reset();
    bookForm.action = addUrl;
    document.getElementById('book-dialog-title').textContent = 'Add a new book';
    document.getElementById('book-dialog-eyebrow').textContent = 'A NEW CHAPTER';
    document.getElementById('save-book-button').innerHTML = 'Add book <svg class="icon"><use href="#i-arrow"/></svg>';
    bookDialog.showModal();
    document.getElementById('book-title').focus();
  }

  function openEdit(book) {
    bookForm.reset();
    bookForm.action = `/books/${encodeURIComponent(book.id)}/edit`;
    for (const name of ['title', 'author', 'genre', 'isbn', 'price', 'quantity', 'description']) {
      setField(name, book[name]);
    }
    document.getElementById('book-dialog-title').textContent = 'Edit book details';
    document.getElementById('book-dialog-eyebrow').textContent = 'MAKE IT JUST RIGHT';
    document.getElementById('save-book-button').innerHTML = 'Save changes <svg class="icon"><use href="#i-check"/></svg>';
    bookDialog.showModal();
    document.getElementById('book-title').focus();
  }

  function openDelete(id, title) {
    deleteForm.action = `/books/${encodeURIComponent(id)}/delete`;
    document.getElementById('delete-book-name').textContent = `“${title}”`;
    deleteDialog.showModal();
  }

  document.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-action], button[data-close]');
    if (!button) return;
    if (button.dataset.close) {
      document.getElementById(button.dataset.close)?.close();
      return;
    }
    if (button.dataset.action === 'add') openAdd();
    if (button.dataset.action === 'edit') {
      try { openEdit(JSON.parse(button.dataset.book)); }
      catch (error) { console.error('Unable to open book editor', error); }
    }
    if (button.dataset.action === 'delete') openDelete(button.dataset.id, button.dataset.title);
  });

  // Native dialogs also close on Escape; clicking their dimmed backdrop closes them.
  for (const dialog of [bookDialog, deleteDialog]) {
    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) dialog.close();
    });
  }
})();
