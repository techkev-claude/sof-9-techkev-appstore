(function () {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file");
    const filenameDisplay = document.getElementById("filename-display");

    if (!dropzone || !fileInput) return;

    function showFilename() {
        if (fileInput.files.length > 0) {
            filenameDisplay.textContent = fileInput.files[0].name;
        }
    }

    fileInput.addEventListener("change", showFilename);

    ["dragenter", "dragover"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
        });
    });

    dropzone.addEventListener("drop", (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            showFilename();
        }
    });
})();
