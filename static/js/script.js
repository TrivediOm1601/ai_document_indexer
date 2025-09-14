document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  if (!form) return;
  const fileInput = form.querySelector('input[type="file"]');
  const progressBar = document.createElement('div');
  progressBar.className = 'progress mt-3';
  const bar = document.createElement('div');
  bar.className = 'progress-bar';
  bar.setAttribute('role', 'progressbar');
  progressBar.appendChild(bar);
  form.appendChild(progressBar);

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!fileInput.files.length) {
      alert('Please select a file.');
      return;
    }
    const file = fileInput.files[0];
    const xhr = new XMLHttpRequest();
    xhr.open('POST', form.action, true);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

    xhr.upload.onprogress = function (e) {
      if (e.lengthComputable) {
        const percent = (e.loaded / e.total) * 100;
        bar.style.width = percent + '%';
        bar.textContent = Math.floor(percent) + '%';
      }
    };

    xhr.onload = function () {
      if (xhr.status === 200) {
        window.location.reload();
      } else {
        alert('Upload failed.');
      }
    };

    const formData = new FormData();
    formData.append(fileInput.name, file);
    xhr.send(formData);
  });
});

// AJAX dashboard filter
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.querySelector('#dashboard-search');
  if (!searchInput) return;
  const tableBody = document.querySelector('table tbody');

  searchInput.addEventListener('input', () => {
    const filter = searchInput.value.toLowerCase();
    for (const row of tableBody.rows) {
      const title = row.cells[0].textContent.toLowerCase();
      const category = row.cells[1].textContent.toLowerCase();
      if (title.includes(filter) || category.includes(filter)) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    }
  });
});