document.addEventListener('DOMContentLoaded', () => {
  const uploadBox = document.getElementById('upload-box');
  const fileInput = document.getElementById('file-input');
  const dateInput = document.getElementById('date');
  const form = document.getElementById('upload-form');
  const preview = document.createElement('img');
  preview.style.maxWidth = '200px';
  preview.style.maxHeight = '200px';
  uploadBox.appendChild(preview);

  // Function to handle file drop
  function handleDrop(event) {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files.length) {
      fileInput.files = files;
      updatePreview(files[0]);
    }
  }

  // Function to update the image preview
  function updatePreview(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      preview.src = e.target.result;
      preview.alt = 'Preview';
    };
    reader.readAsDataURL(file);
  }

  // Function to handle file selection via the input
  fileInput.addEventListener('change', function() {
    if (this.files.length) {
      updatePreview(this.files[0]);
    }
  });

  // Function to handle drag over
  function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
  }

  // Attach event listeners
  uploadBox.addEventListener('dragover', handleDragOver, false);
  uploadBox.addEventListener('drop', handleDrop, false);

  // Form submission handler
  form.addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData(this);
    formData.append('date', dateInput.value); // Append the date to the FormData object

    // Perform the AJAX request
    fetch('/add_data_stamp', { // Replace with your actual endpoint
      method: 'POST',
      body: formData
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'downloaded_file.jpg'; // Set the filename for the download
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    })
    .catch(error => {
      console.error('Upload failed:', error);
      alert('An error occurred while uploading the file.');
    });
  });
});
